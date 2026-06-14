# PHASE-A-C-HARDENING.md — закалка Тайги до «как должно быть»

> Из GAP-AUDIT (аудит-веер №2). Порядок: 2 МИНЫ → быстрые победы → критичное → высокое → остальное.
> Отмечай [x] по мере фикса. Критичные правки — адверсариально проверять веером ревью-агентов ДО коммита.

## 🔴 ФАЗА A — ДВЕ МИНЫ (до публичного запуска / для денег)

### #0 Безопасность — подделываемый owner → аноним-RCE
- [ ] Единый `resolve_caller(self) -> (uid, is_owner)` ТОЛЬКО из проверенного подписанного токена (не из поля `user` тела/квери).
- [ ] Прогнать ВСЕ owner-гейты и dev/RCE-путь через него; убрать body-derived is_owner.
- [ ] Гейтнуть `run_code_file`/`tool_shell`/`tool_read_file` за проверенным owner + скоуп пути (read сейчас без allowlist).
- [ ] Скилл-JS гонять в Web Worker (Blob) или cross-origin sandboxed iframe, НЕ в host-origin через new Function().
- [ ] ⚠️ ДО фикса — НЕ проксировать бэк наружу (спасает только bind 127.0.0.1).

### #1 Бизнес — RU-платёж не подключён (решение владельца: какой процессор)
- [ ] Выбрать процессор (YooKassa / CloudPayments / Robokassa / Tinkoff / Telegram Pay / крипто BTCPay-NOWPayments). ← РЕШЕНИЕ DAMIR
- [ ] Интерфейс `PaymentProvider`: create_invoice → редирект на оплату → вебхук с ПОДПИСЬЮ → идемпотентное зачисление.
- [ ] Таблица идемпотентности (op_type, external_id); обернуть topup/charge/refund.
- [ ] Удалить глобальный `test_topup` и `billing.enabled`-байпас (кран бесплатных денег).

## ⚡ Быстрые победы (часы, делать сразу после/параллельно минам)
- [ ] Meter the served model (stream_model) instead of the originally-selected model in the non-brain billing branch — a one-line correctness fix on real money (Chat core).
- [ ] Wire the MCP transport through the already-existing _ssrf_safe_opener().open(...) in _mcp_rpc and _mcp_ensure — closes redirect-based metadata/loopback SSRF with a two-call change (MCP).
- [ ] Delete test_topup as a global gate and remove the billing.enabled global free-bypass — small edits that close the open-mint faucet and revenue kill-switch (Billing).
- [ ] Store a target weekday for weekly routines (default = createdTs weekday) instead of hardcoding Mondays — small fix to a misleading user-facing trigger (Routines).
- [ ] Fire _routine_fire_event internally next to each emit('done') and on each chat message, or badge the two event triggers 'скоро' in the UI — small change that ends the orphan-promise (Routines).
- [ ] Add a Content-Length cap in _body() — a few lines that immediately blunt the base64 OOM/DoS on media endpoints (Studio/Infra).
- [ ] Add unauthenticated /healthz and /readyz endpoints and a SIGTERM handler calling srv.shutdown() + final WAL checkpoint — small, unblocks LB health-gating and zero-downtime deploys (Infra).
- [ ] Pick the Council synthesizer by bench (max over good) instead of good[0] (first-to-return) — one-line change that makes 'best advisor synthesizes' actually true (Orchestration).
- [ ] Surface usage_out['__degrade_note__'] into meta.note after the stream so NanoGPT-path depth/token degradation becomes visible to the user — it is already computed, just never read (Chat core).
- [ ] Make price_of fail closed with a max-price floor + log for off-catalog/null-priced models — small guard that stops silent $0 billing (Billing).
- [ ] Route Compare members through _subchat_tool_loop (history+RAG) instead of bare 1200-token venice_complete so the side-by-side comparison reflects real model quality (Orchestration).

