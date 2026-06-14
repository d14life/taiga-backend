"""L12 — FULL SKILLS: «вставь GitHub Claude-Code-навык → ЛЮБАЯ модель пользуется им как Claude Code».

Расширяет существующий импорт навыков (install_skill_from_url тянул ТОЛЬКО текст SKILL.md):
  1. WHOLE-FOLDER импорт — SKILL.md + bundled scripts/ + resources/, в стор сервера на аккаунт
     (user_dir(uid)/skills/<name>/), с КАПом общего размера (≤2МБ). Скачанное НЕ исполняется при импорте.
  2. RUN bundled-скриптов — БЕЗОПАСНО ГЕЙТИТСЯ (ARCH-DECISIONS «никогда на голом бэкенде»):
       • владельцу — прямой запуск через переданный code-runner (owner-gated, как run_code);
       • юзеру — отдаём текст скрипта + runtime:"browser-wasm" → фронт крутит его в Pyodide в своей вкладке;
       • тяжёлый/cloud-sandbox путь = TODO-заглушка (отложенная инфра), на сервере НЕ гоняем.
  3. AUTO-TRIGGER — в обычном чате матчим сообщение юзера на описания установленных навыков
     (дешёвый keyword/overlap-матч) и инжектим SKILL.md в системный промпт (как харнес).
  4. MODEL-AGNOSTIC — инжект инструкций SKILL.md + экспонирование run-скрипта тулзой → GPT/Gemini/
     DeepSeek следуют Claude-формату навыков так же, как Claude Code.

МЕРЖ-БЕЗОПАСНО: вся логика тут; server.py только импортирует и зовёт. Зависимости (user_dir, SSRF-фетчер,
github-tree, store-helpers) приходят ПАРАМЕТРАМИ из server.py — модуль не дёргает приватные имена напрямую.
"""

import json
import re
import os
import threading
import time as _time
from pathlib import Path

# Анализатор возможностей навыка (Lane A, repo-root) — статический, НЕ исполняет навык.
# Мягкая зависимость: если файла нет/ошибка импорта — деградируем (badge="unsupported").
try:
    import skill_caps as _skill_caps
except Exception:
    _skill_caps = None


def _analyze_caps(skill_dir):
    """Прогнать static-анализатор по фолдеру навыка → (caps_dict, badge).
    Fail-soft: ЛЮБАЯ ошибка → ({}, "unsupported"); импорт навыка НИКОГДА не падает из-за анализа."""
    if _skill_caps is None:
        return {}, "unsupported"
    try:
        res = _skill_caps.analyze_skill(str(skill_dir))
        if not isinstance(res, dict):
            return {}, "unsupported"
        badge = res.pop("badge", None) or "unsupported"
        return res, badge
    except Exception:
        return {}, "unsupported"


def _caps_summary(caps):
    """Короткая человекочитаемая сводка caps для панели (без полного словаря).
    Возвращает {language, packages[], needs[], media[], claude} — компактно для фронта."""
    caps = caps or {}
    needs = [k.split("needs_", 1)[1] for k in (
        "needs_argv", "needs_resources", "needs_shell", "needs_network", "needs_node")
        if caps.get(k)]
    return {
        "language": caps.get("language", "none"),
        "packages": list(caps.get("third_party_packages") or [])[:12],
        "needs": needs,
        "media": list(caps.get("media_verbs") or [])[:6],
        "claude": bool(caps.get("claude_authored")),
    }

# ── Капы (анти-DoS / анти-abuse) ──
FOLDER_MAX_BYTES = 2 * 1024 * 1024      # ≤2МБ на весь навык-фолдер (Damir: «cap total size e.g. ≤2MB»)
FOLDER_MAX_FILES = 60                   # потолок числа файлов в одном навыке
FILE_MAX_BYTES = 512 * 1024            # один бандл-файл (скрипт/ресурс)
SCRIPT_EXTS = (".py", ".js", ".mjs", ".sh", ".bash")
# что вообще тянем в фолдер навыка (текст-инструкции + скрипты + лёгкие ресурсы)
BUNDLE_EXTS = SCRIPT_EXTS + (".md", ".txt", ".json", ".yaml", ".yml", ".csv", ".toml", ".cfg")
AUTO_TRIGGER_MAX = 2                    # сколько навыков max авто-инжектим за сообщение (не раздуваем промпт)


