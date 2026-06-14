"""Память → песочница: складываем долгую память юзера файлом MEMORY.md в его E2B-сессию чата.

Зачем: когда юзер (или ИИ) работает в общей персистентной песочнице чата (терминал + run_code,
см. skills_run.sandbox_session_run), удобно иметь рядом файл MEMORY.md — чтобы скрипты/агент
в песочнице могли «увидеть» что Тайга помнит о пользователе, как Claude Code видит ~/CLAUDE.md.

Граница ответственности (как в skills_run.py): server.py НЕ редактируется. Этот модуль НЕ импортирует
server.py. Чтение памяти приходит ПАРАМЕТРАМИ-функциями из server.py (load_memory, опц. filter_tombstoned),
а запись идёт через соседний standalone-модуль skills_run (stdlib-only, без server-импорта) —
его и только его мы импортируем напрямую.

Запись — через base64: произвольный кириллический/markdown-текст памяти НЕ экранируется в shell
(никаких проблем с кавычками/переводами строк/$), на той стороне python3 декодирует и пишет файл атомарно.
"""

import base64
import time as _time

# Соседний standalone-модуль (только stdlib, server.py не тянет) — безопасно импортировать напрямую.
import skills_run

# Куда кладём файл В ПЕСОЧНИЦЕ (E2B стартует в /home/user). Относительный путь от рабочей директории —
# чтобы юзер сразу видел MEMORY.md в Files-дереве (оно строит `find .` от той же cwd).
MEMORY_FILENAME = "MEMORY.md"

# Сколько фактов максимум выгружаем (память и так капается ~80 в server.py; тут страховочный потолок).
MAX_FACTS = 200
# Потолок длины одного факта в файле (анти-раздувание; память хранит до 240 симв.).
MAX_FACT_LEN = 400


def _facts_from_memory(mem):
    """Из сырой памяти (список {'text','ts'}) собрать чистый список строк-фактов в порядке свежести.

    Память в server.py — список dict'ов вида {"text": str, "ts": float}, новые в конце.
    Здесь нормализуем: выкидываем пустые, режем длину, дедупим без учёта регистра, держим порядок.
    """
    out, seen = [], set()
    for m in (mem or []):
        if isinstance(m, dict):
            txt = str(m.get("text", "")).strip()
        else:
            txt = str(m or "").strip()
        if not txt:
            continue
        txt = txt[:MAX_FACT_LEN]
        key = txt.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(txt)
    return out[:MAX_FACTS]


def render_memory_md(facts, *, uid=""):
    """Отрендерить MEMORY.md из списка строк-фактов. Чистый markdown, на русском, тон «ты».

    Формат специально простой и стабильный: шапка-объяснение + маркированный список фактов.
    Пустая память → валидный файл с понятной пометкой (а не пустышка), чтобы в песочнице было ясно.
    """
    ts = _time.strftime("%Y-%m-%d %H:%M", _time.localtime())
    lines = [
        "# Память Тайги о пользователе",
        "",
        "Это то, что Тайга помнит о тебе из долгой памяти (живёт между чатами).",
        "Файл выгружен в песочницу автоматически — скрипты и агент тут могут на него опираться.",
        f"_Обновлено: {ts}._",
        "",
    ]
    if facts:
        lines.append("## Факты")
        lines.append("")
        for f in facts:
            # одну строку на факт; внутренние переводы строк схлопываем, чтобы список не «разъехался»
            one = " ".join(f.split())
            lines.append(f"- {one}")
    else:
        lines.append("_Память пока пустая — Тайга ещё ничего о тебе не запомнила._")
    lines.append("")
    return "\n".join(lines)


def _b64_write_cmd(text, filename):
    """Shell-команда, которая декодирует base64 и атомарно пишет файл в текущую директорию песочницы.

    python3 есть в E2B-образе по умолчанию. Пишем во временный файл + os.replace → читатель никогда
    не видит «полузаписанный» MEMORY.md. base64 без переводов строк (одна строка) — безопасно для shell.
    """
    payload = base64.b64encode(text.encode("utf-8")).decode("ascii")
    # filename фиксированный (MEMORY.md), но всё равно прогоняем через repr на той стороне — без инъекций.
    return (
        "python3 - <<'PYEOF'\n"
        "import base64, os\n"
        f"name = {filename!r}\n"
        f"data = base64.b64decode({payload!r})\n"
        "tmp = name + '.tmp'\n"
        "open(tmp, 'wb').write(data)\n"
        "os.replace(tmp, name)\n"
        "print('wrote', name, len(data), 'bytes')\n"
        "PYEOF"
    )


def write_memory_to_sandbox(chat_id, uid, *, load_memory, filter_tombstoned=None,
                            filename=MEMORY_FILENAME):
    """Прочитать долгую память юзера и записать её файлом MEMORY.md в персистентную E2B-сессию чата.

    chat_id            — id чата (та же сессия, что у терминала/run_code этого чата).
    uid                — id юзера, чью память выгружаем.
    load_memory        — функция server.py: load_memory(uid) -> list[{"text","ts"}]. ОБЯЗАТЕЛЬНА
                         (так модуль не импортирует server.py — зависимость приходит параметром).
    filter_tombstoned  — опц. функция server.py: filter_tombstoned(uid, facts) -> facts. Если передана,
                         убираем из выгрузки факты, которые юзер просил забыть (иначе «забудь X» утечёт в файл).
    filename           — имя файла в песочнице (по умолчанию MEMORY.md).

    Возврат: {ok, facts, bytes, path, sandbox_id} | {ok: False, error, facts}.
    Сетевой/инфра-путь (запуск в песочнице) полностью на skills_run.sandbox_session_run — мягко
    деградирует, если E2B не настроен (вернёт ok:False с понятной ошибкой).
    """
    if not callable(load_memory):
        return {"ok": False, "error": "load_memory не передан (нужна функция server.py)", "facts": 0}

    try:
        mem = load_memory(uid)
    except Exception as e:
        return {"ok": False, "error": f"не смог прочитать память: {str(e)[:200]}", "facts": 0}

    facts = _facts_from_memory(mem)
    # уважаем тумбстоуны (забытые факты), если server.py дал фильтр
    if callable(filter_tombstoned):
        try:
            facts = [f for f in filter_tombstoned(uid, facts) if str(f).strip()]
        except Exception:
            pass  # фильтр упал — не валим всю выгрузку, пишем как есть

    md = render_memory_md(facts, uid=str(uid or ""))
    cmd = _b64_write_cmd(md, filename)

    res = skills_run.sandbox_session_run(chat_id, cmd)
    if not res.get("ok"):
        return {"ok": False, "error": res.get("error", "песочница недоступна"),
                "facts": len(facts)}
    return {
        "ok": True,
        "facts": len(facts),
        "bytes": len(md.encode("utf-8")),
        "path": filename,
        "sandbox_id": res.get("sandbox_id"),
    }
