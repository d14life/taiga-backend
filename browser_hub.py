"""Серверный агентный браузер (Playwright/Chromium) для in-chat браузера Тайги.

Идея: ОДИН воркер-поток держит Chromium и обрабатывает команды из очереди — так
Playwright (sync API) всегда работает на одном потоке, а HTTP-хендлеры просто кладут
команду и ждут результат. Сессия = страница на юзера (через browser contexts).
ИИ и юзер видят один и тот же снимок (screenshot + читаемый текст + ссылки), оба могут
действовать. Playwright грузится ЛЕНИВО — импорт этого модуля никогда не валит сервер.
"""
import threading
import queue
import base64
import time

try:
    from guard import redact_secrets
except Exception:
    def redact_secrets(s):
        return s

_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/123.0 Safari/537.36")

IDLE_SEC = 600        # неактивная браузер-сессия закрывается через 10 мин
MAX_SESSIONS = 4      # лимит одновременных Chromium-контекстов (ресурс)


def _normalize_cookies(items) -> list:
    """JSON-куки (экспорт расширений) → формат Playwright."""
    out = []
    for c in items or []:
        if not isinstance(c, dict) or not c.get("name") or not c.get("domain"):
            continue
        nc = {"name": c["name"], "value": c.get("value", ""),
              "domain": c["domain"], "path": c.get("path") or "/",
              "secure": bool(c.get("secure")), "httpOnly": bool(c.get("httpOnly"))}
        exp = c.get("expires") or c.get("expirationDate")
        if exp:
            try:
                nc["expires"] = float(exp)
            except Exception:
                pass
        ss = c.get("sameSite")
        if isinstance(ss, str) and ss.capitalize() in ("Strict", "Lax", "None"):
            nc["sameSite"] = ss.capitalize()
        out.append(nc)
    return out


def _parse_cookies_txt(raw: str) -> list:
    """Netscape cookies.txt (экспорт «Get cookies.txt LOCALLY») → формат Playwright."""
    out = []
    for line in (raw or "").splitlines():
        http_only = False
        if line.startswith("#HttpOnly_"):
            http_only = True
            line = line[len("#HttpOnly_"):]
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 7:
            continue
        domain, _sub, path, secure, expiry, name, value = parts[:7]
        c = {"name": name, "value": value, "domain": domain, "path": path or "/",
             "secure": secure.strip().upper() == "TRUE", "httpOnly": http_only}
        try:
            e = float(expiry)
            if e > 0:
                c["expires"] = e
        except Exception:
            pass
        out.append(c)
    return out


def parse_cookies(raw) -> list:
    """Принимает: список Playwright-куки · JSON-экспорт · текст cookies.txt — всё → Playwright."""
    if isinstance(raw, list):
        return _normalize_cookies(raw)
    s = str(raw or "").strip()
    if not s:
        return []
    if s[0] in "[{":
        try:
            import json as _json
            data = _json.loads(s)
            if isinstance(data, dict):
                data = data.get("cookies") or [data]
            return _normalize_cookies(data)
        except Exception:
            pass
    return _parse_cookies_txt(s)


