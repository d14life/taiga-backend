# Overnight builder — Claude — STATUS (binary lines)

Wave 0 (handoff, while Damir asleep):
- design canvas (real, live, iterate, versions, brand-grounded) ........ DONE  fe 08600d8
- artifact preview blank-white fix (lazy + extraction) ................ DONE  fe 08600d8
- design-system reference→tokens (vision + color-extract fallback) .... DONE  be 27ee520  (smoke 200, source=degrade ok)
- agent task board (agentic-os concepts, our code) ................... DONE  fe 08600d8
- agent Задачи sub-tab wired ......................................... DONE  fe 08600d8

Queue (see OVERNIGHT-BUILD-QUEUE.md): 1 inline-html-preview · 2 templates · 3 runs-sidebar · 4 ralph-monitor · 5 scheduler · 6 slides-in-canvas
Loop builds top-down, commits only-if-green, checks items here.

---

## Wave 1 (workflow) — ALL 6 queue items integrated + verified — fe 42fdac5

Aesthetic matched to design-system-studio.tsx / design-canvas-workspace.tsx (open-design concepts,
our own code; license: open-design Apache-2.0 + paperclip/ralph MIT reimplemented, agentic-os ideas only).
Each feature lives in its OWN new file; chat.tsx is the only integration point (51-line diff).

### Restoration-grade per-item log (rebuild from this if context is lost)

