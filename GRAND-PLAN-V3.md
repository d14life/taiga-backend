# GRAND PLAN V3 — push to production-grade (batches 9→onward)
Continuation of GRAND-PLAN-V2 (batches 0-8 DONE). Founder said "do all 26 batches".
HONEST SCOPE NOTE: 3 independent scrapers verified the 40+ planning docs are ~95% STALE — almost everything they flag as "missing" is already built. The genuine, no-external-dep remaining work is ~17 parity gaps + real production-hardening (tests/perf/a11y/i18n/mobile/security/observability) = ~13 batches of REAL value. I will NOT pad with filler to hit a round 26 — for a flagship app, busywork lowers quality. If genuine work surfaces beyond B21 I extend; otherwise I stop and report.

## RULES (same as V2)
Batches of ≤4 disjoint-file lanes. ≤1 server.py lane + ≤1 chat.tsx lane per batch (god-file contention). Agents build+verify (tsc/ast) but DON'T commit; coordinator merges/verifies/commits each batch. Commit LOCAL only (never push). Self-reschedule until done. Live: backend :8777, dev :3000.

## STATUS (source of truth for resume)
- [x] BATCH 9  — RAG retrieval-quality (S) + pre-send cost (C) + schema param-form + server-persona editor — DONE (FE 7c98c79 / parent 06eb7a7)
- [x] BATCH 10 — workflow-runner+negative_prompt (S) + workflows-wire + memory-budget sliders + brand-click catalog — DONE (FE 26f38a0 / parent e384123)
- [x] BATCH 11 — stream-recovery holdback (S) + hands-free voice loop (C) + real OOXML docx + per-model playground — DONE (FE 6e30c3a / parent next)
- [x] BATCH 12 — agent typed-events+permission-gate (S) + permission-modal + agent timeline + ACL-for-tools — DONE (FE 6d1d4ff / parent next)
- [x] BATCH 13 — RAG multimodal ingest (S) + image-studio param-form wire + catalog deep-filters + empty/error states pass — DONE (FE 180bb53 / parent next)
- [ ] BATCH 14 — TaskPacket per-subtask model (S+orchestrator) + mobile/responsive deep polish (C) + onboarding depth + settings IA cleanup
- [ ] BATCH 15 — sleep-time memory consolidation (S+scheduler) + RU i18n/copy pass + delight/micro-interactions + sub-meters depth
- [ ] BATCH 16 — /sprint self-test (S+builtins) + frontend unit tests (vitest: decision/rag/money/usage-log) + tool-card polish + changelog depth
- [ ] BATCH 17 — security hardening (S: rate-limit/validation/owner-gate audit) + accessibility pass (C: focus/keyboard/ARIA) + a11y on panels + error-boundary
- [ ] BATCH 18 — performance backend (S: response cache, FTS/RAG query opt) + bundle/code-split FE + image lazy/opt + streaming-latency tune
- [ ] BATCH 19 — backend test suite (NEW tests/, stdlib unittest endpoint smoke) + lib hardening + harden gen-image/video error paths + retry/backoff polish
- [ ] BATCH 20 — observability (S: structured logs, error envelopes, friendly errors everywhere) + agent-timeline integration polish (C) + toast/notif system + status surfacing
- [ ] BATCH 21 — provider breadth + health checks (S) + model-catalog health UI + provider-fallback transparency + FINAL polish lane
- [ ] FINAL — full code review (batches 9-21) + full smoke + update FINAL SUMMARY + STOP

## LANE DETAIL (refined at dispatch)
### BATCH 9
- 9A server.py: RAG retrieval quality — server-side multi-query rewrite + RRF hybrid (FTS/BM25 ∪ dense cosine) + optional LLM rerank, behind the existing smart flag; back-compat default = current single-query.
- 9B chat.tsx: pre-send «≈ ₽ за это сообщение» cost estimate in composer using lib/money.ts (input-token estimate × active-model rate); hide if free/owner.
- 9C NEW components/param-form.tsx: schema-driven control renderer (string→textarea, number+min/max→slider, enum→select, bool→switch) from a model `inputs` schema. Pure, reusable; no chat.tsx/server.py.
- 9D settings-panel.tsx + NEW route app/api/identity/route.ts: server persona/identity editor wired to existing /api/identity (GET+POST already in server.py) so persona persists server-side, not just localStorage.

### BATCH 10
- 10A server.py: workflow runner (/api/workflow: run a templated multi-step pipeline over existing primitives — chat/image/rag/web) + real `negative_prompt` field passthrough into venice_image (currently text-concatenated «Избегай:»).
- 10B workflows.tsx: wire the gallery to the new runner (run template, show steps/result); remove the «скоро» stub.
- 10C settings-panel.tsx + dev-mode-panel.tsx: memory-budget sliders (protected_recent 2-40, memory_max_chars 200-2000) → existing userconfig POST.
- 10D model-catalog.tsx + image-studio.tsx + gen-image.ts: brand-click→filter-to-brand's-newest; swap image-studio negative box to send real negative_prompt.

