#!/usr/bin/env python3
"""
auto_update.py — авто-обновление каталога и бенчмарков Тайги (standalone, stdlib-only).

Что делает (запускать по таймеру launchd, см. низ файла):
  1) Тянет у каждого провайдера (Venice/NanoGPT/Chutes/Redpill) список моделей + ЦЕНЫ
     с их /models эндпоинта (Bearer-ключ из HOME) → пишет снапшот ~/.taiga/catalog-snapshot.json.
  2) Если есть ~/.aa_key — тянет бенчмарки Artificial Analysis (Intelligence + категории:
     coding/agentic/reasoning/...) → пишет ~/.taiga/aa-benchmarks.json (для авто-роутинга).
     Нет ключа → честный фолбэк: пишет заметку, статический _BENCH в server.py не трогаем.
  3) НЕ импортирует server.py (нет цикла), НЕ правит код. Только данные в ~/.taiga/.

Сервер потом МОЖЕТ опционально читать ~/.taiga/aa-benchmarks.json и подмешивать в bench()
(1 защищённая строка — добавляется отдельно, см. WIRE-заметку внизу). Сам скрипт безопасен:
сеть в try/except, частичный успех ок, ничего не ломает.
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

OUT_DIR = Path("~/.taiga").expanduser()
OUT_DIR.mkdir(parents=True, exist_ok=True)

PROVIDERS = {
    "venice":  {"models_url": "https://api.venice.ai/api/v1/models",            "key": "~/.venice_key"},
    "nanogpt": {"models_url": "https://nano-gpt.com/api/v1/models?detailed=true", "key": "~/.nanogpt_key"},
    "chutes":  {"models_url": "https://llm.chutes.ai/v1/models",                 "key": "~/.chutes_key"},
    "redpill": {"models_url": "https://api.redpill.ai/v1/models",                "key": "~/.redpill_key"},
}

TIMEOUT = 20


def _read_key(path: str):
    p = Path(path).expanduser()
    try:
        return p.read_text().strip() if p.exists() else None
    except Exception:
        return None


def _get_json(url: str, key: str = None):
    headers = {"Accept": "application/json", "User-Agent": "taiga-auto-update/1"}
    if key:
        headers["Authorization"] = "Bearer " + key
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def _pricing_of(m: dict):
    """Best-effort нормализация цены модели (форматы провайдеров разные)."""
    for k in ("pricing", "price", "cost"):
        if isinstance(m.get(k), dict):
            return m[k]
    out = {}
    for k in ("input", "output", "prompt", "completion", "input_price", "output_price",
              "prompt_price", "completion_price", "per1k", "per_million"):
        if k in m:
            out[k] = m[k]
    return out or None


def fetch_providers():
    snap = {"ts": time.time(), "ts_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "providers": {}}
    for name, cfg in PROVIDERS.items():
        key = _read_key(cfg["key"])
        entry = {"configured": bool(key), "models": [], "error": None}
        if not key:
            entry["error"] = "no key"
            snap["providers"][name] = entry
            print(f"  {name}: нет ключа — пропуск")
            continue
        try:
            data = _get_json(cfg["models_url"], key)
            rows = data.get("data") if isinstance(data, dict) else data
            rows = rows if isinstance(rows, list) else []
            for m in rows:
                if not isinstance(m, dict):
                    continue
                mid = m.get("id") or m.get("model") or m.get("name")
                if not mid:
                    continue
                entry["models"].append({"id": mid, "pricing": _pricing_of(m)})
            print(f"  {name}: {len(entry['models'])} моделей" + (" (+цены)" if any(x.get('pricing') for x in entry['models']) else ""))
        except urllib.error.HTTPError as e:
            entry["error"] = f"HTTP {e.code}"
            print(f"  {name}: ошибка HTTP {e.code}")
        except Exception as e:
            entry["error"] = str(e)[:120]
            print(f"  {name}: ошибка {str(e)[:80]}")
        snap["providers"][name] = entry
    return snap


# Artificial Analysis — бенчмарки/категории. Эндпоинт v2 (нужен ключ в заголовке).
AA_URL = "https://artificialanalysis.ai/api/v2/data/llms/models"


def fetch_aa():
    key = _read_key("~/.aa_key")
    out = {"ts": time.time(), "configured": bool(key), "models": [], "note": ""}
    if not key:
        out["note"] = ("нет ~/.aa_key — авто-обновление бенчмарков выключено. "
                       "Добавь ключ Artificial Analysis в ~/.aa_key, чтобы тянуть Intelligence + категории "
                       "(coding/agentic/reasoning) и подмешивать в авто-роутер. Пока используется статический _BENCH.")
        print("  AA: нет ключа — фолбэк (статический бенч)")
        return out
    try:
        data = _get_json(AA_URL, key)
        rows = data.get("data") if isinstance(data, dict) else data
        for m in (rows or []):
            if not isinstance(m, dict):
                continue
            out["models"].append({
                "name": m.get("name") or m.get("slug") or m.get("id"),
                "intelligence": (m.get("evaluations") or {}).get("artificial_analysis_intelligence_index")
                                or m.get("intelligence_index"),
                "coding": (m.get("evaluations") or {}).get("artificial_analysis_coding_index"),
                "agentic": (m.get("evaluations") or {}).get("artificial_analysis_agentic_index"),
                "math": (m.get("evaluations") or {}).get("artificial_analysis_math_index"),
            })
        print(f"  AA: {len(out['models'])} моделей с бенчами")
    except Exception as e:
        out["note"] = f"AA fetch error: {str(e)[:120]}"
        print(f"  AA: ошибка {str(e)[:80]}")
    return out


def main():
    print("=== auto_update: провайдеры (модели + цены) ===")
    snap = fetch_providers()
    (OUT_DIR / "catalog-snapshot.json").write_text(json.dumps(snap, ensure_ascii=False, indent=2))
    print("=== auto_update: Artificial Analysis (бенчмарки) ===")
    aa = fetch_aa()
    (OUT_DIR / "aa-benchmarks.json").write_text(json.dumps(aa, ensure_ascii=False, indent=2))
    total = sum(len(p["models"]) for p in snap["providers"].values())
    print(f"\nГотово: {total} моделей в снапшоте, AA={'on' if aa['configured'] else 'fallback'} → {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

# ── WIRE-заметка (опционально, добавить ОТДЕЛЬНО и аккуратно) ──────────────────────
# Чтобы сервер подмешивал свежие AA-бенчи в авто-роутер, в server.py в bench() ПЕРЕД возвратом
# можно (1 защищённая строка) глянуть ~/.taiga/aa-benchmarks.json и, если там есть модель, скорректировать
# балл. Делать осторожно (это горячий путь), с кэшем по mtime. Пока скрипт только готовит данные.