def _slug(name: str) -> str:
    return (re.sub(r"[^a-z0-9_-]", "", str(name or "").lower().replace(" ", "-"))[:60]
            or "skill")


def _skill_dir(user_dir, uid: str, sid: str) -> Path:
    return user_dir(uid) / "skills" / "_folders" / _slug(sid)


def _lang_for(path: str) -> str:
    p = path.lower()
    if p.endswith(".py"):
        return "python"
    if p.endswith((".js", ".mjs")):
        return "js"
    if p.endswith((".sh", ".bash")):
        return "bash"
    return "text"


# ───────────────────────────── 1. WHOLE-FOLDER IMPORT ─────────────────────────────

def import_skill_folder(uid, url, *, user_dir, parse_github_repo_url, github_trees,
                        fetch_text_guarded, parse_skill, store_user_skill, token=""):
    """Импортировать ВЕСЬ навык-фолдер из GitHub (SKILL.md + scripts/ + resources/).

    Берём ссылку на репо/папку навыка, через trees API находим SKILL.md, тянем его + все соседние
    бандл-файлы из ТОЙ ЖЕ директории (и подпапок scripts/ resources/ assets/), складываем фолдер
    server-side: user_dir(uid)/skills/_folders/<slug>/ + регистрируем в личном индексе (store_user_skill,
    чтобы навык виден в поиске/обзоре, как и текстовые). Возвращает {ok, skill, files, bytes,...}.

    Скачанное НЕ исполняется — только сохраняется. Все фетчи идут через тот же SSRF-страж сервера.
    """
    parsed = parse_github_repo_url(url)
    if not parsed:
        # не репо-ссылка — фолбэк на одиночный SKILL.md по прямой ссылке (текст-навык)
        text, err = fetch_text_guarded(url, token=token)
        if err:
            return {"ok": False, "error": err}
        name, desc, body = parse_skill(text)
        if not name:
            h = re.search(r"^#\s+(.+)$", text, re.M)
            name = h.group(1).strip() if h else "skill"
        sk = store_user_skill(uid, name, desc, body, source_url=url)
        return {"ok": True, "skill": sk, "files": ["SKILL.md"], "bytes": len(body.encode("utf-8")),
                "folder": False, "note": "одиночный SKILL.md (не репозиторий)"}

    owner, repo, branch, subpath = parsed
    branches = [branch] if branch else ["main", "master"]
    paths, used_branch, err = None, None, "ветка не найдена"
    for b in branches:
        paths, e = github_trees(owner, repo, b, token=token)
        if paths is not None:
            used_branch, err = b, None
            break
        err = e
    if paths is None:
        return {"ok": False, "error": err or "не удалось получить дерево репозитория"}

    # найти SKILL.md (внутри subpath, если задан) — это «корень» навыка
    def _in_scope(p):
        return not subpath or p == subpath or p.startswith(subpath.rstrip("/") + "/")
    skill_mds = [p for p in paths if p.rsplit("/", 1)[-1].lower() == "skill.md" and _in_scope(p)]
    if not skill_mds:
        return {"ok": False, "error": "в репозитории/папке не найден SKILL.md"}
    skill_md = sorted(skill_mds, key=len)[0]            # самый верхний SKILL.md
    root = skill_md.rsplit("/", 1)[0] if "/" in skill_md else ""

    # бандл-файлы = всё в директории навыка (рекурсивно) с разрешённым расширением
    prefix = (root + "/") if root else ""
    bundle = [skill_md]
    for p in paths:
        if p == skill_md:
            continue
        if root and not p.startswith(prefix):
            continue
        if not root and "/" in p:
            continue                                    # навык в корне репо — только top-level
        if p.lower().endswith(BUNDLE_EXTS):
            bundle.append(p)
    bundle = bundle[:FOLDER_MAX_FILES]

    sdir = _skill_dir(user_dir, uid, _slug(repo if not root else root.rsplit("/", 1)[-1]))
    # подчистим прошлую версию того же навыка (идемпотентная переустановка)
    try:
        import shutil
        if sdir.exists():
            shutil.rmtree(sdir)
    except Exception:
        pass
    sdir.mkdir(parents=True, exist_ok=True)

    total, saved, scripts, skipped = 0, [], [], []
    skill_text = ""
    for p in bundle:
        rel = p[len(prefix):] if prefix and p.startswith(prefix) else p.rsplit("/", 1)[-1]
        raw = f"https://raw.githubusercontent.com/{owner}/{repo}/{used_branch}/{p}"
        text, e = fetch_text_guarded(raw, token=token)
        if e or text is None:
            skipped.append(rel)
            continue
        data = text.encode("utf-8", "ignore")
        if len(data) > FILE_MAX_BYTES:
            skipped.append(rel + " (>512КБ)")
            continue
        if total + len(data) > FOLDER_MAX_BYTES:
            skipped.append(rel + " (превышен общий лимит 2МБ)")
            break
        dest = sdir / rel
        # анти-traversal: финальный путь обязан остаться внутри sdir
        try:
            dest.resolve().relative_to(sdir.resolve())
        except Exception:
            skipped.append(rel + " (небезопасный путь)")
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, "utf-8")
        total += len(data)
        saved.append(rel)
        if rel.lower().endswith(SCRIPT_EXTS):
            scripts.append(rel)
        if p == skill_md:
            skill_text = text

    # имя/описание из SKILL.md + регистрируем в личном индексе (чтобы навык был в поиске/обзоре)
    name, desc, body = parse_skill(skill_text)
    if not name:
        h = re.search(r"^#\s+(.+)$", skill_text, re.M)
        name = h.group(1).strip() if h else (repo if not root else root.rsplit("/", 1)[-1])
    sk = store_user_skill(uid, name, desc, body, source_url=url)
    # СТАТИЧЕСКИЙ анализ возможностей навыка (caps + badge) — НЕ исполняет код, fail-soft.
    caps, badge = _analyze_caps(sdir)
    # дописываем мету фолдера в индекс-запись (folder=slug, scripts=[...], caps, badge)
    _attach_folder_meta(user_dir, uid, sk.get("id"), sdir.name, scripts, caps=caps, badge=badge)
    return {"ok": True,
            "skill": {**sk, "folder": sdir.name, "scripts": scripts,
                      "badge": badge, "caps": _caps_summary(caps)},
            "files": saved, "scripts": scripts, "skipped": skipped[:12],
            "bytes": total, "folder": True, "branch": used_branch, "repo": f"{owner}/{repo}",
            "badge": badge, "caps": _caps_summary(caps)}


