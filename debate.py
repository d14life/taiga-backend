"""Архитектор↔Критик — движок дебатов.

PURE модуль: нет импортов из server.py, нет прямых сетевых вызовов.
Всё взаимодействие с моделью идёт через инъецированные колбэки.

Быстрый старт:
    python3 debate.py          # запустит встроенный эхо-демо (никакой реальной модели)

Интеграция:
    from debate import run_debate
    result = run_debate(
        topic="Система кеширования RAG-эмбеддингов",
        ask_model=lambda system, user: my_llm_call(system, user),
        ask_human=lambda q, ctx="": input(f"[Вопрос от архитектора] {q}\n> "),
        emit=lambda kind, data: print(kind, data),
    )
"""

from __future__ import annotations

import re
from typing import Callable, Optional


# ─────────────────────────────────────────────────────────────────────────────
# Строки умолчаний для персон (внешний код может перекрыть через параметры)
# ─────────────────────────────────────────────────────────────────────────────

_DEFAULT_ARCHITECT_SYS = """Ты агент-архитектор. Твоя задача — построить ЧЁТКИЙ БЛЮПРИНТ системы.

Правила:
1. В первом ответе сразу выдай блюпринт: компоненты, интерфейсы, потоки данных, ключевые решения.
2. В каждом следующем раунде ОБНОВЛЯЙ блюпринт, явно помечая изменения против критики.
3. Если стоишь перед развилкой, которую не можешь разрешить самостоятельно, выведи РОВНО ОДНУ строку:
   ВОПРОС: <короткий открытый вопрос к пользователю>
   Если вопрос задан, остальной текст продолжается ниже (архитектор пишет предположение «если ответа нет»).
4. Не распыляйся на общие слова — конкретные компоненты, конкретные trade-offs.
5. Будь готов отстоять или пересмотреть любое решение, когда критик указывает на слабые места."""

_DEFAULT_CRITIC_SYS = """Ты агент-критик. Твоя задача — найти ВСЕ слабые места блюпринта.

Правила:
1. Будь резким и конкретным: называй компоненты, сценарии, граничные случаи.
2. Не хвали без причины. Если исправлено — отметь коротко и атакуй следующее.
3. Сосредоточься на НОВЫХ проблемах, не повторяй то, что уже исправлено.
4. В конце ответа — ОБЯЗАТЕЛЬНО последняя строка в точном формате:
   ВЕРДИКТ: согласен
   ИЛИ
   ВЕРДИКТ: есть замечания
   (только одна из двух формулировок, без вариаций)."""


# ─────────────────────────────────────────────────────────────────────────────
# Вспомогательные функции
# ─────────────────────────────────────────────────────────────────────────────

_VERDICT_AGREE_RE = re.compile(r"ВЕРДИКТ\s*:\s*согласен", re.IGNORECASE)
_VERDICT_REMARKS_RE = re.compile(r"ВЕРДИКТ\s*:\s*есть замечания", re.IGNORECASE)
_QUESTION_RE = re.compile(r"^ВОПРОС\s*:\s*(.+)$", re.MULTILINE)


def _extract_question(text: str) -> Optional[str]:
    """Вернуть первый ВОПРОС: из текста архитектора (или None)."""
    m = _QUESTION_RE.search(text)
    return m.group(1).strip() if m else None


def _clean_blueprint(text: str) -> str:
    """Убрать ведущую служебную метку, которую модель иногда эхает из истории
    («[Архитектор, раунд N]:» / «[ЭХО …]:»). Косметика финального чертежа."""
    out = re.sub(r"^\s*\[(?:Архитектор|ЭХО)[^\]]*\]:?\s*", "", text or "", flags=re.IGNORECASE).strip()
    return out or (text or "")


def _critic_agreed(text: str) -> bool:
    """Критик явно написал ВЕРДИКТ: согласен."""
    return bool(_VERDICT_AGREE_RE.search(text))


def _extract_issues(text: str) -> set[str]:
    """Грубое «что упомянул критик» — набор нормализованных слов длиной >4.
    Используем для дешёвого сравнения «новые ли проблемы»."""
    words = re.findall(r"[а-яёa-z]{5,}", text.lower())
    return set(words)


def _no_new_issues(prev_issues: set[str], curr_text: str) -> bool:
    """Вернуть True, если текущий ответ критика не добавил существенно новых слов."""
    if not prev_issues:
        return False
    curr = _extract_issues(curr_text)
    new_words = curr - prev_issues
    # порог: меньше 5 новых «значимых» слов = считаем конвергенцию
    return len(new_words) < 5


# ─────────────────────────────────────────────────────────────────────────────
# Основная функция
# ─────────────────────────────────────────────────────────────────────────────

