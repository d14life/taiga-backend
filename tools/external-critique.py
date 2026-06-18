#!/usr/bin/env python3
"""
external-critique.py — ВНЕШНИЙ критик: живой веб + НЕ-Claude модель.
Даёт «другой взгляд на шестерёнки системы» + сверку с вебом (best-practices/реальность),
чтобы Claude не судил сам себя. Работает из РФ.

Источники (по убыванию приоритета, авто-фолбэк):
  1) Gemini 2.5 + Google-grounding (живой цитируемый веб) — если поднят туннель :1080
  2) Serper (Google-веб напрямую из РФ, без туннеля) + NVIDIA-модель (deepseek/llama) — основной путь
Ключи берутся из ~/.reel-intelligence.env (NVIDIA + SERPER + GEMINI).

Usage:
  python3 tools/external-critique.py "Критикуй: <фича/решение/claim>" [--context "<доп.контекст>"]
"""
import os, sys, json, urllib.request, urllib.error, argparse, socket

ENV = os.path.expanduser("~/.reel-intelligence.env")

def load_env():
    d = {}
    try:
        for line in open(ENV):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                d[k.strip()] = v.strip()
    except FileNotFoundError:
        pass
    return d

def tunnel_up(port=1080):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            return True
    except OSError:
        return False

def serper_web(query, key, n=6):
    """Живой Google-веб напрямую (работает из РФ)."""
    try:
        req = urllib.request.Request(
            "https://google.serper.dev/search",
            data=json.dumps({"q": query, "num": n}).encode(),
            headers={"X-API-KEY": key, "Content-Type": "application/json"},
        )
        r = json.load(urllib.request.urlopen(req, timeout=20))
        out = []
        for o in r.get("organic", [])[:n]:
            out.append(f"- {o.get('title','')}: {o.get('snippet','')} ({o.get('link','')})")
        return "\n".join(out) or "(веб ничего не вернул)"
    except Exception as e:
        return f"(serper-ошибка: {e})"

def nvidia_critique(prompt, web, key, model="deepseek-ai/deepseek-r1"):
    """Независимая НЕ-Claude модель на NVIDIA (работает из РФ)."""
    sys_p = ("Ты независимый внешний критик-инженер. Твоя задача — НАЙТИ слабые места, риски, "
             "несоответствия best-practices и лучшие альтернативы. Будь конкретным и честным, "
             "не льсти. Опирайся на веб-факты ниже, где уместно.")
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": sys_p},
            {"role": "user", "content": f"{prompt}\n\nЖИВОЙ ВЕБ (для сверки):\n{web}\n\n"
                                        f"Дай критику: 1) что не так/рискованно, 2) что говорит веб/индустрия, "
                                        f"3) лучшие альтернативы, 4) вердикт."},
        ],
        "temperature": 0.3, "max_tokens": 1200,
    }
    try:
        req = urllib.request.Request(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            data=json.dumps(body).encode(),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        )
        r = json.load(urllib.request.urlopen(req, timeout=90))
        return r["choices"][0]["message"]["content"]
    except Exception as e:
        # фолбэк на llama если deepseek недоступен
        if "deepseek" in model:
            return nvidia_critique(prompt, web, key, model="meta/llama-3.3-70b-instruct")
        return f"(nvidia-ошибка: {e})"

def gemini_grounded(prompt, gkey):
    """Gemini 2.5 + Google-grounding через немецкий туннель (живой цитируемый веб + другой LLM)."""
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=gkey, http_options=types.HttpOptions(
            client_args={"proxy": "socks5://127.0.0.1:1080"}))
        cfg = types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())])
        r = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Ты независимый внешний критик. Найди слабые места, риски, что говорит индустрия, "
                     f"лучшие альтернативы. Сверься с живым вебом.\n\n{prompt}",
            config=cfg)
        return r.text
    except Exception as e:
        return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt")
    ap.add_argument("--context", default="")
    args = ap.parse_args()
    env = load_env()
    full = args.prompt + (f"\n\nКонтекст:\n{args.context}" if args.context else "")

    # 1) Gemini + grounding если туннель жив (лучший: другой LLM + цитируемый веб)
    gkey = env.get("GEMINI_API_KEY")
    if gkey and tunnel_up():
        g = gemini_grounded(full, gkey)
        if g:
            print("=== ВНЕШНИЙ КРИТИК (Gemini 2.5 + Google-grounding) ===\n")
            print(g); return

    # 2) Serper веб + NVIDIA независимая модель (надёжно из РФ)
    serper = env.get("SERPER_API_KEY", "")
    nv = env.get("NVIDIA_API_KEY", "")
    web = serper_web(args.prompt[:120], serper) if serper else "(нет Serper-ключа)"
    if nv:
        print("=== ВНЕШНИЙ КРИТИК (NVIDIA deepseek + Serper-веб) ===\n")
        print(nvidia_critique(full, web, nv))
    else:
        print("ЖИВОЙ ВЕБ:\n" + web + "\n\n(нет NVIDIA-ключа для модели-критика)")

if __name__ == "__main__":
    main()
