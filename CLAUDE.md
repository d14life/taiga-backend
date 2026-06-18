# CLAUDE.md — правила для чистой сессии пересборки Тайги

Ты в проекте **Тайга ИИ** — приватный uncensored мульти-модельный AI для RU/CIS (чат + агенты + студия + дизайн).

> ⚡ ГЛАВНАЯ ТОЧКА ВХОДА: **сначала прочитай `docs/MANIFEST.md` ПОЛНОСТЬЮ** — это мастер-рельсы
> (законы, память-MCP, источники фич = docs/design/FEATURE-LEDGER.md 139 фич, 2 дизайна, поток сборки,
> оценка кода). MANIFEST новее и главнее этого файла. Потом docs/NEW-SESSION-START.md и доки ниже.

Твоя задача: **чистая пересборка через strangler-fig** (см. REBUILD-BRIEF.md). Доп-чтение:
`REBUILD-BRIEF.md` (план+мины) · `ARCHITECTURE-MAP.md` (что где) · `docs/design/FEATURE-LEDGER.md` (139 фич, главный реестр) · этот файл (правила).

## Стек и пути
- Бэк: `server.py` (stdlib http.server, БЕЗ фреймворка), `orchestrator.py`, `skill_caps.py`, `skills_run.py`, `scheduler.py`.
- Фронт: `taiga-web/` (Next.js 16 / React 19 / Tailwind 4, ВЛОЖЕННЫЙ git). Прочитай `taiga-web/AGENTS.md` — там «это не тот Next, что ты знаешь».
- Данные: `~/.mostik-ai/` (db/taiga.db SQLite, identity.txt, u/<uid>/). Бэк на :8777, фронт :3000.

## Рабочий цикл (СТРОГО — never break)
1. Маленький шаг (один вынос/фикс).
2. Проверка: из `taiga-web` → `npx tsc --noEmit` (0 ошибок); трогал бэк → `python3 -c "import ast;ast.parse(open('server.py').read())"` (+ skill_caps.py/skills_run.py); `/app`=200; смоук фичи.
3. ТОЛЬКО зелёное → коммит (сначала `taiga-web`, потом корень-указатель) → push.
4. После правок server.py: `launchctl kickstart -k gui/$(id -u)/com.taiga.backend`.
5. НИКОГДА не коммить сломанное. Один вынос = один коммит. Поведение байт-в-байт (FEATURE-INVENTORY = чек-лист, не регрессить).
6. Footer коммита: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.

## Какие скиллы под что
- UI/дизайн (chat.tsx декомпозиция, панели): `refero-design` / `impeccable` / `frontend-design` / `high-end-visual-design`.
- Рефактор/баги: `superpowers:systematic-debugging`, `superpowers:test-driven-development`, `superpowers:verification-before-completion`.
- Перед любой новой фичей: `superpowers:brainstorming`.
- Параллельные независимые выносы: `superpowers:dispatching-parallel-agents`.
- Прод-БД: `supabase` / `supabase-postgres-best-practices`.

## Безопасность (анти-RCE — святое)
- Импорт скилла НЕ исполняет код (только `skill_caps.analyze_skill` — чтение). Запуск гейтится.
- НЕ доверять полю `user` из тела — резолвить вызывающего из проверенного токена (см. мину #0 в REBUILD-BRIEF).
- Воркерам/головам — только безопасные read-тулзы; shell/run_code/файлы — owner-гейт + песочница + денилист.

## Две мины — помни (детали в REBUILD-BRIEF.md)
- ✅ #0 owner-spoof → RCE: **УЖЕ ЗАКРЫТА** (`resolve_caller`/`caller_is_owner` проброшен в RCE+money гейты + CORS/инъекция/SSRF, sec-коммиты 1-6). Осталось довынести в `authz.py`. НЕ переделывать.
- 🟡 #1 RU-платёж не подключён → PaymentProvider (YooKassa/CloudPayments) + вебхук + идемпотентность. ГЕЙТ перед ПУБЛИЧНЫМ выкатом — Damir ОТЛОЖИЛ, сейчас не блокер сборки (см. START-HERE).

## Что НЕ делать
- НЕ переписывать с нуля. НЕ big-bang. НЕ менять фичи во время выноса. НЕ копировать чужой лицензированный код (только идеи).