def _index_path(user_dir, uid):
    return user_dir(uid) / "skills" / "index.json"


def _load_index(user_dir, uid):
    try:
        d = json.loads(_index_path(user_dir, uid).read_text("utf-8"))
        return d if isinstance(d, list) else []
    except Exception:
        return []


def _save_index(user_dir, uid, idx):
    p = _index_path(user_dir, uid)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(idx, ensure_ascii=False))
    tmp.replace(p)


def _attach_folder_meta(user_dir, uid, sid, folder_slug, scripts, caps=None, badge=None):
    """Дописать в индекс-запись навыка инфо о фолдере (folder, scripts) + по умолчанию enabled.
    Также персистим результат static-анализатора: caps (полный словарь) + badge (чип-совместимость),
    чтобы фронт показал бейдж, а рантайм-выбор (server/browser-wasm/E2B) шёл по этим caps."""
    idx = _load_index(user_dir, uid)
    for s in idx:
        if s.get("id") == sid:
            s["folder"] = folder_slug
            s["scripts"] = scripts
            if caps is not None:
                s["caps"] = caps
            if badge is not None:
                s["badge"] = badge
            s.setdefault("enabled", True)
            break
    _save_index(user_dir, uid, idx)


# ───────────────────────────── ON/OFF TOGGLE + LIST ─────────────────────────────

def set_skill_enabled(user_dir, uid, sid, enabled):
    """Тумблер навыка (выкл. → не авто-триггерится и не инжектится). Возвращает True если найден."""
    idx = _load_index(user_dir, uid)
    hit = False
    for s in idx:
        if s.get("id") == sid:
            s["enabled"] = bool(enabled)
            hit = True
            break
    if hit:
        _save_index(user_dir, uid, idx)
    return hit


