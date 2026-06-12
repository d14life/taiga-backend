# LIFT-MAP-2 — что взять из гитхаб-реп (глубокий разбор кода, 2026-06-12)

ВСЕ репо ниже = **MIT** → код можно КОПИРОВАТЬ (сохрани MIT-нотис в скопированных файлах).
Исключения (НЕ трогать): anthropics/claude-code (закрыт) · tanbiralam/claude-code (слит/DMCA).
free-claude-code подтверждён как ОРИГИНАЛЬНЫЙ (не слитый) → безопасен.

## 🔴 ВЫСШИЙ ПРИОРИТЕТ — drop-in код

### 1. free-claude-code → роутинг/связка (BACKEND/ural) [COPY-CODE, Python, MIT]
Это Anthropic↔провайдер-прокси на Python. Бери ~1500 строк:
- `core/anthropic/conversion.py` (`AnthropicToOpenAIConverter`) — полная конверсия сообщений/тулзов/
  системы/thinking с edge-кейсами. Заменяет наш ad-hoc формат-клей.
- `core/anthropic/stream_recovery.py` — холдбек-буфер + ТИХИЙ ретрай оборванного стрима + починка
  обрезанного tool-JSON. Лечит главную боль дешёвых провайдеров (обрывы) — сложно написать с нуля.
- `core/anthropic/tools.py` (`HeuristicToolParser`) — ловит tool-call'ы в ПЛЕЙН-ТЕКСТЕ → tool_use.
  **Включает тулзы на моделях БЕЗ нативного function-calling** (огромно для uncensored-моделей).
- тянуть вместе с `core/anthropic/sse.py` (общие хелперы).

### 2. RAG-Anything → RAG апгрейд (BACKEND/ural) [COPY-CODE, MIT]
Наш RAG — текст-only. Бери мультимодал:
- MinerU/Docling парсер (реальные PDF/таблицы/картинки с лейаутом) — `insert_content_list()` API.
- `ImageModalProcessor` + `TableModalProcessor` (VLM-caption → эмбеддинг; у нас vision уже есть → почти даром).
- `content_list` JSON-схема `{type:text|image|table|equation, page_idx}` — единый ингест-контракт.
- VLM-Enhanced Query (картинку из контекста скармливаем зрячей модели на ответе).

### 3. open-generative-ai → студия (STUDIO/amur) [COPY-CODE, MIT]
- `packages/studio/src/muapi.js` `submitAndPoll/pollForResult/uploadFile` — async submit→poll→
  нормализация для image/video/music. Выкинь Muapi-URL, оставь цикл. Готовый движок генерации.
- `models_dump.json` — 200+ моделей с param-схемами (aspect/duration/enum) — сид каталога студии.
- [PATTERN] schema-driven форма из `inputs` (они НЕ доделали — мы сделаем: string→textarea, int+min/max→слайдер, enum→select).

### 4. ECC + claude-skills → скиллы/маркетплейс (CORE-B/sosna) [COPY-CODE, MIT]
- **ECC:** формат `skills/<name>/SKILL.md` (frontmatter name/description/origin) + `skills-health.js`
  (валидатор) + `skill-create-output.js` (скаффолдер) = почти наш skill-builder/библиотека вербатим.
  Готовые скиллы тянуть: `deep-research`, `agentic-os`, `universal-scraping-architect`, `cost-tracking`.
- **claude-skills:** `.claude-plugin/marketplace.json` схема (name/source/description/version/keywords/
  **category**) = ровно наш категоризированный-с-тумблерами реестр. + `write-a-skill`, `workflow-builder`.
- ⛔ НЕ тянуть в дефолт: `prompt-governance`/`security-guidance` (цензура — мы uncensored).

### 5. ECC agentic-os + claw-code → агент/мозг (BACKEND/CORE)
- **ECC `agentic-os` SKILL.md** — ядро router→специалисты→file-state = блюпринт нашей агент-системы [COPY-CODE].
- **claw-code `task_packet.rs` `TaskPacket`** — конверт делегации с моделью/провайдером НА ПОД-ЗАДАЧУ
  + acceptance/verification (идеально для agent-builder + связки) [PATTERN, Rust→Python].
- **claude-skills `handoff`/`agenthub`** — координация мульти-агентов [PATTERN].

## 🟡 СРЕДНИЙ
- **claw-code `tools/src/lib.rs`** — таблица 58 tool-спеков (JSON input_schema) — готовый каталог тулз [COPY JSON].
- **langchain-text-splitters** [COPY-CODE, MIT] — `RecursiveCharacterTextSplitter` + `SemanticChunker` +
  code/markdown-aware сплиттеры (наш RAG бьёт фикс-размером → апгрейд).
- **LangChain retriever-паттерны** [PATTERN]: MultiQuery (рерайт запроса→N поисков), Ensemble+RRF
  (dense+BM25 гибрид), ParentDocument (мелкий-чанк-эмбед/крупный-верни), ContextualCompression (реранк).
- **claw-code provider-robustness** (body-size капы, 8× jittered backoff) [COPY constants].

## РАСКИДКА ПО СЕССИЯМ (добавить к ADDON-FINAL)
- **ural (BACKEND):** #1 free-claude-code конверсия+stream-recovery+heuristic-tools · #2 RAG-Anything мультимодал · langchain-splitters · TaskPacket-делегация.
- **amur (STUDIO):** #3 muapi submitAndPoll движок + models_dump каталог + schema-форма.
- **sosna (CORE-B):** #4 ECC SKILL.md формат + skills-health + claude-skills marketplace.json + готовые скиллы.
- **kedr (CORE):** schema-driven форма (студия-параметры), tool-каталог 58-спеков (для tools-меню).

ЛЕГАЛЬНО: всё MIT. free-claude-code — оригинал, не слив (в отличие от 2 claude-code). Сохраняй MIT-нотис в копиях.
