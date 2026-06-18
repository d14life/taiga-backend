# Тайга ИИ — СТАРТ НОВОЙ СЕССИИ (единая точка входа)

Это «чертёж дома». Один файл, из которого новая Claude Code сессия видит ВСЁ:
дизайн (с доком), скрины, историю чатов, доки фич, юзер-кейсы, репо, скиллы,
dynamic workflows, параллельных агентов и бесконечную петлю сборки.

---

## 0. ПРОМПТ ДЛЯ ВСТАВКИ (копировать целиком в новую сессию)

```
ultracode

Проект Тайга ИИ — приватный uncensored мульти-модельный AI-чат для RU/CIS. Модель Opus 4.8,
dynamic workflows, до 20 агентов, бесконечная петля до идеала. Без emoji, без заглушек, всё прод-грейд.

ЗАКОНЫ (приоритет над всем): 1) НЕ пропускать ни одной просьбы Damir — каждую в задачу.
2) НЕ гадать — не уверен → спроси память (gbrain/graphify/RAG), нет ответа → спроси Damir.
3) Каждый факт с цитатой источника, иначе честно «не знаю». 4) Пруфы перед «готово».

ШАГ 0: прочитай docs/MANIFEST.md (законы + рельсы) и подними ПАМЯТЬ КАК MCP В АППЕ
(работаем в приложении, не терминале — поэтому MCP/плагины, агент зовёт их сам):
  export NV=$(grep ^NVIDIA_API_KEY= ~/.reel-intelligence.env|cut -d= -f2-)
  A. graphify (граф кода, MCP): uv tool install "graphifyy[mcp]" && graphify update .
     && claude mcp add graphify -- graphify-mcp "$PWD/graphify-out/graph.json"   # ✓ авто-тулзы в аппе
  B. gbrain (память+цитаты, MCP): gbrain init --pglite --embedding-model openai:baai/bge-m3 --embedding-dimensions 1024
     (env OPENAI_BASE_URL=https://integrate.api.nvidia.com/v1 OPENAI_API_KEY=$NV) && gbrain import .
     && claude mcp add gbrain --env OPENAI_BASE_URL=https://integrate.api.nvidia.com/v1 --env OPENAI_API_KEY=$NV -- gbrain serve
  C. ponytail (экономия токенов, плагин): в аппе /plugin marketplace add DietrichGebert/ponytail затем /ponytail full
  D. rag-anything (опц., CLI для тяжёлого PDF-парса): pip install 'raganything[all]' — НЕ app-native, gbrain закрывает доки в аппе.
  Эмбеддинги через NVIDIA (bge-m3) работают из РФ. Дальше вместо грепанья/догадок — спрашивай память (gbrain/graphify MCP).
  Читай docs/REFERENCE-REPOS.md + docs/PARKED-FEATURES.md. Потом docs/NEW-SESSION-START.md.

ЦЕЛЬ: построить рабочее веб-приложение A-to-Z по всему наработанному (100+ часов), НЕ с нуля.
Ничего из 182 фич не потерять.

РЕПО (склонируй оба):
- backend + ВСЕ доки: https://github.com/d14life/taiga-backend
- frontend Next.js 16/React 19/Tailwind 4: https://github.com/d14life/taiga-web

ЧИТАЙ ПЕРЕД КОДОМ: START-HERE.md, docs/PROJECT-BIBLE.md, docs/LOVABLE-HANDOFF.md,
REBUILD-BRIEF.md, FEATURE-INVENTORY.md, ARCHITECTURE-MAP.md, BACKEND-API.md,
TAIGA-REQUIREMENTS.md, GRAND-PLAN-V3.md, USER-CASES.md.

ДИЗАЙН — всё в docs/design/ (см. docs/design/README.md):
- design-v3-current-shell-jun17.html — ТЕКУЩИЙ КАНОН (macOS-окна). Строим по нему, НЕ ломать.
- usertest-jun15/ — старый дизайн с юзер-теста (32 экрана + PDF). Доминантный донор, Damir любит этот вид.
- design-v2/v1/v0 — доноры. design-icons-liquid-glass.html + assets/ (лого). Скрины: docs/screenshots/ (48), docs/qa/.
- ДОК: в v3 добавить macOS-док снизу — ряд иконок-приложений (запуск разделов/окон), как было раньше.
  Переносить из доноров ТОЛЬКО когда я укажу.

СКИЛЛЫ: прогоняй КАЖДУЮ задачу через мета-скилл pick-skills (discover→route→chain
process→implementation→verify). Дизайн = brainstorming + high-end-visual-design + impeccable +
refero-design + react/next-best-practices. Баги = systematic-debugging. Большая независимая
работа = dispatching-parallel-agents / Workflow-тулза. Финал каждой задачи = verification-before-completion.

ПОРЯДОК:
1. ПОНИМАНИЕ — fan-out читателей по 11 подсистемам, синтез в карту.
2. ВОПРОСЫ — ВСЕ открытые решения в ОДИН список, задать мне ДО кода.
3. ПЛАН — дизайн-панель 2-3 подхода, судьи, синтез.
4. ПЕРВАЯ ЗАДАЧА — добавить macOS-док в v3 (иконки-приложения снизу, как раньше). Сверить с usertest-jun15.
5. СБОРКА — pipeline фаз LOVABLE-HANDOFF: Shell+Chat→Modes→Studio→Agent→Memory→Code→Settings→Polish.
   Воркеры строят, верификаторы проверяют КАЖДУЮ фичу: tsc --noEmit=0, /app=200, смоук, скриншот, сверка с v3+screenshots.
6. ФИКС-ПЕТЛЯ (loop-until-perfect, по каждой фазе и в конце): a) верификация; b) критик ищет
   расхождения визуала/мёртвые фичи/регрессии против FEATURE-INVENTORY/баги/заглушки; c) найдено —
   fan-out фикс-агентов → возврат к (a); два чистых прогона = принято; d) финальный критик «что упущено» → ещё круг.
   Дальше ТОЛЬКО на зелёном.
7. ТЕСТ — полный прогон USER-CASES.md, сверка со скринами, петля до perfect.

ЖЕЛЕЗНО: поведение фич байт-в-байт по FEATURE-INVENTORY. Security: мина #0 (resolve_caller — не доверять
полю user из тела), мина #1 (RU-платёж YooKassa/CloudPayments + вебхук + идемпотентность) — обязательны
перед публичным выкатом. После правок server.py: ast.parse. Footer коммита:
Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>.

Начни с ПОНИМАНИЯ.
```

