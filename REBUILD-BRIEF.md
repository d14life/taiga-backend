# REBUILD-BRIEF.md — чистая пересборка Тайги (strangler-fig)

> ⚠️ СТАТУС-ПОПРАВКА (читай docs/MANIFEST.md — он перевешивает): (1) Мина #0 (resolve_caller/owner-spoof
> RCE/SSRF/инъекции) — **УЖЕ СДЕЛАНА** ✅ (sec-коммиты 1-6), не переделывать, осталось довынести в authz.py.
> (2) Мина #1 платёж + Фаза D масштаб — ОТЛОЖЕНЫ (гейт перед публичным выкатом, не сейчас).
> (3) Номера строк ниже — со СТАРОГО снапшота; реально server.py=15125, chat.tsx=8157. Ищи по ИМЕНИ
> (`def chat(self)`, `export function Chat()`, `def api_topup`), не по номеру строки.
>
> Это бриф для НОВОЙ чистой Claude-Code сессии. Читай вместе с: ARCHITECTURE-MAP.md, docs/design/FEATURE-LEDGER.md, CLAUDE.md.

## ⚠️ ДВЕ МИНЫ — РЕШИТЬ ДО ЛЮБОГО РЕФАКТОРА

### 🔴 #0 БЕЗОПАСНОСТЬ (блокер публичного запуска)
Подделываемый владелец: авторизация из непроверенного поля `user` в теле; `is_owner("default")=True`.
Любой `{"user":"default"}` → владелец → `dev=true` → shell/run_code (RCE) + чтение любого файла.
Спасает только привязка к 127.0.0.1. **НЕЛЬЗЯ проксировать наружу как есть.** Фикс: единый `resolve_caller()`
из проверенного токена/сессии на ВСЕХ owner-гейтах и dev-пути; не доверять полю `user`.

### 🔴 #1 БИЗНЕС (монетизация нерабочая)
NO RU PAYMENT PROCESSOR IS WIRED — monetization is non-functional. From the billing audit (critical): an exhaustive search for yookassa/yoomoney/cloudpayments/robokassa/tinkoff/stripe/telegram-pay/provider_token/invoice/btcpay/nowpayments found ZERO integration code (independently re-verified by grep against server.py — the only hit is a comment at L12284 'провайдер платежей (BTCPay/NOWPayments) после оплаты дёргает этот код'). api_topup (L12279) credits the wallet directly with NO charge step and, for non-owners, short-circuits to HTTP 503 'Оплата временно недоступна — подключаем платёжную систему' unless the owner sets test_topup=True. The only working ways to add balance today are (a) owner manually crediting via /api/billing action=topup, or (b) owner enabling the global test_topup flag (a single boolean that, if left on, lets ANY user self-credit for free). There is NO webhook/callback route (no /api/pay, /webhook, /callback) for a processor to confirm payment. Notably the only mentioned processors are crypto (BTCPay/NOWPayments) — no RU card processor is even scaffolded. Wiring a real RU processor (YooKassa/CloudPayments/Robokassa/Tinkoff or Telegram Payments) behind a new PaymentProvider interface (create_invoice + verify_webhook + idempotent credit) is greenfield work, not a refactor, and is the #1 business blocker for the rebuild.

## Философия (НЕ нарушать)
- **STRANGLER-FIG, НЕ переписывание с нуля.** Вынимаем по одному модулю из работающего монолита; каждый вынос
  проверяем зелёным; система НИКОГДА не сломана. Рабочий код = выстраданное знание, его не выбрасывают.
- **Always-green:** после каждого выноса — tsc=0 / ast.parse / смоук / поведение неизменно / монолит уменьшился.
- **Поведение байт-в-байт:** рефактор НЕ меняет фичи (см. FEATURE-INVENTORY как чек-лист). Сначала вынести, потом улучшать.
- **Один вынос = один зелёный коммит.** Маленькие шаги.

