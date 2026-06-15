# ad_gen.py — L14 AD-GENERATOR (Arcads-style UGC video ads), Studio-side.
#
# Поток: пользователь описывает ОДИН продукт (текст + опц. фото/URL) → Тайга пишет
# N коротких UGC-сценариев (RU, живой разговорный тон «как человек снял на телефон»).
# Дальше фронт (ad-generator.tsx) на каждый выбранный сценарий:
#   1) озвучка через существующий /api/audio (TTS),
#   2) говорящий аватар через существующий /api/video (avatar-модель: фото + аудио),
# то есть мы ОРКЕСТРИРУЕМ готовый медиа-стек, а не переписываем генерацию.
#
# Этот модуль отвечает ТОЛЬКО за «мозговую» часть, которую дёшево сделать на сервере:
#   • написать сценарии/хуки по брифу (один вызов модели, как verify/hook-aihelp),
#   • отдать фронту список avatar-моделей + рекомендованную (из живого VIDEO_MODELS).
# Никаких новых сетевых медиа-вызовов тут нет → нечего ломать в биллинге.
#
# Импортируется в server.py; использует его helpers (venice_complete, best_for_task,
# _extract_json_object, tool_fetch_url, CHEAP_MODEL). Чтобы не плодить циклический
# импорт, тянем их лениво через переданный модуль server в ad_scripts(...).

from __future__ import annotations

# Тон UGC — это и есть весь секрет Arcads-подобных реклам: НЕ корпоративный диктор,
# а живой человек с эмоцией, разговорной речью, конкретикой и одним чётким призывом.
_AD_SYS = (
    "Ты — сценарист коротких UGC-видеореклам (как у Arcads): человек на камеру телефона "
    "честно, живо и по-разговорному рассказывает о продукте. Пишешь по-русски, на «ты», "
    "без канцелярита и рекламного пафоса. Каждый ролик — 8–20 секунд речи (примерно "
    "25–55 слов), читается вслух за это время.\n"
    "Структура каждого сценария: 1) ХУК первой фразой (зацепить за 2 секунды — боль, "
    "вопрос, неожиданность), 2) суть/выгода продукта простыми словами с конкретикой, "
    "3) короткий чёткий призыв к действию.\n"
    "Разные сценарии = РАЗНЫЕ углы (боль / результат / сравнение / FOMO / личная история). "
    "Никаких ремарок в скобках, эмодзи, хэштегов, markdown — только то, что человек "
    "произнесёт вслух. Без обещаний, которых не было в брифе; без медицинских/финансовых "
    "гарантий.\n"
    "Верни СТРОГО JSON-объект: {\"scripts\":[{\"hook\":\"первая фраза-зацепка\","
    "\"script\":\"полный текст для озвучки, включая хук\",\"angle\":\"короткий ярлык угла "
    "по-русски\"}]}. Ровно N штук, ничего вне JSON."
)


def _clamp(n, lo, hi, default):
    try:
        n = int(n)
    except Exception:
        return default
    return max(lo, min(hi, n))


