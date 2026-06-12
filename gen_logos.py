#!/usr/bin/env python3
"""Гоним 4 логотип-иконки Тайга ИИ через наш бэкенд (/api/chat, image-модель)."""
import json, base64, os, sys, urllib.request, urllib.error

OUT = os.path.expanduser("~/Downloads/claude-sessions/2026-06-12/taiga-logos")
os.makedirs(OUT, exist_ok=True)
API = "http://localhost:3000/api/chat"
MODEL = "recraft-v4-pro"

BASE = ("minimalist vector logo, flat iconic mark, centered, on deep charcoal black "
        "background, premium tech brand, clean negative space, high contrast, app icon, "
        "1:1, no text, no letters, crisp edges")

VARIANTS = {
    "1_cedar_neural": ("Single stylized evergreen pine/cedar tree where the branches turn into "
                       "glowing neural-network nodes and connecting lines, geometric and minimal, "
                       "warm orange-to-magenta gradient glow, dark boreal-tech feel, monoline style. "),
    "2_monogram_T":   ("A geometric letter shaped like a triangular pine tree and a mountain peak, "
                       "sharp minimal monogram, subtle gradient from amber orange to hot pink, emblem mark. "),
    "3_taiga_spark":  ("Abstract minimal silhouette of a layered taiga forest and a mountain ridge, "
                       "with a single glowing spark/orb of light rising above like an AI core, "
                       "aurora gradient (orange, magenta, hint of cyan), calm premium, lots of dark space. "),
    "4_geo_neurocedar":("Ultra-minimal geometric mark: a triangle made of thin connected lines and dots "
                        "(constellation/circuit) forming an abstract pine tree, single-weight lines, "
                        "glowing gradient stroke orange to pink on black, modern AI startup logo. "),
}

def gen(name, prompt):
    body = json.dumps({
        "user": "default", "model": MODEL, "agent": True,
        "max_tokens": 256, "messages": [{"role": "user", "content": prompt + BASE}],
    }).encode()
    req = urllib.request.Request(API, data=body, headers={"content-type": "application/json"})
    url, err = "", ""
    try:
        with urllib.request.urlopen(req, timeout=240) as r:
            buf = ""
            for raw in r:
                buf += raw.decode("utf-8", "ignore")
                while "\n\n" in buf:
                    chunk, buf = buf.split("\n\n", 1)
                    line = next((l for l in chunk.split("\n") if l.startswith("data:")), None)
                    if not line:
                        continue
                    try:
                        ev = json.loads(line[5:].strip())
                    except Exception:
                        continue
                    if ev.get("type") == "image" and ev.get("url"):
                        url = ev["url"]
                    elif ev.get("type") == "error":
                        err = ev.get("message") or ev.get("error") or "ошибка"
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}: {e.read().decode('utf-8','ignore')[:200]}"
    except Exception as e:
        return None, str(e)
    if not url:
        return None, err or "картинка не пришла"
    path = os.path.join(OUT, name + ".png")
    if url.startswith("data:"):
        b64 = url.split(",", 1)[1]
        with open(path, "wb") as f:
            f.write(base64.b64decode(b64))
    else:
        try:
            with urllib.request.urlopen(url, timeout=120) as ir, open(path, "wb") as f:
                f.write(ir.read())
        except Exception as e:
            return None, f"download fail: {e}"
    return path, None

for name, prompt in VARIANTS.items():
    print(f"… генерю {name}", flush=True)
    path, err = gen(name, prompt)
    if path:
        print(f"OK  {path} ({os.path.getsize(path)} bytes)", flush=True)
    else:
        print(f"FAIL {name}: {err}", flush=True)
print("DONE ->", OUT)