---

## 1. РЕПОЗИТОРИИ
- backend + все доки + дизайн: https://github.com/d14life/taiga-backend
- frontend: https://github.com/d14life/taiga-web
- Reference-репо, которые изучали (LibreChat, Hermes, Claude Code, RAG-Anything, Open-Design, Ralph и др.):
  полный список и чему научились — в `docs/PROJECT-BIBLE.md`.

## 2. ГЛАВНЫЕ ДОКИ
- `START-HERE.md` — точка входа
- `docs/PROJECT-BIBLE.md` — блюпринт: 182 фичи, все решения, история чатов (сжато), reference-репо
- `docs/LOVABLE-HANDOFF.md` — build-spec: весь API-контракт, SSE-формат, дизайн-токены, 8 фаз
- `REBUILD-BRIEF.md` — план strangler-fig + 2 мины (RCE, RU-платёж)
- `ARCHITECTURE-MAP.md` (59 KB), `BACKEND-API.md` — что где, все эндпоинты
- `TAIGA-REQUIREMENTS.md`, `GRAND-PLAN-V3.md` — требования и план

## 3. ФИЧИ (не потерять — 182 шт)
- `FEATURE-INVENTORY.md` — чек-лист, поведение байт-в-байт
- `GAP-AUDIT.md` (94 KB) — гэпы и недоделки

## 4. ТЕСТЫ / ЮЗЕР-КЕЙСЫ
- `USER-CASES.md` — все юзер-сценарии для теста
- `QA-PLAN.md` (157 KB), `TEST-CHECKLIST.md`
- `docs/qa/` — интерактивные галереи (EVIDENCE, USER-CASES, TEST-MATRIX, SYSTEM-MAP, NAV-IA, BEFORE-AFTER)

