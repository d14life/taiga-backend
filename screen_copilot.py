# screen_copilot.py — L21 Real-time screen co-pilot.
#
# Фронт (screen-copilot.tsx) через getDisplayMedia() шарит экран, РЕДКО (раз в N секунд,
# дёшево) снимает кадр и шлёт сюда. Мы зовём ЗРЯЧУЮ модель (тот же путь, что RAG-VLM:
# image_url-часть → venice_complete) и возвращаем КОРОТКУЮ подсказку «нажми сюда / сделай
# это» для всплывающего пузыря-оверлея. Опц. озвучка делается на фронте существующим TTS.
#
# Стоимость под контролем: один зрячий вызов на кадр, кадры редкие, max_tokens мал.
# Этот модуль — pure helper; server.py передаёт себя (его helpers: _rag_vision_model,
# vision_ok, venice_complete, _extract_json_object).

from __future__ import annotations

_COPILOT_SYS = (
    "Ты — со-пилот, который смотрит на экран пользователя и помогает шаг за шагом. "
    "Тебе дают СКРИНШОТ экрана и (опционально) ЦЕЛЬ пользователя и твою прошлую подсказку. "
    "Дай ОДНО следующее короткое действие — что нажать или сделать прямо сейчас, чтобы "
    "продвинуться к цели. Пиши по-русски, на «ты», конкретно и коротко (одна-две фразы), "
    "как живой помощник за плечом. Указывай на видимый элемент словами («кнопка „Войти“ "
    "справа вверху»), без координат. Если цель не задана — пойми по экрану, чем занят "
    "человек, и подскажи разумный следующий шаг. Если на экране всё готово / делать нечего "
    "— так и скажи коротко.\n"
    "Верни СТРОГО JSON: {\"tip\":\"одна короткая подсказка-действие\","
    "\"target\":\"на какой элемент смотреть (коротко, можно пусто)\","
    "\"done\":true|false}. done=true только если цель явно достигнута / делать нечего. "
    "Ничего вне JSON."
)


def screen_guidance(server, frame_data_url: str, goal: str = "",
                    last_tip: str = "") -> dict:
    """Один зрячий вызов: кадр экрана (+ цель/прошлая подсказка) → короткая подсказка.
    Возвращает {tip, target, done, model}. Тихо деградирует — никогда не кидает наверх."""
    frame_data_url = (frame_data_url or "").strip()
    if not frame_data_url.startswith("data:image"):
        return {"tip": "", "target": "", "done": False, "error": "нужен кадр экрана"}

    try:
        model = server._rag_vision_model()
    except Exception:
        model = ""
    if not model or not server.vision_ok(model):
        return {"tip": "", "target": "", "done": False,
                "error": "нет зрячей модели — co-pilot недоступен"}

    parts = []
    if goal.strip():
        parts.append(f"ЦЕЛЬ ПОЛЬЗОВАТЕЛЯ: {goal.strip()[:400]}")
    if last_tip.strip():
        parts.append(f"ТВОЯ ПРОШЛАЯ ПОДСКАЗКА (не повторяйся дословно): {last_tip.strip()[:300]}")
    parts.append("Посмотри на текущий экран и дай следующий шаг.")
    text = "\n".join(parts)

    msgs = [{"role": "user", "content": [
        {"type": "text", "text": text},
        {"type": "image_url", "image_url": {"url": frame_data_url}},
    ]}]
    try:
        raw = server.venice_complete(model, [
            {"role": "system", "content": _COPILOT_SYS},
            *msgs,
        ], max_tokens=220, temperature=0.3) or ""
    except Exception as e:
        return {"tip": "", "target": "", "done": False, "error": f"co-pilot не ответил: {e}"}

    data = server._extract_json_object(raw)
    if isinstance(data, dict) and (data.get("tip") or data.get("done")):
        return {
            "tip": str(data.get("tip") or "").strip()[:300],
            "target": str(data.get("target") or "").strip()[:120],
            "done": bool(data.get("done")),
            "model": model,
        }
    # фоллбэк: модель не дала JSON — отдаём сырой текст как подсказку, не роняем UI
    tip = (raw or "").strip()
    return {"tip": tip[:300], "target": "", "done": False, "model": model}
