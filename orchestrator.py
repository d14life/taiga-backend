"""Оркестратор агентов Тайги на LangGraph.

Главный мозг декомпозирует задачу → раздаёт ВОРКЕРАМ-АГЕНТАМ (модель+скилл на каждого) →
воркеры пашут параллельно → синтез. Стримит шаги (emit) для таймлайна (как Copilot Agents).

Воркеры = НАШИ модели по умолчанию; юзер может подставить СВОЙ ключ/модель (BYOK) на любого
воркера через worker.key / worker.base. Граф на LangGraph (StateGraph): plan → workers → synth.
"""
import json
import operator
import urllib.request
from pathlib import Path
from typing import TypedDict, Annotated

from langgraph.graph import StateGraph, START, END

NANO = "https://nano-gpt.com/api/v1/chat/completions"
# дешёвые-надёжные дефолты + фолбэк (если id модели не тот — пробуем следующий)
PLANNER_MODEL = "gemini-2.5-flash"
SYNTH_MODEL = "gemini-2.5-flash"
DEFAULT_WORKER_MODEL = "gemini-2.5-flash"
# Запасные модели — только подтверждённо-живые в каталоге (проверено 2026-06-12).
# Старые deepseek-v4-flash / gpt-5.1-mini / qwen3-235b-a22b пропали из раздачи → убраны.
_FALLBACK = ["gemini-2.5-flash", "mistralai/Mistral-Nemo-Instruct-2407", "sonar"]
# Потолок ожидания всей параллельной фазы воркеров (сек). Кто не успел — синтез без него,
# чтобы оркестратор не «висел долго не отвечает» из-за одной медленной модели.
WORKER_BUDGET = 110

# Скиллы-персоны воркеров (вдохновлено ECC — 64 агента / 262 скилла, MIT).
SKILLS = {
    "general":    "Ты толковый агент-исполнитель. Отвечай по делу, конкретно, без воды.",
    "researcher": "Ты агент-исследователь. Найди факты, дай источники, будь точным и свежим.",
    "coder":      "Ты агент-программист. Пиши рабочий код, кратко поясняй ключевое.",
    "critic":     "Ты агент-критик. Найди слабые места, риски и дыры. Будь резок и конкретен.",
    "writer":     "Ты агент-копирайтер. Пиши ясно, живо, по-русски, без канцелярита.",
    "planner":    "Ты агент-планировщик. Разложи на чёткие шаги с приоритетами и зависимостями.",
    "architect":  "Ты агент-архитектор. Спроектируй структуру/систему: компоненты, интерфейсы, trade-offs.",
    "security":   "Ты агент-безопасник. Найди уязвимости, утечки, инъекции, риски приватности. Конкретно.",
    "reviewer":   "Ты агент-ревьюер кода. Проверь корректность, баги, читаемость; дай точечные правки.",
    "debugger":   "Ты агент-дебагер. Сформулируй гипотезы о причине, проверь, найди корень. Без угадайки.",
    "optimizer":  "Ты агент-оптимизатор. Найди узкие места (скорость/память/стоимость) и как ускорить.",
    "analyst":    "Ты агент-аналитик. Разбери данные/ситуацию, выдели инсайты и вывод с цифрами.",
    "marketer":   "Ты агент-маркетолог. Позиционирование, оффер, аудитория, хук. Резко и продающе.",
    "summarizer": "Ты агент-суммаризатор. Сожми до сути: главное, без потерь смысла, структурно.",
    "translator": "Ты агент-переводчик. Переводи точно и естественно, сохраняя тон и термины.",
    "devops":     "Ты агент-devops. Деплой, CI/CD, инфра, надёжность. Практичные команды и конфиги.",
    "qa":         "Ты агент-тестировщик. Придумай тест-кейсы, граничные случаи, способы сломать.",
}


def _nano_key() -> str:
    p = Path("~/.nanogpt_key").expanduser()
    return p.read_text().strip() if p.exists() else ""


def _complete(model: str, messages: list, key: str = None, base: str = None,
              max_tokens: int = 900, timeout: int = 90) -> str:
    """Один вызов модели. По умолчанию NanoGPT (наш ключ); BYOK → key/base юзера.
    Фолбэк по списку моделей, если id не тот. timeout — потолок на один HTTP-вызов."""
    base = base or NANO
    use_key = key or _nano_key()
    tries = [model] if model else []
    tries += [m for m in _FALLBACK if m not in tries]
    last = ""
    for mdl in tries:
        try:
            body = {"model": mdl, "messages": messages, "max_tokens": max_tokens}
            req = urllib.request.Request(base, data=json.dumps(body).encode(),
                headers={"Authorization": f"Bearer {use_key}", "content-type": "application/json"},
                method="POST")
            with urllib.request.urlopen(req, timeout=timeout) as r:
                d = json.load(r)
            txt = (d.get("choices") or [{}])[0].get("message", {}).get("content", "")
            if txt:
                return txt
        except Exception as e:
            last = str(e)[:160]
            continue
    raise RuntimeError("complete failed: " + last)


def _extract_list(raw: str) -> list:
    """Достаём JSON-массив подзадач из ответа планировщика. Терпим к хвостовым запятым."""
    import re
    s = raw.strip()
    a, b = s.find("["), s.rfind("]")
    if a != -1 and b > a:
        frag = re.sub(r",\s*([\]}])", r"\1", s[a:b + 1])     # убираем хвостовые запятые → валидный JSON
        try:
            arr = json.loads(frag)
            out = [str(x).strip() for x in arr if str(x).strip()]
            if out:
                return out
        except Exception:
            pass
    # фолбэк: строки-пункты — чистим маркеры, кавычки, запятые, слэши
    _strip = " \t-•*0123456789.\"',\\"
    return [ln.strip(_strip) for ln in s.splitlines() if len(ln.strip(_strip)) > 8][:4]