## 🟠 ФАЗА C — критичное (безопасность/деньги/данные)
- [ ] (M (1-2 days; the helper is small, the sweep is mechanical but wide)) Add a single resolve_caller(self) that derives uid (and owner flag) ONLY from a verified signed token (auth.uid_from_token / cookie); replace every c.get('user','default') (~75 sites) and stop treating literal 'default' as owner on any network-exposed bind.
- [ ] (M) Gate native run_code_file/tool_shell behind the verified-owner flag from resolve_caller and remove the body-derived is_owner path; jail tool_read_file/list_dir/write_file/edit_file to an allowlisted realpath root and hard-deny .auth_secret/.cookie_key/dotfiles.
- [ ] (M) Run untrusted skill JS in a Web Worker (Blob URL, no DOM) or cross-origin sandboxed iframe (sandbox=allow-scripts, null origin) instead of new Function() on the main page thread; until shipped, show JS skills as code-for-review only, never auto-run.
- [ ] (L (3-5 days incl. webhook, reconciliation, sandbox testing)) Integrate a real PaymentProvider (YooKassa/CloudPayments/BTCPay/NOWPayments): create_invoice → redirect to pay → credit wallet ONLY from a /api/pay/webhook that verifies the processor HMAC/RSA signature with hmac.compare_digest and validates amount+currency+status.
- [ ] (M) Add an idempotency table keyed by (op_type, external_id) and wrap topup/meter/charge_media/refund_media so a replayed webhook or double-clicked/retried request applies exactly once; key media reserve/refund by run_id.
- [ ] (S) Delete test_topup as a global gate; if a test path is needed restrict crediting to is_owner(self.caller) crediting only self, labelled 'test' in the ledger. Remove the billing.enabled global free-bypass in favor of per-account/maintenance gating that still meters.
- [ ] (M) Automated, tested, off-host backups of taiga.db (VACUUM INTO/.backup to object storage on a cron now; Postgres PITR after migration) plus a written, tested restore runbook with RPO/RTO.
- [ ] (M) Add a global Content-Length cap in _body() and stop returning media as base64-in-JSON: write generated image/audio/video to object storage (or local served files) and return URLs; stream the cinema-export MP4 instead of base64-embedding it.

## 🟡 ФАЗА C — высокое (корректность/качество)
- [ ] (L) Replace the single shared Fernet key with per-user envelope encryption (HKDF(master,uid) or versioned keyed envelope), move the master into OS keychain/KMS (not a plaintext sibling file), add rotation, and encrypt chats.data + memory.data at rest.
- [ ] (S) In the non-brain branch, meter against stream_model (the model that actually served after silent fallback), not the originally-selected model; pass the served model id into the cost event.
- [ ] (M) Make price_of fail closed: an off-catalog/null-priced model must refuse the call or apply a conservative max-price floor and log it, instead of metering at exactly $0; prefer provider-reported usage over the est_tokens len//4 heuristic (use ~3 chars/token for Cyrillic).
- [ ] (M) Reserve estimated max cost atomically before doing the work (single lock spanning estimate→reserve), block when balance < estimated need everywhere (not just <=0), reconcile to actual on completion, and wrap BOTH topup paths in _balance_lock.
- [ ] (XL) Move off the stdlib ThreadingHTTPServer to ASGI (Starlette/FastAPI) under uvicorn/gunicorn with multiple worker processes behind nginx/Caddy for TLS; migrate the single mutexed SQLite connection to managed Postgres with a connection pool (keep the _db() seam).
- [ ] (S) Switch _mcp_rpc and _mcp_ensure from urllib.request.urlopen to _ssrf_safe_opener().open(...), and re-run _is_public_url on each RPC call (pinning the validated IP to close the DNS-rebind TOCTOU).
- [ ] (M) Call _fts_index_memory(conn, uid) from save_memory (under lock, fail-safe), index each fact as its own FTS row (not one __memory__ blob), and add memory scanning to the _like_search fallback.
- [ ] (M) Embed grounding source chunks and memory facts and run the existing dense+keyword+RRF hybrid over them; reuse _rag_chunks for grounding chunking; default-enable LLM rerank for small candidate sets (or paid tiers).
- [ ] (M) Add a media_jobs table (id, uid, kind, provider, request_id, status, reserved, created) written at submit and updated on terminal states, a GET /api/media-job?id= re-attach endpoint, and a startup reconciler that re-polls or refunds orphaned reserved jobs.
- [ ] (M) Wire the orchestrator's existing _orchestrate_verifier result into control flow: on verified=False (or empty/error/timeout), re-dispatch just that subtask with the failure reason appended (retry cap ~2) via add_conditional_edges; flag still-failing subtasks in the synth prompt instead of presenting them as clean.
- [ ] (S) Add unauthenticated /healthz (process up) and /readyz (DB SELECT 1 + key files present) endpoints, a SIGTERM handler that calls srv.shutdown(), drains in-flight requests/SSE within a deadline, and runs a final WAL checkpoint before exit.
- [ ] (S) Fire event routines internally: call _routine_fire_event(uid,'run_done',...) next to each emit('done') at agent run-completion and _routine_fire_event(uid,'chat_match',text) on each chat message (try/except, off-thread). Until wired, badge on_run_done/on_chat_match 'скоро' in the UI.
- [ ] (L) Implement real answer-level fusion: annotate the panel with cross-model agreement ('N of M models state X'), use a neutral synthesizer not in the panel (or strip self-attribution), pick the synthesizer by bench not by first-to-return, and replace 16k char-truncation with per-answer budgeting so no member is dropped.
- [ ] (L) Externalize coordination state (rate limits, agent permits/answers, per-uid balance lock, caches) to Redis and make app nodes stateless so multiple nodes can run behind a load balancer.
- [ ] (L) Implement the MCP OAuth client: parse WWW-Authenticate on 401, do oauth-protected-resource/authorization-server discovery, RFC 7591 dynamic registration, authorization-code+PKCE via /api/mcp/oauth/start+callback, store+refresh tokens encrypted, retry the RPC; route all discovery fetches through _ssrf_safe_opener.
- [ ] (L) Extract a memoized MessageRow (React.memo by id) and wrap the message list in react-virtuoso; lazy-import (React.lazy) the ~40 heavy panels so they code-split; lift the inline render-IIFE logic out.
- [ ] (XL) Introduce a state store (Zustand or 3-4 Context+useReducer slices) for cross-cutting state (settings/modes/panels/billing), delete the prop-drilling and the 37 'xRef.current = x' stale-closure mirrors, and add a usePersistentState(key,default) hook to collapse the ~100 lines of duplicated localStorage effects.
- [ ] (M) Wrap the app root, the extracted MessageList, and each lazy panel in the existing <ErrorBoundary>; add testing-library coverage for use-taiga-chat.ts (SSE/failover/coalescer) and the extracted components before/while decomposing.

