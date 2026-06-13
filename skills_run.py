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
    # дописываем мету фолдера в индекс-запись (folder=slug, scripts=[...])
    _attach_folder_meta(user_dir, uid, sk.get("id"), sdir.name, scripts)
    return {"ok": True, "skill": {**sk, "folder": sdir.name, "scripts": scripts},
            "files": saved, "scripts": scripts, "skipped": skipped[:12],
            "bytes": total, "folder": True, "branch": used_branch, "repo": f"{owner}/{repo}"}


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


def _attach_folder_meta(user_dir, uid, sid, folder_slug, scripts):
    """Дописать в индекс-запись навыка инфо о фолдере (folder, scripts) + по умолчанию enabled."""
    idx = _load_index(user_dir, uid)
    for s in idx:
        if s.get("id") == sid:
            s["folder"] = folder_slug
            s["scripts"] = scripts
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
    """Список установленных личных навыков с метой (folder?/scripts/enabled) для панели."""
    out = []
    for s in _load_index(user_dir, uid):
        out.append({
            "id": s.get("id"), "name": s.get("name"), "description": s.get("description", ""),
            "folder": bool(s.get("folder")), "scripts": s.get("scripts") or [],
            "enabled": s.get("enabled", True), "source": s.get("source", ""),
        })
    return out


# ───────────────────────────── 2. RUN bundled scripts (GATED) ─────────────────────────────

def _read_script(user_dir, uid, sid, script_rel):
    """Прочитать текст бандл-скрипта из фолдера навыка (с анти-traversal)."""
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
    return target.read_text("utf-8", "ignore"), None


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


def run_in_cloud_sandbox(code, lang):
    """Тяжёлый/нативный путь: одноразовый E2B Linux-sandbox (реальный терминал, pip, бинарники).
    Один наш аккаунт E2B; расход перекладываем на кредиты юзера на уровне server.py.
    Ленивая загрузка SDK + мягкая деградация, если ключа/SDK нет. Возврат: {ok, output|error, runtime}."""
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
        if lang in ("python", "js", "javascript", "ts", "typescript"):
            ex = sbx.run_code(code)
            out = "".join(ex.logs.stdout or [])
            err = "".join(ex.logs.stderr or [])
            if getattr(ex, "error", None):
                err += f"\n{ex.error}"
            output = (out + ("\n" + err if err.strip() else "")).strip()
        else:  # bash и прочее → как shell-команда
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


def run_skill_script(user_dir, uid, sid, script_rel, *, is_owner, run_code_lang):
    """Запустить бандл-скрипт навыка — БЕЗОПАСНО ГЕЙТИТСЯ.

    ВЛАДЕЛЕЦ → прямой запуск через переданный run_code_lang (тот же owner-gated путь, что run_code:
        subprocess + rlimits + timeout). Реальная мульти-тенант-изоляция = sandbox ниже, тут owner-only.
    ЮЗЕР    → НИКОГДА на бэкенде (анти-RCE по ARCH-DECISIONS). Возвращаем сам скрипт + runtime-маркер
        "browser-wasm" → фронт исполняет в Pyodide/WebContainer в своей вкладке (zero server cost, безопасно).
    Тяжёлый/нативный путь (бинарники/долгий процесс) → cloud-sandbox-per-user = TODO (отложенная инфра).

    Возврат: {ok, runtime: "server"|"browser-wasm", output?|script, lang, ...}.
    """
    code, err = _read_script(user_dir, uid, sid, script_rel)
    if err:
        return {"ok": False, "error": err}
    lang = _lang_for(script_rel)
    if lang == "text":
        return {"ok": False, "error": "это не исполняемый скрипт (.py/.js/.sh)"}

    if is_owner(uid):
        # owner-only прямой запуск (переиспользуем существующий gated code-run путь)
        out = run_code_lang(code, "python" if lang == "python" else lang)
        return {"ok": True, "runtime": "server", "lang": lang, "script": script_rel, "output": out}

    # ЮЗЕР, bash/нативное → облачный E2B-sandbox (реальный Linux). Расход метрится на сервере.
    if lang == "bash":
        res = run_in_cloud_sandbox(code, "bash")
        if res.get("ok"):
            return {"ok": True, "runtime": "cloud-sandbox", "lang": lang,
                    "script": script_rel, "output": res.get("output", "")}
        return {"ok": False, "runtime": "cloud-sandbox", "lang": lang, "script": script_rel,
                "error": res.get("error", "облачный sandbox недоступен")}
    # Питон/JS юзера → browser-WASM (бесплатно). Тяжёлый питон тоже можно отправить в E2B при желании.
    return {"ok": True, "runtime": "browser-wasm", "lang": lang, "script": script_rel,
            "code": code,
            "note": "скрипт выполнится в вашем браузере (Pyodide) — безопасно, без затрат сервера"}


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
                    "folder": bool(s.get("folder"))})
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


def make_run_skill_tool(uid, *, user_dir, is_owner, run_code_lang):
    """Фабрика тулзы run_skill_script для агент/чат-цикла (модель-агностично: любой модели доступна).
    Возвращает callable(args)->str. Юзеру отдаёт browser-wasm-маркер (фронт исполнит); владельцу — вывод."""
    def _tool(args):
        sid = str(args.get("skill") or args.get("id") or "")
        script = str(args.get("script") or "")
        if not sid or not script:
            return 'error: нужны "skill" и "script"'
        res = run_skill_script(user_dir, uid, sid, script,
                               is_owner=is_owner, run_code_lang=run_code_lang)
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
    '- run_skill_script args {"skill":"<id>","script":"<file>"} — выполнить скрипт установленного навыка '
    "(безопасный sandbox: владелец — на сервере, юзер — в браузере). Зови, когда навык требует прогнать "
    "свой скрипт для результата.")
