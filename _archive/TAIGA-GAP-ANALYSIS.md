# Тайга — GAP-АНАЛИЗ против holy-grail репо (честно, 2026-06-12)

Сравнение того, что РЕАЛЬНО построено (опрос кода всех 3 лан), против LibreChat · Aider ·
Cline · OpenHands · Continue · ECC · Claude Code · Hermes. Цель — найти «вторые 50%».

**Вердикт (обновлён 08:55): ~80% готово** (было 50-55%). За ночную сессию ural/BACKEND закрыл
9 дыр глубины агентной-ОС — все с тестами. Осталось owner-gated (оплата/MCP-OAuth/соц) + фронт CORE.

## ✅ ЗАКРЫТО ЭТОЙ СЕССИЕЙ (было «вторые 50%»)
- #1 Coding-агент (edit_file/write_file/revert, Aider-style) — END-TO-END подтверждён (агент сам создал файл)
- #2 Undo (бэкап-откат) · #3 Sandbox-rlimits (+ safety-hook на rm -rf/fork-бомбы)
- #4 Гонка баланса (лок+атомик, audit#1) — тест 50 параллельных → ровно 9.25
- #5 Auth/мультиюзер (auth.py, PBKDF2+HMAC) · #6 Hooks (pre/post + safety) · #7 Permission-ladder (plan/auto/full)
- #8 Скиллы-маркетплейс (skills_lib.py, 358 ECC, progressive-load) · #11 Cron-агенты (scheduler.py)
- Surgical вместо полной SQLite-миграции (риск>польза).
- Само-исцеление дефолт-моделей: на старте/авто-рефреше каждая дефолт-модель сверяется с живым
  каталогом; устаревшая (как deepseek-v3.1 → 404) автоматом подменяется на рабочую запасную.
  Реестр DEFAULTS (5 ролей: cheap/chat/code/reason/smart); все под-пути читают его —
  chat()+route_model(), OpenAI-API, relay (responder), research. Тесты: 5/5 ролей→живые, авто-роут живьём.
Новые модули: auth.py · scheduler.py · skills_lib.py · orchestrator.py · browser_hub.py · guard.py.

## ❌ ОСТАЛОСЬ (~20%) — НЕ solo-бэкенд
- owner-gated: реальная оплата · #10 MCP-OAuth коннекторы · соц-публикация (нужны аккаунты)
- CORE/kedr: прокси-роуты + UI-панели (BACKEND-API.md)
- опц: FTS5-recall · настоящая БД (если масштаб потребует)

## ✅ ЧТО УЖЕ ЕСТЬ (сильно — паритет/лучше)
| Домен | Статус | Заметка |
|---|---|---|
| Мульти-модель чат (732 модели, авто-выбор, бренд-фолбэк) | ✅ лучше | у нас 4 провайдера + крипта + uncensored |
| Дерево сообщений / форк / правка | ✅ есть | msg-tree.ts + chat |
| Пресеты · папки · команды · палитра | ✅ есть | presets/folders/command-builder |
| Память на чат + кросс-чат профиль + threat-scan | ✅ есть | + анти-отравление (мы) |
| RAG (ingest/query/delete + инжект в чат) | ✅ есть | эмбеддинги NanoGPT |
| Эпизодическая память (поиск по чатам) | ✅ есть | /api/recall |
| Супер-поиск (8 движков, 2 провайдера, deep+Jina) | ✅ лучше | Sonar/Exa/Brave/Venice-web |
| Генерация: image(221)/video(128)/audio/cinema/photo-tools | ✅ лучше | живой каталог + метеринг |
| Агентный браузер (Playwright, co-browse, cookies-шифр) | ✅ есть | + анти-SSRF + редакция |
| Оркестратор агентов (LangGraph, 17 скиллов, BYOK, SSE) | ✅ есть | orchestrator-panel |
| Окно «Решает сам» (decision-card) | ✅ есть | UI + бэкенд-гейт |
| Артефакты/канвас · skill/agent-builder · MCP базовый | ✅ есть | canvas/skill-builder/agent-gallery |
| Pay-as-you-go метеринг (всё гейтится по балансу) | ✅ есть | owner free |