def run_debate(
    topic: str,
    ask_model: Callable[[str, str], str],
    ask_human: Optional[Callable[..., Optional[str]]] = None,
    emit: Optional[Callable[[str, dict], None]] = None,
    max_rounds: int = 4,
    architect_sys: Optional[str] = None,
    critic_sys: Optional[str] = None,
) -> dict:
    """Запустить дебаты Архитектор↔Критик.

    Параметры
    ---------
    topic : str
        Задача / тема для проектирования.
    ask_model : (system: str, user: str) -> str
        ОБЯЗАТЕЛЬНЫЙ колбэк — один вызов модели. Инъецируется интегратором.
    ask_human : ((question: str, context: str) -> str | None) | None
        ОПЦИОНАЛЬНЫЙ колбэк — задать вопрос пользователю.
        Если None, архитектор продолжает с собственным предположением.
    emit : ((kind: str, data: dict) -> None) | None
        ОПЦИОНАЛЬНЫЙ колбэк таймлайна. kind="debate",
        data={round, role:"architect"|"critic", text, status}.
    max_rounds : int
        Максимальное число полных раундов (архитектор + критик = 1 раунд).
    architect_sys : str | None
        Системный промпт архитектора. Если None — встроенный.
    critic_sys : str | None
        Системный промпт критика. Если None — встроенный.

    Возвращает
    ----------
    {
        "blueprint": str,         # финальный блюпринт архитектора
        "rounds": [               # все шаги
            {"round": int, "role": str, "text": str}, ...
        ],
        "converged": bool,        # True = достигнут консенсус
        "stop_reason": str,       # "agreed" | "no_new_issues" | "max_rounds" | "error"
        "questions": [            # вопросы архитектора (с ответами или без)
            {"round": int, "question": str, "answer": str | None}, ...
        ],
    }
    """
    arch_sys = architect_sys or _DEFAULT_ARCHITECT_SYS
    crit_sys = critic_sys or _DEFAULT_CRITIC_SYS

    rounds: list[dict] = []
    questions: list[dict] = []
    blueprint = ""
    converged = False
    stop_reason = "max_rounds"

    # история для архитектора (накапливаем, чтобы он видел весь диалог)
    arch_history: list[str] = []
    prev_critic_issues: set[str] = set()

    # ------- Раунд 0: первый блюпринт ----------------------------------------
    arch_user_0 = (
        f"Тема для проектирования:\n{topic}\n\n"
        "Построй детальный блюпринт: компоненты, интерфейсы, потоки данных, ключевые решения.\n"
        "ВАЖНО: тема может быть мутной/неполной. Если для блюпринта не хватает КЛЮЧЕВОГО решения "
        "(приватность/E2E-шифрование? масштаб? платформы? онлайн/оффлайн? бюджет?), НЕ гадай молча — "
        "выведи РОВНО ОДНУ строку «ВОПРОС: <самая важная развилка>», а ниже дай блюпринт с пометкой "
        "«если ответа нет — предполагаю …»."
    )

    arch_reply = ""
    try:
        arch_reply = ask_model(arch_sys, arch_user_0)
    except Exception as exc:  # noqa: BLE001
        arch_reply = f"[Ошибка архитектора в раунде 0: {exc}]"

    blueprint = _clean_blueprint(arch_reply)
    arch_history.append(f"[Архитектор, раунд 0]:\n{arch_reply}")

    rounds.append({"round": 0, "role": "architect", "text": arch_reply})
    _safe_emit(emit, "debate", {"round": 0, "role": "architect", "text": arch_reply, "status": "ok"})

    # Проверяем ВОПРОС от архитектора
    q_text = _extract_question(arch_reply)
    if q_text and ask_human is not None:
        answer = _call_human(ask_human, q_text, topic)
        questions.append({"round": 0, "question": q_text, "answer": answer})
        if answer:
            arch_history.append(f"[Пользователь ответил на вопрос «{q_text}»]: {answer}")

    # ------- Основной цикл ---------------------------------------------------
    for rnd in range(1, max_rounds + 1):
        # ── Критик ──
        crit_context = "\n\n".join(arch_history)
        crit_user = (
            f"Вот текущее состояние дебатов по теме «{topic}»:\n\n"
            f"{crit_context}\n\n"
            "Найди слабые места. Закончи строкой ВЕРДИКТ: согласен или ВЕРДИКТ: есть замечания."
        )
        crit_reply = ""
        try:
            crit_reply = ask_model(crit_sys, crit_user)
        except Exception as exc:  # noqa: BLE001
            crit_reply = f"[Ошибка критика в раунде {rnd}: {exc}]\nВЕРДИКТ: есть замечания"

        rounds.append({"round": rnd, "role": "critic", "text": crit_reply})
        _safe_emit(emit, "debate", {"round": rnd, "role": "critic", "text": crit_reply, "status": "ok"})

        arch_history.append(f"[Критик, раунд {rnd}]:\n{crit_reply}")

        # ── Проверка конвергенции после критика ──
        if _critic_agreed(crit_reply):
            converged = True
            stop_reason = "agreed"
            break

        curr_issues = _extract_issues(crit_reply)
        if rnd > 1 and _no_new_issues(prev_critic_issues, crit_reply):
            converged = True
            stop_reason = "no_new_issues"
            break

        prev_critic_issues = curr_issues

        if rnd >= max_rounds:
            stop_reason = "max_rounds"
            break

        # ── Архитектор отвечает на критику ──
        arch_user_n = (
            f"Критик дал замечания (раунд {rnd}). Обнови блюпринт, явно устраняя каждый пункт.\n"
            "Если видишь неразрешимую развилку — задай ВОПРОС:. Иначе — продолжай."
        )
        arch_context = "\n\n".join(arch_history)
        arch_full_user = f"{arch_context}\n\n{arch_user_n}"

        arch_reply = ""
        try:
            arch_reply = ask_model(arch_sys, arch_full_user)
        except Exception as exc:  # noqa: BLE001
            arch_reply = f"[Ошибка архитектора в раунде {rnd}: {exc}]"

        blueprint = _clean_blueprint(arch_reply)
        arch_history.append(f"[Архитектор, раунд {rnd}]:\n{arch_reply}")
        rounds.append({"round": rnd, "role": "architect", "text": arch_reply})
        _safe_emit(emit, "debate", {"round": rnd, "role": "architect", "text": arch_reply, "status": "ok"})

        # Проверяем ВОПРОС
        q_text = _extract_question(arch_reply)
        if q_text and ask_human is not None:
            answer = _call_human(ask_human, q_text, f"Раунд {rnd}, тема: {topic}")
            questions.append({"round": rnd, "question": q_text, "answer": answer})
            if answer:
                arch_history.append(f"[Пользователь ответил на вопрос «{q_text}»]: {answer}")

    return {
        "blueprint": blueprint,
        "rounds": rounds,
        "converged": converged,
        "stop_reason": stop_reason,
        "questions": questions,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Внутренние хелперы
# ─────────────────────────────────────────────────────────────────────────────

def _safe_emit(emit: Optional[Callable], kind: str, data: dict) -> None:
    """Вызвать emit безопасно — ошибка не роняет цикл."""
    if emit is None:
        return
    try:
        emit(kind, data)
    except Exception:  # noqa: BLE001
        pass


def _call_human(
    ask_human: Callable,
    question: str,
    context: str = "",
) -> Optional[str]:
    """Вызвать ask_human безопасно. Возвращает ответ или None."""
    try:
        # ask_human может принимать 1 или 2 аргумента — пробуем оба варианта
        try:
            return ask_human(question, context) or None
        except TypeError:
            return ask_human(question) or None
    except Exception:  # noqa: BLE001
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Демо (эхо без реальной модели)
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    _ROUND_COUNTER = [0]

    def _echo_model(system: str, user: str) -> str:
        """Фейковая модель: архитектор пишет план, критик сразу соглашается на 2-м раунде."""
        _ROUND_COUNTER[0] += 1
        n = _ROUND_COUNTER[0]
        if "критик" in system.lower() or "critic" in system.lower():
            if n >= 3:
                return (
                    "Архитектор учёл все замечания. Компоненты теперь изолированы.\n"
                    "ВЕРДИКТ: согласен"
                )
            return (
                f"[ЭХО критик, вызов {n}]\n"
                "1. Нет описания механизма отказа для компонента B.\n"
                "2. Нет SLA для потока данных.\n"
                "ВЕРДИКТ: есть замечания"
            )
        else:
            if n == 1:
                return (
                    f"[ЭХО архитектор, вызов {n}]\n"
                    "БЛЮПРИНТ:\n"
                    "  Компонент A — приём запросов\n"
                    "  Компонент B — обработка\n"
                    "  Компонент C — хранение\n"
                    "ВОПРОС: Какой уровень доступности нужен для компонента B — 99.9% или 99.99%?"
                )
            return (
                f"[ЭХО архитектор, вызов {n}]\n"
                "ОБНОВЛЁННЫЙ БЛЮПРИНТ:\n"
                "  Компонент A — приём (с fallback на реплику)\n"
                "  Компонент B — обработка (SLA 99.9%, graceful shutdown)\n"
                "  Компонент C — хранение (WAL + репликация)\n"
            )

    def _echo_human(question: str, context: str = "") -> Optional[str]:
        print(f"  [Вопрос архитектора]: {question}")
        return "99.9% достаточно, это внутренний инструмент"

    def _print_emit(kind: str, data: dict) -> None:
        role = data.get("role", "?")
        rnd = data.get("round", "?")
        text_snippet = str(data.get("text", ""))[:80].replace("\n", " ")
        print(f"  emit [{kind}] раунд={rnd} роль={role}: {text_snippet}…")

    print("=== Дебаты: эхо-демо (без реальной модели) ===")
    result = run_debate(
        topic="Система кеширования эмбеддингов для RAG",
        ask_model=_echo_model,
        ask_human=_echo_human,
        emit=_print_emit,
        max_rounds=4,
    )
    print(f"\nСтоп-причина : {result['stop_reason']}")
    print(f"Конвергенция : {result['converged']}")
    print(f"Раундов сыграно: {len(set(r['round'] for r in result['rounds']))}")
    print(f"Вопросов задано: {len(result['questions'])}")
    for q in result["questions"]:
        print(f"  раунд {q['round']}: {q['question']!r} → {q['answer']!r}")
    print(f"\nФинальный блюпринт ({len(result['blueprint'])} симв.):")
    print(result["blueprint"][:400])
    print("=== Демо завершён ===")