**1. Inline unfenced-HTML → live preview** — feature.
- What/why: a model often replies with a WHOLE `<!doctype html>…</html>` page as PLAIN TEXT (no ```fence).
  Before: rendered as a wall of escaped markdown text. Now: rendered as a live `<WebPreview>` card.
- Files: NEW `taiga-web/src/lib/markdown-html.ts` (guard helper `bareHtmlDocument(content)`);
  EDIT `taiga-web/src/components/markdown.tsx` (early-return WebPreview when bareDoc detected).
- Guards (so it never hijacks normal markdown): fires ONLY when text has NO ``` triple-fence, is
  anchored `^` to `<!doctype html`/`<html`, AND contains a closing `</html>`. Fenced ```html path
  (code renderer) left 100% untouched. Uses existing `stripReasoning` to skip `<think>` preamble.
- Endpoints/tools: none (pure client render).

**2. Design templates gallery** — feature.
- What/why: quick-start brief grid so a user one-taps a template instead of writing a brief from scratch.
- Files: NEW `taiga-web/src/components/design-templates.tsx` (grid of quick-start briefs, each
  {brief, kind} + label/thumb); EDIT chat.tsx (renders `<DesignTemplates onPick=…>` as a STRIP above
  the brief box in Дизайн «Создать», `designGen===null` branch).
- Wiring: onPick → `setDesignGen({ brief, kind })` → opens the existing DesignCanvas with that brief
  (reuses the canvas path, NOT the chat path). Mirrors open-design HomeTemplatesReveal concept.
- Endpoints/tools: none new (reuses design-canvas → existing design endpoints).

**3. Agent runs sidebar (paperclip concept)** — feature.
- What/why: one unified list of agent runs (automations + tasks + loops from localStorage) with status
  badge, last-run time, output peek; open a run back into chat.
- Files: NEW `taiga-web/src/components/agent-runs-panel.tsx`; EDIT chat.tsx (new Агент sub-tab «Прогоны»;
  pill `["runs","Прогоны"]`; renders `<AgentRunsPanel onOpen=…>`).
- Wiring: onOpen(run) → `setBigTab("none"); setMode("chat"); void send(run.title)` (same routing as
  neighboring sub-tabs). `agentSub` union widened to `modes|auto|tasks|runs|ralph`. MIT-safe, our code.
- Endpoints/tools: none new (reads existing localStorage run stores).

**4. Ralph monitor (verify→retry→decompose)** — feature.
- What/why: visualize a loop run as iterations with per-step verify/retry/decompose state + iteration
  counter + session notes (Ralph pattern from task #10, now surfaced in UI).
- Files: NEW `taiga-web/src/components/agent-ralph-monitor.tsx` (prop `runs?` optional); EDIT chat.tsx
  (new Агент sub-tab «Ralph»; pill `["ralph","Ralph"]`; renders `<RalphMonitor />`).
- Endpoints/tools: none new (concept visualizer, MIT-safe our code).

**5. Backend automation scheduler** — feature (replaces the old "once background scheduling is on" stub).
- What/why: Автоматизации now ACTUALLY FIRE. Real per-user routine store + a background thread that
  wakes every 60 s, finds due routines (cron/interval honoring user tz), runs each via the model path,
  records a run. Honest cron, owner-first, gated.
- Files: EDIT `server.py` — endpoint `api_routines` (POST `/api/routines` {user, action:list|save|delete,
  routine?, id?} → {ok, routines}); store helpers `load/save_routines_store`, `_sanitize_routine`,
  `_routine_due/_routine_local_now/_routine_rate_ok/_routine_run_prompt/_routine_tick_user/
  _routine_auto_allowed/_all_routine_users`; daemon `_start_routine_scheduler(interval=60)` started at
  boot (line ~13054). Client EDIT `taiga-web/src/components/agent-automations.tsx` (talks to /api/routines).
- ANTI-RCE (important): the store keeps ONLY the text prompt; routines are executed by the MODEL only —
  no exec/eval, no shell. Per-user cap `_ROUTINE_MAX_PER_USER`, rate-limit, owner-first auto-allow.
- New endpoint: `POST /api/routines`. Smoke: returns `{"ok": true, "routines": []}` (200-path JSON).

**6. Slides-in-canvas** — feature.
- What/why: real slide-deck preview INSIDE DesignCanvas (kind:"slides") instead of dumping a pptx into chat.
- Files: NEW `taiga-web/src/components/slides-canvas.tsx` (live reveal-style HTML deck, prev/next,
  `brief`+`onClose` props); EDIT `taiga-web/src/components/design-studio.tsx` (DesignStudio.onGenerate
  type `slides` → `setDesignGen({ brief, kind:"slides" })`); EDIT chat.tsx (when `designGen.kind==="slides"`
  render `<SlidesCanvas brief onClose>` in the canvas area, NOT in chat). DesignCanvas kind union extended.
- Endpoints/tools: none new (client-side deck render).

### Brain (Мозг) & Council (Совет) — what was checked / state

- Brain front-contract (chat.tsx `dispatchSend` brain branch, ~L1695-1711): sends EXACTLY the backend
  contract — `brain:true`, `driver:<cheap leader>` (brainLead→auto uncensored), `brainExperts:N (1-3)`,
  `model:<expert>` (auto→`autoModelId("ultra")`=top model). No separate expert field — expert IS `model`.
  Toggle sets `brainOn`; `brain = ov?.brain ?? (brainOn && canTwo)` (Heavy no longer triggers Brain).
  `SendOpts` (use-taiga-chat.ts) forwards brain/driver/brainExperts; proxy route.ts allow-lists them.
  NO front fix was needed — chain was already correct; verified end-to-end, not changed.
- Brain backend pipeline (server.py ~L12117-12500): `brain=True` → leader streams with `ask_expert`
  tool registered (BRAIN_PROMPT) → on escalation emits SSE `tool:ask_expert`; if `brainExperts>1` runs
  N best-for-task experts (`council_step` events) fused by BEAM_FUSION critic; else single expert;
  then `tool_done:ask_expert`. Hardened fallback (task #17, L12248-12348): if the LEADER's upstream
  fails, `_pick_fallback()` first retries the default BRAIN_DRIVER to KEEP the pipeline alive, then
  funded fallbacks; only if NOTHING is funded does it surface an HONEST error — it never silently
  collapses to a single wrong-model answer.
- VERIFICATION (honest): a full content stream could NOT complete in THIS local env because the Venice
  pool key returns **HTTP 402 Payment Required** (unfunded) — confirmed by a direct `venice_stream`
  probe AND by a PLAIN non-brain chat to the same Venice model failing identically. So this is an
  ENVIRONMENT funding issue, NOT a code regression. Branch-level proof captured: brain request returns
  meta with the resolved expert (`arcee-trinity-large-thinking`), both leader+expert keys resolve
  (`resolve_key` PRESENT), the brain branch enters and ATTEMPTS the multi-model stream, and on total
  upstream failure returns the honest error (no silent single-model fallback). Council shares the same
  multi-model venice_stream path, so it is blocked by the same 402 in-env; its request fields
  (council/councilModels/n/memberPrompts/beam) are wired and allow-listed.

### Binary lines (feature … done / hash)
- inline unfenced-HTML → live preview ........ done  fe 42fdac5  (tsc 0; markdown-html.ts guarded)
- design templates gallery .................. done  fe 42fdac5  (Дизайн «Создать» strip → DesignCanvas)
- agent runs sidebar (Прогоны) .............. done  fe 42fdac5  (Агент sub-tab, MIT concept)
- ralph monitor (Ralph) ..................... done  fe 42fdac5  (Агент sub-tab, verify/retry/decompose)
- backend automation scheduler ............. done  be (root commit) /api/routines smoke {ok,routines:[]} 200, anti-RCE model-only
- slides-in-canvas ......................... done  fe 42fdac5  (kind:slides live deck, prev/next)
- design-system regression ................. green  POST /api/design-system → 200
- /app (frontend) .......................... green  GET /app → 200
- tsc --noEmit (taiga-web) ................. green  exit 0
- AST server.py + skills_run.py ............ green  AST OK
- brain branch executes (no silent collapse) green  branch entered + honest error; e2e blocked by env Venice 402 (not code)

---

## Agent-OS Wave-1 pieces — chat↔agent bridge (additive, chat.tsx wiring NEXT) — fe 9278884 / be ba15490

The mortar for a future Чат⇄Агент bridge. Every piece compiles and is backward-compatible, but
chat.tsx was NOT touched — the feature is not yet exposed in the hub. With nothing wired, the new
props are unused and behavior is unchanged everywhere. NEXT step is the chat.tsx integration that
passes onMerge / onOpenAsChat / seedContext and feeds derived goals into orchestrate(seed).

### What was added (rebuild from this if context is lost)

**lib (taiga-web/src/lib):**
- `agent-runs.ts` (extended, nothing broken): types `RunStepKind`, `RunStep` (kind/label/content/model?/ok?/ts?);
  `AgentRun` gains optional `trace?: RunStep[]` + `goal?`; helpers `recordRunTrace`, `getRunTrace`,
  `loadRunsWithTrace` (trace survives localStorage via recordRun).
- `run-to-chat.ts` (NEW): `runTraceToMessages(run)` — render a run trace as a chat transcript
  (goal = first user turn; each step = assistant turn; tool-steps collapsible via message.steps;
  pure, deterministic ids).
- `derive-goal.ts` (NEW): `deriveGoal(messages, signal?)` — folds a transcript into ONE agent goal
  via `POST /api/improve` ({text}→{text}); fallback = trimmed last user message on any error.
- `orchestrator.ts` (edit): optional trailing `seed?` on `orchestrate` / `orchestrateStream`, sent in
  the body only when non-empty (old backend ignores it).

**components (taiga-web/src/components):**
- `loop-studio.tsx`: optional `seedContext?` prop + "контекст из чата" cyan badge; mixes seed into the
  goal body (capped 4000) so it flows through {{input}} to every stage; records full run trace on
  done/error via `recordRunTrace` (same id as recordRun → upsert, no dup).
- `agent-runs-panel.tsx`: optional `onOpenAsChat?(run)` prop + "Открыть как чат" chip (loads via
  loadRunsWithTrace, hands back the full record w/ trace); ActionChip stopPropagation.
- `agent-ralph-monitor.tsx`: props typed `{ runs?: AgentRun[] }`; real per-iteration data built from a
  run's trace (`iterationsFromTrace`: plan/worker/stage/synth→implement, tool→implement, verify→verify
  (+retry/decompose on fail), note→session note); demo only as fallback when no usable trace.
- `sidebar.tsx`: optional `onMerge?(ids)` prop + multi-select mode (toggle + ~480ms long-press) to merge
  chats; entire select UI hidden until onMerge is wired.

**backend:**
- `server.py`: `/api/orchestrate` reads optional `seed` (clamped SEC_MAX_PROMPT_CHARS) → forwards to
  `run_orchestration(..., seed=seed)` in BOTH SSE + JSON branches; `_scheduled_runner` intentionally
  passes no seed (no originating chat).
- `orchestrator.py`: `run_orchestration(..., seed=None)` — normalized/clamped (SEED_MAX_CHARS=8000) chat
  context block mixed into the planner system prompt + every worker prompt; content-only, never exec/eval
  (double clamp: 200k at server.py + 8k here). seed empty/None/whitespace → block "" → prior behavior.
- `ROADMAP-AGENT-OS.md` (NEW): Agent-OS wave roadmap.

### Binary lines
- agent-runs trace helpers ................. done  fe 9278884  (RunStep/trace, loadRunsWithTrace)
- run-to-chat bridge ....................... done  fe 9278884  (runTraceToMessages, pure)
- derive-goal ............................. done  fe 9278884  (/api/improve fold + fallback)
- orchestrator seed param (fe) ............ done  fe 9278884  (sent only when non-empty)
- loop-studio seedContext + trace ......... done  fe 9278884  (badge + recordRunTrace)
- runs-panel open-as-chat .................. done  fe 9278884  (onOpenAsChat chip)
- ralph monitor real data ................. done  fe 9278884  (iterationsFromTrace, demo fallback)
- sidebar multi-select merge .............. done  fe 9278884  (onMerge, hidden until wired)
- backend seed plumbing ................... done  be ba15490  (server.py + orchestrator.py, model-only)
- ROADMAP-AGENT-OS.md ..................... done  be ba15490
- chat.tsx wiring ......................... PENDING (next: pass onMerge/onOpenAsChat/seedContext + deriveGoal→seed)
- tsc --noEmit (taiga-web) ................. green  exit 0
- AST server.py + orchestrator.py ......... green  AST OK
- /app (frontend) .......................... green  GET /app → 200 (after backend restart)

---

## Agent-OS Wave A — live dock + run replay/stepper + task DAG + session lib — fe d4a63ba / be 8ac81d7

Status: GREEN. tsc --noEmit exit 0 (project-wide, incl. new files); GET /app → 200 (dev server live,
HMR picked up edits). Committed + pushed both repos.

### Features
- **Live agent dock** — global, always-on floating dock (`position: fixed`), visible on every tab,
  doesn't cover the composer. Opens a run into replay via `onOpenRun`.
- **Run replay / stepper** — full-screen overlay; play back a run's recorded trace step-by-step; can
  "Открыть как чат" (reuses the exact run-to-chat bridge: `runTraceToMessages` → guard empty →
  close replay → mode chat → new chatId → load).
- **Task dependency-graph (DAG)** — lives inside the existing `AgentTasks` (sub-tab Задачи, already
  mounted ~line 5545); no extra wiring needed in chat.tsx.
- **Unified session lib** — net-new `src/lib/session.ts` (174 lines); standalone, builds clean. Not yet
  imported by other modules (supporting lib; surface-wiring lands in a later wave).

### Files (taiga-web/src)
- `components/agent-dock.tsx` (NEW, 486 ln): floating live dock; `onOpenRun(run)` callback.
- `components/run-replay.tsx` (NEW, 634 ln): full-screen run stepper; `onClose` + `onOpenAsChat`.
- `lib/session.ts` (NEW, 174 ln): unified session helpers.
- `components/agent-tasks.tsx` (MOD, +534): task dependency-graph inside Задачи sub-tab.
- `components/chat.tsx` (MOD, +26): only file touched for mount —
  - imports `AgentDock`, `RunReplay`, `import type { AgentRun }` (~ln 159-161);
  - `const [replayRun, setReplayRun] = useState<AgentRun | null>(null)` (~ln 392);
  - top-level render (just before root `</div>`, alongside McpPanel/Playground/PermissionModal/toast):
    `<AgentDock onOpenRun={(run) => setReplayRun(run)} />` (ln 6438) + `{replayRun && <RunReplay … />}`
    (ln 6441-6443).

### UI reachable
- Dock mounted **once** at top level (outside all tab scroll-containers) → visible on every tab, every
  mode; fixed-position so it never covers the composer.
- Replay overlay renders above everything when `replayRun` is set; opened from the dock per spec
  (`AgentRunsPanel` exposes no replay prop — only onOpen/onOpenAsChat/className — so the dock is the
  entry point).
- Task DAG reachable via Задачи sub-tab (already live).

### Binary lines
- agent dock (live, global) ................ done  fe d4a63ba  (agent-dock.tsx, onOpenRun)
- run replay / stepper ..................... done  fe d4a63ba  (run-replay.tsx, onClose/onOpenAsChat)
- task dependency-graph .................... done  fe d4a63ba  (agent-tasks.tsx, in Задачи)
- unified session lib ..................... done  fe d4a63ba  (lib/session.ts, standalone)
- chat.tsx wiring (dock + replay mount) .... done  fe d4a63ba  (was PENDING above; now mounted, +26)
- tsc --noEmit (taiga-web) ................. green  exit 0
- GET /app ................................ green  200
- pushed (taiga-web) ...................... done  609254e..d4a63ba main
- pushed (root bump) ...................... done  f7eb908..8ac81d7 main

---

## Agent-OS Wave B — auto-approve + event triggers/heartbeats + run checkpoints

Three agent-OS slices, all surfaced in the UI. Front commit `7395ee5` (taiga-web), backend/bump
commit `2feb6d3` (root).

### Features
- **Auto-approve safe tool-calls** — a per-session policy `ask | smart | full` deciding mid-run
  tool-permission requests automatically (safe calls auto-approved under `smart`, everything under
  `full`; default `ask` = unchanged old behavior). Policy is owned by the chat hook and persisted to
  `localStorage` (`taiga.approve.policy`). Risk classification lives in net-new `lib/tool-risk.ts`
  (`APPROVE_POLICIES`, `APPROVE_POLICY_LABELS`, `APPROVE_POLICY_HINTS`, `isApprovePolicy`,
  `type ApprovePolicy`). This is a separate axis from `permMode` (server-side tool gate before a run);
  approve-policy is the mid-run client decision.
- **Event triggers / heartbeats** — routines can now fire on events, not just on a clock. A routine
  carries an optional `trigger: { kind: "time" | "on_run_done" | "on_chat_match", pattern? }`.
  `time` (default) → time daemon. `on_run_done` → fired when any agent run finishes. `on_chat_match`
  → fired when a chat message matches `pattern`. Backend contract: `POST /api/routine_event
  {user, event:"run_done"|"chat_match", text?}` → runs the user's matching event-routines and returns
  `{ok, fired:[…]}`; the time daemon ignores event-kind triggers (and vice-versa).
- **Run checkpoints** — the loop engine emits a `checkpoint` event at each stage boundary; replay can
  insert it as a `note` step (marker `⟢checkpoint⟣`, survives `sanitizeStep`). From the replay overlay
  you can resume from a checkpoint or branch a fresh agent run seeded with the trace up to that step.

### Files
- `taiga-web/src/lib/tool-risk.ts` (NEW): approve-policy enum + labels/hints + `isApprovePolicy` guard
  + per-tool risk classification.
- `taiga-web/src/lib/use-taiga-chat.ts` (MOD, +183): owns `approvePolicy` / `setApprovePolicy`,
  `localStorage` persistence (`taiga.approve.policy`), default `ask`, optional `approvePolicy` option.
- `taiga-web/src/components/chat.tsx` (MOD, +66): compact approve toggle chip (ShieldCheck,
  Спрашивать/Умный авто/Полный авто) next to the «Права агента» pill; `cycleApprovePolicy()` with hint
  toast; `branchFromCheckpoint(run, stepIndex)` wired into `<RunReplay onBranch=…>` (seeds the Команда
  panel from the trace, same seed-bridge as `promoteToAgent`); replay still opened from `AgentDock
  onOpenRun`.
- `taiga-web/src/components/agent-automations.tsx` (MOD, +266): `trigger` field on routines, `TriggerKind`,
  `normalizeTrigger` (defaults to `time`, keeps `pattern` only for `on_chat_match`), `TRIGGERS` picker UI.
- `taiga-web/src/components/run-replay.tsx` (MOD, +37): `onBranch(run, stepIndex)` prop; resume-from /
  branch-from-checkpoint buttons.
- `taiga-web/src/lib/loop-engine.ts` (MOD, +43): `checkpoint` event at stage boundaries; `CHECKPOINT_MARK`,
  `stageCheckpointStep`, `checkpointLabel`, `isCheckpointStep`.
- `server.py` (MOD, +165/-25): `POST /api/routine_event` handler (`api_routine_event`), event→trigger.kind
  mapping, event-routine runner; time daemon scoped to `trigger.kind=="time"` only.

### UI reachable
- Approve chip lives in the mode-pill cluster (right after «Права агента»), visible wherever the
  composer is.
- Trigger picker lives in the routine editor inside Automations.
- Checkpoint resume / branch buttons render in the run-replay overlay (opened from the global dock).

### Checks (all green)
- `npx tsc --noEmit` (taiga-web) ........... green  exit 0  (note: literal `--noEmit=0` is invalid tsc
  flag TS5025; correct form `--noEmit` is the one run)
- `python3 ast.parse(server.py)` .......... green  AST OK
- `GET 127.0.0.1:3000/app` ................ green  200
- `POST /api/routine_event` smoke ......... green  200  `{"ok": true, "fired": []}`

### Binary lines
- auto-approve safe tool-calls ............. done  fe 7395ee5  (tool-risk.ts + use-taiga-chat.ts + chat.tsx chip)
- event triggers / heartbeats (FE) ........ done  fe 7395ee5  (agent-automations.tsx trigger picker)
- event triggers / heartbeats (BE) ........ done  be 2feb6d3  (server.py /api/routine_event)
- run checkpoints (emit + branch/resume) .. done  fe 7395ee5  (loop-engine.ts + run-replay.tsx + chat.tsx)
- tsc --noEmit (taiga-web) ................. green  exit 0
- server.py AST ........................... green  OK
- GET /app ................................ green  200
- routine_event smoke ..................... green  200 {"ok":true,"fired":[]}
- pushed (taiga-web) ...................... done  d4a63ba..7395ee5 main
- pushed (root bump) ...................... done  8ac81d7..2feb6d3 main

---

## Wave C — sandbox surface + MCP/skill marketplace + eval harness (Agent sub-tabs)

Top unchecked FINISH-ALL item #1. Three parallel-agent components on NEW files, integrated into
chat.tsx in ONE pass (existing motion-pill sub-tab pattern). Layered on top of the existing
sandbox/terminal/browser/mcp/skills routes — nothing rewired underneath.

### Features
- **Песочница** (sub-tab `sandbox`) — computer-use surface: terminal + files + browser sharing ONE
  session via the chat`s own `chatId`; `onAskPage` bridges page text back into chat (existing
  `setBigTab("none")`+`setMode("chat")`+`send` path).
- **Инструменты** (sub-tab `tools`) — MCP / skill marketplace; install wired to the existing
  `addSkill` store, `installedSkillNames` derived from live `skills` state (skill-badge surface).
- **Оценки** (sub-tab `evals`) — loop eval harness (embedded), small local store.

### Files
- `taiga-web/src/components/run-sandbox.tsx` (NEW, 774 lines) — sandbox/computer-use surface.
- `taiga-web/src/components/tool-marketplace.tsx` (NEW, 1045 lines) — MCP/skill marketplace.
- `taiga-web/src/components/loop-evals.tsx` (NEW, 1037 lines) — loop eval harness + store.
- `taiga-web/src/components/chat.tsx` (MOD, +39/-2): imports (L46-48); `agentSub` union extended with
  `sandbox|tools|evals` (L576); three motion-pills `Песочница`/`Инструменты`/`Оценки` in the Agent
  sub-nav; three render branches (L5744-5775; former `truth` else-fallback made explicit).

### UI reachable
- Agent tab → sub-nav pills `Песочница` / `Инструменты` / `Оценки`, alongside the existing
  Режимы/Автоматизации/Задачи/Прогоны/Ralph/Источник-правды pills.

### Checks (all green)
- `npx tsc --noEmit` (taiga-web) ........... green  exit 0  (whole project clean)
- `GET 127.0.0.1:3000/app` ................ green  200
- backend untouched this wave (no server.py change, no restart needed)

### Binary lines
- sandbox surface (Песочница) ............. done  fe 4f8a8c7  (run-sandbox.tsx)
- MCP/skill marketplace (Инструменты) ..... done  fe 4f8a8c7  (tool-marketplace.tsx)
- eval harness (Оценки) ................... done  fe 4f8a8c7  (loop-evals.tsx)
- chat.tsx integration (3 sub-tabs) ....... done  fe 4f8a8c7  (imports + agentSub + pills + branches)
- tsc --noEmit (taiga-web) ................. green  exit 0
- GET /app ................................ green  200
- pushed (taiga-web) ...................... done  fe 4f8a8c7 main
- pushed (root bump) ...................... done  this commit (root gitlink → 4f8a8c7) main

---
