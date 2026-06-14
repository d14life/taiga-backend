# Аудит конфигурируемых параметров Taiga AI (2026-06-14)

**Краткий ответ Damir'у:** Да — у Агентов, Совета и Мозга есть полноценный выбор моделей и параметры, и явный выбор пользователя честно уважается бэкендом (catalog-gated, не перетирается молча). После фикса 2026-06-14 деградация бюджета НЕ свапает явно выбранную модель (только авто-режим).

## Главные дыры (кандидаты на доработку)
1. **per-worker модель в «Команде»** доступна ТОЛЬКО через сохранённых агентов; у встроенных ролей (Стратег/Инженер/…) модель не выбирается — падают на дефолт воркера. → добавить инлайн-пикер модели на роль.
2. **`server_memory` / `rag_smart` / `rag_workspace`** читаются `/api/chat` и Советом, но основной чат `send()` их НЕ шлёт (память/RAG собираются на клиенте и вшиваются в `system`). Несогласованность: воркеры оркестратора их читают, чат — нет.
3. **Режим воркеров `mode` (parallel/sequential)**, **verify/accept-конверт**, **BYOK-на-воркера** — есть в бэкенде, в UI «Команды» не выведены.
4. **Слияние (beam)** полностью реализовано в бэке (`chat_council(beam=True)`, фьюжн-дегаллюцинация), но `beamOn` захардкожен `false` и убран из UI (свёрнут в Совет).
5. **Авто-Мозг** на `__auto__`+трудный запрос включается молча (`query_is_hard`) — нельзя отключить точечно, только выбрав явную модель/режим.

## 1. Глобальные настройки чата
- **Модель (per-feature override)** — пикер/кастом-пилюли/cog → `overrides[feature]`; `__auto__` или id каталога. AUTO ✓ honored ✓ → `model`+`fallbacks`.
- **Температура** — per-mode конфиг → `temperature` (0…1.5). honored ✓, но сохранённый per-mode конфиг бьёт значение из запроса.
- **Длина ответа** — `budget` eco/norm/max = 1024/2048/8000 → `max_tokens`.
- **Ценовой потолок (тир)** — `costTier` off/cheap/mid/top → `tier`. AUTO-only: бьёт ТОЛЬКО по `__auto__`.
- **Глубина** — DepthSlider 1-5 → `reasoning_effort` off/low/medium/high (только думающим; ур.4-5 = deepVariant).
- **Окно памяти** — `memWindow` 0-40 (клиент режет историю).
- **Лимит $** — `spendCap` → `max_spend`. honored ✓.
- **Источник правды** — `grounded` тумблер → `grounded` (+ цитаты [N], режет web-поиск). honored ✓.
- **Ultra/без отказов** — `noRefusal` → через `system`.
- **memMode local/server, smartRag** — КЛИЕНТСКИЕ; НЕ шлют `server_memory`/`rag_smart`.

## 2. Режимы ответа
- **Обычный чат:** `__auto__`→route_model() иначе явная. honored ✓. Авто-Мозг на трудном запросе (молча).
- **Мозг:** driver (`brainLead`, пусто=авто) + эксперт `model` (`brainExpert` auto/picked, дефолт auto); `brainExperts` 1-3. honored ✓ → `brain`,`driver`,`model`,`brainExperts`.
- **Совет:** участники 2-5 (`councilMembers`→`councilModels`, пусто=авто топ-N); синтез (`councilSynth`, иначе модель юзера); `memberPrompts[]`; `councilN`. honored ✓. beam убран из UI.
- **Сравнение:** `compareModels` веер без синтеза. honored ✓.
- **Ресёрч:** `researchDepth` fast/medium/deep → `depth`; `researchSourcesN` → `sources`; `researchSynth`→`model`. honored ✓.
- **Глубоко/Ультра:** 2-шаг sendPipeline; план-модель=авто-ultra, ОТВЕТ-модель уважает пикер юзера. honored ✓. Оба шага шлют `grounded` (item 4).

## 3. Агенты / Оркестратор («Команда»)
- **Цель** → `task`; **роли** (6) → `workers[].skill`; **сохранённые агенты** → `workers[].model` (catalog-gated). honored ✓.
- **Бюджет** $0.2/$1/$5/0 → `max_spend`; **seed** (Чат→Агент) → `seed`.
- **Мышление воркеров** `workerThink` normal/brain/council → `worker_think` (item 5). honored ✓.
- Воркеры = полноценные чаты: память+RAG+grounding+safe-тулзы+tool-loop (item 2).

## Опорные файлы
- chat.tsx — стейт/пикеры/диспетч `dispatchSend`; use-taiga-chat.ts — `SendOpts`+`baseBody`+`sendPipeline`; orchestrator.ts — `orchestrateStream`; team-panel.tsx — роли/бюджет/`workerThink`; depth-slider.tsx — глубина→effort; server.py — `chat()`/`chat_council`/`api_orchestrate`/`_orchestrate_worker_runner`/`budget_degrade`.
