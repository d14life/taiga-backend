#!/usr/bin/env python3
"""
mlx_compressor.py — ЛОКАЛЬНЫЙ компрессор на Apple Silicon (MLX). Дух CLaRa: сжимаем найденные
куски/память ПРЯМО на Mac, бесплатно и приватно (идеал для RU-uncensored). Когда Apple выпустит
MLX-CLaRa — подменим только MODEL, остальное тут готово.

Запуск (в mlx-venv): ~/.taiga/mlx-venv/bin/python3 mlx_compressor.py
Эндпоинт: POST http://127.0.0.1:8791/compress  {"text": "...", "ratio": 6}  → {"compressed": "..."}
          GET  /health → {"ok": true, "model": "..."}
Бэкенд Тайги зовёт это для RAG/памяти; если сервис не поднят — у бэка текст-фолбэк (дешёвая модель).
Модель задаётся env TAIGA_MLX_MODEL (дефолт — небольшая 4-bit, влезает на 16GB/тесный диск).
"""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MODEL = os.environ.get("TAIGA_MLX_MODEL", "mlx-community/Qwen2.5-3B-Instruct-4bit")
PORT = int(os.environ.get("TAIGA_MLX_PORT", "8791"))

_model = None
_tok = None


def _load():
    global _model, _tok
    if _model is None:
        from mlx_lm import load  # тяжёлый импорт — лениво
        print(f"[mlx_compressor] загружаю {MODEL} …", flush=True)
        _model, _tok = load(MODEL)
        print("[mlx_compressor] модель готова", flush=True)
    return _model, _tok


def compress(text: str, ratio: int = 6) -> str:
    from mlx_lm import generate
    model, tok = _load()
    target = max(20, len(text) // max(2, ratio))
    prompt = (
        "Ты — компрессор знаний. Сожми текст ниже до сути, сохрани ВСЕ факты, числа, имена, сущности; "
        f"выкинь воду и повторы. Не длиннее ~{target} символов. Верни ТОЛЬКО сжатый текст.\n\nТЕКСТ:\n" + text
    )
    msgs = [{"role": "user", "content": prompt}]
    try:
        chat = tok.apply_chat_template(msgs, add_generation_prompt=True)
        out = generate(model, tok, prompt=chat, max_tokens=max(64, target // 2), verbose=False)
    except Exception:
        out = generate(model, tok, prompt=prompt, max_tokens=max(64, target // 2), verbose=False)
    return (out or "").strip()


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self._send(200, {"ok": True, "model": MODEL, "loaded": _model is not None})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/compress":
            return self._send(404, {"error": "not found"})
        try:
            n = int(self.headers.get("Content-Length") or 0)
            req = json.loads(self.rfile.read(n).decode("utf-8") or "{}")
            text = str(req.get("text") or "").strip()
            if not text:
                return self._send(400, {"error": "empty text"})
            ratio = int(req.get("ratio") or 6)
            out = compress(text, ratio)
            self._send(200, {"compressed": out, "orig_len": len(text), "comp_len": len(out), "model": MODEL})
        except Exception as e:
            self._send(500, {"error": str(e)[:200]})


def main():
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), H)
    print(f"[mlx_compressor] слушаю http://127.0.0.1:{PORT} (модель {MODEL})", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    sys.exit(main())
