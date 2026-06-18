#!/usr/bin/env python3
"""
external-critique.py — СОВЕТ внешних моделей + СИНТЕЗ (как «Совет» в Тайге).
Несколько НЕ-Claude моделей независимо критикуют кусок кода / док требований, сверяясь с живым
вебом, потом chairman синтезирует в один вердикт. «Другой взгляд на шестерёнки» + анти-само-суд Claude.

Работает из РФ напрямую:
  • Совет: NVIDIA deepseek-r1 + NVIDIA llama-3.3-70b (разные семейства = разный взгляд)
  • Веб: Serper (живой Google, из РФ напрямую)
  • Gemini 2.5 + Google-grounding — добавляется в совет КОГДА есть маршрут (немецкий туннель :1080
    или ssh mostik); если нет — совет идёт без него, не падает.
  • Синтез: chairman (NVIDIA) сводит критики: согласие = высокая уверенность, расхождения = флаг.
Ключи — ~/.reel-intelligence.env (NVIDIA + SERPER + GEMINI).

Usage:
  python3 tools/external-critique.py "Критикуй: <claim/решение>"
  python3 tools/external-critique.py --file path/to/chunk.tsx "Эта реализация фичи X корректна/идеальна?"
  python3 tools/external-critique.py --file docs/TAIGA-REQUIREMENTS.md "Эти требования полны и непротиворечивы?"
"""
import os, sys, json, urllib.request, argparse, socket
from concurrent.futures import ThreadPoolExecutor

ENV = os.path.expanduser("~/.reel-intelligence.env")
NV_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

def load_env():
    d = {}
    try:
        for line in open(ENV):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1); d[k.strip()] = v.strip()
    except FileNotFoundError: pass
    return d

def tunnel_up(port=1080):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1): return True
    except OSError: return False

def serper_web(query, key, n=6):
    if not key: return "(нет Serper-ключа)"
    try:
        req = urllib.request.Request("https://google.serper.dev/search",
            data=json.dumps({"q": query, "num": n}).encode(),
            headers={"X-API-KEY": key, "Content-Type": "application/json"})
        r = json.load(urllib.request.urlopen(req, timeout=20))
        return "\n".join(f"- {o.get('title','')}: {o.get('snippet','')} ({o.get('link','')})"
                         for o in r.get("organic", [])[:n]) or "(веб пусто)"
    except Exception as e: return f"(serper-ошибка: {e})"

def nvidia(messages, key, model, max_tokens=1200, temp=0.3, timeout=75):
    body = {"model": model, "messages": messages, "temperature": temp, "max_tokens": max_tokens}
    req = urllib.request.Request(NV_URL, data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    return r["choices"][0]["message"]["content"]

CRITIC_SYS = ("Ты независимый внешний критик-инженер в совете моделей. Найди слабые места, риски, "
              "несоответствия best-practices, баги, что упущено — и лучшие альтернативы. Будь конкретным "
              "и честным, НЕ льсти. Опирайся на веб-факты где уместно. Заверши явным вердиктом: ИДЕАЛЬНО / "
              "НУЖНЫ ПРАВКИ (список).")

def member_nvidia(subject, web, key, model):
    try:
        return nvidia([{"role": "system", "content": CRITIC_SYS},
                       {"role": "user", "content": f"{subject}\n\nЖИВОЙ ВЕБ:\n{web}"}], key, model)
    except Exception as e:
        if "deepseek" in model:  # фолбэк
            return member_nvidia(subject, web, key, "meta/llama-3.3-70b-instruct")
        return f"(модель {model} недоступна: {e})"

def member_gemini(subject, gkey):
    """Gemini + grounding, если есть маршрут (туннель :1080). Иначе None — совет идёт без него."""
    if not gkey or not tunnel_up(): return None
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=gkey, http_options=types.HttpOptions(
            client_args={"proxy": "socks5://127.0.0.1:1080"}))
        cfg = types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())])
        r = client.models.generate_content(model="gemini-2.5-flash",
            contents=f"{CRITIC_SYS}\n\n{subject}", config=cfg)
        return r.text
    except Exception:
        return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt")
    ap.add_argument("--file", default="")
    args = ap.parse_args()
    env = load_env()
    nv = env.get("NVIDIA_API_KEY", ""); serper = env.get("SERPER_API_KEY", ""); gkey = env.get("GEMINI_API_KEY", "")
    if not nv:
        print("Нет NVIDIA_API_KEY в ~/.reel-intelligence.env — совет не запустить."); sys.exit(1)

    subject = args.prompt
    if args.file:
        try:
            body = open(args.file).read()
            subject += f"\n\n=== ФАЙЛ {args.file} ===\n{body[:14000]}"
        except Exception as e:
            print(f"Не прочитать {args.file}: {e}"); sys.exit(1)

    web = serper_web(args.prompt[:120], serper)

    # СОВЕТ — параллельно: deepseek + llama (+ gemini если маршрут)
    with ThreadPoolExecutor(max_workers=3) as ex:
        f_ds = ex.submit(member_nvidia, subject, web, nv, "deepseek-ai/deepseek-r1")
        f_ll = ex.submit(member_nvidia, subject, web, nv, "meta/llama-3.3-70b-instruct")
        f_gm = ex.submit(member_gemini, subject, gkey)
        ds, ll, gm = f_ds.result(), f_ll.result(), f_gm.result()

    panel = [("deepseek-r1", ds), ("llama-3.3-70b", ll)]
    if gm: panel.append(("gemini-2.5-grounded", gm))

    for name, txt in panel:
        print(f"\n===== СОВЕТНИК: {name} =====\n{txt}")

    # СИНТЕЗ — chairman сводит совет
    joined = "\n\n".join(f"[{n}]\n{t}" for n, t in panel)
    try:
        synth = nvidia([
            {"role": "system", "content": "Ты chairman совета критиков. Сведи мнения советников в ОДИН "
             "вердикт: что ВСЕ согласны (высокая уверенность) · где расходятся (флаг, осторожно) · "
             "итоговый список правок по приоритету · финал ИДЕАЛЬНО / НУЖНЫ ПРАВКИ."},
            {"role": "user", "content": f"Тема: {args.prompt}\n\nМНЕНИЯ СОВЕТА:\n{joined}"}],
            nv, "meta/llama-3.1-8b-instruct", max_tokens=1000, timeout=60)
        print(f"\n\n##### СИНТЕЗ (chairman) #####\n{synth}")
    except Exception as e:
        print(f"\n(синтез недоступен: {e})")
    print(f"\n[совет: {len(panel)} модели{'+gemini' if gm else ', gemini вне маршрута'} · веб: serper]")

if __name__ == "__main__":
    main()