def ad_scripts(server, brief: str, n: int = 3, url: str = "",
               product: str = "", tone: str = "") -> dict:
    """Пишет N UGC-сценариев по брифу. server = модуль server.py (для его helpers).
    Возвращает {scripts:[{hook,script,angle}], model, n}. Никогда не кидает наверх."""
    brief = (brief or "").strip()
    product = (product or "").strip()
    n = _clamp(n, 1, 6, 3)

    # Опционально подтянуть страницу продукта (тот же анти-SSRF fetch, что и в чате).
    page = ""
    url = (url or "").strip()
    if url:
        try:
            txt = server.tool_fetch_url({"url": url})
            if txt and not txt.startswith("error:"):
                page = txt[:2500]
        except Exception:
            page = ""

    if not brief and not product and not page:
        return {"scripts": [], "model": "", "n": n,
                "error": "опиши продукт — пару слов о том, что рекламируем"}

    parts = []
    if product:
        parts.append(f"ПРОДУКТ: {product}")
    if brief:
        parts.append(f"БРИФ (что важно сказать): {brief}")
    if tone.strip():
        parts.append(f"ЖЕЛАЕМЫЙ ТОН: {tone.strip()}")
    if page:
        parts.append(f"ВЫЖИМКА СО СТРАНИЦЫ ПРОДУКТА:\n{page}")
    parts.append(f"Сделай ровно {n} разных коротких UGC-сценария.")
    payload = "\n\n".join(parts)

    # Сильная не-фантомная модель под текст/копирайт; падаем на дешёвую.
    try:
        model = server.best_for_task("smart")
    except Exception:
        model = getattr(server, "CHEAP_MODEL", "")
    try:
        raw = server.venice_complete(model, [
            {"role": "system", "content": _AD_SYS},
            {"role": "user", "content": payload},
        ], max_tokens=1100, temperature=0.85).strip()
    except Exception as e:
        return {"scripts": [], "model": model, "n": n,
                "error": f"не вышло написать сценарии: {e}"}

    data = server._extract_json_object(raw)
    scripts = []
    if isinstance(data, dict) and isinstance(data.get("scripts"), list):
        for it in data["scripts"][:n]:
            if not isinstance(it, dict):
                continue
            text = str(it.get("script") or it.get("text") or "").strip()
            if not text:
                continue
            scripts.append({
                "hook": str(it.get("hook") or "").strip()[:200],
                "script": text[:1200],
                "angle": str(it.get("angle") or "").strip()[:60],
            })
    if not scripts:
        # Мягкий фоллбэк: не роняем UI — отдаём сырой текст одним сценарием.
        cleaned = raw.strip()
        if cleaned:
            scripts = [{"hook": "", "script": cleaned[:1200], "angle": "черновик"}]
    return {"scripts": scripts, "model": model, "n": n,
            "page_used": bool(page)}


# ── Avatar-модели для говорящей головы (из живого VIDEO_MODELS server.py) ──
# Фронту нужен короткий список «фото→говорит» моделей + рекомендованная (дешёвая,
# рабочая). Берём kind=="avatar" из каталога; если каталог пуст — пусто, фронт
# подскажет загрузить фото и выбрать модель вручную.

def ad_avatar_models(server) -> dict:
    def _pick(lst):
        # только ФОТО→говорит аватары: lip-sync (latentsync/kling-lipsync) хотят ВХОДНОЕ ВИДЕО,
        # а UGC даёт ФОТО → их выкидываем (иначе 400 «LatentSync requires a video»).
        out = []
        for m in (lst or []):
            if not (isinstance(m, dict) and m.get("kind") == "avatar"):
                continue
            nm = (str(m.get("id") or "") + " " + str(m.get("name") or "")).lower()
            if "lipsync" in nm or "lip-sync" in nm or "latentsync" in nm:
                continue
            out.append({"id": m.get("id"), "name": m.get("name") or m.get("id"),
                        "usd": m.get("usd"), "featured": bool(m.get("featured"))})
        return out
    try:
        # живой каталог; если в нём НЕТ фото-аватаров (только lip-sync или пусто) — запасной
        # VIDEO_FALLBACK, чтобы UGC ВСЕГДА имел фото→говорит модели, а не «нет моделей».
        models = _pick(getattr(server, "VIDEO_MODELS", None)) or _pick(getattr(server, "VIDEO_FALLBACK", None))
    except Exception:
        models = []
    # Рекомендуем самую дешёвую featured (или просто самую дешёвую) — чтобы первый
    # ролик не стоил пользователю много, а «ещё»-ретраи были по карману.
    rec = ""
    if models:
        def _cost(x):
            try:
                return float(x.get("usd") or 999)
            except Exception:
                return 999.0
        feat = [m for m in models if m.get("featured")] or models
        rec = sorted(feat, key=_cost)[0].get("id") or ""
    return {"models": models, "recommended": rec,
            "have": bool(models)}
