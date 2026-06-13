# PROJECT-STATE.md — Тайга ИИ — handoff for a fresh session
_Last updated after batch 17 + independent 3-agent audit (all green). Read this + GRAND-PLAN-V3.md to resume._

## What this is
**Тайга ИИ** — privacy-first, uncensored, multi-model AI super-app for the RU/CIS market. Owner = Damir (solo founder). This is a SEPARATE project from Mostik VPN (the CLAUDE.md "never say Cudy / Xiaomi AX3000T" rules are about Mostik VPN routers, NOT Тайга — ignore them here).

## Where it lives
- Repo root: `/Users/damir12/Downloads/claude-sessions/2026-06-10/mostik-ai/`
- Backend: `server.py` — stdlib-only Python `http.server`, ~10,476 lines, port **8777**. Also `orchestrator.py` (LangGraph multi-worker) + `scheduler.py` (cron daemon).
- Frontend: `taiga-web/` — Next.js 16 (Turbopack) / React / Tailwind v4 / TS, dev port **3000**. **It is a git SUBMODULE** (tracked as a gitlink; there is no `.gitmodules` mapping — commit FE first, then the parent bumps the pointer).
- God-files: `server.py` (backend) and `taiga-web/src/components/chat.tsx` (frontend shell). 69+ components, 44+ libs, 43+ API routes.
- DB: SQLite (stdlib sqlite3, FTS5). Providers: Venice / NanoGPT / Chutes / RedPill (chat) + AIMLAPI (media). Owner default model = `ng:deepseek-ai/deepseek-v3.2` (cheap; free via NanoGPT sub for owner). NEVER default to Opus for the app.

## Architecture pattern (critical)
Every frontend `fetch("/api/X")` → `taiga-web/src/app/api/X/route.ts` (Next proxy) → `http://127.0.0.1:8777`. Proxy convention: `runtime="nodejs"`, `dynamic="force-dynamic"`, `const BACKEND = process.env.TAIGA_BACKEND ?? "http://127.0.0.1:8777"`. New backend endpoints need a matching route.ts proxy (mirror `src/app/api/recall/route.ts`).

