"""Auth для Тайги: signup/login (PBKDF2) + подписанные session-токены (HMAC).

Аддитивно — НЕ ломает текущий uid-режим; фронт может перейти на токены постепенно.
Пароли НИКОГДА не хранятся в открытом виде (только PBKDF2-SHA256 хэш + соль).
Хранилище — BASE/auth.json; секрет подписи — BASE/.auth_secret (0600).
"""
import json
import os
import re
import hmac
import time
import base64
import hashlib
from pathlib import Path

BASE = Path("~/.mostik-ai").expanduser()
_AUTH_FILE = BASE / "auth.json"


def _secret() -> bytes:
    p = BASE / ".auth_secret"
    if not p.exists():
        BASE.mkdir(parents=True, exist_ok=True)
        p.write_bytes(base64.b64encode(os.urandom(32)))
        try:
            p.chmod(0o600)
        except Exception:
            pass
    return p.read_bytes()


def _load() -> dict:
    try:
        return json.loads(_AUTH_FILE.read_text())
    except Exception:
        return {}


def _save(d: dict):
    BASE.mkdir(parents=True, exist_ok=True)
    tmp = _AUTH_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False))
    tmp.replace(_AUTH_FILE)
    try:
        _AUTH_FILE.chmod(0o600)
    except Exception:
        pass


_PBKDF2_ITERS = 600000   # OWASP-2023 минимум для PBKDF2-SHA256


def _hash_pw(pw: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), _PBKDF2_ITERS).hex()


def _safe_uname(u) -> str:
    return re.sub(r"[^a-z0-9_.-]", "", str(u).lower())[:40]


def make_token(uid: str, days: int = 30) -> str:
    body = f"{uid}.{int(time.time()) + days * 86400}"
    sig = hmac.new(_secret(), body.encode(), hashlib.sha256).hexdigest()[:32]
    return base64.urlsafe_b64encode(f"{body}.{sig}".encode()).decode()


def uid_from_token(token: str):
    """Вернуть uid если токен валиден и не просрочен, иначе None."""
    try:
        raw = base64.urlsafe_b64decode(str(token).encode()).decode()
        uid, exp, sig = raw.rsplit(".", 2)
        good = hmac.new(_secret(), f"{uid}.{exp}".encode(), hashlib.sha256).hexdigest()[:32]
        if hmac.compare_digest(sig, good) and int(exp) > int(time.time()):
            return uid
    except Exception:
        pass
    return None


def signup(username: str, password: str) -> dict:
    u = _safe_uname(username)
    if not u or len(str(password)) < 6:
        return {"error": "имя и пароль (≥6 символов) обязательны"}
    d = _load()
    if u in d:
        return {"error": "имя занято"}
    salt = base64.b64encode(os.urandom(12)).decode()
    uid = "u_" + hashlib.sha256((u + salt).encode()).hexdigest()[:16]
    d[u] = {"uid": uid, "salt": salt, "pw": _hash_pw(password, salt), "created": int(time.time())}
    _save(d)
    return {"ok": True, "uid": uid, "token": make_token(uid), "username": u}


def login(username: str, password: str) -> dict:
    u = _safe_uname(username)
    rec = _load().get(u)
    # PBKDF2 считаем ВСЕГДА (даже если юзера нет) + сравнение constant-time —
    # иначе по времени ответа можно перебрать существующие имена (user-enumeration).
    salt = (rec or {}).get("salt") or "x" * 16
    stored = (rec or {}).get("pw") or "0" * 64
    calc = _hash_pw(str(password), salt)
    if not rec or not hmac.compare_digest(stored, calc):
        return {"error": "неверное имя или пароль"}
    return {"ok": True, "uid": rec["uid"], "token": make_token(rec["uid"]), "username": u}
