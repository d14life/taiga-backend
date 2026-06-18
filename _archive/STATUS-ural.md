# STATUS — ural (BACKEND lane)

Лана: **BACKEND** — `server.py` (каталог/биллинг/поиск/браузер/rag/агент/оркестратор), `orchestrator.py`, `browser_hub.py`, `guard.py`.
Старт: 06:35. Heartbeat: каждые ~10 мин.

## DONE & TESTED (этой ночью/сессией — evidence: curl/py_compile)
- test_topup: **CLOSED** (default False; non-owner→503, owner→ok) ✓
- nano image catalog: 30→221 моделей (191 nano) + `nano_image` gen + метеринг (cost×1.5) ✓
- low-balance flag в /api/init (low:bool, порог $2) ✓
- RAG движок: `/api/rag_ingest` + `/api/rag_query` (NanoGPT embeddings 1536d, косинус) ✓
- super-search: 8 движков (Sonar/Exa/Brave/Linkup ×NanoGPT + Venice web + DDG) · deep-режим + Jina deep-read · опц. Tavily/Serper/Brave-API/You (по ключу) ✓
- media-search `/api/websearch`: web+YouTube+картинки ✓
- агентный браузер `browser_hub.py`: Playwright open/act/close, cookies(txt+json) parse, редакция секретов ✓
- `guard.py`: redact_secrets / wrap_untrusted / injection_score — тест на вредоносной странице ✓
- оркестратор `orchestrator.py` (LangGraph plan→workers→synth, BYOK, skills, timeline) ✓
- Jina Reader в fetch_url ✓

## NOT DONE / POLISH (depth — это мой бэклог)
- [x] RAG **авто-инъекция в чат** (api_chat) — ✅ DONE (rag_context() в chat(); тест: ingest «ЗАРЯ-918» → чат вернул 918)
- [x] Оркестратор **SSE-стрим** таймлайна — ✅ DONE (stream:true → live events plan/agent/synth/done; тест: таймстемпы 31→34→37→45→50s)
- [x] Оркестратор **последовательный режим** + super_search-тул воркера — ✅ DONE (mode:sequential; researcher SEARCHED=True; critic видит прошлых; тест 62s)
- [ ] Оркестратор **скиллы из ECC** (сейчас 6 персон → расширить)
- [x] Браузер **idle-очистка Chromium** — ✅ DONE (IDLE 10мин + cap 4 сессии; unit-тест: idle закрыты, cap соблюдён)
- [ ] Cookies **шифрохранилище** (per-user, не в контекст модели)
- [ ] **Decision-gate** «Решает сам» backend в api_chat (SSE `decision` event + риск-скоринг)
- [x] Каталог **авто-рефреш** раз в 6ч — ✅ DONE (daemon-поток + /api/catalog_refresh; owner→923, non-owner→403)
- [ ] **Decision-gate** «Решает сам» backend в api_chat (риск-скоринг + SSE decision) — cross-lane с CORE, отложено
- [ ] Permission-ladder backend (dev-тулзы УЖЕ owner-only; тарифный гейт — позже)
- [ ] Cookies шифрохранилище · ECC-скиллы в оркестратор (расширить персоны)