## Hard rules (from founder + session)
1. **Commit LOCAL only. NEVER push.** (Remote isn't even auth-reachable here.)
2. Every git commit message ends with: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`
3. Plain English / RU «ты»-tone in UI copy. Binary per-deliverable status to Damir.
4. Decide technical stuff yourself (fix priority, merge order, agent dispatch). Don't pile choices on him. "keep going"/"go"/"do it" = drive autonomously.
5. Do NOT pad with filler — honest scope over hitting a round number.

## Build method (the autonomous loop)
- **Source of truth for resume = GRAND-PLAN-V3.md STATUS checkboxes** (and GRAND-PLAN-V2.md for batches 0-8).
- Each batch = up to **4 parallel disjoint-file lanes**, rule: **≤1 server.py lane + ≤1 chat.tsx lane per batch** (god-file contention). Dispatch 4 general-purpose agents with exact file ownership + "DO NOT touch other files" + back-compat requirements. Agents build + self-verify (`python3 -c "import ast"` / `npx tsc --noEmit`) but **do NOT commit** and **do NOT restart the server**.
- Coordinator (you) then: ast server.py (+orchestrator/scheduler if touched) → full `cd taiga-web && npx tsc --noEmit` on the MERGED state (ignore transient errors agents saw from each other's mid-edits) → `npx vitest run` (73 tests exist, keep green) → restart backend → smoke → commit FE submodule first, then parent (incl. GRAND-PLAN-V3.md STATUS update with FE+parent SHAs).
- **Backend restart (slow bind ~10s):** `for p in $(lsof -ti:8777); do kill -9 $p; done; pkill -9 -f "python3 server.py"; sleep 2;` then start via Bash `run_in_background:true` running `python3 server.py > server.out 2>&1` (NOT with `&`/`disown` — those die when the shell exits); `sleep 10`; then curl. Smoke: init 200, chat stream (meta/delta/cost/done), + the batch's new endpoint.

## Progress (audited green, batch 17)
**GRAND-PLAN-V2 batches 0-8: DONE** (search/themes/stream-recovery/office-export/onboarding/heuristic-tools/analytics/aux-models/RAG-chunking/tasks-panel/catalog/agent-tabs/Beam/camera/cron/sub-meters/Aider-editblocks/risk-gate/RAG-retrievers/model-catalog/smart-RAG-wiring/custom-instructions/changelog/MCP-picker/per-chat-RAG/tool-cards/workflow-gallery). Final review cleared.

**GRAND-PLAN-V3 batches 9-17: DONE** (FE / parent SHAs):
- 9 (7c98c79/3dcac25) smart-RAG (`rag_query_smart`) · pre-send ₽ estimate · param-form.tsx · server-persona editor + /api/identity route
- 10 (26f38a0/dccf432) workflow runner (`api_workflow`+4 templates) · real negative_prompt · memory-budget sliders · brand-click catalog
- 11 (6e30c3a/3d91393) stream-recovery holdback+silent-retry · hands-free voice loop · real OOXML .docx (docx@9.7.1) · playground.tsx (ORPHAN — see loose ends)
- 12 (6d1d4ff/f7d99b4) agent typed-events + interactive permission gate (/api/agent_permit, no-hang) · agent-events.ts · permission-modal.tsx · thinking-steps agentSteps · tool-ACL
- 13 (180bb53/7f49a40) multimodal RAG ingest (VLM caption) · studio param-forms · catalog deep-filters+saved-chips · ui-states.tsx
- 14 (a989525/bf1a440) TaskPacket per-subtask models+verify · mobile deep-polish · onboarding tour (capability-tour.tsx) · settings IA reorg
- 15 (419a44a/3b42aca) sleep-time memory consolidation (off by default, /api/memory_consolidate) · i18n.ts · motion.ts · meters depth
- 16 (2b55637/7a7a136) /sprint self-test (/api/selftest, 6 checks) · vitest + 73 tests · tool-card polish · versioned changelog
- 17 (8428d01/f455ad3) security (per-IP rate-limit + input validation + owner-gate audit) · a11y (chat + settings) · error-boundary.tsx

## REMAINING (batches 18-21 + FINAL — specs in GRAND-PLAN-V3.md LANE DETAIL)
- **18** performance: backend response cache + FTS/RAG query opt (server.py) · FE bundle/code-split · image lazy/opt · streaming-latency tune
- **19** backend test suite (NEW tests/, stdlib unittest) · lib hardening · media error paths · retry/backoff
- **20** observability (server.py: structured logs, error envelopes, friendly errors) · **agent-timeline integration into chat.tsx (the dormant wiring — see below)** · toast/notif system · status surfacing
- **21** provider breadth + health checks (server.py) · model-catalog health UI · provider-fallback transparency · FINAL polish lane
- **FINAL** full code review of batches 9-21 + full smoke + update FINAL SUMMARY in GRAND-PLAN-V3.md + STOP (no reschedule)

## Known loose ends to wire in batch 20's chat.tsx lane
- **playground.tsx** — built (batch 11), NOT mounted anywhere. Mount it (e.g. from settings or a plus-menu entry).
- **agent-events UI** — backend + hook (`sendPermit`) + permission-modal + thinking-steps `agentSteps` all ready, but chat.tsx doesn't pass `agentSteps`, mount `<PermissionModal>`, or set `agent_events`/`interactive_perms`. Wire a toggle. (Note: chat.tsx's `pendingPerm` is a SEPARATE pre-existing slash-command perm flow — don't confuse.)
- **capability-tour** — built, not mounted. Mount `<CapabilityTour>` + pass `onStartTour` to `<Onboarding>`.
- **/sprint dispatch** — builtin + /api/selftest + proxy exist; add a chat.tsx dispatch (mirror the `/recall` interception in `submit()`) that POSTs /api/selftest and renders ✅/❌ checks.

## DEFERRED / BLOCKED (need founder keys/infra/decision — do NOT auto-build)
Real payments (СБП/BTCPay/crypto), self-hosted ML voice/guard, sqlite-vec, E2B sandbox, ComfyUI/manim/FLUX-schnell free-media, Taiga-Coder v2 autonomous loop, own GPU host, desktop Tauri, social publishing, login/signup UI, ACE-Step music, 3D .glb (provider down), deepfake/face consent guard, MCP OAuth full browser flow (needs Google OAuth creds), Coder git-push/PR (needs GitHub token).

## Audit note (batch-17 checkpoint)
3 independent fresh-context auditors verified backend (all features real+wired+live), frontend (tsc 0 / vitest 73 / real `next build` succeeds), and git (clean tree, nothing pushed, all SHAs real, diffs consistent). No hallucinations, no regressions. The ~40 planning docs in the repo are ~95% STALE — trust the CODE, not the docs. This file + GRAND-PLAN-V3.md are the current truth.
