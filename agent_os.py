"""
agent_os.py — ТАЙГА AGENT-OS HARNESS (L15 + L13).

Crown-jewel agentic harness. "Думай как Совет, действуй как агент."

ПРИНЦИП (walkinglabs/learn-harness-engineering): «модель умная — харнес надёжный».
Пять подсистем оформлены явно:
  • SCOPE          — декомпозиция цели в под-цели, по одной за раз, с явным done-условием.
  • THINK          — мульти-модельная делиберация (propose → critique-repair → adversarial → fuse),
                     лучшая модель ПОД ПОД-ЗАДАЧУ, обёрнутая в TaskPacket.
  • ACT            — исполнение через СУЩЕСТВУЮЩИЕ типизированные тулзы (web/code/browser/studio)
                     как code-as-action: инспектируемо и (где можно) обратимо.
  • VERIFY         — результат против критерия приёмки под-цели; только passing = done.
                     На fail → critique-repair цикл с ограниченными ретраями.
  • STATE          — слои памяти (working / semantic / experiential / long-term) поверх
                     существующего user_dir + RAG; resumable прогресс на диск.

МЕРЖ-БЕЗОПАСНОСТЬ: этот модуль НЕ импортирует server.py (избегаем циклов и конфликтов).
Всё, что нужно из server.py (модели, тулзы, память, ключи), приходит ОДНИМ объектом-контекстом
`HarnessDeps` через dependency-injection из тонкого вызова `agent_os.run(...)` в server.py.
Так server.py меняется на 3-4 строки, а вся логика живёт здесь.

L13 (MULTI-AGENT, Chad-style): `fan_out(...)` раскидывает N изолированных под-агентов на
непересекающиеся под-задачи (логическая изоляция, in-process async) → каждый прогоняет тот же
харнес → результаты сливаются чисто. Переиспользует THINK/ACT/VERIFY на каждого под-агента.
"""

from __future__ import annotations

import json
import re
import time
import uuid
import threading
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Callable, Optional

# ──────────────────────────────────────────────────────────────────────────────
# DEPENDENCY-INJECTION КОНТЕКСТ — мост к server.py без import-цикла.
# server.py собирает этот объект из своих существующих функций и передаёт в run().
# Ни одного поля мы не «изобретаем»: всё уже живёт в server.py (см. директивы).
# ──────────────────────────────────────────────────────────────────────────────


@dataclass
class HarnessDeps:
    """Инъекция зависимостей из server.py. Харнес ОРКЕСТРИРУЕТ их, не дублирует."""
    # мульти-модельный примитив (не-стрим): (model, messages, max_tokens, key?, temperature?, reasoning_effort?) -> str
    complete: Callable[..., str]
    # ключ под (uid, model) -> (key, byok, err). Берём из resolve_key.
    resolve_key: Callable[[str, str], tuple]
    # лучшая модель под задачу: (task_text, tier?) -> model_id  (best_for_task)
    best_for_task: Callable[..., str]
    # топ-N моделей под задачу: (task_text, n, tier?) -> [model_id]  (best_n_for_task)
    best_n_for_task: Callable[..., list]
    # тип задачи из текста: (messages, has_images) -> "general|code|reason|vision"  (detect_task)
    detect_task: Callable[[list, bool], str]
    # реестр типизированных тулз (ACT): {name: callable(args_dict)->str}. = {**TOOLS, **DEV_TOOLS?}
    tools: dict
    # дешёвая служебная модель для планирования/судейства (aux_model('plan'))
    aux_model: str
    # каталог моделей-фразы → bool думающая ли (model_reasons), чтобы слать reasoning_effort
    model_reasons: Callable[[str], bool]
    # директория памяти юзера: uid -> Path (user_dir). Туда пишем resumable-состояние/опыт.
    user_dir: Callable[[str], Path]
    # owner-флаг (для гейтинга dev-тулз): uid -> bool
    is_owner: Callable[[str], bool]
    # необязательный RAG-контекст: (uid, messages) -> str. Может быть None.
    rag_context: Optional[Callable[[str, list], str]] = None


# ──────────────────────────────────────────────────────────────────────────────
# TASKPACKET (claw-code) — конверт делегирования под-задачи.
# Несёт {модель/провайдер, выбранные для ЭТОЙ под-задачи; саму задачу; критерий приёмки}.
# ──────────────────────────────────────────────────────────────────────────────


