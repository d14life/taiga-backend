# Тайга ИИ — MANIFEST (анти-путаница система)

**Назначение:** жёсткие рельсы, чтобы сессия НЕ путалась и НЕ забывала (как было раньше).
Читается ПЕРВЫМ. Порядок ниже — не пропускать шаги.

---

## ЗАКОНЫ (RULE 0 — приоритет над всем, нарушать НЕЛЬЗЯ)

1. **НЕ ПРОПУСКАТЬ НИ ОДНОЙ просьбы Damir.** Каждый его запрос → отдельная задача (TaskCreate),
   ничего не теряется. В конце сверяться: всё ли из сказанного сделано.
2. **НЕ ГАДАТЬ (анти-галлюцинация).** Если не уверен на 100% — НЕ выдумывать. Сначала спросить
   память/граф (`gbrain think`, `/graphify query`, RAG), и если ответа нет — **задать вопрос Damir**.
   Лучше спросить, чем угадать неверно.
3. **Каждый факт — с источником.** Утверждение про код/фичу/дизайн → цитата файла/узла графа.
   Нет источника → честно сказать «не знаю / это пробел», как делает `gbrain think`.
4. **Пруфы перед «готово».** Никогда не заявлять «сделано» без верификации (скрин/tsc/смоук).
5. **Лучшие методы всегда:** `pick-skills` на каждую задачу → process-скилл (`brainstorming` для
   нового / `systematic-debugging` для багов / `test-driven-development`) → implementation-скиллы →
   `verification-before-completion`. Dynamic workflows + до 20 параллельных агентов на масштаб.
   **ponytail включён** (`/ponytail full`) — минимальный код, −22% токенов, без урезания
   валидации/безопасности. Использовать superpowers, MCP (gbrain MCP + другие), скачивание тулз
   и reference-репо (docs/REFERENCE-REPOS.md) — всё разрешено и нужно.
6. **Экономия моделей (opusplan-стиль):** Opus 4.8 — на планирование, архитектуру, сложную
   логику, ревью. Sonnet — на простую механику (бойлерплейт, переименования, мелкие правки,
   массовые однотипные выносы). Дорогую модель не жечь на лёгком. В Claude Code: команда
   `/opusplan` (Opus планирует → Sonnet исполняет); в Workflow — `model: 'sonnet'` на лёгкие
   агенты, Opus на судей/синтез. ponytail сверху режет лишний код.

Эти законы встроены в систему И являются правилом для самой сессии.

---

## ШАГ 0 — ПОДНЯТЬ ПАМЯТЬ (тройной стек) — делать ДО всего

Чтобы НЕ путаться и НЕ галлюцинировать — не держать в голове, а **спрашивать память**.
Три слоя, каждый под своё:

**A. graphify — граф КОДА** (что с чем связано в коде; 36 языков + доки + PDF + скрины)
```bash
uv tool install graphifyy && graphify install && /graphify .
/graphify query "как связаны чат-режимы и оркестратор?"
/graphify path "PaymentProvider" "scheduler"
```
Даёт graph.html / GRAPH_REPORT.md / graph.json. Репо: https://github.com/safishamsi/graphify

**B. gbrain — ПАМЯТЬ агента + синтез с цитатами** (анти-галлюцинация: отвечает с источниками
и честно помечает пробелы; Dream Cycle фоном ищет противоречия). MCP прямо в Claude Code.
```bash
gbrain init --pglite
gbrain import .                        # проиндексировать все 115 доков + дизайн
claude mcp add gbrain -- gbrain serve  # память как MCP в сессии
gbrain think "какой дизайн канон и почему?"   # ответ С ЦИТАТАМИ + пометки о пробелах
```
Репо: https://github.com/garrytan/gbrain (MIT, MCP, hybrid search, self-wiring граф)