## Целевая архитектура (пакеты вместо монолита)
```
server.py (14.7k) → тонкий роутер + пакеты:
  providers.py · catalog.py · routing.py     — провайдеры, каталог, авто-роут + ОДИН budget-degrade
  modes/        (brain, council, compare, research, _subchat, fusion)
  agent_os/     (orchestrator, debate) — уже почти чистые модули
  mcp/          (transport, store, client, catalog, api)
  skills/       (caps, runtime, sandbox, store, github)
  context/      (memory, rag, grounding, inject)
  storage/      (db, migrate, crypto-vault, fts)
  billing.py    + require_balance() + RU-процессор за интерфейсом PaymentProvider
  studio_media/ (image, video, audio_tts, music3d, cinema) + общий MediaJob
  authz.py · guards.py · sandbox.py          — единый resolve_caller, лимиты, песочница
  automations/  (scheduler, routines, workflow) — свести 2-3 планировщика в один
  chat_handler.py — разобранная chat() (parse → assemble → resolve → stream-loop → brain → fallback → billing)
chat.tsx (7.8k) → <MessageItem> + <Composer> + commandHandlers + <PanelHost> + чат-стор (хуки-срезы)
```

## Порядок выноса (strangler — система зелёная на каждом шаге)
- [ ] **1. Confirmed-dead-code deletion (frontend window-rearrange.tsx, resizable-shell.tsx, lib/features.ts, lib/session.ts ~740 lines; backend OpenRouter remnants OR_MODELS/OR_CTX/OR_LIVE/_or_balance, RESALE_FORBIDDEN dead branch, _read_script, _VERDICT_REMARKS_RE, _DB_MIGRATED; quarantine beamOn dead branch & FunctionBuilderStub)**  — из `both monoliths` · сложность=easy · риск=very-low
    - Pure deletion of code proven to have zero callers. Shrinks the surface before any real lift and removes confusing 'live-looking' no-ops. Do FIRST so later extraction isn't carrying ghosts. Also fix stale docstrings (skill_caps 'wire later' lie, skills_run 'TODO-заглушка' lie).
- [ ] **2. agent_os/orchestrator.py + agent_os/debate.py (lift into a package, already pure modules with injected callbacks)**  — из `orchestrator.py + debate.py (already standalone)` · сложность=easy · риск=low
    - These are ALREADY decoupled (pure, callback-injected). Lowest-risk real extraction; establishes the dependency-injection pattern (HarnessDeps) that every later backend lift will reuse. self_manifest imports orchestrator.SKILLS — preserve that import.
- [ ] **3. skills/ package (caps.py, runtime.py, sandbox.py, store.py, github.py — unify the two GitHub import pipelines, dedup the two index.json readers and the duplicated constants)**  — из `skill_caps.py + skills_run.py + server.py import_skill_repo_from_url` · сложность=medium · риск=medium
    - Boundaries already clean (free-standing modules, DI-by-kwargs, no DB — per-user JSON + in-process E2B dict). Risk is the load-bearing caps schema mirrored by a TS twin (rename a key -> silent frontend break) and the 5-tier badge precedence that drives runtime routing. Add badge-precedence + import-path tests first; fix source_url plumbing so claude-authorship detection works.
- [ ] **4. mcp/ package (transport.py, store.py, client.py, catalog.py, api_mcp.py)**  — из `server.py L6643-6927 + the two REST handlers + agent-tool wiring` · сложность=medium · риск=medium
    - Contiguous block with only 4 external deps (_db_kv, _cookie_fernet, _is_public_url, _now_ts). Risk: move module-global caches into a singleton without changing threading; preserve the 'enabled is not False' tri-state and the DB 'mcp' key shape byte-for-byte. DURING the move, fix the SSRF-redirect hole by routing _mcp_rpc through _ssrf_safe_opener and collapse the 3 connector-creation blocks.
- [ ] **5. storage/ package (db.py connection+schema+JSON/kv accessors, migrate.py, crypto.py vault, search.py FTS) + per-store repos**  — из `server.py storage layer (6979-7698, 1290-1370, 2718-2749)` · сложность=medium · риск=high
    - Nearly everything funnels through 4 accessors, so the seam is clean — but the SAME shared connection + _DB_LOCK instance is grabbed by name from far-flung call sites for read-modify-write, the lazy migration runs order-sensitively inside connection-init (empty0 snapshot), and the single Fernet key + 'enc:v1:' prefix + plaintext fallback must stay byte-compatible or stored keys decrypt to ''. Replace the %-format table interpolation with a whitelist during the move; add a real schema-version row. Must land before billing/memory because they depend on the exact DB contract.