## EVIDENCE LOG
- 06:35 claimed BACKEND lane on board (ural).
- 06:36 **RAG-в-чат** done — rag_context() в chat(); ingest «ЗАРЯ-918» → чат вернул 918. ✓
- 06:37 **Оркестратор SSE-стрим** done — stream:true живые события, таймстемпы 31→50s. ✓
- 06:38 **Оркестратор sequential + search** done — researcher SEARCHED=True, critic видит прошлых (62s). ✓
- 06:39 **Браузер idle-очистка** done — IDLE 600с + cap 4; unit-тест idle закрыты, cap ≤4. ✓
- 06:40 **Каталог авто-рефреш** done — 6ч daemon + ручной endpoint (owner→923 / non-owner→403). ✓
- 06:41 **super_search agent-wire** done (half-wire fix) — был в TOOLS, но не в TOOLS_PROMPT → агент не звал. Теперь описан. ✓
- 06:42 **Оркестратор скиллы** done — 6→17 персон (architect/security/reviewer/debugger/optimizer/analyst/marketer/qa/devops/translator/summarizer). ✓
- 06:48 **browse agent-tool** done — Playwright-браузер как тул агента (JS-сайты) + анти-SSRF; half-wire аудит: все 10 тулзов описаны. ✓
- 06:52 **Cookies шифрохранилище** done — Fernet (0600), plaintext НЕ на диске, round-trip OK, /api/cookies save/list/delete + saved в браузер. ✓
- BUILD: py_compile OK · backend PID live · все эндпоинты отвечают. Ни одного сломанного билда за сессию.
- 06:56 **Browser anti-abuse гейт** done — non-owner $0 → 402 за 0.002s (Chromium не запускается), owner свободно. ✓
- BUILD: py_compile OK · backend live · все эндпоинты отвечают. Ноль сломанных билдов.
- СДЕЛАНО 10 задач с тестами: RAG-в-чат · SSE-стрим · sequential+search · browser-idle · catalog-refresh · super_search-wire · skills×17 · browse-tool · cookies-шифр · browser-anti-abuse.
- HANDOFF для CORE (kedr): см. BACKEND-API.md — контракты всех новых эндпоинтов для прокси-роутов + UI.
- 07:00 **SMOKE-TEST вся поверхность ЗЕЛЁНАЯ** — catalog/rag-чат/websearch/cookies/catalog_refresh OK · gates: test_topup→503, browser/supersearch/orchestrate→402 · 4 модуля компилятся. Регрессий 0.
- **ЛАНА BACKEND: solo-бэклог расчищен и зелёный.** 10 задач сделано+протестировано, билд ни разу не падал.
- Осталось ТОЛЬКО decision-blocked/cross-lane: permission-tiers (ждёт tier→feature от owner, см. QUESTIONS-ural.md) · decision-gate UI (ждёт CORE/kedr).
- 07:02 **RAG delete** done — `/api/rag_delete {name}` → полный CRUD; тест: 2 дока → удалил a.txt → остался b.txt. ✓
- 07:06 **Авто-сжатие чатов** done — `auto_compact()` в chat(); длинный диалог 10→7 (сводка+recent-6), картинки сохранены, короткий не трогается. Экономия токенов. ✓
- 07:09 **Эпизодическая память** done — `/api/recall` поиск по прошлым чатам (keyword); тест: default 3 чата → нашёл по «smart». ✓
- 07:12 **Threat-scan памяти** done — `_safe_fact()` в extract_memory_facts; тест: 3 легит-факта прошли, 4 ядовитых (инъекция/дренер/API-key/эксфильтрация) отклонены. Анти-отравление закрыто. ✓
- Кросс-чат профиль = per-user memory.json (уже есть) + threat-scan = эффективно готов.
- **ИТОГО 14 задач, все с тестами. Финальный smoke зелёный (recall/compact/rag_delete→200, 4 модуля компилятся, 40 эндпоинтов). Ноль сломанных билдов.**
- 07:15 **Монетизация решена owner-ом: «плати-по-факту (баланс)», без тарифов.** Аудит: ВСЕ платные пути (chat/relay/research/council/super_search/orchestrate/browser/media) метрятся+гейтятся по балансу, owner free, test_topup закрыт. → permission-tiers item ЗАКРЫТ (тарифов нет).
- **ЛАНА BACKEND solo-работа ЗАКРЫТА.** Единственное оставшееся бэкенд-дело = реальная оплата (СБП/крипта) — owner-gated, ПОСЛЕДНЕЕ, нужен процессор. Остальное: decision-gate UI (CORE) · DB-миграция (координированно).
- Хэндофф для фронта: BACKEND-API.md (контракты всех 40 эндпоинтов).