def list_installed(user_dir, uid):
    """Список установленных личных навыков с метой (folder?/scripts/enabled/badge/caps) для панели.

    badge ∈ {full,partial,instruction-only,needs-server,unsupported} — чип-совместимости (фронт
    рисует бейдж). caps — короткая сводка (язык/пакеты/потребности/медиа/claude) для тултипа.
    Старые навыки без сохранённого badge (импорт до анализатора) → badge="" / caps={} (фронт
    деградирует мягко)."""
    out = []
    for s in _load_index(user_dir, uid):
        out.append({
            "id": s.get("id"), "name": s.get("name"), "description": s.get("description", ""),
            "folder": bool(s.get("folder")), "scripts": s.get("scripts") or [],
            "enabled": s.get("enabled", True), "source": s.get("source", ""),
            "badge": s.get("badge") or "",
            "caps": _caps_summary(s.get("caps")) if s.get("caps") else {},
        })
    return out


# ───────────────────────────── 2. RUN bundled scripts (GATED) ─────────────────────────────

def _resolve_script(user_dir, uid, sid, script_rel):
    """Найти бандл-скрипт навыка + вернуть всё нужное для запуска/выбора рантайма.
    Возвращает (info, err): при успехе (dict, None), при отказе (None, "причина").
    info = {code, sdir(Path), target(Path), rec(index-запись с caps/badge/scripts)}.
    Анти-traversal: финальный путь обязан остаться ВНУТРИ фолдера навыка."""
    idx = _load_index(user_dir, uid)
    rec = next((s for s in idx if s.get("id") == sid), None)
    if not rec or not rec.get("folder"):
        return None, "у навыка нет загруженного фолдера со скриптами"
    sdir = (user_dir(uid) / "skills" / "_folders" / rec["folder"]).resolve()
    target = (sdir / script_rel).resolve()
    try:
        target.relative_to(sdir)
    except Exception:
        return None, "небезопасный путь скрипта"
    if not target.exists() or not target.is_file():
        return None, "скрипт не найден"
    if target.stat().st_size > FILE_MAX_BYTES:
        return None, "скрипт слишком большой"
    return {"code": target.read_text("utf-8", "ignore"),
            "sdir": sdir, "target": target, "rec": rec}, None


def _read_script(user_dir, uid, sid, script_rel):
    """Прочитать текст бандл-скрипта из фолдера навыка (с анти-traversal). Тонкая обёртка
    над _resolve_script (сохранена для совместимости — возвращает только (text, err))."""
    info, err = _resolve_script(user_dir, uid, sid, script_rel)
    if err:
        return None, err
    return info["code"], None


def _e2b_api_key():
    """E2B-ключ из ~/.e2b_key или env E2B_API_KEY (один наш аккаунт; расход метрим на юзера в server.py)."""
    import os
    from pathlib import Path
    try:
        p = Path.home() / ".e2b_key"
        if p.exists():
            k = p.read_text("utf-8", "ignore").strip()
            if k:
                return k
    except Exception:
        pass
    return os.environ.get("E2B_API_KEY") or ""