class OrchState(TypedDict):
    task: str
    plan: list
    results: Annotated[list, operator.add]
    final: str


def run_orchestration(task: str, workers: list = None, emit=None, mode: str = "parallel", tools: dict = None) -> dict:
    """Запуск оркестрации. workers = [{model, skill, key?, base?}, ...]; emit(kind, data) → таймлайн.
    mode='parallel'|'sequential' (sequential = воркеры видят результаты прошлых, для зависимых задач).
    tools={'search': fn} → воркер-researcher реально ищет через супер-поиск."""
    emit = emit or (lambda *a, **k: None)
    tools = tools or {}
    workers = workers or [{"skill": "researcher"}, {"skill": "critic"}]

    def plan_node(state):
        emit("step", {"node": "plan", "status": "running", "label": "Декомпозиция задачи"})
        raw = _complete(PLANNER_MODEL, [
            {"role": "system", "content": "Разбей задачу на 2-4 чёткие независимые подзадачи. "
                                          "Верни ТОЛЬКО JSON-массив строк."},
            {"role": "user", "content": state["task"]}], max_tokens=400)
        plan = _extract_list(raw) or [state["task"]]
        plan = plan[:max(2, min(4, len(workers)))]
        emit("step", {"node": "plan", "status": "done", "plan": plan})
        return {"plan": plan}

    def _worker(i, sub, prior=""):
        w = workers[i % len(workers)]
        model = w.get("model") or DEFAULT_WORKER_MODEL
        skill = w.get("skill", "general")
        emit("agent", {"worker": i, "model": model, "skill": skill, "status": "running", "task": sub})
        ctx = ""
        if skill == "researcher" and tools.get("search"):     # researcher реально ищет
            try:
                emit("agent", {"worker": i, "status": "searching"})
                sr = tools["search"](sub)
                ans = "\n".join(a.get("answer", "") for a in (sr.get("answers") or [])[:3])
                srcs = "; ".join(s.get("url", "") for s in (sr.get("sources") or [])[:6])
                ctx = f"\n\nРЕЗУЛЬТАТЫ ПОИСКА (опирайся на них):\n{ans}\nИсточники: {srcs}"
            except Exception:
                pass
        user_msg = sub + (f"\n\nКОНТЕКСТ от прошлых агентов:\n{prior}" if prior else "") + ctx
        try:
            res = _complete(model, [
                {"role": "system", "content": SKILLS.get(skill, SKILLS["general"])},
                {"role": "user", "content": user_msg}], key=w.get("key"), base=w.get("base"))
        except Exception as e:
            res = f"[ошибка воркера: {e}]"
        emit("agent", {"worker": i, "status": "done", "result": res[:160]})
        return {"worker": i, "skill": skill, "model": model, "task": sub, "result": res}

    def workers_node(state):
        plan = state["plan"]
        if mode == "sequential":               # зависимые задачи: каждый видит результаты прошлых
            results, prior = [], ""
            for i, sub in enumerate(plan):
                r = _worker(i, sub, prior)
                results.append(r)
                prior += f"\n### {r['task']}\n{r['result']}"
            return {"results": results}
        # Параллельно с БЮДЖЕТОМ: медленный воркер не должен подвешивать синтез/таймлайн.
        # Кто не успел к WORKER_BUDGET — отдаём заглушкой, синтез идёт по тому, что есть.
        import concurrent.futures as cf
        results_map = {}
        with cf.ThreadPoolExecutor(max_workers=4) as ex:
            futs = {ex.submit(_worker, i, sub): i for i, sub in enumerate(plan)}
            try:
                for fut in cf.as_completed(list(futs), timeout=WORKER_BUDGET):
                    r = fut.result()
                    results_map[r["worker"]] = r
            except cf.TimeoutError:
                pass
            for fut, i in futs.items():
                if i not in results_map:
                    fut.cancel()
                    emit("agent", {"worker": i, "status": "timeout"})
                    results_map[i] = {"worker": i, "skill": workers[i % len(workers)].get("skill", "general"),
                                      "model": "—", "task": plan[i],
                                      "result": "[агент не успел к таймауту — синтез без него]"}
        return {"results": [results_map[i] for i in range(len(plan))]}

    def synth_node(state):
        emit("step", {"node": "synth", "status": "running", "label": "Синтез результата"})
        joined = "\n\n".join(f"### {r['task']}\n{r['result']}" for r in state["results"])
        final = _complete(SYNTH_MODEL, [
            {"role": "system", "content": "Собери единый связный ответ из результатов агентов. "
                                          "Без повторов, по делу, по-русски."},
            {"role": "user", "content": f"Задача: {state['task']}\n\nРезультаты агентов:\n{joined}"}],
            max_tokens=1200)
        emit("step", {"node": "synth", "status": "done"})
        return {"final": final}

    g = StateGraph(OrchState)
    g.add_node("plan", plan_node)
    g.add_node("workers", workers_node)
    g.add_node("synth", synth_node)
    g.add_edge(START, "plan")
    g.add_edge("plan", "workers")
    g.add_edge("workers", "synth")
    g.add_edge("synth", END)
    app = g.compile()

    out = app.invoke({"task": task, "plan": [], "results": [], "final": ""})
    return {"task": task, "plan": out.get("plan"), "results": out.get("results"), "final": out.get("final")}
