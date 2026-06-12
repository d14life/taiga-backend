#!/usr/bin/env python3
"""Тест НОВЫХ эндпоинтов на отдельном порту 8779 (не трогаем :8777)."""
import threading, time, json, urllib.request
import server
from http.server import ThreadingHTTPServer

srv = ThreadingHTTPServer(("127.0.0.1", 8779), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
time.sleep(0.4)
B = "http://127.0.0.1:8779"

print("=== GET /api/video-models ===")
d = json.loads(urllib.request.urlopen(B + "/api/video-models", timeout=10).read())
print("have nanogpt:", d.get("have"), "| models:", len(d.get("models", [])))
print("first:", d["models"][0])

print("\n=== POST /api/video (wan-turbo, SSE) ===")
body = json.dumps({"user": "default", "model": "wan-video-22-turbo",
                   "prompt": "neon tiger in a snowy taiga, cinematic", "duration": "5",
                   "aspect_ratio": "16:9"}).encode()
req = urllib.request.Request(B + "/api/video", data=body,
                             headers={"Content-Type": "application/json"}, method="POST")
got_url = None
with urllib.request.urlopen(req, timeout=600) as r:
    buf = ""
    for raw in r:
        buf += raw.decode("utf-8", "ignore")
        while "\n\n" in buf:
            chunk, buf = buf.split("\n\n", 1)
            line = next((l for l in chunk.split("\n") if l.startswith("data:")), None)
            if not line:
                continue
            ev = json.loads(line[5:].strip())
            t = ev.get("type")
            if t == "video_status":
                print(f"  status={ev.get('status')} elapsed={ev.get('elapsed','')}")
            elif t == "video":
                got_url = ev.get("url")
                print("  VIDEO url:", got_url, "| cost:", ev.get("cost"))
            elif t == "error":
                print("  ERROR:", ev.get("message"))
            elif t == "done":
                print("  done")
srv.shutdown()
print("\nRESULT:", "OK" if got_url else "NO URL")