def run_in_cloud_sandbox(code, lang, stdin_text=None):
    """Тяжёлый/нативный путь: одноразовый E2B Linux-sandbox (реальный терминал, pip, бинарники).
    Один наш аккаунт E2B; расход перекладываем на кредиты юзера на уровне server.py.
    Ленивая загрузка SDK + мягкая деградация, если ключа/SDK нет. Возврат: {ok, output|error, runtime}.

    stdin_text (опц.) — STDIN для скрипта: пишем во временный файл в песочнице и редиректим в процесс
    (универсально, без завязки на версию SDK), плюс кладём в env SKILL_INPUT."""
    import os
    key = _e2b_api_key()
    if not key:
        return {"ok": False, "runtime": "cloud-sandbox", "error": "E2B не настроен (нет ключа ~/.e2b_key)"}
    try:
        from e2b_code_interpreter import Sandbox
    except Exception:
        return {"ok": False, "runtime": "cloud-sandbox",
                "error": "E2B SDK не установлен (pip install e2b-code-interpreter)"}
    os.environ.setdefault("E2B_API_KEY", key)
    sbx = None
    try:
        sbx = Sandbox.create()
        _stdin = None if stdin_text is None else str(stdin_text)[:100000]
        if _stdin is not None:
            # кладём stdin в файл песочницы → процесс читает реальный STDIN через редирект ниже
            try:
                sbx.files.write("/tmp/_skill_stdin", _stdin)
            except Exception:
                _stdin = None     # запись не удалась → деградируем без stdin (не падаем)
        if lang in ("python", "js", "javascript", "ts", "typescript"):
            if _stdin is not None:
                try:
                    ex = sbx.run_code(code, stdin=_stdin)      # новые SDK принимают stdin
                except TypeError:
                    ex = sbx.run_code(code)                    # старый SDK — скрипт прочтёт /tmp/_skill_stdin
            else:
                ex = sbx.run_code(code)
            out = "".join(ex.logs.stdout or [])
            err = "".join(ex.logs.stderr or [])
            if getattr(ex, "error", None):
                err += f"\n{ex.error}"
            output = (out + ("\n" + err if err.strip() else "")).strip()
        else:  # bash и прочее → как shell-команда; stdin через редирект файла
            if _stdin is not None:
                # оборачиваем команду так, чтобы её STDIN шёл из файла (script может читать `read`/`cat`)
                wrapped = "{ " + code + "\n; } < /tmp/_skill_stdin"
                try:
                    r = sbx.commands.run(wrapped, envs={"SKILL_INPUT": _stdin})
                except TypeError:
                    r = sbx.commands.run(wrapped)              # старый SDK без envs — stdin-редирект всё равно работает
            else:
                r = sbx.commands.run(code)
            output = ((r.stdout or "") + ("\n" + r.stderr if (r.stderr or "").strip() else "")).strip()
        return {"ok": True, "runtime": "cloud-sandbox", "output": output[:20000]}
    except Exception as e:
        return {"ok": False, "runtime": "cloud-sandbox", "error": f"sandbox: {str(e)[:300]}"}
    finally:
        try:
            if sbx is not None:
                sbx.kill()
        except Exception:
            pass


# ── ПЕРСИСТЕНТНАЯ E2B-СЕССИЯ НА ЧАТ ── ОБЩАЯ ПЕСОЧНИЦА: терминал юзера + run_code ИИ → ОДНА сессия,
# cd/env/файлы живут между командами, ИИ и юзер делят одну ФС. E2B сам гасит по таймауту (1ч).
_E2B_SESSIONS = {}                       # chat_id -> {"id": sandbox_id, "ts": float}
_E2B_SESS_LOCK = threading.Lock()


def sandbox_session_run(chat_id, cmd):
    """Команда в ПЕРСИСТЕНТНОЙ E2B-сессии чата (reconnect к той же песочнице по id → состояние сохранено).
    cd/env/файлы живут между вызовами; ИИ (run_code) и юзер (терминал) делят ОДНУ сессию.
    Возврат: {ok, output|error, sandbox_id}."""
    key = _e2b_api_key()
    if not key:
        return {"ok": False, "error": "E2B не настроен (нет ключа ~/.e2b_key)"}
    try:
        from e2b_code_interpreter import Sandbox
    except Exception:
        return {"ok": False, "error": "E2B SDK не установлен"}
    os.environ.setdefault("E2B_API_KEY", key)
    cid = str(chat_id or "default")
    with _E2B_SESS_LOCK:
        prev = _E2B_SESSIONS.get(cid)
    sbx = None
    try:
        if prev:
            try:
                sbx = Sandbox.connect(prev["id"])         # та же сессия → cd/env/файлы на месте
                try:
                    sbx.set_timeout(3600)
                except Exception:
                    pass
            except Exception:
                sbx = None                                # сессия умерла → создаём новую ниже
        if sbx is None:
            sbx = Sandbox.create()
            try:
                sbx.set_timeout(3600)
            except Exception:
                pass
        with _E2B_SESS_LOCK:
            _E2B_SESSIONS[cid] = {"id": sbx.sandbox_id, "ts": _time.time()}
        r = sbx.commands.run(cmd)
        out = ((r.stdout or "") + ("\n" + r.stderr if (r.stderr or "").strip() else "")).strip()
        return {"ok": True, "output": out[:20000], "sandbox_id": sbx.sandbox_id}
    except Exception as e:
        return {"ok": False, "error": f"sandbox: {str(e)[:300]}"}
    # НЕ убиваем — сессия персистентна; E2B сам закроет по таймауту.