## 5. ДИЗАЙН (вся история + старый юзер-тест)
- `docs/design/README.md` — карта версий
- `design-v3-current-shell-jun17.html` — ТЕКУЩИЙ КАНОН (macOS-окна + convo-dock). НЕ ломать.
- `design-v2-redesign-jun16.html` / `design-v1-539kb-jun13-resize-windows.html` / `design-v0-original-react-chat-jun12.tsx.txt` — доноры
- `usertest-jun15/` — СТАРЫЙ дизайн юзер-теста: 32 экрана (01-mcp…32-designcanvas) + 2 PDF-каталога + галереи. Доминантный донор.
- `design-icons-liquid-glass.html` + `assets/` (4 лого)
- `docs/screenshots/` — 48 скринов всех экранов (эталоны для сверки)
- **ДОК (требование Damir):** в v3 добавить macOS-док снизу — ряд иконок-приложений для запуска разделов/окон, как было в раннем дизайне. Референс вида — usertest-jun15.

## 6. ИСТОРИЯ ЧАТОВ — контекст для ПОНИМАНИЯ, НЕ источник истины
- Чат-история нужна, чтобы ПОНЯТЬ замысел/решения/почему. Но **ИСТОЧНИК ИСТИНЫ ДЛЯ КОДА =
  репо** (taiga-backend + taiga-web + доки). Если чат и код расходятся — прав КОД, не чат.
- Сжатая история (всё важное) — внутри `docs/PROJECT-BIBLE.md` (таймлайн + развилки).
- Сырые транскрипты (локально, ~460 MB, в репо не кладём): `/Users/damir12/.claude/projects/-Users-damir12/*.jsonl`
  (`2ab72971-…jsonl` = текущая длинная сессия). Грепать для контекста, НЕ копировать как истину.

## 7. СКИЛЛЫ — всегда использовать (мета-подход)
- **Мета-скилл `pick-skills`** — прогоняй ЧЕРЕЗ НЕГО каждую задачу: discover → route → chain
  (process-скилл → implementation-скиллы → verify). `find-skills` — поиск по 89 установленным скиллам.
- **Дизайн/фронт:** `brainstorming` (новое) → `high-end-visual-design` + `impeccable` + `ui-ux-pro-max`
  + (`design-taste-frontend` лендинг / `refero-design` продукт) → `emil-design-eng`/`framer-motion` →
  `shadcn` → `react-best-practices` + `next-best-practices`.
- **Баги:** `systematic-debugging` → `test-driven-development` → verify.
- **Рефактор/прод-грейд:** `dispatching-parallel-agents` или Workflow (агент на часть) → quality-скиллы → verify.
- **AI-фичи:** `ai-sdk` + `ai-gateway` + `chat-sdk`. **Next.js:** `nextjs` + `next-best-practices`.
- **БД:** `supabase` + `supabase-postgres-best-practices`. **Деплой:** `deployments-cicd` + `vercel-cli`.
- **Финал любой задачи:** `verification-before-completion` — проверка в браузере/preview, пруфы, никогда «готово» без верификации.
- **Планка всегда:** без emoji (только line/SVG иконки), без плейсхолдеров (`full-output-enforcement`), пруфы.

## 8. DYNAMIC WORKFLOWS + ПАРАЛЛЕЛЬНЫЕ АГЕНТЫ (как масштабировать)
- `ultracode` в начале = многоагентные воркфлоу по умолчанию.
- **Workflow-тулза:** детерминированная оркестрация — `pipeline()` (по умолчанию, без барьеров),
  `parallel()` (барьер, когда нужны все результаты), `agent()` со `schema` для структурного вывода.
- Паттерны: fan-out читателей → синтез; дизайн-панель (N подходов → судьи → синтез);
  find→adversarial-verify; loop-until-dry (петля пока N чистых прогонов подряд); completeness-critic.
- **Параллельные агенты** (`dispatching-parallel-agents`): один агент на независимую подсистему/проблему,
  без общего состояния. До 20 агентов.
- **Бесконечная петля:** каждая фаза и финал гоняются через ФИКС-ПЕТЛЮ (см. промпт п.6) пока не идеально.

## 9. БЕЗОПАСНОСТЬ (перед публичным выкатом — обязательно)
- Мина #0: `resolve_caller()` — НЕ доверять полю `user` из тела запроса (иначе подделка owner → RCE).
- Мина #1: RU-платёж не подключён → монетизация мертва. PaymentProvider (YooKassa/CloudPayments) +
  вебхук + идемпотентное зачисление.
- Импорт скилла НЕ исполняет код; запуск гейтится owner-ом + песочница + денилист.

---

Это полный чертёж. Новая сессия: вставь промпт из п.0, дальше всё отсюда.