**C. rag-anything — мультимодальный RAG по ДОКАМ/PDF/скринам** (текст+картинки+таблицы+формулы;
на LightRAG; идеально для 2 PDF-каталогов + 48 скринов + дизайнов).
```bash
pip install 'raganything[all]'
# process_document_complete по PDF-каталогам и докам → query mode="hybrid" vlm_enhanced=True
```
Репо: https://github.com/hkuds/rag-anything

**Правило: прежде чем что-то утверждать или строить — спроси нужный слой памяти.
Не уверен после памяти — спроси Damir. НИКОГДА не гадай.**

---

## ШАГ 1 — СТРОГИЙ ПОРЯДОК ЧТЕНИЯ (не пропускать)
1. `docs/MANIFEST.md` (этот файл) — рельсы + гардрейлы
2. `docs/NEW-SESSION-START.md` — точка входа + готовый промпт
3. `docs/PROJECT-BIBLE.md` — блюпринт: 182 фичи, решения, история
4. `docs/LOVABLE-HANDOFF.md` — build-spec: API + SSE + токены + 8 фаз
5. `REBUILD-BRIEF.md` — план + 2 мины
6. `docs/design/FEATURE-LEDGER.md` — ГЛАВНЫЙ реестр фич (17 июн, 139 фич, 13 агентов по 100ч-чату,
   [GAP]=восстановленные) + `GAPS-RECOVERED.md` + `FEATURE-INVENTORY.md` (184 буллета) +
   `server.py:self_manifest()` (живой список App Store). Поведение байт-в-байт. НЕ терять ни одной.
7. `ARCHITECTURE-MAP.md` + `BACKEND-API.md` — что где + эндпоинты
8. `docs/design/README.md` — какой дизайн канон, какие доноры
9. `docs/REFERENCE-REPOS.md` — все внешние репо (память, ponytail, opendesign) + как использовать
10. `docs/PARKED-FEATURES.md` — отложенные фичи (голос-режим, sandbox-файлы, skill-transform, MCP) — НЕ потерять
11. `docs/MEMORY-SETUP.md` — статус стека памяти + NVIDIA-разблок эмбеддингов
12. `docs/TEST-WORKFLOW.md` — A-to-Z поток: слой за слоем, авто-петля строй→тест→фикс→скрин→сверка, strangler-fig
13. `docs/REFERENCE-REPOS.md` — ~95 внешних репо-источников по категориям

## ШАГ 2 — ГАРДРЕЙЛЫ «НЕ ПУТАТЬСЯ» (локнутые истины — НИКОГДА не нарушать)
- **Дизайн-канон = `design-v3-current-shell-jun17.html`.** НЕ пересобирать с v0/v1/v2 — они ДОНОРЫ.
  Из доноров тянуть ТОЛЬКО когда Damir прямо укажет. usertest-jun15/ = старый вид, тоже донор.
- **ДОК УЖЕ ЕСТЬ в v3 — НЕ пересобирать.** macOS-док (`#dock` в shell.html, строки 238-326 + JS
  1360-1401): закреплённые апп-иконки + разделитель + открытые окна, видим по умолчанию (строка 1389
  `dock.classList.add('show')`), джигл-удаление, drag-to-pin. Дефолт-иконки: Картинки/Команда/Терминал/
  Модель. НЕ видно при открытии `shell.html` как file:// — рендерится ТОЛЬКО в запущенном аппе
  (фронт :3000 + бэк :8777). Задача — не строить, а проверить что он жив в рабочем аппе и допилить вид.
- **Не ломать shell.html** (macOS-окна + convo-dock) — он зафиксирован.
- **Стек:** фронт `taiga-web` (Next.js 16/React 19/Tailwind 4/@ai-sdk), бэк `server.py` (stdlib http.server, БЕЗ фреймворка).
- **Данные:** `~/.mostik-ai/` (db/taiga.db SQLite). Бэк :8777, фронт :3000, маршрут `/app`.
- **Security мины (перед публичным выкатом — обязательны):**
  - #0 `resolve_caller()` — НЕ доверять полю `user` из тела (подделка owner → RCE).
  - #1 RU-платёж не подключён → PaymentProvider (YooKassa/CloudPayments) + вебхук + идемпотентность.
