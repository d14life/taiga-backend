# GRAND PLAN V2 — autonomous overnight build (idea→production)
Founder asleep ~10h. Work AUTONOMOUSLY. Batches of 4 disjoint lanes. Verify (tsc/build/ast) + commit each batch. Update STATUS. Re-schedule self until ALL done.
Rule: ≤1 server.py lane + ≤1 chat.tsx lane per batch (god-file contention). Commit LOCAL only (no push). Live: backend :8777, dev :3000.

## STATUS (source of truth for resume)
- [x] BATCH 0 — requirements scrape (3 agents, 18 docs) — DONE
- [x] BATCH 1 — proxies+wirings, FTS5, themes — DONE (FE 930d121 / parent af5e1bb)
- [x] BATCH 2 — stream-recovery, office-export, img2img, onboarding — DONE (FE 5d2d84c / parent 4fd3715)
- [x] BATCH 3 — heuristic-tools, analytics, aux-models-UI, voice-picker — DONE (FE c65980a / parent 19fc2fd)
- [x] BATCH 4 — RAG-chunking, bg-tasks-panel, catalog-screen, agent-tabs — DONE (FE 2350f4c / parent 2cec45b)
- [x] BATCH 5 — Beam-fusion, camera+Beam-UI, cron-triggers, sub-meters — DONE (FE 07ba126 / parent c6fc7d5)
- [x] BATCH 6 — Aider-editblock, OpenHands-risk-gate, richer-RAG-retrievers, model-catalog-badges — DONE (FE b561887 / parent 0f163f2)
- [x] BATCH 7 — wire smart-RAG+risk-gate, usage-log refactor, MCP-at-creation+memory-budget, custom-instructions+changelog — DONE (FE ae6df49 / parent 8020f0b)
- [x] BATCH 8 — per-chat RAG workspace, assistant-ui tool-cards, workflow-marketplace, MCP-picker-in-builders — DONE (FE 9a4e364 / parent PENDING)
- [ ] FINAL — full code review + smoke + report

## LANES (each = dedicated agent; detailed prompt at dispatch)
### BATCH 1
- 1A server.py: FTS5 full-text search across chats+memory (sqlite FTS5 virtual table, /api/search_chats).
- 1B route.ts: create app/api/improve/route.ts + app/api/recall/route.ts proxies (backend endpoints exist).
- 1C chat.tsx: wire prompt-polish (/api/improve), episodic recall (/api/recall) caller, dev-mode safe-tools toggles consumed in dispatch, image_intent auto-route caller.
- 1D theme.ts+theme-panel.tsx: Light/Dark/System toggle + font-by-mode.

### BATCH 2
- 2A server.py: stream-recovery (holdback buffer + silent retry of cut streams + tool-JSON repair) — robustness lift.
- 2B lib/export-doc.ts(+artifacts/sheet.ts): native .xlsx + .pptx file creation (docx/pdf already exist).
- 2C image-studio.tsx: img2img/inpaint (init-image) exposure + price-before-gen on every model.
- 2D NEW components/onboarding.tsx: first-run + capability-cards empty state ("Что умеет Тайга").

### BATCH 3
- 3A server.py: HeuristicToolParser (parse tool-calls from plain text → tools work on non-function-calling uncensored models).
- 3B NEW components/usage-analytics.tsx: spend/tokens/requests by period + per-model bars (reads /api/billing).
- 3C dev-mode-panel.tsx: auxiliary-models-per-task config UI (backend aux_model exists; surface override).
- 3D voice-pref.ts(+settings): voice provider picker (Google/Web/NanoGPT) selection.

### BATCH 4
- 4A server.py: smarter RAG chunking (recursive/semantic splitter, code+markdown aware) replacing fixed-size.
- 4B NEW components/tasks-panel.tsx: background-tasks Running/Finished dashboard (orchestrator/jobs, tokens/time/phase).
- 4C model-picker.tsx: full catalog SCREEN — filters (context/freedom/price/lang/specialty) + category + badges.
- 4D agents-marketplace.tsx: My/Featured/My-Chats tabs + author + starter-chips.

### BATCH 5
- 5A server.py: Beam-fusion mode (fan-out N models → merge/de-hallucinate synthesis) extending council.
- 5B chat.tsx: Beam UI trigger + camera capture button (getUserMedia) in composer.
- 5C scheduler.py+jobs-panel.tsx: richer cron triggers (weekday / time-of-day "по будням 18:30").
- 5D NEW components/sub-meters.tsx: subscription meters UI (weekly tokens / daily images / reset) — owner.

### BATCH 6
- 6A server.py: Aider-style editblock diff/apply engine (find/replace blocks, fuzzy) for coder file edits.
- 6B lib/decision.ts(+server risk): OpenHands-style self risk-gate (analyze action risk → auto plan/auto/full).
- 6C lib/rag.ts+rag-manage.ts: MultiQuery/Ensemble retriever patterns (frontend RAG controls).
- 6D NEW components/model-catalog.tsx: dedicated catalog page wired from 4C (badges new/cheapest/TEE/uncensored%).

### BATCH 7 (follow-ups — make shipped features real)
- 7A chat.tsx: wire smart multi-query RAG behind a «умный поиск» toggle into the send path; wire OpenHands risk-gate (riskOf/policyFor) into the agent permission flow (keep back-compat with toolRisk).
- 7B lib/usage-log.ts (NEW) + usage-analytics.tsx + use-taiga-chat.ts: move recordUsage/loadUsage/UsageEntry/USAGE_EVENT to lib; component + hook import from lib (architecture tidy).
- 7C server.py: MCP-connector-at-creation (skill/agent builder can attach an MCP connector by id/url) + memory budget control (protected-recent N messages + max memory chars per request).
- 7D NEW components/custom-instructions.tsx + components/whats-new.tsx (mounted in settings): ChatGPT-style «что Тайге знать о тебе / как отвечать» → master-prompt/profile; changelog feed.

