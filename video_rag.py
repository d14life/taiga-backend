# video_rag.py — L22: запомнить/сослаться на веб-видео (RAG).
#
# Дано URL видео → достаём ТРАНСКРИПТ (бесплатно, где можно) + при возможности сэмплим
# несколько КАДРОВ (зрячая модель подписывает) → склеиваем в текст → кладём в существующий
# RAG-стор юзера (rag_ingest, source="video"). Дальше юзер задаёт вопросы по видео в чате.
#
# Реалистично и дёшево, stdlib-only оркестрация над тем, что уже есть в server.py:
#   • YouTube → timedtext-субтитры (без ключа) + текст страницы через Jina Reader.
#   • прямой медиа-URL (mp4/webm/…) → ffmpeg сэмплит N кадров → _rag_vlm_caption их подписывает.
#   • любая страница → _jina_read как фоллбэк (описание/расшифровка часто есть в HTML).
# Тяжёлого скачивания произвольных стримов НЕ делаем (стоимость/риск) — деградируем мягко.
#
# server.py передаёт себя (helpers: _jina_read, _is_public_url, _ssrf_safe_opener,
# _rag_vlm_caption, rag_ingest, _rag_chunks). Pure module, без сайд-эффектов на импорте.

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import urllib.parse
import urllib.request


_YT_RE = re.compile(r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)([A-Za-z0-9_-]{6,})")
_MEDIA_EXT = (".mp4", ".webm", ".mov", ".m4v", ".mkv", ".avi")
_UA = "Mozilla/5.0"


def _yt_id(url: str) -> str:
    m = _YT_RE.search(url or "")
    return m.group(1) if m else ""


def _yt_transcript(server, vid: str) -> str:
    """Бесплатные субтитры YouTube через timedtext (ru→en→авто). Пусто при отсутствии."""
    base = "https://www.youtube.com/api/timedtext"
    for params in (
        {"lang": "ru", "v": vid},
        {"lang": "en", "v": vid},
        {"lang": "ru", "v": vid, "kind": "asr"},
        {"lang": "en", "v": vid, "kind": "asr"},
    ):
        try:
            u = base + "?" + urllib.parse.urlencode(params)
            req = urllib.request.Request(u, headers={"User-Agent": _UA})
            xml = server._ssrf_safe_opener().open(req, timeout=20).read(2_000_000).decode("utf-8", "ignore")
        except Exception:
            continue
        if not xml or "<text" not in xml:
            continue
        # вытаскиваем текст из <text ...>…</text>, чистим html-сущности
        import html as _html
        parts = re.findall(r"<text[^>]*>(.*?)</text>", xml, flags=re.S)
        txt = " ".join(_html.unescape(re.sub(r"<[^>]+>", " ", p)).strip() for p in parts)
        txt = re.sub(r"\s+", " ", txt).strip()
        if len(txt) > 80:
            return txt
    return ""


def _page_text(server, url: str) -> str:
    """Текст страницы видео (описание/расшифровка) через Jina Reader. Пусто при сбое."""
    try:
        t = server._jina_read(url)
        return re.sub(r"\s+", " ", t or "").strip()
    except Exception:
        return ""


def _sample_frames_captions(server, url: str, n_frames: int = 3, max_mb: int = 60) -> str:
    """Прямой медиа-URL → ffmpeg сэмплит n кадров → зрячая модель подписывает.
    Возвращает склеенные подписи (или '' — если не медиа / нет ffmpeg / сбой). Безопасно."""
    if not shutil.which("ffmpeg"):
        return ""
    low = (url or "").lower().split("?")[0]
    if not low.endswith(_MEDIA_EXT):
        return ""               # подписываем кадры только у прямых медиа-файлов
    if not server._is_public_url(url):
        return ""
    tmp = tempfile.mkdtemp(prefix="taiga-vrag-")
    try:
        src = os.path.join(tmp, "v.mp4")
        try:
            rq = urllib.request.Request(url, headers={"User-Agent": _UA})
            with server._ssrf_safe_opener().open(rq, timeout=90) as r, open(src, "wb") as f:
                limit = max_mb * 1024 * 1024
                got = 0
                while True:
                    chunk = r.read(262144)
                    if not chunk:
                        break
                    got += len(chunk)
                    if got > limit:     # не тянем гигантские файлы — берём начало для кадров
                        break
                    f.write(chunk)
        except Exception:
            return ""
        # равномерно n кадров (fps очень низкий) в jpg
        pat = os.path.join(tmp, "f%02d.jpg")
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-i", src, "-vf", "fps=1/30,scale=768:-1",
                 "-frames:v", str(max(1, n_frames)), pat],
                capture_output=True, timeout=120)
        except Exception:
            return ""
        caps = []
        for i in range(1, n_frames + 1):
            fp = os.path.join(tmp, "f%02d.jpg" % i)
            if not os.path.exists(fp):
                continue
            try:
                import base64
                raw = open(fp, "rb").read()
                data_url = "data:image/jpeg;base64," + base64.b64encode(raw).decode("ascii")
                cap = server._rag_vlm_caption(data_url, hint="Это кадр из видео. Опиши, что на нём.")
                if cap:
                    caps.append(f"[кадр {i}] {cap}")
            except Exception:
                continue
        return "\n".join(caps)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def ingest_video(server, uid: str, url: str, name: str = "",
                 workspace=None, with_frames: bool = True) -> dict:
    """Главная: URL видео → транскрипт (+опц. кадры) → RAG-стор юзера.
    Возвращает {ok, chunks, name, parts:[...], error?}. Не кидает наверх."""
    url = (url or "").strip()
    if not url.startswith(("http://", "https://")):
        return {"ok": False, "error": "нужен http(s) URL видео"}
    if not server._is_public_url(url):
        return {"ok": False, "error": "разрешены только публичные URL"}

    parts = []           # из чего собрали (для UI)
    blocks = []          # текстовые блоки для индексации
    vid = _yt_id(url)
    if vid:
        tr = _yt_transcript(server, vid)
        if tr:
            blocks.append("ТРАНСКРИПТ:\n" + tr)
            parts.append("субтитры")

    page = _page_text(server, url)
    if page:
        blocks.append("СТРАНИЦА ВИДЕО:\n" + page[:6000])
        parts.append("описание страницы")

    if with_frames:
        caps = _sample_frames_captions(server, url)
        if caps:
            blocks.append("КАДРЫ ВИДЕО:\n" + caps)
            parts.append("кадры")

    text = ("ИСТОЧНИК: " + url + "\n\n" + "\n\n".join(blocks)).strip()
    if not blocks or len(text) < 120:
        return {"ok": False, "error": "не удалось достать содержимое видео (нет субтитров/расшифровки) — попробуй другое видео или вставь текст вручную",
                "parts": parts}

    doc = (name or "").strip() or _default_name(url, vid)
    try:
        n = server.rag_ingest(uid, doc, text, workspace=workspace, source="video")
    except Exception as e:
        return {"ok": False, "error": f"не сохранил в память: {e}", "parts": parts}
    return {"ok": True, "chunks": n, "name": doc, "parts": parts}


def _default_name(url: str, vid: str) -> str:
    if vid:
        return f"видео-{vid}"
    tail = urllib.parse.urlparse(url).path.rsplit("/", 1)[-1]
    return ("видео-" + (tail or "url"))[:60]