- **Импорт скилла НЕ исполняет код**; запуск гейтится owner + песочница + денилист.
- **Планка:** без emoji (line/SVG иконки), без заглушек (`full-output-enforcement`), пруфы перед «готово».
- **Скиллы:** каждую задачу через `pick-skills` → process→implementation→verify. Не строить с нуля если скилл есть.
- **Не путать продукт:** это Тайга (AI-чат), НЕ Mostik (VPN-роутер). Разные проекты.
- **Источник истины = КОД репо** (taiga-backend + taiga-web + доки). Чат-история/транскрипты —
  только для ПОНИМАНИЯ замысла, НЕ истина. Расходятся чат и код → прав код. Память (gbrain/graphify)
  отвечает по докам/коду; чат грепать лишь для контекста.

## ШАГ 3 — КАРТА РЕСУРСОВ ПО ОБЛАСТЯМ (фича → где доки/скрины/флоу/код)
| Область | Доки | Визуал |
|---------|------|--------|
| Ядро чата + режимы (Мозг/Совет/Сравнение/Ресёрч/Дебаты) | PROJECT-BIBLE, FEATURE-INVENTORY | screenshots/10-14, flows brain/council/debate |
| Студия (картинки/видео/музыка/озвучка/3D) | LOVABLE-HANDOFF (API), BACKEND-API | screenshots/13, flows image-gen/video-gen/music-gen/tts-gen |
| Агенты / Agent-OS | ROADMAP-AGENT-OS, AGENTIC-OS-UNBLOCK | screenshots/30-39, flows agent-multitool/orchestrate/team-run |
| Навыки + код + MCP + skill-transform | SKILL-TRANSFORMER-PLAN, DEV-TOOLING | screenshots/45,50-52, flows mcp-connect-use/skill-import-run |
| Память / RAG / grounding | PROJECT-BIBLE (память) | screenshots/46, usertest panels 05-memory/06-smartrag/07-knowledge |
| Голос / непрерывный разговор | LOVABLE-HANDOFF (audio API) | usertest panels 20-voice, flows tts-gen |
| Песочница / sandbox | REBUILD-BRIEF (security), PHASE-A-C-HARDENING | usertest panels 14-workspace/15-terminal |
| Биллинг / кошелёк | REBUILD-BRIEF (мина #1) | usertest panels 11-jobs, screenshots billing |
| Аккаунты / безопасность | REBUILD-BRIEF (мина #0) | settings screenshots |
| Автоматизация / крон | scheduler в ARCHITECTURE-MAP | usertest panels 24-loops |
| Настройки / кастомизация | GRAND-PLAN-CUSTOMIZABILITY | screenshots/44, usertest 17-settings/18-hooks |

Дизайн: `docs/design/` (v0-v3 + usertest-jun15 + 32 панели + 16 feature-flows + 2 PDF + 48 скринов + галереи).
Юзер-кейсы для теста: `USER-CASES.md` + `docs/qa/`.

## ШАГ 4 — ПОТОК СБОРКИ (детерминированный, см. промпт в NEW-SESSION-START)
ПОНИМАНИЕ → ВОПРОСЫ → ПЛАН → ДОК(задача 1) → СБОРКА(pipeline фаз) → ФИКС-ПЕТЛЯ(loop-until-perfect) → ТЕСТ.
Каждая фаза: tsc=0, /app=200, смоук, скрин, сверка с v3+screenshots. Дальше ТОЛЬКО на зелёном.
Масштаб: ultracode, dynamic workflows, до 20 параллельных агентов, бесконечная петля до идеала.

---
**Если сессия в чём-то не уверена — НЕ гадать: спросить граф (`/graphify query`) или спросить Damir.**