### BATCH 8 (parity polish)
- 8A server.py: per-chat RAG workspace scope (tag rag chunks by chat_id; optional query-within-this-chat) — AnythingLLM pattern.
- 8B NEW components/tool-card.tsx + wire in chat timeline: assistant-ui-style structured tool-call cards (name/args/result, collapsible).
- 8C NEW components/workflows.tsx (mounted): Templates/Мои/Опубликованные — workflow gallery built on existing pipelines/lib.
- 8D agent-builder.tsx + skill-builder.tsx: MCP-connector picker in the builders (frontend of 7C) — attach a connector while building.

## DEFERRED / BLOCKED (accounted-for, NOT building autonomously — reason)
- Real payments (СБП/BTCPay/crypto) — Damir-deferred until decensor; needs processor account.
- Login/signup UI — auth.py ready; single-user fine; multi-user-only, deferred.
- Self-hosted voice (Kokoro/faster-whisper), LLM-Guard, sqlite-vec, manim/ComfyUI/FLUX-schnell, E2B sandbox — need heavy ML deps / external keys / services; not safe to auto-install on founder's Mac.
- 3D .glb output — AIMLAPI triposr provider down (no code fix).
- Taiga-Coder v2 autonomous plan→test→PR loop, own GPU host, desktop Tauri, social publishing — explicit v2/post-launch.
- ACE-Step free music — needs provider/host.
- Face-swap deepfake consent guard — Damir-deferred (FINISH-PLAN ОТЛОЖЕНО).

## ✅ FINAL SUMMARY (overnight build complete — all 6 batches + final review)
All 6 batches DONE, verified (tsc=0 / build PASS / backend smoke green / FTS+council+studio+skills smoke green), committed LOCALLY (never pushed). Final code-review run: cleared as ship-able; the one 🔴 it found (heuristic tool-parser misfiring on prose-JSON in agent mode) was FIXED + verified.

### Shipped this session
- **Robustness:** instruction-source boundary (anti prompt-injection), anti-copy-loop, scoped memory, lean conditional prompt, stream-recovery (holdback + cut-retry + tool-JSON repair), heuristic tool-parser (loose formats on non-function-calling models, prose-JSON-safe).
- **Intelligence:** auto-escalate hard questions to Brain (free Opus for owner), Beam-fusion mode (de-hallucinated fan-out→merge), skills-as-/slashcommands.
- **Search/RAG:** FTS5 full-text chat+memory search; structure-aware recursive RAG chunking; client MultiQuery+RRF+compression retrievers (available; not yet default-wired into send — see follow-ups).
- **Studio/files:** img2img + price-before-gen; native .xlsx + .pptx export; (artifacts/PDF/Word already shipped).
- **Ecosystem:** GitHub-repo skill import (191 imported earlier), 36 agent presets, agent-marketplace tabs, MCP token-auth+resources+plain-chat, aux-models-per-task (owner override, end-to-end), heuristic tools.
- **Coder:** Aider-style editblock diff/apply engine (exact>whitespace>anchor, all-or-nothing) on owner-gated edit_file; OpenHands-style client risk-gate (riskOf/policyFor — advisory, server _perm_check authoritative).
- **UI:** Light/Dark/System + font picker; full model-catalog screen (filters/categories/badges) + dedicated catalog page; usage-analytics dashboard; background-tasks panel; subscription meters (owner); onboarding capability-cards; camera capture; mobile pass (sidebar drawer + 6 panels + tablet breakpoint); premium $100M landing redesign; unified skill/agent registry.
- **Billing/cron:** total-balance across 5 wallets + live refresh; free=owner-only; subscription hidden from users; usage-log from cost events; cron weekday/time triggers.
- **Security/QA:** /api/users auth hole closed; cinema-export SSRF+gating; prefixed-model-ID fix; friendly provider errors + silent fallback; vision verified; td3 fast-fail; 14-bug sweep.

### Known follow-ups (non-blocking — for founder review)
- Smart multi-query RAG (lib/rag ragSearch) is built but the chat send path still calls plain ragQuery — wire behind a "умный поиск" toggle (multi-query adds latency/cost, so not default-on).
- lib/decision.ts riskOf/policyFor gate is exported but not yet consumed by chat.tsx's permission flow (existing toolRisk/shouldAsk still drive it; new gate is advisory-ready).
- recordUsage imported into use-taiga-chat from a component — works (SSR-guarded), but belongs in a lib/usage-log.ts (architecture tidy).
- Heuristic parser recovers fenced/<tool_call>/name(args)/name:value formats; bare unquoted positional (`TOOL: web_search курс`) falls through to prose (safe, not a regression).
- Edit-block whitespace/anchor fallback normalizes CRLF→LF (cosmetic; exact-match path preserves bytes).

### Deferred (need founder keys/infra/decision — see DEFERRED list above): payments, self-hosted ML voice/guard, sqlite-vec, E2B sandbox, ComfyUI/manim/FLUX-schnell free-media, Taiga-Coder v2 autonomous loop, GPU host, desktop app, social publishing, login UI, ACE-Step, deepfake guard.

STATUS: autonomous loop STOPPED (all batches done). Live: backend :8777, dev :3000. All work in local git (16 batch commits af5e1bb→0f163f2 + final fix).