def _caps_needs_server(caps, lang):
    """Жёсткое требование сервера/нативного рантайма по caps (или по языку как фолбэк).
    True → скрипт НЕ запустится в браузере (shell/сеть/Node/не-Pyodide-пакет), нужен E2B/нативный мост."""
    if caps:
        if (caps.get("needs_shell") or caps.get("needs_network")
                or caps.get("needs_node") or (caps.get("pyodide_no") or [])):
            return True
        return False
    # caps нет (старый навык) → решаем по языку: bash/js всегда нужен сервер, python — нет.
    return lang in ("bash", "js")


def run_skill_script(user_dir, uid, sid, script_rel, *, is_owner, run_code_lang,
                     input=None, argv=None, run_code_file=None):
    """Запустить бандл-скрипт навыка — БЕЗОПАСНО ГЕЙТИТСЯ + ВЫБОР РАНТАЙМА ПО caps.

    ВЛАДЕЛЕЦ (script) → НАТИВНЫЙ запуск ИЗ ПАПКИ НАВЫКА: `python <skilldir>/<script> <argv...>`,
        cwd=skilldir, stdin=input, реальный env. Это чинит argv/sys.argv (argparse/click), cwd и
        чтение СОСЕДНИХ ресурсов (open("references/x.md"), __file__-относительные пути) — то, что
        ломалось при старом `python -I -c <code>` в пустой временной папке. Безопасность сохранена:
        rlimits + timeout + кап вывода (см. run_code_file в server.py). Если file-раннер не передан
        (старый вызов) — деградируем на прежний run_code_lang (без argv/cwd, но рабочий).
    ЮЗЕР    → НИКОГДА на бэкенде (анти-RCE по ARCH-DECISIONS). По caps/badge:
        • pure/pyodide-ok python/js → runtime-маркер "browser-wasm" (+code, +input, +pyodide-пакеты),
          фронт исполняет в Pyodide/WebContainer в своей вкладке (zero server cost, безопасно);
        • needs-server (shell/сеть/Node/не-Pyodide-пакет) → E2B-облако, если есть ~/.e2b_key,
          иначе понятный маркер "needs-native-bridge" (UI покажет CTA настроить E2B/мост).

    input (опц., строка) — STDIN для скрипта. На сервере/в облаке подаётся процессу на stdin (и в env
    как SKILL_INPUT). Для browser-wasm возвращаем его фронту полем `input` (Pyodide-stdin эмулируется
    фронтом). Поле строго называется `input`.
    argv (опц., список) — аргументы командной строки для скрипта (owner-нативный путь — реальный
    sys.argv; browser-wasm — отдаём фронту полем `argv`, Pyodide-шим выставит sys.argv).

    Возврат: {ok, runtime: "server"|"cloud-sandbox"|"browser-wasm"|"needs-native-bridge",
              output?|code, lang, input?, argv?, badge?, ...}.
    """
    info, err = _resolve_script(user_dir, uid, sid, script_rel)
    if err:
        return {"ok": False, "error": err}
    code = info["code"]
    sdir = info["sdir"]
    target = info["target"]
    rec = info["rec"]
    caps = rec.get("caps") or {}
    badge = rec.get("badge") or ""
    lang = _lang_for(script_rel)
    if lang == "text":
        return {"ok": False, "error": "это не исполняемый скрипт (.py/.js/.sh)"}
    stdin_text = None if input is None else str(input)
    argv_list = [str(a) for a in argv] if argv else []

    if is_owner(uid):
        # ── owner-нативный путь: запуск ИЗ ПАПКИ НАВЫКА с argv/cwd/stdin (фиделити-шим) ──
        if run_code_file is not None:
            out = run_code_file(str(target), lang, cwd=str(sdir),
                                argv=argv_list, stdin_text=stdin_text)
        else:
            # фолбэк (file-раннер не пробросили): старый -c путь, без argv/cwd, но рабочий
            out = run_code_lang(code, "python" if lang == "python" else lang,
                                stdin_text=stdin_text)
        res = {"ok": True, "runtime": "server", "lang": lang, "script": script_rel,
               "output": out, "badge": badge}
        if argv_list:
            res["argv"] = argv_list
        return res

    # ── ЮЗЕР: на голом бэкенде НЕ запускаем. Выбор по caps/badge. ──
    needs_server = _caps_needs_server(caps, lang)
    if needs_server:
        # нативное требование (shell/сеть/Node/не-Pyodide-пакет) → E2B, если есть ключ.
        if _e2b_api_key():
            res = run_in_cloud_sandbox(code, lang, stdin_text=stdin_text)
            if res.get("ok"):
                return {"ok": True, "runtime": "cloud-sandbox", "lang": lang,
                        "script": script_rel, "output": res.get("output", ""), "badge": badge}
            return {"ok": False, "runtime": "cloud-sandbox", "lang": lang, "script": script_rel,
                    "error": res.get("error", "облачный sandbox недоступен"), "badge": badge}
        # ключа нет → честный маркер: нужен нативный мост или E2B (UI покажет CTA)
        why = []
        if caps.get("needs_shell"):
            why.append("shell/бинарники")
        if caps.get("needs_network"):
            why.append("сеть")
        if caps.get("needs_node"):
            why.append("Node.js")
        if caps.get("pyodide_no"):
            why.append("пакеты не из Pyodide: " + ", ".join((caps.get("pyodide_no") or [])[:6]))
        if not why and lang in ("bash", "js"):
            why.append("bash/Node" if lang == "bash" else "Node.js")
        return {"ok": False, "runtime": "needs-native-bridge", "lang": lang, "script": script_rel,
                "badge": badge or "needs-server", "reason": "; ".join(why) or "нативное окружение",
                "error": ("этому навыку нужно нативное окружение (" + ("; ".join(why) or "shell/сеть/Node")
                          + "). Настройте E2B-ключ (~/.e2b_key) или нативный мост — тогда запустим.")}

    # Питон/JS юзера, который УМЕЕТ в браузер (pure stdlib / только pyodide_ok) → browser-WASM.
    out = {"ok": True, "runtime": "browser-wasm", "lang": lang, "script": script_rel,
           "code": code, "badge": badge,
           "note": "скрипт выполнится в вашем браузере (Pyodide) — безопасно, без затрат сервера"}
    # фронту: какие Pyodide-пакеты подгрузить (loadPackagesFromImports + micropip) — чтобы import работал
    if caps.get("pyodide_ok"):
        out["pyodide_packages"] = list(caps.get("pyodide_ok") or [])
    if stdin_text is not None:
        out["input"] = stdin_text          # фронт подаёт это в Pyodide-stdin
    if argv_list:
        out["argv"] = argv_list            # фронт выставит sys.argv в Pyodide-шиме
    return out


