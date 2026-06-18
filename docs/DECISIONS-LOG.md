# DECISIONS-LOG — что решили и что записать (агент-регистратор)

Журнал решений, просьб Damir и важных находок. **Агент-регистратор** дописывает сюда
(новое — наверх) И дублирует в память: `gbrain capture "<суть>"`. Чтобы ничего не терялось
и новая сессия видела «почему так».

Формат строки: `YYYY-MM-DD — [тип] суть (источник/почему)`. Типы: РЕШЕНИЕ · ПРОСЬБА · НАХОДКА · ОТЛОЖЕНО.

---

## 2026-06-18
- ПИВОТ (критично, подтверждён кодом) — **ЖИВОЙ ПРОДУКТ = `taiga-web/public/shell.html`** (365KB ванильный HTML/JS macOS-апп) + модули `/shell/*.js` (api/modes/studio/design/agent/code/memory/chats/account/automations). `taiga-web/src/app/app/page.tsx` отдаёт его iframe на `/app` («живой macOS-апп… НЕ трогая логику»). React-компоненты (chat.tsx, image-studio.tsx…) = **СТАРОЕ ПРИБЛИЖЕНИЕ, НЕ продукт.** Все 6 столов (Чат/Дизайн/Студия/Агент/Код/Ultra) — отполированные мокапы по design-v3. ЧАСТИЧНО оживлены: **Чат `/api/chat`, память `/api/remember|forget|recall`, init/settings — ЖИВЫЕ**; Студия-ген/Дизайн/Агент — фейк, домотать к бэку. BUILD = оживить shell.html (wire `/shell/*.js` → server.py), НЕ строить React. Понимание-веер + док + Студия-веер целили в React = НЕ ТОТ СЛОЙ (исправлено). Скрины 6 столов: `~/Downloads/claude-sessions/2026-06-18/taiga-screens/`. Совпадает с памятью feedback_taiga_exact_mockup.
- НАХОДКА (критично) — Статическое ПОНИМАНИЕ (11 читателей) ЗАНИЗИЛО готовность UI. Живой апп УЖЕ имеет: **6 столов** (Чат/Дизайн/Студия/Агент/Код/Ultra) — `shell/taiga-topnav.tsx`; **effort-контрол «Усилие»** — `model-control/effort-dial.tsx` + `depth-slider.tsx` (нативный reasoning per-provider); **модель-контрол «Авто»** — `model-control/`; кнопки модов Совет/Мозг/Дебаты/Ресёрч; **нижний macOS-док с iOS-плитками**. UNDERSTANDING-MAP/CHECKLIST ОШИБОЧНО писали «док отсутствует + 5 плоских пиллов». Построил ДУБЛИКАТ AppDock → РЕВЕРТНУЛ (правило скриншотов Damir поймало). УРОК: **истина = живой апп + дизайн, НЕ статический гэп-анализ**; верифицировать UI в браузере ДО сборки. Переориентация «5 столов + effort» — **в основном УЖЕ построена**. Скрин: `~/Downloads/claude-sessions/2026-06-18/taiga-screens/01-existing-app-state.jpeg`.
- РЕШЕНИЕ — **ОБА дизайна = источник истины**: design-v3 (НОВЫЙ — КАК строить, визуальный канон) + usertest-jun15 (СТАРЫЙ — ЧТО система должна делать, фич-поведение). Не только v3. (Damir: «old design second one source of truth too — what the system should do».)
- ПРОСЬБА/РЕШЕНИЕ — **Taiga AI сама использует graphify + эффективные RAG-тулзы** в своей памяти/RAG (граф-память над кодом/доками юзера + мультимодал поверх текущего вектор-RAG `server.py:_rag_*`, Mem0/Letta/grounding). Дать продукту наш граф+RAG-стек. Слой Memory. (Damir: «make taiga ai use graphify too and other effective rag tools».)
- ИСПРАВЛЕНИЕ (Damir уточнил, отменяет прошлую формулировку) — «Мозг/Совет/Дебаты/Сравнить» — это **МОДЫ** (гоняют несколько моделей, думают), НЕ просто усилие. **Усилие (effort) = ОТДЕЛЬНЫЙ ПАРАМЕТР системы:** `deep` (GPT-стиль глубокое рассуждение), `native` (Claude нативное мышление), `fast` (чат) и др. — реализуется НАТИВНО через API (reasoning_effort/thinking-budget per-provider) ЛИБО подбором моделей из списка. Нужен **КОНТРОЛ: модель + мод + усилие** в одном UI. Топ-навигация = **5 столов: Чат/Студия/Дизайн/Агенты/Код + Ultra**. (Damir: «it modes as they have couple models thinking; effort just the parameter — deep for gpt, native for claude, fast for chat; need a control such this model and just different mode, other native passed by api or by models from list».)
- РЕШЕНИЕ — **Эталон-репо = ИСТОЧНИК ИСТИНЫ, юзать ВСЕГДА** как базу каждого стола (правило). (Damir: «we have code repos for them to base you from, use it at all times».)
- РЕШЕНИЕ — **Студия = медиа-студия на базе github.com/anil-matcha/open-generative-ai** (его база + наше; у нас ~7-10 режимов vs его 4). (Damir.)
- ОТЛОЖЕНО — github.com/clawnify/open-studio (ComfyUI-подобное) → PARKED, на потом. (Damir: «leave for later».)
- ПРОСЬБА — Добавить юзер-фичу **«Save»** = ВСЕ ТРИ (Damir: «all»): (1) кэш ответов/контекста (prompt/response caching — повтор не биллится), (2) сохранить ответ/артефакт в личную библиотеку для переиспользования без регенерации, (3) eco-режим (авто-дешёвая модель/короткий ответ/ponytail-промпт на запрос). Экономия денег юзеру; новое, важное. Строить в cross-cut/Settings слое.
- РЕШЕНИЕ — **Дешевизна (ponytail) = ДЕФОЛТ-ОН на всех тирах**; критик-совет гонит КАЖДЫЙ бит и через удешевление использования (не только наши токены). (Damir.)
- РЕШЕНИЕ — Damir = источник истины > доки (доки могут врать). Двойной критик (внутр Claude multi-lens + внешний `external-critique.py`) на каждый бит, пока ОБА не «идеально». (Damir + ENGINEERING-PRINCIPLES #10.)
- НАХОДКА — Построена ФИЧА 1: macOS app-dock (`taiga-web` d7e3617), tsc=0 / app=200; пины = старые мод-пиллы → переориентировать на 5 столов (см. правку выше).
- РЕШЕНИЕ — Внешний критик = веб (Serper, из РФ напрямую) + НЕ-Claude модель (NVIDIA deepseek), Gemini+grounding через туннель как бонус. Хелпер `tools/external-critique.py`. (Damir: «другой взгляд на шестерёнки + сверка с вебом».)
- РЕШЕНИЕ — Критик-агент = постоянная роль (на каждую фичу + на доки + финал на код). Сборка фича-за-фичей, каждый бит до идеала.
- РЕШЕНИЕ — Репо почищен: 63 устаревших дока → _archive/, 23 канон оставлены. 2 дизайна (v3 новый + usertest-jun15 старый).
- НАХОДКА — Security мина #0 (RCE/owner-spoof/SSRF/инъекции) УЖЕ закрыта (sec-коммиты 1-6); не переделывать.
- ОТЛОЖЕНО — Платёж #1 (YooKassa) + Фаза D масштаб = гейт перед публичным выкатом, не сейчас.
- РЕШЕНИЕ — Главный реестр фич = FEATURE-LEDGER (139 сверенных), не «182». Будущие фичи → PARKED-FEATURES.
- РЕШЕНИЕ — Память как MCP в аппе: gbrain (NVIDIA bge-m3) + graphify. Источник истины = код, чат = контекст.

(ниже — дописывать старое по мере переноса из чата)
