"""Планировщик фоновых/расписание-агентов Тайги (дыра #11 vs Hermes/GitHub Agents).

Джоб = {id, uid, task, workers, kind, interval_sec, at_time, weekdays,
        next_run, enabled, last_run, last_result}.
Демон-поток раз в минуту проверяет due-джобы и гонит их через orchestrator (runner из server.py).
Анти-runaway: мин интервал 600с; если non-owner с нулевым балансом — джоб пропускается.

Два типа триггера:
  • kind="interval" — старый «каждые N секунд» (interval_sec). BACK-COMPAT: джобы без kind
    считаются interval.
  • kind="time"     — «в заданное время»: at_time="HH:MM" + weekdays (множество дней недели
    или токен "daily"/"weekdays"/"weekends"). Время — в локальной таймзоне сервера.

compute_next_run(schedule, now) — чистый, тестируемый: по dict-расписанию и unix-времени
возвращает unix-таймштамп следующего запуска для ОБОИХ типов.
"""
import json
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path("~/.mostik-ai").expanduser()
_JOBS = BASE / "jobs.json"
_MIN_INTERVAL = 600          # не чаще раза в 10 минут (анти-абуз/стоимость)
_RUNNER = None               # callback(uid, task, workers) -> dict; ставит server.py
_LOCK = threading.Lock()

# Канонический порядок дней недели; индекс совпадает с datetime.weekday() (пн=0 … вс=6)
_WEEKDAY_NAMES = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
_WEEKDAY_TOKENS = {
    "daily": set(_WEEKDAY_NAMES),
    "everyday": set(_WEEKDAY_NAMES),
    "weekdays": {"mon", "tue", "wed", "thu", "fri"},
    "weekends": {"sat", "sun"},
}


def set_runner(fn):
    global _RUNNER
    _RUNNER = fn


def _load() -> list:
    try:
        return json.loads(_JOBS.read_text())
    except Exception:
        return []


def _save(jobs: list):
    BASE.mkdir(parents=True, exist_ok=True)
    tmp = _JOBS.with_suffix(".tmp")
    tmp.write_text(json.dumps(jobs, ensure_ascii=False))
    tmp.replace(_JOBS)


def _jid(uid: str) -> str:
    return "j" + str(int(time.time() * 1000))[-9:] + str(abs(hash(uid)) % 1000)


# --------------------------------------------------------------------------- #
#  Расписание: нормализация полей + чистый расчёт следующего запуска
# --------------------------------------------------------------------------- #

def _parse_hhmm(at_time) -> tuple:
    """('HH','MM') -> (hour, minute), с клампом в валидный диапазон. Кривое → (9, 0)."""
    try:
        hh, mm = str(at_time).strip().split(":", 1)
        h = max(0, min(23, int(hh)))
        m = max(0, min(59, int(mm)))
        return h, m
    except Exception:
        return 9, 0


def _normalize_weekdays(weekdays) -> set:
    """Любой вход (токен-строка / список дней / пусто) -> множество канонических дней {'mon',...}.

    Принимает: "daily"/"weekdays"/"weekends", список вида ["mon","wed"], строку "mon,wed".
    Пустое/мусор -> все дни (т.е. ежедневно)."""
    if not weekdays:
        return set(_WEEKDAY_NAMES)
    if isinstance(weekdays, str):
        tok = weekdays.strip().lower()
        if tok in _WEEKDAY_TOKENS:
            return set(_WEEKDAY_TOKENS[tok])
        parts = [p.strip().lower()[:3] for p in tok.replace(" ", ",").split(",")]
        days = {p for p in parts if p in _WEEKDAY_NAMES}
        return days or set(_WEEKDAY_NAMES)
    if isinstance(weekdays, (list, tuple, set)):
        days = set()
        for w in weekdays:
            w = str(w).strip().lower()[:3]
            if w in _WEEKDAY_NAMES:
                days.add(w)
        return days or set(_WEEKDAY_NAMES)
    return set(_WEEKDAY_NAMES)