# ───────────────────────────── 3 + 4. AUTO-TRIGGER + INJECT (model-agnostic) ─────────────────────────────

_STOP = set("the a an and or to of in on for with is are was как что это для при под над без the и в на с по от до или the или".split())


def _tokens(s):
    return {t for t in re.findall(r"[\wа-яё]{3,}", str(s or "").lower()) if t not in _STOP}


def match_skills(user_dir, uid, message, *, skill_body, limit=AUTO_TRIGGER_MAX):
    """Дешёвый keyword/overlap-матч сообщения юзера на ВКЛЮЧЁННЫЕ навыки (name+description+id+первые
    строки тела). Без эмбеддингов — по пересечению токенов с лёгким бонусом за точное слово в описании.
    Возвращает [{id,name,description,score,body,scripts,folder}], максимум `limit`. body уже подрезан.

    Это «как харнес»: совпавший навык даёт текст SKILL.md, который инжектится в системный промпт → ЛЮБАЯ
    модель (GPT/Gemini/DeepSeek) следует Claude-формату навыка."""
    msg_tok = _tokens(message)
    if not msg_tok:
        return []
    scored = []
    for s in _load_index(user_dir, uid):
        if not s.get("enabled", True):
            continue
        name = str(s.get("name") or "")
        desc = str(s.get("description") or "")
        sid = str(s.get("id") or "")
        blob_tok = _tokens(name + " " + desc + " " + sid.replace("-", " "))
        overlap = msg_tok & blob_tok
        if not overlap:
            continue
        # score: пересечение + бонус если совпавшее слово стоит в имени навыка
        name_tok = _tokens(name)
        score = len(overlap) + 0.5 * len(overlap & name_tok)
        scored.append((score, s))
    scored.sort(key=lambda x: x[0], reverse=True)
    out = []
    for score, s in scored[:limit]:
        body = skill_body(uid, s.get("id")) or ""
        out.append({"id": s.get("id"), "name": s.get("name"),
                    "description": s.get("description", ""), "score": round(float(score), 1),
                    "body": body[:8000], "scripts": s.get("scripts") or [],
                    "folder": bool(s.get("folder")),
                    # caps/badge нужны вызывающему для МОДЕЛЬ-ПИНА claude-authored навыков
                    # (claude_authored + recommended_model) и для индикатора в UI.
                    "caps": s.get("caps") or {}, "badge": s.get("badge") or ""})
    return out


