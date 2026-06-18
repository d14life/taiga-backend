# LIFT-MAP-3 — репы, что Damir НЕ находил (research head-engineer, 2026-06-12)

✅=permissive (MIT/Apache, копировать код OK) · ⚠️=copyleft/условно (GPL/AGPL/non-commercial — осторожно) · 🚫=не копировать.

## 🧠 ПАМЯТЬ — самый слабый наш узел, лучшие апгрейды
- 🔴 **Mem0** (`mem0ai/mem0`, Apache ✅) [DEPENDENCY] — авто-извлечение фактов + **реконсиляция ADD/UPDATE/DELETE** (память не раздувается). Дроп-ин долгосрочная память за нашим RAG. → BACKEND.
- 🔴 **Letta/MemGPT** (`letta-ai/letta`, Apache ✅) [PATTERN+COPY промптов] — **модель САМА правит свою память** через тулзы (core_memory_append/replace) + «sleep-time» консолидация на простое. → BACKEND/память. (Это и есть «Тайга умнеет со временем».)
- 🟡 **Zep/Graphiti** (Apache ✅) — би-темпоральный граф (знает КОГДА факт был верен, гасит устаревшее). Нужен граф-DB → позже, когда всплывут противоречия.

## 💬 ЧАТ-UI / ОРКЕСТРАЦИЯ
- 🔴 **big-AGI** (`enricoros/big-AGI`, MIT ✅) [COPY] — **Beam**: один промпт веером на N моделей → **Merge/Fusion** в один ответ (де-галлюцинация). Сильнейший апгрейд мульти-модель-ядра. → оркестратор/связка.
- 🔴 **assistant-ui** (`assistant-ui/assistant-ui`, MIT ✅) [COPY, npm] — React-примитивы чата + **generative-UI** (рендер tool-call как компонент) + **inline-аппрув тулзов**. Next.js — низкое трение. → фронт.
- 🟡 **Open-WebUI** (BSD-3 ✅, не копируй пост-0.6.6 брендинг) [PATTERN] — **Pipelines/Functions** middleware (фильтр/трансформ/роут на каждое сообщение). → связка/оркестратор.
- 🟡 **AnythingLLM** (MIT ✅) [PATTERN+COPY] — **workspaces** = изолированный RAG-контейнер на чат + готовые ingestion-коннекторы (PDF/DOCX/YT/GitHub). → память/RAG.
- 🟢 **Lobe Chat** (ПРОПРИЕТАРНАЯ 🚫 — только смотреть) — артефакты-UX + пер-плагин-права. ИМИТИРОВАТЬ, не копировать.
- 🚫 Cherry Studio / Jan (AGPL) — не копировать.

## 🎬 МЕДИА FREE/ЛОКАЛЬНО — и ЛИЦЕНЗ-ЛОВУШКИ (критично для платного сервиса!)
- 🔴 **ComfyUI** (GPL ⚠️ — **RUN-AS-SERVICE**, НЕ линковать в код) — локальный движок image/img2video/audio, workflow=JSON через API. Бэкплейн free-студии. → студия.
- 🔴 **FLUX.1 schnell** (Apache ✅) — image-модель для прода. 🚫 ЛОВУШКА: **FLUX.1 dev = НЕ для коммерции** (платная лицензия). Дефолт free = schnell + SDXL.
- 🔴 **ACE-Step 1.5** (`ace-step/ACE-Step`, Apache/MIT ✅) — FREE музыка с вокалом, коммерч-OK. 🚫 ЗАМЕНЯЕТ **MusicGen (CC-BY-NC = НЕЛЬЗЯ в платном!)** и Stable-Audio (non-commercial). → студия-музыка.
- 🔴 **Kokoro-82M** (Apache ✅, быстрый дефолт-TTS) + **Chatterbox** (MIT ✅, клон голоса). 🚫 ЛОВУШКИ: новый **Piper=GPL**, **Coqui XTTS=CPML** (ограничения). → voice-TTS.
- 🔴 **faster-whisper** (MIT ✅) — STT. + WhisperX (MIT) для таймкодов/диаризации. → voice-STT.
- 🟡 видео кодом: **manim+MoviePy (MIT ✅)** — спина free-видео. 🚫 ЛОВУШКА: **Remotion НЕ бесплатен для команд 4+ ($100/мес)** — у нас 5 сессий/команда → manim+MoviePy дефолт, Remotion опц.

## 🗄 БД / ИНФРА / БЕЗОПАСНОСТЬ (бэкенд stdlib-only — всё лёгкое/сайдкар)
- 🔴 **sqlite-vec** (Apache/MIT ✅) [DEP, C-расширение, zero-dep] — векторный поиск ВНУТРИ .db файла. Память+RAG+реляционка в одном SQLite. → миграция БД.
- 🔴 **sqlite-utils + sqlite-migrate** (`simonw`, Apache ✅) [DEP build-time] — инструмент самой JSON→SQLite миграции (transform/migrations, чего stdlib не умеет). → миграция.
- 🟡 **Litestream** (Apache ✅) [RUN-AS-SERVICE, Go-бинарь] — реплика WAL SQLite в S3 (бэкап/PITR, без БД-сервера). → durability когда юзеры.
- 🔴 **LLM-Guard** (`protectai/llm-guard`, MIT ✅) [RUN-AS-SERVICE] — анти-инъекция (DeBERTa). Для нас: ОТКЛЮЧИТЬ цензур-сканеры, оставить безопасность. Тяжёлый (torch) → сайдкаром, не в stdlib-бэк. (Rebuff мёртв.)
- 🟡 **LlamaFirewall** (Meta) — агент-грейд защита (когда тулзы/браузер untrusted) — фаза 2.
- 🟢 **BTCPayServer** (MIT ✅) [RUN-AS-SERVICE] — self-host крипто-оплата 0% (когда оплату расцензурим).
- 🟡 **pyrate-limiter** (MIT ✅) — rate-limit (in-memory stdlib mode) — анти-абуз.

## РАСКИДКА (добавить к беклогу — сессии авто-доберут)
- BACKEND/ural: Mem0 + Letta-память-паттерн · sqlite-vec+sqlite-utils (миграция) · LLM-Guard сайдкар · big-AGI Beam (оркестратор).
- STUDIO/amur: ComfyUI-сервис + FLUX-schnell + **ACE-Step (вместо MusicGen!)** + manim/MoviePy (вместо Remotion).
- CORE/kedr: assistant-ui примитивы (generative-UI/tool-аппрув) · Beam-Merge UI.
- CORE-B/sosna: AnythingLLM workspace-изоляция · Kokoro/Chatterbox/faster-whisper для Voice.