- [ ] **6. billing.py (config, wallet, pricing, meter/charge/refund, FX) + NEW require_balance() helper + provider_wallets.py split-out**  — из `server.py L8135-8321, 3378-3628, 12275-12410` · сложность=medium · риск=medium
    - Pure-billing core is already cohesive (light deps: _db_*, PRICE, is_owner, _now_ts). Risk is the ~30 copy-pasted balance gates with per-call-site owner-exemption inconsistencies — refactor to one require_balance(uid, need, owner) WITHOUT changing the (leaky) owner behavior, or deliberately fix it as a documented decision. Split provider-wallet display (get_balances/_nano_balance) into its own module to kill the 'balance' naming collision. Fix money-as-float -> integer-cents and the 200-entry ledger cap as a tracked migration. NOTE: the RU payment processor is GREENFIELD here (see payment_status), not a refactor.
- [ ] **7. context/ package (memory.py + tombstones + consolidation, rag.py, grounding.py, inject.py composer) behind a deps object**  — из `server.py L1117-2066, 7406-7769, 8334-8896` · сложность=medium · риск=medium
    - Pure functions with clean-ish boundaries. FIX FIRST the save_memory->FTS staleness bug (save_memory never calls _fts_index_memory, so fact search is stale until restart) — extracting without fixing perpetuates it. Must keep the exact DB contract (80-cap, '<uid>::tombstones' key, rag_chunks schema, cache invalidation) and the load-bearing fallbacks (smart->cosine, reconcile->append). Migrate all THREE injection call sites (chat, council, worker) to the shared build_grounding_addons() together or they drift. Depends on storage (step 5).
- [ ] **8. automations/ package (scheduler.py kept, routines.py lifted from server, workflow.py as a step-registry) + maintenance/ for memory consolidation**  — из `scheduler.py (clean) + server.py L14127-14480, 11282` · сложность=medium · риск=medium
    - Routines block is mostly self-contained (talks to server only via venice_complete/aux_model/taiga_identity/is_owner/user_dir/BASE). Risk: daemon thread start-ordering relies on injected module-globals (_RUNNER) — preserve or schedules silently no-op; _routine_due tz/same-day logic is fragile. DECIDE the dead event-trigger path here: either wire producers (emit run_done from orchestrate/jobs completion, chat_match from chat) or delete it — do not ship it still-dead. Unify the 3 duplicate weekday/next-run calculators onto scheduler.compute_next_run. Add a ReDoS guard before the on_chat_match path is ever made live.
- [ ] **9. providers.py (PROVIDERS registry, prefix routing, resolve_key/BYOK/pool, transport stream()+complete()) + catalog.py (unified CATALOG+RICH+PRICE+MODEL_KIND, atomic refresh) + routing.py (route_model/detect_task + ONE budget-degrade engine)**  — из `server.py L58-450, 2112-2778, 3100-3901, 3491-3800` · сложность=hard · риск=high
    - Clear seams (PROVIDERS dict, *_record builders, resolve_key) make providers/catalog medium-difficulty to start, BUT the global mutable catalog (PRICE.clear()/refill non-atomic, RICH rebind) is read by routing/billing/chat from request threads, and the transport's usage_out contract (__finished__/__degrade_note__ keys) is depended on byte-exactly. MERGE the 3 duplicate budget ladders (budget_degrade, cap_nano_max_tokens, inline max_spend) into one engine — highest drift risk in the system. Catalog/PRICE must be wired before this can route. Do behind characterization tests of routing decisions.
- [ ] **10. studio_media/ package (image, video, audio_tts, music3d, cinema, design_system) with a shared MediaJob submit/poll/reserve/charge/refund base**  — из `server.py L3283-3355, 9150-10288, 10867-11000` · сложность=hard · риск=high
    - Provider clients (nano_image, venice_image, aiml_*, free_tts, catalogs) lift EASILY (few server globals). The hard part is the HTTP handlers bound to Handler + billing globals, the 4-5x duplicated preamble, and the near-identical video/music SSE submit->poll->charge/refund machinery (two copies that drift). Reserve/refund correctness + SSE framing + NANO_VIDEO_FUNDED wallet-gating are subtle and only covered by test_video*. Depends on billing (step 6). Fix the wan-video-22-turbo default and add a real /api/voices endpoint during the move.