def build_skill_injection(matched):
    """Собрать кусок системного промпта из совпавших навыков (model-agnostic — обычный текст инструкций).
    Возвращает (prompt_text, fired_names). Пустой список → ("", [])."""
    if not matched:
        return "", []
    parts = ["\n\n## АКТИВНЫЕ НАВЫКИ (следуй этим экспертным инструкциям, они подобраны под запрос):"]
    names = []
    for m in matched:
        names.append(m.get("name") or m.get("id"))
        block = f"\n### Навык «{m.get('name')}»\n{m.get('body','')}"
        if m.get("scripts"):
            block += ("\n\nУ навыка есть скрипты: " + ", ".join(m["scripts"]) +
                      ". Чтобы выполнить — вызови тулзу run_skill_script "
                      f'{{"skill":"{m.get("id")}","script":"<имя>"}}.')
        parts.append(block)
    return "\n".join(parts), names


def make_run_skill_tool(uid, *, user_dir, is_owner, run_code_lang, run_code_file=None):
    """Фабрика тулзы run_skill_script для агент/чат-цикла (модель-агностично: любой модели доступна).
    Возвращает callable(args)->str. Юзеру отдаёт browser-wasm-маркер (фронт исполнит); владельцу — вывод.
    run_code_file (опц.) — file-based раннер из server.py для owner-фиделити-шима (argv/cwd/resources)."""
    def _tool(args):
        sid = str(args.get("skill") or args.get("id") or "")
        script = str(args.get("script") or "")
        if not sid or not script:
            return 'error: нужны "skill" и "script"'
        _inp = args.get("input")          # опц. STDIN для скрипта (поле строго "input")
        _argv = args.get("argv")          # опц. список аргументов командной строки (sys.argv)
        if isinstance(_argv, str):
            _argv = [_argv]
        res = run_skill_script(user_dir, uid, sid, script,
                               is_owner=is_owner, run_code_lang=run_code_lang,
                               run_code_file=run_code_file,
                               input=(None if _inp is None else str(_inp)),
                               argv=(list(_argv) if isinstance(_argv, (list, tuple)) else None))
        if not res.get("ok"):
            return "error: " + str(res.get("error"))
        if res.get("runtime") == "server":
            return res.get("output") or "(нет вывода)"
        # для юзера: модели сообщаем, что скрипт уйдёт на исполнение в браузер пользователя
        return ("[runtime=browser-wasm] скрипт «" + script + "» отправлен на безопасное исполнение "
                "в браузере пользователя; результат вернётся отдельным сообщением. "
                "Продолжай, исходя из того, что скрипт запущен.")
    return _tool


RUN_SKILL_TOOL_PROMPT = (
    '- run_skill_script args {"skill":"<id>","script":"<file>","input":"<опц. STDIN>",'
    '"argv":["<опц. аргументы>"]} — выполнить скрипт установленного навыка (безопасный sandbox: '
    "владелец — нативно на сервере из папки навыка с argv/cwd/соседними ресурсами, юзер — в браузере "
    "или E2B). Поле input необязательное: строка на STDIN. Поле argv необязательное: список аргументов "
    "командной строки (станет sys.argv у скрипта, для CLI-навыков с argparse). Зови, когда навык требует "
    "прогнать свой скрипт для результата.")