### BATCH 11
- 11A server.py: complete stream-recovery — holdback buffer (don't emit last N chars until next chunk confirms not a cut tool-call) + silent retry/reconnect on truncated/dropped upstream stream (cheap-provider robustness).
- 11B chat.tsx + lib/use-voice-input.ts: hands-free loop — after auto-speak of a reply finishes, auto-reopen the mic (talk→speak→listen), guarded by an explicit «режим разговора» toggle.
- 11C lib/export-doc.ts: real OOXML .docx export (add `docx` npm dep; mirror the SheetJS/pptxgenjs pattern) replacing the application/msword HTML fake.
- 11D NEW components/playground.tsx: per-model playground (Input/Result, Form/JSON toggle, system-prompt, live price on the run button, copy-able API/embed snippet) reusing existing media/chat proxies.

### BATCH 12
- 12A server.py: agent loop emits typed SSE events (plan/tool/permission/result/verify/run_done) + interactive permission wait (once/always/deny) before active_tools execution; back-compat (no wait when client doesn't negotiate it).
- 12B lib/use-taiga-chat.ts + NEW components/permission-modal.tsx: parse new events; interactive approve/deny-once/always UI mid-run.
- 12C components/thinking-steps.tsx + lib/permissions.ts: live plan→tool→result→verify timeline; extend ACL from slash-commands to real backend tool calls.
- 12D NEW lib/agent-events.ts: typed event parser/types shared by hook + components (keeps 12B/12C decoupled).

### BATCH 13
- 13A server.py: RAG multimodal ingest — VLM-caption images/tables on ingest → embed the caption text (vision model already wired); scanned-PDF OCR-via-VLM fallback.
- 13B image-studio.tsx + cinema-studio.tsx: render param-form.tsx (from 9C) for per-model inputs instead of hardcoded aspect/duration.
- 13C model-catalog.tsx: deep filters (context/freedom/price/lang/specialty/TEE) polish + saved-filter chips.
- 13D cross-panel empty/error/loading-state pass (NEW lib/ui-states.ts + apply to tasks-panel/workflows/usage-analytics/model-catalog).

### BATCH 14
- 14A server.py + orchestrator.py: per-subtask model delegation (TaskPacket) — each orchestrator subtask carries its own model/provider override + acceptance/verify envelope.
- 14B chat.tsx: mobile/responsive deep polish (composer, drawer, message density, safe-area, tablet breakpoint audit).
- 14C onboarding.tsx + NEW capability-tour: deeper first-run (interactive capability tour, sample prompts per mode).
- 14D settings-panel.tsx: information-architecture cleanup (group/section/search within settings).

### BATCH 15
- 15A scheduler.py + server.py: sleep-time/idle memory consolidation (background re-reconcile when user away; dedup/merge memory).
- 15B RU i18n/copy pass (NEW lib/i18n strings audit; fix mixed RU/EN, tone «ты»).
- 15C delight/micro-interactions (motion polish on key surfaces, reduced-motion safe).
- 15D sub-meters.tsx + usage-analytics.tsx depth (reset timers, per-model breakdown, export).

### BATCH 16
- 16A server.py + lib/commands/builtins.ts: /sprint self-test (Taiga runs a smoke of its own endpoints + reports).
- 16B NEW frontend unit tests (vitest + RTL): decision.ts, rag.ts, money.ts, usage-log.ts, msg-tree.ts.
- 16C tool-card.tsx polish (arg/result formatting, copy, collapse-all).
- 16D whats-new.tsx changelog depth (versioned entries, "new since last visit").

### BATCH 17
- 17A server.py: security hardening — per-IP/token rate-limit on expensive endpoints, input validation sweep, owner-gate audit (re-confirm no non-owner can hit owner-only paths).
- 17B chat.tsx: accessibility — keyboard nav, focus management, ARIA roles on composer/messages, contrast fixes.
- 17C a11y on settings/studio panels + skip-links + focus-visible.
- 17D NEW components/error-boundary.tsx + wrap risky panels.

### BATCH 18
- 18A server.py: performance — response caching for catalog/init, FTS/RAG query optimization, lazy model-catalog load.
- 18B FE bundle/code-split (dynamic import heavy panels: studio/catalog/workflows).
- 18C image lazy-load/opt + next/image audit.
- 18D streaming-latency tune (first-token, flush cadence) FE side.

### BATCH 19
- 19A NEW tests/ (stdlib unittest): endpoint smoke for init/chat/council/search/rag/image guards.
- 19B lib hardening (null-guards, error paths in gen-image.ts/video-gen.ts/rag.ts).
- 19C harden media error paths (provider-down UX, refund-on-fail surfacing).
- 19D retry/backoff polish across providers (server.py is taken by 19A? no — 19A is NEW tests file, not server.py edit; keep 19D as lib/client backoff to avoid server contention).

### BATCH 20
- 20A server.py: observability — structured request logging, consistent error envelopes, friendly errors on every endpoint.
- 20B chat.tsx: agent-timeline integration polish (final wiring of 12 into the main chat view).
- 20C NEW components/toast system + global status surfacing.
- 20D settings: diagnostics/health page (backend status, provider balances, last errors).

### BATCH 21
- 21A server.py: provider breadth + health checks (add/verify providers, periodic health-ping, auto-hide dead).
- 21B model-catalog.tsx: live health UI (up/down/latency badges).
- 21C provider-fallback transparency (show which provider served a reply when fallback fired).
- 21D FINAL polish lane (loose ends, TODO sweep, dead-code removal).

## DEFERRED / BLOCKED (need founder keys/infra/decision — NOT auto-building)
Same as V2 DEFERRED list: real payments, self-hosted ML voice/guard, sqlite-vec, E2B sandbox, ComfyUI/manim/FLUX-schnell, Taiga-Coder v2 autonomous loop, GPU host, desktop Tauri, social publishing, login UI, ACE-Step, 3D .glb (provider down), deepfake/face consent guard (needs vision face-detect), MCP OAuth full browser flow (needs Google OAuth client creds), Coder git-push/PR (needs GitHub token).
