"""Скиллы-маркетплейс Тайги (дыра #8 vs ECC/Claude Code).

Библиотека SKILL.md с поиском + security-scan + ПРОГРЕССИВНОЙ загрузкой (агент ищет скилл →
грузит тело по требованию, не держит всё в контексте). Источник seed — ECC (MIT, 868 скиллов).
Индекс — BASE/skills_index.json; тела — BASE/skills_lib/<id>.md.
"""
import json
import re
from pathlib import Path

BASE = Path("~/.mostik-ai").expanduser()
_DIR = BASE / "skills_lib"
_INDEX = BASE / "skills_index.json"


def load_index() -> list:
    try:
        return json.loads(_INDEX.read_text())
    except Exception:
        return []


def save_index(idx: list):
    BASE.mkdir(parents=True, exist_ok=True)
    tmp = _INDEX.with_suffix(".tmp")
    tmp.write_text(json.dumps(idx, ensure_ascii=False))
    tmp.replace(_INDEX)


def _parse_skill(text: str):
    """SKILL.md: frontmatter (name/description) + body. Фолбэк — первый #заголовок/абзац."""
    name, desc, body = "", "", text
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)
    if m:
        fm, body = m.group(1), m.group(2)
        for line in fm.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                k, v = k.strip().lower(), v.strip().strip('"\'')
                if k == "name":
                    name = v
                elif k == "description":
                    desc = v
    if not name:
        h = re.search(r"^#\s+(.+)$", body, re.M)
        name = h.group(1).strip() if h else ""
    if not desc:
        p = re.search(r"^\s*([A-Za-zА-Яа-я].{20,})$", body, re.M)
        desc = p.group(1).strip() if p else ""
    return name.strip()[:80], desc[:300], body


def _scan(text: str) -> str:
    """Security-scan: режем секреты в импортируемых скиллах (не отклоняем — скиллы легитимны)."""
    try:
        from guard import redact_secrets
        return redact_secrets(text)
    except Exception:
        return text


def import_dir(src_dir: str, limit: int = 400) -> int:
    _DIR.mkdir(parents=True, exist_ok=True)
    idx = load_index()
    have = {s["name"] for s in idx}
    n = 0
    for fp in sorted(Path(src_dir).rglob("*.md")):
        if n >= limit:
            break
        try:
            text = fp.read_text("utf-8", "ignore")
        except Exception:
            continue
        if len(text) < 120:
            continue
        name, desc, body = _parse_skill(text)
        if not name or name in have:
            continue
        sid = (re.sub(r"[^a-z0-9_-]", "", name.lower().replace(" ", "-"))[:60] or f"skill{n}")
        (_DIR / f"{sid}.md").write_text(_scan(body))
        idx.append({"id": sid, "name": name, "description": desc})
        have.add(name)
        n += 1
    save_index(idx)
    return n


def search_skills(query: str, k: int = 8) -> list:
    """Прогрессивный поиск: вернуть имена+описания (без тел) релевантных скиллов."""
    terms = re.findall(r"\w{3,}", (query or "").lower())
    if not terms:
        return []
    scored = []
    for s in load_index():
        hay = (s["name"] + " " + s.get("description", "")).lower()
        score = sum(1 for t in set(terms) if t in hay)
        if score:
            scored.append((score, {"id": s["id"], "name": s["name"], "description": s.get("description", "")}))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in scored[:k]]


def get_skill(sid_or_name: str) -> str:
    """Загрузить тело скилла по id или имени (progressive load)."""
    key = (sid_or_name or "").lower()
    for s in load_index():
        if s["id"] == key or s["name"].lower() == key:
            try:
                return (_DIR / f"{s['id']}.md").read_text("utf-8", "ignore")[:8000]
            except Exception:
                return ""
    return ""


def count() -> int:
    return len(load_index())
