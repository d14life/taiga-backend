"""Планировщик фоновых/расписание-агентов Тайги (дыра #11 vs Hermes/GitHub Agents).

Джоб = {id, uid, task, workers, interval_sec, next_run, enabled, last_run, last_result}.
Демон-поток раз в минуту проверяет due-джобы и гонит их через orchestrator (runner из server.py).
Анти-runaway: мин интервал 600с; если non-owner с нулевым балансом — джоб пропускается.
"""
import json
import time
import threading
from pathlib import Path

BASE = Path("~/.mostik-ai").expanduser()
_JOBS = BASE / "jobs.json"
_MIN_INTERVAL = 600          # не чаще раза в 10 минут (анти-абуз/стоимость)
_RUNNER = None               # callback(uid, task, workers) -> dict; ставит server.py
_LOCK = threading.Lock()


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


def add_job(uid: str, task: str, interval_sec: int, workers=None) -> dict:
    task = str(task or "").strip()
    if not task:
        return {"error": "пустая задача"}
    interval = max(_MIN_INTERVAL, int(interval_sec or 3600))
    with _LOCK:
        jobs = _load()
        job = {"id": _jid(uid), "uid": uid, "task": task[:500], "workers": workers,
               "interval_sec": interval, "next_run": time.time() + interval,
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
        j["next_run"] = now + j.get("interval_sec", 3600)
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
