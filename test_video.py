#!/usr/bin/env python3
"""Прямой тест видео-API NanoGPT: submit -> poll -> url. Дешёвая модель."""
import json, time, os, urllib.request, urllib.error

KEY = open(os.path.expanduser("~/.nanogpt_key")).read().strip()
SUBMIT = "https://nano-gpt.com/api/generate-video"
STATUS = "https://nano-gpt.com/api/video/status?requestId="
H = {"x-api-key": KEY, "Content-Type": "application/json"}

def post(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=H, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())

def get(url):
    req = urllib.request.Request(url, headers=H, method="GET")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())

print(">> submit wan-video-22-turbo …")
try:
    sub = post(SUBMIT, {
        "model": "wan-video-22-turbo",
        "prompt": "a misty taiga forest at dawn, cinematic slow camera, soft light",
        "duration": "5",
        "aspect_ratio": "16:9",
    })
except urllib.error.HTTPError as e:
    print("SUBMIT HTTP", e.code, e.read().decode("utf-8","ignore")[:400]); raise SystemExit
print("submit resp:", json.dumps(sub)[:300])
rid = sub.get("runId") or sub.get("id")
if not rid:
    print("NO runId — full resp:", json.dumps(sub)); raise SystemExit
print("runId:", rid, "| cost:", sub.get("cost"), "| balance:", sub.get("remainingBalance"))

t0 = time.time()
for i in range(75):  # ~5 min @ 4s
    time.sleep(4)
    try:
        st = get(STATUS + rid)
    except urllib.error.HTTPError as e:
        if e.code >= 500:
            continue
        print("POLL HTTP", e.code, e.read().decode("utf-8","ignore")[:300]); raise SystemExit
    data = st.get("data", st)
    status = str(data.get("status", "")).upper()
    print(f"  [{int(time.time()-t0)}s] status={status}")
    if status == "COMPLETED":
        url = (((data.get("output") or {}).get("video") or {}).get("url")
               or data.get("url") or (data.get("output") or {}).get("url"))
        print("DONE url:", url)
        break
    if status in ("FAILED", "ERROR"):
        print("FAILED:", json.dumps(data)[:400]); break
else:
    print("TIMEOUT")