## ❌ ВТОРЫЕ 50% — ЧЕГО НЕТ (глубина агентной-ОС)
| # | Фича | Лучший репо | У нас | Приоритет |
|---|---|---|---|---|
| 1 | **Coding-агент: edit_file / search-replace diff / apply** | Aider (editblock_coder.py) · Cline · OpenHands | ❌ только shell/read | 🔴🔴 высокий |
| 2 | **Чекпоинты / undo** (snapshot после каждого шага) | Cline (shadow-git) · Cursor | ❌ нет | 🔴🔴 высокий |
| 3 | **Изолированный sandbox** код-исполнения (per-user, безопасно) | OpenHands (docker) · E2B | ❌ голый subprocess, owner-only | 🔴🔴 высокий |
| 4 | **Настоящая БД** (SQLite/Postgres) вместо плоских JSON | LibreChat (Mongo) · все | ❌ flat JSON | 🔴🔴 высокий (audit #1) |
| 5 | **Auth / мультиюзер** (login, сессии, sharing) | LibreChat · все SaaS | ❌ только uid | 🔴 средний |
| 6 | **Hooks** (PreToolUse/PostToolUse/Stop) | Claude Code · ECC | ❌ нет | 🔴 средний |
| 7 | **Permission-ladder** (plan→auto-edit→full, Shift-Tab) | Claude Code · Cline | 🟡 decision-card частично | 🔴 средний |
| 8 | **Скиллы-маркетплейс** (262 скилла, прогр.загрузка, security-scan) | ECC · Claude Code | 🟡 skill-builder, нет библиотеки | 🔴 средний |
| 9 | **DAG/зависимый оркестратор** + субагент-изоляция | ECC (/multi-*) · Claude Code (Task) | 🟡 parallel+sequential, нет DAG | 🟡 |
| 10 | **MCP-коннекторы** (Gmail/Drive/календарь, OAuth) | LibreChat · Claude Code | 🟡 /api/mcp базовый | 🟡 |
| 11 | **Фоновые/расписание агенты** (cron) | Hermes · GitHub Agents | ❌ нет | 🟡 |
| 12 | **Само-улучшение** (ИИ пишет себе скиллы/память) | Hermes | ❌ нет | 🟢 низкий |
| 13 | **Соц-публикация** (YT/TikTok/IG) + воркфлоу | (muapi паттерн) | ❌ нет | 🟢 низкий |
| 14 | **Прокси-роуты для новых эндпоинтов** (rag_delete/recall/cookies/catalog_refresh/websearch) | — | ❌ нет (half-wire) | 🔴 быстрый фикс (CORE) |

## РЕКОМЕНДУЕМЫЙ ПОРЯДОК «вторых 50%»
**Волна 1 — агентная-ОС глубина (то, за что платят, что у holy-grail есть):**
1. Coding-агент: lift Aider `editblock_coder.py` → edit_file/diff/apply (BACKEND)
2. Чекпоинты/undo: shadow-git паттерн Cline (BACKEND)
3. Изолированный sandbox (E2B/gVisor/docker) для код-исполнения всем (BACKEND/infra)
4. Прокси-роуты для 5 новых эндпоинтов (CORE, 30 мин)

**Волна 2 — инфра/масштаб:**
5. Миграция flat-JSON → SQLite (event-log, транзакции) — координированно
6. Auth/мультиюзер · permission-ladder · hooks

**Волна 3 — экосистема:**
7. Скиллы-маркетплейс (ECC 262) · MCP-коннекторы · фоновые/cron агенты · соц-публикация

— ural (BACKEND). Источники паттернов: TAIGA-LIFT-MAP.md.