@dataclass
class TaskPacket:
    """Конверт делегирования (claw-code): что делать, кем и как принять."""
    goal: str                                   # текст под-цели
    model: str                                  # модель, выбранная под эту под-задачу
    accept: str                                 # критерий приёмки (done-условие, человекочитаемо)
    task_type: str = "general"                  # general/code/reason/vision (для маршрутизации)
    tier: Optional[str] = None                  # ценовой тир (cheap/mid/top), опционально
    provider: Optional[str] = None              # провайдер, если важен (аддитивно)
    id: str = field(default_factory=lambda: "tp_" + uuid.uuid4().hex[:8])

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SubGoalResult:
    """Итог одной под-цели после THINK→ACT→VERIFY."""
    packet: TaskPacket
    answer: str = ""
    verified: Optional[bool] = None             # None = проверка не запускалась/упала
    verify_reason: str = ""
    tool_runs: list = field(default_factory=list)   # [{name, args, result_preview}]
    attempts: int = 1

    def to_dict(self) -> dict:
        d = asdict(self)
        d["packet"] = self.packet.to_dict()
        return d


# ──────────────────────────────────────────────────────────────────────────────
# STATE — слои памяти + resumable прогресс на диск (поверх user_dir).
# working    — оперативная (этот прогон): план, промежуточные ответы.
# semantic   — факты/выводы, годные дальше (кладём в experiential журнал по завершении).
# experiential — журнал прошлых прогонов агента (учимся на опыте).
# long-term  — существующий RAG/факты юзера (читаем через deps.rag_context).
# ──────────────────────────────────────────────────────────────────────────────


