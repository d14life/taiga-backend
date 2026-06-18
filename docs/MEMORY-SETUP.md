# Стек памяти — статус установки (2026-06-18)

Поставлено на Мак Damir-а ДО старта сборки. Состояние честное.

## graphify — РАБОТАЕТ ПОЛНОСТЬЮ (offline, без API)
- Установлен: `uv tool install graphifyy` (graphify 0.8.41 + graphify-mcp).
- Скилл зарегистрирован в Claude Code (`/graphify`).
- **Граф кода построен:** 6073 узла, 10602 ребра, 431 кластер по 532 файлам → `graphify-out/`
  (закоммичен: graph.json, GRAPH_REPORT.md).
- Запрос работает: `graphify query "..."`, `graphify path "A" "B"`, `graphify explain "X"`.
- Обновлять: `graphify update .` (AST, без LLM). Доки/PDF семантически — нужен LLM-бэкенд
  (`--backend gemini|openai|deepseek|ollama`, или OPENAI_BASE_URL на NVIDIA-совместимый).

## gbrain — УСТАНОВЛЕН + ДОКИ ИМПОРТИРОВАНЫ, поиск ждёт эмбеддинги
- Установлен: `bun install -g github:garrytan/gbrain` (gbrain 0.42.51). Bun поставлен через brew.
- Инициализирован локально: `gbrain init --pglite --no-embedding` (PGLite, без облака).
- **Импортировано: 118 доков, 575 чанков.**
- Зарегистрирован как MCP в Claude Code: `claude mcp add gbrain -- gbrain serve`.
- ОГРАНИЧЕНИЕ: hybrid-поиск и self-wiring граф включаются на ЭМБЕДДИНГАХ. OpenAI/Voyage/
  ZeroEntropy гео-блокнуты в РФ. РАЗБЛОК: указать NVIDIA-эмбеддинги (OpenAI-совместимо,
  работает из РФ, модель `baai/bge-m3` уже юзалась в reel-intelligence):
  `gbrain config set embedding_model openai:baai/bge-m3` + OPENAI_BASE_URL=https://integrate.api.nvidia.com/v1
  + OPENAI_API_KEY=<nvidia> → затем `gbrain embed --stale && gbrain extract links`.

## rag-anything — СТАВИТСЯ (мультимодальный RAG по PDF/докам/скринам)
- `pip install 'raganything[all]'` (LightRAG + парсеры). MinerU-модели качаются при первом запуске.
- Нужен OpenAI-совместимый LLM + vision. РАЗБЛОК тот же: NVIDIA endpoint (bge-m3 эмбеддинги +
  llama-vision для картинок) — работает из РФ.

## ИТОГ для новой сессии
- **graphify готов прямо сейчас** — спрашивай граф кода вместо грепа.
- **gbrain**: доки уже внутри; включи NVIDIA-эмбеддинги одной командой → заработает синтез с цитатами.
- **rag-anything**: добери после установки, наведи на NVIDIA endpoint для PDF/скринов.
- Ключи NVIDIA/Gemini: `~/.reel-intelligence.env`. Gemini из РФ — только через туннель `ssh -fN -D 1080 mostik`.
