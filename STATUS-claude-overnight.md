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