class AgentState:
    """Resumable состояние одного прогона харнеса. Персист — JSON в user_dir/agent_os/<run_id>.json."""

    def __init__(self, deps: HarnessDeps, uid: str, run_id: str, goal: str):
        self.deps = deps
        self.uid = uid
        self.run_id = run_id
        self.goal = goal
        self.working: dict = {"sub_goals": [], "done": [], "cursor": 0}
        self.semantic: list = []          # накопленные выводы (кратко)
        self.results: list = []           # [SubGoalResult.to_dict()]
        self.created = time.time()

    def _path(self) -> Path:
        try:
            d = self.deps.user_dir(self.uid) / "agent_os"
            d.mkdir(parents=True, exist_ok=True)
            return d / f"{self.run_id}.json"
        except Exception:
            return Path("/tmp") / f"agent_os_{self.run_id}.json"

    def persist(self):
        try:
            self._path().write_text(json.dumps({
                "run_id": self.run_id, "goal": self.goal, "uid": self.uid,
                "working": self.working, "semantic": self.semantic,
                "results": self.results, "created": self.created,
            }, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass                          # персист — best-effort, не валит прогон

    @classmethod
    def resume(cls, deps: HarnessDeps, uid: str, run_id: str) -> Optional["AgentState"]:
        try:
            p = (deps.user_dir(uid) / "agent_os" / f"{run_id}.json")
            raw = json.loads(p.read_text(encoding="utf-8"))
            st = cls(deps, uid, run_id, raw.get("goal", ""))
            st.working = raw.get("working") or st.working
            st.semantic = raw.get("semantic") or []
            st.results = raw.get("results") or []
            st.created = raw.get("created") or time.time()
            return st
        except Exception:
            return None

    def record_experience(self):
        """experiential слой: дописываем краткий итог прогона в журнал агента юзера."""
        try:
            d = self.deps.user_dir(self.uid) / "agent_os"
            d.mkdir(parents=True, exist_ok=True)
            jline = {
                "ts": int(time.time()), "run_id": self.run_id, "goal": self.goal[:300],
                "sub_goals": len(self.results),
                "verified": sum(1 for r in self.results if r.get("verified")),
                "takeaways": self.semantic[-5:],
            }
            with (d / "experience.jsonl").open("a", encoding="utf-8") as f:
                f.write(json.dumps(jline, ensure_ascii=False) + "\n")
        except Exception:
            pass


# ──────────────────────────────────────────────────────────────────────────────
# Утилиты-парсеры (терпимы к обёрткам/мусору вокруг JSON, как в server.py).
# ──────────────────────────────────────────────────────────────────────────────


def _extract_json(raw: str):
    s = (raw or "").strip()
    a, b = s.find("["), s.rfind("]")
    if a != -1 and b > a:
        try:
            return json.loads(s[a:b + 1])
        except Exception:
            pass
    a, b = s.find("{"), s.rfind("}")
    if a != -1 and b > a:
        try:
            return json.loads(s[a:b + 1])
        except Exception:
            pass
    return None


def _strip_tool_call(text: str):
    """Достаёт первый вызов тулзы из ответа модели. Поддерживает <tool_call>{...}</tool_call>,
    ```json{...}``` и голый JSON c полями name/tool + args. Возвращает (name, args) или None.
    Минимальная самодостаточная версия (харнес не лезет в server.parse_tool_call, чтобы не
    плодить зависимостей; реальное исполнение всё равно идёт через deps.tools)."""
    if not text:
        return None
    m = re.search(r"<(?:tool_call|function_call|tool)\b[^>]*>(.*?)</(?:tool_call|function_call|tool)>",
                  text, re.DOTALL | re.IGNORECASE)
    candidates = []
    if m:
        candidates.append(m.group(1))
    for fb in re.findall(r"```(?:json|tool|tool_call)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE):
        candidates.append(fb)
    candidates.append(text)
    for c in candidates:
        obj = _extract_json(c)
        if isinstance(obj, dict):
            name = obj.get("name") or obj.get("tool") or obj.get("function")
            args = obj.get("args") or obj.get("arguments") or obj.get("parameters") or {}
            if isinstance(name, str) and name:
                if not isinstance(args, dict):
                    args = {"input": args}
                return (name, args)
    return None


# ──────────────────────────────────────────────────────────────────────────────
# ЯДРО ХАРНЕСА
# ──────────────────────────────────────────────────────────────────────────────

MAX_SUBGOALS = 5
MAX_REPAIR_RETRIES = 2          # bounded retries в VERIFY-фейле
MAX_ACT_STEPS = 4               # сколько тул-вызовов на под-цель максимум


class Harness:
    """L15 харнес. emit(kind, data) → таймлайн (SSE или собранный лог)."""

    def __init__(self, deps: HarnessDeps, uid: str, emit: Callable[[str, dict], None] = None,
                 owner_dev: bool = False, tier: str = None):
        self.deps = deps
        self.uid = uid
        self.emit = emit or (lambda k, d: None)
        self.tier = tier
        # ACT: тулзы. Dev-тулзы (shell/код) — только владельцу (анти-RCE, как в server.py).
        self.tools = dict(deps.tools or {})
        self.owner_dev = owner_dev and deps.is_owner(uid)

    # ── общий вызов модели с ключом юзера ──
    def _ask(self, model: str, system: str, user: str, max_tokens: int = 1200) -> str:
        key, _byok, err = self.deps.resolve_key(self.uid, model)
        if err or not key:
            # фолбэк на дешёвую служебную модель, если по выбранной нет ключа
            model = self.deps.aux_model
            key, _byok, err = self.deps.resolve_key(self.uid, model)
            if err or not key:
                return ""
        eff = "high" if self.deps.model_reasons(model) else None
        try:
            return self.deps.complete(
                model, [{"role": "system", "content": system},
                        {"role": "user", "content": user}],
                max_tokens, key, reasoning_effort=eff) or ""
        except Exception as e:
            return f"[ошибка модели: {str(e)[:160]}]"

    # ── SCOPE: декомпозиция цели в под-цели + done-условия ──
    def scope(self, goal: str, context: str = "") -> list:
        self.emit("phase", {"phase": "scope", "label": "Разбиваю цель на под-цели"})
        sys = ("Ты планировщик агента. Разбей ЦЕЛЬ на 1-5 последовательных под-целей. "
               "Для КАЖДОЙ дай явный критерий готовности (done-условие). "
               "Верни ТОЛЬКО JSON-массив объектов: "
               '[{"goal":"...", "accept":"...", "type":"general|code|reason|vision"}]. '
               "Меньше — лучше: не дроби лишнего, объединяй мелочь.")
        usr = f"ЦЕЛЬ:\n{goal}" + (f"\n\nКОНТЕКСТ ЧАТА:\n{context[:3000]}" if context else "")
        raw = self._ask(self.deps.aux_model, sys, usr, max_tokens=600)
        arr = _extract_json(raw)
        packets = []
        if isinstance(arr, list):
            for it in arr[:MAX_SUBGOALS]:
                if not isinstance(it, dict):
                    continue
                g = str(it.get("goal") or "").strip()
                if not g:
                    continue
                ttype = str(it.get("type") or "general")
                if ttype not in ("general", "code", "reason", "vision"):
                    ttype = "general"
                model = self.deps.best_for_task(g, tier=self.tier)
                packets.append(TaskPacket(
                    goal=g, model=model, task_type=ttype,
                    accept=str(it.get("accept") or "ответ по существу под-цели").strip(),
                    tier=self.tier))
        if not packets:        # план не распарсился → вся цель = одна под-цель (робастно)
            packets = [TaskPacket(goal=goal, model=self.deps.best_for_task(goal, tier=self.tier),
                                  accept="ответ полностью покрывает цель", tier=self.tier)]
        self.emit("scope", {"sub_goals": [{"goal": p.goal, "accept": p.accept,
                                           "model": p.model.split("/")[-1], "type": p.task_type}
                                          for p in packets]})
        return packets

    # ── THINK: мульти-модельная делиберация propose→critique-repair→adversarial→fuse ──
    def think(self, packet: TaskPacket, prior: str = "") -> str:
        self.emit("phase", {"phase": "think", "packet": packet.id,
                            "label": f"Думаю над: {packet.goal[:80]}"})
        ctx = (f"\n\nКОНТЕКСТ от прошлых под-целей:\n{prior[:4000]}" if prior else "")
        # 1) PROPOSE — N лучших-под-задачу моделей отвечают независимо
        experts = self.deps.best_n_for_task(packet.goal, 2, tier=self.tier) or [packet.model]
        proposals = []
        for m in experts:
            txt = self._ask(m, "Реши под-задачу точно, по существу, без воды.",
                            packet.goal + ctx, max_tokens=1200)
            if txt.strip() and not txt.startswith("[ошибка"):
                proposals.append((m, txt))
                self.emit("think_step", {"packet": packet.id, "stage": "propose",
                                         "model": m.split("/")[-1]})
        if not proposals:
            return self._ask(packet.model, "Реши под-задачу точно.", packet.goal + ctx)
        # 2) CRITIQUE-AND-REPAIR — сильнейшая модель критикует и чинит лучший черновик
        best_model = experts[0]
        draft = proposals[0][1]
        crit = self._ask(
            best_model,
            "Ты строгий критик-инженер. Найди ошибки/пробелы/риски в ЧЕРНОВИКЕ и сразу ВЫДАЙ "
            "исправленную, улучшенную версию. Не хвали — чини.",
            f"ПОД-ЗАДАЧА:\n{packet.goal}\n\nЧЕРНОВИК:\n{draft}", max_tokens=1400)
        if crit.strip() and not crit.startswith("[ошибка"):
            draft = crit
            self.emit("think_step", {"packet": packet.id, "stage": "critique-repair",
                                     "model": best_model.split("/")[-1]})
        # 3) ADVERSARIAL — оппонент атакует слабые места (только если есть 2+ мнения)
        adversary = ""
        if len(proposals) > 1:
            adversary = self._ask(
                best_model,
                "Ты адвокат дьявола. Кратко: где ответ может быть НЕВЕРЕН или неполон? "
                "Только конкретные возражения, по пунктам.",
                f"ПОД-ЗАДАЧА:\n{packet.goal}\n\nОТВЕТ:\n{draft}", max_tokens=500)
            if adversary.strip():
                self.emit("think_step", {"packet": packet.id, "stage": "adversarial"})
        # 4) FUSE — сплавляем черновик + возражения + альтернативы в один выверенный ответ
        panel = "\n\n".join(f"[Мнение {i+1}]\n{t}" for i, (_, t) in enumerate(proposals))[:8000]
        fused = self._ask(
            best_model,
            "Сплавь мнения и критику в ОДИН выверенный ответ. Бери согласованное, отбрасывай "
            "то, что выдумала лишь одна модель, учти возражения. Отвечай по-русски, по делу.",
            f"ПОД-ЗАДАЧА:\n{packet.goal}\n\nМНЕНИЯ:\n{panel}\n\n"
            f"УЛУЧШЕННЫЙ ЧЕРНОВИК:\n{draft}\n\nВОЗРАЖЕНИЯ:\n{adversary or '—'}",
            max_tokens=1600)
        self.emit("think_step", {"packet": packet.id, "stage": "fuse"})
        return fused.strip() or draft

    # ── ACT: code-as-action через существующие тулзы (инспектируемо) ──
    def act(self, packet: TaskPacket, thought: str) -> tuple:
        """Если под-цель требует действия (поиск/код/браузер), модель вызывает тулзу из реестра.
        Возвращает (final_text, tool_runs). Тулзы — те же deps.tools, новый exec-путь НЕ изобретаем."""
        if not self.tools:
            return thought, []
        tool_names = sorted(self.tools.keys())
        sys = ("Если для под-цели нужно ДЕЙСТВИЕ (поиск в вебе, запуск кода, открыть страницу), "
               "ВЕРНИ РОВНО ОДИН вызов инструмента в формате "
               '```json{"name":"<инструмент>","args":{...}}```. '
               f"Доступные инструменты: {', '.join(tool_names)}. "
               "Если действие НЕ нужно (ответ уже готов в размышлении) — верни слово NOACTION.")
        runs = []
        cur = thought
        for step in range(MAX_ACT_STEPS):
            decision = self._ask(packet.model, sys,
                                 f"ПОД-ЦЕЛЬ:\n{packet.goal}\n\nТЕКУЩЕЕ РАЗМЫШЛЕНИЕ:\n{cur[:3000]}",
                                 max_tokens=400)
            if "NOACTION" in decision.upper()[:40]:
                break
            call = _strip_tool_call(decision)
            if not call:
                break
            name, args = call
            if name not in self.tools:
                break
            self.emit("act", {"packet": packet.id, "tool": name, "args": args, "status": "running"})
            try:
                result = self.tools[name](args)
            except Exception as e:
                result = f"error: {e}"
            ok = not str(result).startswith("error:")
            runs.append({"name": name, "args": args, "result_preview": str(result)[:400], "ok": ok})
            self.emit("act", {"packet": packet.id, "tool": name, "status": "done", "ok": ok,
                              "preview": str(result)[:300]})
            # фолдим результат тулзы обратно в размышление (даём модели «увидеть» результат)
            cur = self._ask(
                packet.model,
                "Учти РЕЗУЛЬТАТ инструмента и дай обновлённый ответ на под-цель. По-русски, по делу.",
                f"ПОД-ЦЕЛЬ:\n{packet.goal}\n\nБЫЛО:\n{cur[:2000]}\n\n"
                f"РЕЗУЛЬТАТ {name}:\n{str(result)[:3000]}", max_tokens=1400) or cur
        return cur, runs

    # ── VERIFY: результат против accept-критерия; только passing = done ──
    def verify(self, packet: TaskPacket, answer: str) -> tuple:
        self.emit("phase", {"phase": "verify", "packet": packet.id, "label": "Проверяю результат"})
        sys = ("Ты строгий приёмщик. Проверь, удовлетворяет ли РЕЗУЛЬТАТ критерию приёмки. "
               'Верни ТОЛЬКО JSON: {"verified": true|false, "reason": "кратко почему"}.')
        usr = (f"ПОД-ЦЕЛЬ:\n{packet.goal}\n\nКРИТЕРИЙ ПРИЁМКИ:\n{packet.accept}\n\n"
               f"РЕЗУЛЬТАТ:\n{str(answer)[:4000]}")
        raw = self._ask(self.deps.aux_model, sys, usr, max_tokens=200)
        obj = _extract_json(raw)
        if isinstance(obj, dict):
            ok = bool(obj.get("verified"))
            reason = str(obj.get("reason") or "")[:300]
        else:                              # не распарсили строгий JSON → эвристика, не врём «прошло»
            low = (raw or "").lower()
            ok = ("true" in low or "да" in low or "прош" in low) and not (
                "false" in low or "не прош" in low)
            reason = (raw or "")[:300] or "нет внятного вердикта"
        self.emit("verify_done", {"packet": packet.id, "verified": ok, "reason": reason})
        return ok, reason

    # ── один под-цикл: THINK→ACT→VERIFY с bounded critique-repair ретраями ──
    def run_subgoal(self, packet: TaskPacket, prior: str = "") -> SubGoalResult:
        res = SubGoalResult(packet=packet)
        feedback = ""
        for attempt in range(1, MAX_REPAIR_RETRIES + 2):     # 1 + retries
            res.attempts = attempt
            thought = self.think(packet, prior + ("\n\nПРОШЛАЯ ПОПЫТКА НЕ ПРОШЛА: " + feedback
                                                  if feedback else ""))
            answer, runs = self.act(packet, thought)
            res.tool_runs.extend(runs)
            ok, reason = self.verify(packet, answer)
            res.answer = answer
            res.verified = ok
            res.verify_reason = reason
            if ok:
                break
            feedback = reason
            if attempt <= MAX_REPAIR_RETRIES:
                self.emit("repair", {"packet": packet.id, "attempt": attempt, "reason": reason})
        return res

    # ── ПОЛНЫЙ ПРОГОН L15 ──
    def run(self, goal: str, context: str = "", run_id: str = None) -> dict:
        run_id = run_id or ("aos_" + uuid.uuid4().hex[:10])
        state = AgentState(self.deps, self.uid, run_id, goal)
        self.emit("start", {"run_id": run_id, "goal": goal})
        # STATE/long-term: подмешиваем RAG-контекст юзера, если доступен
        if self.deps.rag_context and not context:
            try:
                context = self.deps.rag_context(self.uid, [{"role": "user", "content": goal}]) or ""
            except Exception:
                context = ""
        packets = self.scope(goal, context)
        state.working["sub_goals"] = [p.to_dict() for p in packets]
        state.persist()
        prior = ""
        for i, packet in enumerate(packets):
            self.emit("subgoal", {"index": i, "total": len(packets), "goal": packet.goal,
                                  "packet": packet.to_dict()})
            r = self.run_subgoal(packet, prior)
            state.results.append(r.to_dict())
            state.working["cursor"] = i + 1
            state.semantic.append(f"{packet.goal[:120]} → {('OK' if r.verified else 'частично')}")
            prior += f"\n\n### {packet.goal}\n{r.answer}"
            state.persist()
        # ИТОГ: сплавляем под-цели в один связный ответ
        final = self._synthesize(goal, state.results)
        self.emit("final", {"run_id": run_id, "text": final,
                            "verified": sum(1 for r in state.results if r.get("verified")),
                            "total": len(state.results)})
        state.semantic.append(f"ИТОГ: {final[:200]}")
        state.record_experience()
        state.persist()
        return {"run_id": run_id, "goal": goal, "final": final,
                "sub_goals": state.results,
                "plan": [p.goal for p in packets]}

    def _synthesize(self, goal: str, results: list) -> str:
        if len(results) == 1:
            return results[0].get("answer", "")
        joined = "\n\n".join(f"### {r['packet']['goal']}\n{r.get('answer','')}" for r in results)[:12000]
        return self._ask(
            self.deps.best_for_task(goal, tier=self.tier),
            "Собери единый связный ответ из результатов под-целей. Без повторов, по делу, по-русски. "
            "Это финальный ответ агента пользователю.",
            f"ЦЕЛЬ:\n{goal}\n\nРЕЗУЛЬТАТЫ ПОД-ЦЕЛЕЙ:\n{joined}", max_tokens=1800) or joined


# ──────────────────────────────────────────────────────────────────────────────
# ПУБЛИЧНЫЙ API
# ──────────────────────────────────────────────────────────────────────────────


def run(deps: HarnessDeps, uid: str, goal: str, context: str = "",
        emit: Callable[[str, dict], None] = None, owner_dev: bool = False,
        tier: str = None, run_id: str = None) -> dict:
    """L15: один прогон харнеса по цели. server.py вызывает это тонкой строкой из /api/agent_os."""
    h = Harness(deps, uid, emit=emit, owner_dev=owner_dev, tier=tier)
    return h.run(goal, context=context, run_id=run_id)


def resume(deps: HarnessDeps, uid: str, run_id: str,
           emit: Callable[[str, dict], None] = None) -> Optional[dict]:
    """Возобновить прерванный прогон по run_id (STATE/resumable). Догоняет недоделанные под-цели."""
    st = AgentState.resume(deps, uid, run_id)
    if not st:
        return None
    h = Harness(deps, uid, emit=emit)
    packets = [TaskPacket(**{k: v for k, v in p.items() if k in TaskPacket.__dataclass_fields__})
               for p in st.working.get("sub_goals", [])]
    cursor = int(st.working.get("cursor") or 0)
    prior = "\n\n".join(f"### {r['packet']['goal']}\n{r.get('answer','')}" for r in st.results)
    for i in range(cursor, len(packets)):
        r = h.run_subgoal(packets[i], prior)
        st.results.append(r.to_dict())
        st.working["cursor"] = i + 1
        prior += f"\n\n### {packets[i].goal}\n{r.answer}"
        st.persist()
    final = h._synthesize(st.goal, st.results)
    st.record_experience()
    st.persist()
    return {"run_id": run_id, "goal": st.goal, "final": final, "sub_goals": st.results,
            "plan": [p.goal for p in packets]}


# ──────────────────────────────────────────────────────────────────────────────
# L13 — MULTI-AGENT (Chad-style): N изолированных под-агентов → чистый мерж.
# Логическая изоляция задач + слияние результатов (in-process async, не git-worktrees).
# Переиспользует тот же харнес на каждого под-агента.
# ──────────────────────────────────────────────────────────────────────────────


def fan_out(deps: HarnessDeps, uid: str, goal: str,
            emit: Callable[[str, dict], None] = None, n: int = 3,
            owner_dev: bool = False, tier: str = None) -> dict:
    """L13: разложить цель на N непересекающихся под-задач → запустить N изолированных
    под-агентов параллельно (каждый = свой Harness-прогон) → слить чисто.
    Изоляция здесь = логическая (свой run_id, своя память-прогон, своя ветка таймлайна)."""
    emit = emit or (lambda k, d: None)
    n = max(2, min(int(n or 3), 5))
    emit("fanout_start", {"goal": goal, "n": n})

    # 1) РАЗБИЕНИЕ на непересекающиеся под-задачи (отдельный планировщик — disjoint важен)
    plan_h = Harness(deps, uid, emit=lambda k, d: None, tier=tier)
    raw = plan_h._ask(
        deps.aux_model,
        f"Разбей задачу на ровно {n} НЕПЕРЕСЕКАЮЩИХСЯ независимых под-задачи, которые можно "
        "решать параллельно разными агентами без общего состояния. "
        'Верни ТОЛЬКО JSON-массив строк длиной ' + str(n) + ".",
        f"ЗАДАЧА:\n{goal}", max_tokens=500)
    subtasks = _extract_json(raw)
    if not isinstance(subtasks, list) or not subtasks:
        subtasks = [goal]
    subtasks = [str(s).strip() for s in subtasks if str(s).strip()][:n]
    emit("fanout_plan", {"subtasks": subtasks})

    # 2) ПАРАЛЛЕЛЬНЫЙ ЗАПУСК изолированных под-агентов
    results: dict = {}
    lock = threading.Lock()

    def _agent(idx: int, sub: str):
        rid = f"fa_{uuid.uuid4().hex[:8]}_{idx}"
        emit("agent", {"agent": idx, "task": sub, "status": "running", "run_id": rid})

        def sub_emit(kind, data):           # пробрасываем под-таймлайн с меткой агента
            emit("agent_step", {"agent": idx, "kind": kind, **data})
        try:
            h = Harness(deps, uid, emit=sub_emit, owner_dev=owner_dev, tier=tier)
            r = h.run(sub, run_id=rid)
            out = r.get("final", "")
        except Exception as e:
            out = f"[под-агент {idx} упал: {str(e)[:160]}]"
        with lock:
            results[idx] = {"agent": idx, "task": sub, "result": out, "run_id": rid}
        emit("agent", {"agent": idx, "status": "done", "preview": str(out)[:200]})

    import concurrent.futures as cf
    with cf.ThreadPoolExecutor(max_workers=min(4, len(subtasks))) as ex:
        futs = [ex.submit(_agent, i, s) for i, s in enumerate(subtasks)]
        for _ in cf.as_completed(futs):
            pass

    ordered = [results[i] for i in sorted(results.keys())]

    # 3) ЧИСТЫЙ МЕРЖ результатов под-агентов
    emit("merge", {"status": "running", "label": "Сливаю результаты под-агентов"})
    joined = "\n\n".join(f"### Агент {r['agent']+1}: {r['task']}\n{r['result']}" for r in ordered)[:12000]
    merged = plan_h._ask(
        deps.best_for_task(goal, tier=tier),
        "Слей результаты независимых под-агентов в ОДИН связный, непротиворечивый ответ. "
        "Убери дубли, согласуй противоречия (отметь, если они есть), по-русски, по делу.",
        f"ИСХОДНАЯ ЗАДАЧА:\n{goal}\n\nРЕЗУЛЬТАТЫ АГЕНТОВ:\n{joined}", max_tokens=1800) or joined
    emit("merge", {"status": "done"})
    emit("fanout_final", {"text": merged, "agents": len(ordered)})
    return {"goal": goal, "merged": merged, "agents": ordered, "subtasks": subtasks}
