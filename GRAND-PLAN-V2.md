# GRAND PLAN V2 — autonomous overnight build (idea→production)
Founder asleep ~10h. Work AUTONOMOUSLY. Batches of 4 disjoint lanes. Verify (tsc/build/ast) + commit each batch. Update STATUS. Re-schedule self until ALL done.
Rule: ≤1 server.py lane + ≤1 chat.tsx lane per batch (god-file contention). Commit LOCAL only (no push). Live: backend :8777, dev :3000.

## STATUS (source of truth for resume)
- [x] BATCH 0 — requirements scrape (3 agents, 18 docs) — DONE
- [x] BATCH 1 — proxies+wirings, FTS5, themes — DONE (FE 930d121 / parent af5e1bb)
- [ ] BATCH 2 — stream-recovery, office-export, img2img, onboarding
- [ ] BATCH 3 — heuristic-tools, analytics, aux-models-UI, voice-picker
- [ ] BATCH 4 — RAG-chunking, bg-tasks-panel, catalog-screen, agent-tabs
- [ ] BATCH 5 — Beam-fusion, camera+Beam-UI, cron-triggers, sub-meters
- [ ] BATCH 6 — Aider-editblock, OpenHands-risk-gate, richer-RAG-retrievers, model-catalog-badges
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

## DEFERRED / BLOCKED (accounted-for, NOT building autonomously — reason)
- Real payments (СБП/BTCPay/crypto) — Damir-deferred until decensor; needs processor account.
- Login/signup UI — auth.py ready; single-user fine; multi-user-only, deferred.
- Self-hosted voice (Kokoro/faster-whisper), LLM-Guard, sqlite-vec, manim/ComfyUI/FLUX-schnell, E2B sandbox — need heavy ML deps / external keys / services; not safe to auto-install on founder's Mac.
- 3D .glb output — AIMLAPI triposr provider down (no code fix).
- Taiga-Coder v2 autonomous plan→test→PR loop, own GPU host, desktop Tauri, social publishing — explicit v2/post-launch.
- ACE-Step free music — needs provider/host.
- Face-swap deepfake consent guard — Damir-deferred (FINISH-PLAN ОТЛОЖЕНО).