class _BrowserHub:
    def __init__(self):
        self._q = queue.Queue()
        self._worker = None
        self._lock = threading.Lock()
        self._ready_err = None
        self._browser = None
        self._pw = None
        self._pages = {}          # uid -> (context, page)
        self._last = {}           # uid -> last_used_epoch (для idle-очистки)

    # ---- публичный API (вызывается из любого потока) ----
    def submit(self, cmd: str, timeout: float = 90, **args) -> dict:
        self._ensure_worker()
        if self._ready_err:
            return {"error": f"браузер не запустился: {self._ready_err}"}
        ev = threading.Event()
        box = {}
        self._q.put((cmd, args, ev, box))
        if not ev.wait(timeout=timeout):
            return {"error": "браузер: таймаут операции"}
        return box.get("result") if box.get("result") is not None else {"error": box.get("error") or "сбой"}

    # ---- внутреннее ----
    def _ensure_worker(self):
        with self._lock:
            if self._worker is None:
                self._worker = threading.Thread(target=self._run, daemon=True)
                self._worker.start()

    def _run(self):
        try:
            from playwright.sync_api import sync_playwright
            self._pw = sync_playwright().start()
            self._browser = self._pw.chromium.launch(headless=True, args=["--no-sandbox"])
        except Exception as e:
            self._ready_err = str(e)
            return
        while True:
            cmd, args, ev, box = self._q.get()
            try:
                box["result"] = getattr(self, "_do_" + cmd)(**args)
            except Exception as e:
                box["error"] = str(e)
            finally:
                ev.set()

    def _page(self, uid: str):
        uid = uid or "default"
        if uid not in self._pages:
            ctx = self._browser.new_context(viewport={"width": 1280, "height": 800}, user_agent=_UA)
            self._pages[uid] = (ctx, ctx.new_page())
        self._last[uid] = time.time()
        return self._pages[uid][1]

    def _close_uid(self, uid):
        ctx, _ = self._pages.pop(uid, (None, None))
        if ctx:
            try:
                ctx.close()
            except Exception:
                pass
        self._last.pop(uid, None)

    def _cleanup(self):
        """Закрыть простаивающие (>IDLE_SEC) и лишние (>MAX_SESSIONS) браузер-сессии."""
        now = time.time()
        for u in list(self._pages):
            if now - self._last.get(u, now) > IDLE_SEC:
                self._close_uid(u)
        while len(self._pages) > MAX_SESSIONS:
            self._close_uid(min(self._pages, key=lambda u: self._last.get(u, 0)))

    def _snapshot(self, page) -> dict:
        png = page.screenshot(full_page=False)
        text, links = "", []
        try:
            text = page.evaluate("() => (document.body && document.body.innerText || '').slice(0, 6000)")
            links = page.evaluate(
                "() => [...document.querySelectorAll('a[href]')].slice(0,40)"
                ".map(a=>({t:(a.innerText||'').trim().slice(0,80), href:a.href}))"
                ".filter(l=>l.t && l.href.startsWith('http'))")
        except Exception:
            pass
        text = redact_secrets(text)                 # режем секреты ДО показа ИИ/юзеру
        for l in links:
            l["t"] = redact_secrets(l.get("t", ""))
        return {
            "screenshot": "data:image/png;base64," + base64.b64encode(png).decode(),
            "title": page.title(), "url": page.url, "text": text, "links": links,
        }

    def _do_open(self, uid=None, url="", cookies=None):
        self._cleanup()                             # закрыть простаивающие/лишние сессии
        page = self._page(uid)
        if cookies:                                 # браузить под логином юзера (его cookies)
            try:
                ck = parse_cookies(cookies)         # cookies.txt / JSON / list → Playwright
                if ck:
                    self._pages[uid or "default"][0].add_cookies(ck)
            except Exception:
                pass
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        # SSRF-страж: резолвим хост, блокируем loopback/private/link-local(169.254 metadata)/reserved
        try:
            import ipaddress as _ip, socket as _sock
            from urllib.parse import urlparse as _up
            _h = _up(url).hostname or ""
            _bad = not _h
            for _inf in (_sock.getaddrinfo(_h, None) if _h else []):
                _a = _ip.ip_address(_inf[4][0])
                if (_a.is_loopback or _a.is_private or _a.is_link_local or _a.is_reserved
                        or _a.is_multicast or _a.is_unspecified):
                    _bad = True
                    break
            if _bad:
                return {"error": "URL заблокирован (приватный/loopback/metadata — SSRF-защита)", "url": url}
        except Exception:
            return {"error": "URL не разрешён (SSRF-защита)", "url": url}
        page.goto(url, timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(500)
        return self._snapshot(page)

    def _do_act(self, uid=None, action="", x=None, y=None, text=None, selector=None):
        page = self._page(uid)
        if action == "click":
            if selector:
                page.click(selector, timeout=8000)
            elif x is not None and y is not None:
                page.mouse.click(float(x), float(y))
        elif action == "type":
            if selector:
                page.fill(selector, text or "")
            else:
                page.keyboard.type(text or "")
        elif action == "scroll":
            page.mouse.wheel(0, int(y or 600))
        elif action == "back":
            page.go_back(timeout=15000)
        elif action == "enter":
            page.keyboard.press("Enter")
        else:
            return {"error": f"неизвестное действие: {action}"}
        page.wait_for_timeout(800)
        return self._snapshot(page)

    def _do_close(self, uid=None):
        self._close_uid(uid or "default")
        return {"ok": True}


BROWSER = _BrowserHub()