## 🟢 ФАЗА C — остальное
- [ ] (med/M) Wrap all balance mutations (incl. both topups) in _balance_lock and convert to atomic SQL UPDATE...WHERE balance>=?; add read-modify-write locking or an optimistic version column for settings/memory/notes blob overwrites.
- [ ] (med/M) Parallelize the Brain multi-expert loop with the same ThreadPoolExecutor pattern Council uses, add a query difficulty short-circuit to Council/Beam (answer with 1 model when not hard) with a per-request member/token budget, and route Compare members through _subchat_tool_loop (history+RAG) instead of bare 1200-token venice_complete.
- [ ] (med/M) Replace debate's exact-phrase/word-set convergence with a cheap LLM convergence judge over ALL prior rounds; store a target weekday for weekly routines (default = createdTs weekday) instead of hardcoding Mondays; meter routine LLM runs before opening MOSTIK_ROUTINES_ALL; add a last-tick heartbeat to both scheduler loops and assert freshness in /sprint.
- [ ] (med/M) Add ingest/update timestamps per chunk and a recency-decay multiplier to fused scores (and overlap*recency in memory_block); batch the embedding pipeline into one call with a local fallback and query-embedding cache; emit an updated meta/'model_switched' event and surface __degrade_note__ when the served model changes mid-stream.
- [ ] (med/M) Replace the substring/prefix provider hacks with an explicit Provider registry (base_url, auth, id_transform, token_param, sub_url, capability flags); make provider_name return None on unknown prefix instead of defaulting to venice; add MCP resources/read + prompts/get + nextCursor pagination + protocol-version adoption.
- [ ] (med/S) Wrap synchronous image/TTS/3D and all media submit calls in a 2-3 attempt retry with backoff on 5xx/timeout/IncompleteRead (keep immediate-fail on 4xx), and charge cinema-export per scene/second of compute or cap concurrent ffmpeg jobs with a semaphore.

## Прим.: AI-фичи «по-настоящему» (вскрылись в GAP)
- [ ] Фьюжн Совета: настоящий дедуп+голосование/консенсус, а не один промпт над склейкой.
- [ ] Верификация агента: реальная проверка, не декоративная эвристика 'true'∈текст.
- [ ] Событийные рутины (on_run_done/on_chat_match): подключить продюсера ИЛИ убрать из UI (сейчас мёртвы).
- [ ] RAG: добавить реранк (сейчас близко к top-k); save_memory индексить FTS на запись.