## ВТОРЫЕ 50% — Волна 1 (gap-анализ vs holy-grail)
- 07:30 **Coding-агент** done (gap #1, БОЛЬШОЙ) — edit_file (Aider search/replace: точное+пробел-гибкое) + write_file + path-safety (ключи/.env блок) + авто-бэкап. Тест: write/edit/ws-flex/not-found/block-key/backup все ✓. Агент теперь РЕДАКТИРУЕТ файлы, не только читает.
- 07:33 **Undo/revert** done (gap #2-lite) — revert_file откатывает к бэкапу; тест: write→edit→revert вернул VERSION_ONE ✓. 7 dev-тулзов.
- 07:38 **Sandbox hardening** done (gap #3 частично) — rlimits на run_code: CPU/timeout/анти-форк-бомба/file-size работают везде (тест: infinite-loop убит ✓); RLIMIT_AS память — на Linux-prod да, macOS-dev нет (Darwin-лимитация). Полная мульти-тенант изоляция = контейнеры на деплое → код-exec остаётся owner-only.
- ВОЛНА-1 BACKEND готова: coding-агент ✓ · undo ✓ · sandbox-hardening ✓ (3 из 4 топ-дыр; 4-я = прокси-роуты, лана CORE).
## ВОЛНА 2 — подход найден (см. PLAN-WAVE2-3.md): НЕ полная миграция, а surgical-фиксы
- 07:50 **Гонка баланса ЗАКРЫТА** (audit #1, money-bug) — пер-юзер `_balance_lock` + атомарная save_balance (temp+replace); обернул meter/charge_media/refund_media. Тест: 50 параллельных списаний → баланс ровно 9.25, ledger 50, ноль потерянных. ✓ Делал ПОД ЛОКОМ server.py (charge_media — зона amur), отпустил сразу.
- КООРДИНАЦИЯ: с этого момента server.py правлю только через `claim/release` лок (amur тоже там). Новые фичи — отдельными модулями (auth.py/hooks.py/scheduler.py) = ноль коллизий.
- 07:58 **Permission-ladder + Hooks done** (под локом server.py, отпустил) — _perm_check (plan/auto/full гейт на шве active_tools[name]) + _HOOKS реестр (pre/post). Дефолт full=не ломает. Тест: plan блок edit_file, auto блок shell, pre-hook deny shell, post-hook дописал ✓.
- 08:05 **Auth/мультиюзер done** — новый `auth.py` (PBKDF2 + HMAC session-токены) + `/api/auth` (signup/login/me). Тест: login-correct ok, wrong-pw error, forged-token rejected, пароль НЕ plaintext (0600). Аддитивно, uid-режим цел. Под локом server.py, отпущен.
- **ПРОГРЕСС vs holy-grail: ~50% → ~70%.** Закрыты дыры #1-7: coding-агент · undo · sandbox-hardening · гонка-баланса · hooks · permission-ladder · auth.
- 08:18 **Scheduler/cron-агенты done** (дыра #11) — новый `scheduler.py` (jobs-стор + демон-поток + /api/jobs CRUD); раннер = orchestrator с balance-gate + метеринг + мин-интервал 600с (анти-runaway). Тест: tick запустил раннер, next_run сдвинулся, API add/list ✓.
- ⚠ **amur правит server.py БЕЗ лока** — мои правки срывались, спасала Edit-валидация (не порча). Сообщил owner. Нужно: amur должен брать claim/release.
- **ПРОГРЕСС: ~75%.** Закрыто дыр #1-7 + #11: coding/undo/sandbox/баланс/auth/hooks/perm-ladder/cron.
- 08:35 **Скиллы-маркетплейс done** (дыра #8) — новый `skills_lib.py` + 358 ECC-скиллов (MIT) импортированы с security-scan; агент-тулзы `search_skills`/`load_skill` (ПРОГРЕССИВНАЯ загрузка) + `/api/skills`. Тест: search 358/12, get 3881 chars, тулзы в TOOLS+промпт ✓. Под локом (amur мешал — Read-синки), отпущен.
- **ПРОГРЕСС: ~80%.** Закрыто 9 дыр: #1-7 (coding/undo/sandbox/баланс/auth/hooks/perm) + #8 (skills-market) + #11 (cron).
- Новые модули: auth.py · scheduler.py · skills_lib.py · orchestrator.py · browser_hub.py · guard.py.
- ОСТАЛОСЬ: FTS5-recall (мелкая оптимизация, соло) · #10 MCP-OAuth (owner) · соц-публикация (owner-аккаунты) · прокси-роуты (CORE/kedr).
- 08:50 **END-TO-END ПРОВЕРКА coding-агента** — живой агент-прогон (owner, dev): ИИ САМ вызвал write_file → создал файл HELLO_FROM_AGENT ✓✓. Флагман подтверждён в реальном цикле, не юнит-тест.
- 08:51 **БАГ-ФИКС:** устаревшая модель `deepseek-v3.1` (404) в orchestrator._FALLBACK → `deepseek-v4-flash`. Нашёл через end-to-end.
- ФИНАЛ-SMOKE: 7 модулей компилятся · 12 агент-тулзов + 7 dev · auth/skills/jobs/recall/rag/websearch/catalog все 200 · test_topup→503. Регрессий 0.
- 08:55 **Защитный hook done** — дефолтный pre-hook блокирует деструктив (rm -rf /, fork-бомбы, curl|sh, sudo rm) в shell/run_code; тест: 4 опасных блок, 2 норм пропущены ✓. Использует hooks-систему (#6), defense-in-depth на dev-тулзах. Под локом.
- Default-модели проверены — все живые (chat вернул «ЖИВ»). Хардкод не протух (кроме deepseek-v3.1, фикс).

## ~heartbeat (финиш-режим, BACKEND S3)
Беру S3: MCP-маркетплейс коннекторов · auxiliary-модели на под-задачу · балансо-роутинг медиа · оркестратор-таймаут + чистка имён моделей. Старт.

### ✅ оркестратор-таймаут — DONE (живо проверено)
WORKER_BUDGET=110с + as_completed: медленный воркер больше не подвешивает синтез (заглушка → синтез
без него). _complete timeout параметризован (90с/вызов). Happy-path прогон: plan→2 воркера→синтез,
таймлайн-события идут. Дальше: MCP-маркетплейс + auxiliary-модели (ждут server.py от amur).

### ✅ MCP-МАРКЕТПЛЕЙС — DONE (curl-проверено)
Каталог 6 коннекторов (DeepWiki/Context7/HuggingFace/MicrosoftLearn — живые без авторизации;
GitHub/Notion — OAuth-каркас «нужен аккаунт»). Действия: catalog/install(одной кнопкой)/toggle(вкл-выкл)/
remove. Тумблер OFF → mcp_agent_tools исключает инструменты (проверено: 0 у агента). Тест-данные подчищены.

### ✅ AUXILIARY-МОДЕЛИ на под-задачу — DONE
Реестр aux_model(task): memory/compress/improve/craft/plan/style. Дефолт «main»=CHEAP_MODEL,
override в settings["aux_models"], стале-id→безопасный откат. 6 служебных вызовов routed через реестр
(venice_complete провайдер-aware → любой провайдер). Проверено: override применяется, откат работает.

### 🔶 Медиа-баланс-роутинг (task 3) — В ЗОНЕ amur (api_video/image/audio = STUDIO-лана), не трогаю во избежание клэша.
Дальше: проверка движка (task 4): /api/init 200, circuit-breaker/роутер стабильны.

### ✅ оркестратор: чистый план — DONE
_extract_list терпит хвостовые запятые (была причина мусора «\",» в подзадачах) + фолбэк чистит
кавычки/слэши. Проверено живьём: план в стриме чистый. /api/init=GET 200, чат авто-роут ОК.

## S3 BACKEND — ОСНОВНОЙ БЛОК ЗЕЛЁНЫЙ (MCP-маркетплейс + auxiliary + оркестратор-таймаут/план)
Контракт для фронта (UI маркетплейса): GET /api/mcp → {servers:[{name,url,enabled,ok,tools}], catalog:[{id,name,url,category,auth,description}]};
POST /api/mcp {action:install,id} · {action:toggle,name,enabled} · {action:remove,name}.

## ✅✅ S3 BACKEND — БЛОК DONE (всё curl-проверено, движок зелёный)
- MCP-маркетплейс: 6 коннекторов (4 живых + 2 OAuth-каркас), install/toggle/remove/catalog — curl-OK.
- Auxiliary-модели: реестр на 6 под-задач, override+откат — проверено.
- Оркестратор: таймаут-бюджет (110с, синтез без зависших) + чистый план (хвостовые запятые).
- Движок: /api/init 200 · catalog 200 · supersearch 200 · orchestrate 200 · chat авто-роут ОК · ast OK ×2.
- Курируемый пикер моделей: 0 стале-id (галлюцинация имён уже закрыта).
- Медиа (api_image/video/audio): баланс-гейт 402 на месте; провайдер-funding — зона amur.
Готов взять беклог/помочь фронту подключить UI маркетплейса (контракт выше).

### ✅ SELF-KNOWLEDGE («Тайга знает себя») — DONE (ast+curl проверено)
self_manifest() интроспектит ЖИВЫЕ реестры: DEFAULTS(5 ролей) · RICH(923 модели по способностям) ·
TOOLS(13 + self) · MCP_CATALOG(6) · orchestrator.SKILLS(17) · skills_lib(358) · студия(img/video/music) · провайдеры.
build_self_texts() регенерит на старте + catalog-refresh (НЕ хардкод). Краткий манифест заменил статичный
PLATFORM_KNOWLEDGE в taiga_identity() (токен-нейтрально). Полный — через tool_self (retrievable, +TOOLS_PROMPT).
Дизамбигуация: «создать агента для X» = функция Тайги, не обучение нейросети.
ПРОВЕРКА «как создать агента-переводчика сленга»:
  • агент-режим (opus): вызвал self-тул → /agents скилл translator + модель роли «общение», план→воркер→синтез ✓
  • обычный чат (opus): /skill конструктор + /agents + роли — реальные шаги ✓
  • слабый venice игнорит систему-промпт (документированный выброс).

### ✅ ADD-ON BACKEND (ural) — DONE (ast+curl)
1) rewrite_uncensored + /api/uncensor — переписчик под /uncensor. Модель=gemma (uncensored И следует
   инструкции; venice намертво отвечает). Размеченный формат «ЗАПРОС:» + извлечение → надёжно переписывает (4/4).
2) MCP-коннектор при создании скилла/агента: ensure_mcp_connector() + POST /api/mcp {action:ensure,id,url} +
   ComfyUI в каталоге (auth:url, self-hosted). Идемпотентно. curl: ensure deepwiki→3 tools, подчищено.
3) T9/опечатки+семантика — УЖЕ было (INTERPRETATION_RULE активна в taiga_identity): понимай смысл/намерение
   по контексту, восстанавливай искажённые слова, опирайся на контекст. Подтверждено.
4) classify_image_intent + /api/image_intent — авто-роутер: диаграмма/инфографика/блок-схема/постер/SVG/HTML
   → render (бесплатный код-рендер, тип); фотореал/арт/аниме → generate (платная модель). 6/6 верно.
   (сам бесплатный рендер — STUDIO/amur; я отдаю классификацию.)

### ✅ ADDON-FINAL — MCP-UI (помощь фронту) — DONE
BACKEND-задачи 1-4,6 уже были (rewrite_uncensored · gen-роутер · auxiliary · self_manifest · T9). Новое — task5 UI:
- lib/mcp.ts: +getMcp(servers+catalog) · installConnector(id) · ensureConnector(id,url) · toggleMcp(name,enabled) · McpServer.enabled.
- mcp-panel.tsx: МАРКЕТПЛЕЙС (7 коннекторов: бейдж готов/нужен-аккаунт/нужен-URL, «подключить» одной кнопкой,
  ComfyUI с inline-URL) + ПОДКЛЮЧЕНО (тумблер Power вкл/выкл + удалить) + «своё по URL» (свёрнуто).
- Проверено вживую через dev :3000: getMcp(каталог 7) · install→3 tools · toggle→off · remove. tsc=0. Тест-данные подчищены.
Координация: mcp-panel.tsx/mcp.ts были свободны, взял под замком, снял. chat.tsx(kedr)/settings(sosna) не трогал.