def compute_next_run(schedule: dict, now: float) -> float:
    """Чистая функция: по расписанию + текущему unix-времени → unix-время следующего запуска.

    schedule поддерживает оба типа:
      interval: {"kind":"interval", "interval_sec": 3600}   (kind можно опустить — BACK-COMPAT)
      time    : {"kind":"time", "at_time":"18:30", "weekdays":["mon","fri"] | "weekdays" | ...}

    Время-of-day считается в ЛОКАЛЬНОЙ таймзоне сервера. Всегда возвращает момент строго в будущем
    относительно `now` (для time — ближайший подходящий день недели в нужный час:минуту)."""
    kind = str((schedule or {}).get("kind") or "interval").lower()

    if kind == "time":
        h, m = _parse_hhmm((schedule or {}).get("at_time", "09:00"))
        days = _normalize_weekdays((schedule or {}).get("weekdays"))
        allowed = {_WEEKDAY_NAMES.index(d) for d in days} or set(range(7))
        base = datetime.fromtimestamp(now)
        # Кандидат на сегодня в нужный час:минуту
        cand = base.replace(hour=h, minute=m, second=0, microsecond=0)
        # Ищем ближайший день (0..7 вперёд), где день недели разрешён И момент строго в будущем
        for add in range(0, 8):
            day = cand + timedelta(days=add)
            if day.weekday() in allowed and day.timestamp() > now:
                return day.timestamp()
        # Теоретически недостижимо (allowed непусто) — но дадим безопасный фолбэк
        return (cand + timedelta(days=1)).timestamp()

    # interval (default / back-compat)
    interval = max(_MIN_INTERVAL, int((schedule or {}).get("interval_sec") or 3600))
    return now + interval


def add_job(uid: str, task: str, interval_sec: int, workers=None,
            kind=None, at_time=None, weekdays=None) -> dict:
    task = str(task or "").strip()
    if not task:
        return {"error": "пустая задача"}
    interval = max(_MIN_INTERVAL, int(interval_sec or 3600))
    kind = "time" if str(kind or "").lower() == "time" else "interval"

    schedule = {"kind": kind, "interval_sec": interval}
    if kind == "time":
        h, m = _parse_hhmm(at_time)
        schedule["at_time"] = f"{h:02d}:{m:02d}"
        schedule["weekdays"] = sorted(
            _normalize_weekdays(weekdays), key=_WEEKDAY_NAMES.index
        )

    with _LOCK:
        jobs = _load()
        job = {"id": _jid(uid), "uid": uid, "task": task[:500], "workers": workers,
               "kind": kind, "interval_sec": interval,
               "at_time": schedule.get("at_time"), "weekdays": schedule.get("weekdays"),
               "next_run": compute_next_run(schedule, time.time()),
               "enabled": True, "last_run": None, "last_result": None}
        jobs.append(job)
        _save(jobs)
    return {"ok": True, "job": job}


def list_jobs(uid: str) -> list:
    return [j for j in _load() if j.get("uid") == uid]


def delete_job(uid: str, job_id: str) -> list:
    with _LOCK:
        jobs = [j for j in _load() if not (j.get("uid") == uid and j.get("id") == job_id)]
        _save(jobs)
    return list_jobs(uid)


def toggle_job(uid: str, job_id: str, enabled: bool) -> list:
    with _LOCK:
        jobs = _load()
        for j in jobs:
            if j.get("uid") == uid and j.get("id") == job_id:
                j["enabled"] = bool(enabled)
        _save(jobs)
    return list_jobs(uid)


def _tick():
    now = time.time()
    with _LOCK:
        jobs = _load()
    changed = False
    for j in jobs:
        if not (j.get("enabled") and j.get("next_run", 0) <= now):
            continue
        if _RUNNER:
            try:
                r = _RUNNER(j["uid"], j["task"], j.get("workers")) or {}
                j["last_result"] = str(r.get("final", ""))[:500]
            except Exception as e:
                j["last_result"] = f"error: {e}"
        j["last_run"] = now
        # Следующий запуск — по типу расписания самого джоба (interval или time-of-day)
        j["next_run"] = compute_next_run(j, now)
        changed = True
    if changed:
        with _LOCK:
            _save(jobs)


def start():
    def _loop():
        while True:
            time.sleep(60)
            try:
                _tick()
            except Exception:
                pass
    threading.Thread(target=_loop, daemon=True).start()