- [ ] **11. authz.py (resolve_caller -> uid, owner/role) + guards.py (rate limit, SEC caps, abuse, scrub_identity) + sandbox.py (run_code/shell, permission ladder, permit/question, SSRF)**  — из `server.py L2459-2948, 4574-4781, 5269-5810, 6971, 9734-9753` · сложность=medium · риск=high
    - Encryption, SSRF guard, and rate limiter lift cleanly (low risk). The HARD/HIGH-RISK piece is caller identity: uid = req.get('user','default') is threaded through 80+ call sites and is_owner returns True for 'default', so a single resolve_caller() that prefers a verified token (only api_users does this today) will break every existing tokenless client. Introduce it carefully (token, else loopback-only fallback). Move the owner-gated admin routes + dev/RCE gate onto it FIRST (small surface), add path-allowlist to read_file/list_dir and rlimits to tool_shell. This is a security hardening step as much as an extraction.
- [ ] **12. modes/ package (brain.py, council.py, compare.py, research.py, _subchat.py, fusion.py) + a shared SSE/preflight harness, one fuse() helper, one select_members() helper**  — из `server.py L6286-6438, 12619-13097` · сложность=hard · риск=high
    - Extract _subchat_* first (self-contained), then chat_research (already a method), then unify council/compare member-selection + the duplicated BEAM fusion. Cannot fully land Brain until the chat() streaming loop is decomposed (Brain is welded via nonlocals). No tests, SSE+billing-sensitive, and Damir's 'never show raw errors' rule means any silent-fallback regression degrades UX invisibly. Build behind a characterization test of the SSE event stream.
- [ ] **13. chat_handler.py — decompose chat() into request-parse, system-assembly, model-resolution, reusable stream-tool-loop with holdback, Brain orchestration, fallback policy, billing**  — из `server.py L13158-14119 (the ~965-line god-function)` · сложность=hard · риск=high
    - THE gravity well — extracted LAST because everything else must be lifted around it. 6-7 levels of nesting, ~10 model-variable reassignments, billing correctness on hand-tuned byte offsets, no-double-emit-on-fallback only enforced by len(buf)+len(hold) slicing, Brain nonlocals reassigned 800 lines apart. Decompose ONLY behind characterization tests of the full SSE event stream + billing because it is load-bearing money/protocol code with byte-identical-output guarantees.
- [ ] **14. Frontend chat.tsx decomposition: extract <MessageItem> + <Composer> + commandHandlers registry + <PanelHost>; then introduce a chat store/context and migrate the 165-189 state atoms slice-by-slice (useChatSessions, useSendPipeline w/ selectFundedChain helper, useComposerState, useFeatureFlags, useMemoryProfile, useAgentsSkills, useChatVoice). Keep use-taiga-chat.ts as the transport engine.**  — из `taiga-web/src/components/chat.tsx (Chat() L451-6977) + lib/use-taiga-chat.ts` · сложность=hard · риск=high
    - Mirror of the backend god-function. DO FIRST the mechanical wins (extract MessageItem from the 365-line messages.map IIFE = biggest perf+readability win; extract Composer; convert the 358-line executeCommand switch to a handler map; introduce one createPersistedStore to kill the 35x load/save + 18x CustomEvent boilerplate AND the 117 inline localStorage ops). THEN introduce a store and migrate state in slices. 189 interdependent atoms + suppressed exhaustive-deps + submitRef stale-closure workaround mean naive splitting introduces stale-state bugs. CRITICAL SECURITY: move the JS-skill runner (full-skills.ts:171 new Function in host origin) into the sandboxed iframe used by artifacts to close the RCE-in-origin hole. AGENTS.md warns Next.js is a modified fork — verify dynamic() before touching settings-panel lazy-load hub.

## Definition of Done (на каждый вынос)
- [ ] модуль вынесен, монолит уменьшился, импорты чистые (без `sys.modules[__name__]`-хаков)
- [ ] `npx tsc --noEmit`=0 (фронт) / `python3 -c "import ast;ast.parse(...)"` (бэк) — зелёно
- [ ] /app=200, смоук затронутых фич зелёный, поведение неизменно (FEATURE-INVENTORY не регрессит)
- [ ] отдельный коммит + push; после server.py — рестарт бэка

## После strangler — прод-закалка
Postgres+pgvector (из SQLite) · объектное хранилище для медиа · изолированные песочницы · евалы · наблюдаемость ·
единый Fernet→per-user ключи · SSRF-гард на MCP-редиректах · sandbox JS-скиллов в iframe.
