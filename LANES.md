# Тайга — build backlog (Damir drives; this file = source of truth, resume from here)

## ▶ START HERE (fresh session)
Repo: /Users/damir12/Downloads/claude-sessions/2026-06-10/mostik-ai/ · backend: `python3 server.py` :8777
State (2026-06-13): 11 commits landed (Agent S identity, phantom-guard, native dial+token budget,
benchmark "ум" matrix + per-task routing, Beam=Council merge, multi-engine memory/effort inheritance,
model-picker sort, cost-tiers backend). WHATS-NEW.md = the casual changelog. Read it + this file, then grind.
ANOTHER claude session may also work this repo — collision-guard before EVERY edit.

## RUN PROTOCOL (each turn = one lane, harness discipline)
1. COLLISION GUARD first: `git log --oneline -3` + `find . -name '*.py' -o -name '*.tsx' -mmin -3` (excl node_modules).
   Other session committed new / writing files → wait 90s, recheck, don't edit.
2. Pick the next unchecked lane (priority order below). Build end-to-end (backend + a VISIBLE UI control).
3. TEST before commit: backend = `python3 -c "import ast;ast.parse(open('server.py').read())"` + import + live curl;
   frontend = `npx tsc --noEmit`. MEASURE, never claim. taiga-web/AGENTS.md: modified Next.js 16 — read its docs.
4. Commit per-lane to main (taiga-web is NESTED git: commit inside it, then `git add taiga-web` + pointer commit).
   Tick the checkbox here. Restart backend if server.py changed.
5. Append ONE casual plain-English line to WHATS-NEW.md: "✨ <feature> — <what it does for the user>".
Rules: NEVER auto-pick dead models. server.py edits sequential. L13 BLOCKED on Damir's harness repo link = skip.
Priority: L4a-ui · L4b · L4c · L19 · L20 · L4f · L6 · L7 · L8 · L9 · L10 · L11 · L12 · L18 · L15 · L16 · L14 · L3 · L21 · L22

## DONE (committed)
- [x] L0 Agent S identity rename + name-stamp fix + default-leak fix        (5f8c24e)
- [x] L0 Phantom-guard: per-model store, _first_live, probe-cron            (5f8c24e)
- [x] L1 Native thinking-effort dial (reasoning_effort, capability-gated)   (ce7c77d)
- [x] L1 Per-model token budget (reasoning_token_floor)                     (ce7c77d)
- [x] L2 Smart-score fix: \bmini\b boundary (Gemini/MiniMax were "ум 28")   (e965962)

## ENGINE (backend, sequential — shared server.py)
- [x] L5 Benchmark intelligence matrix (_BENCH per-task) replaces string-heuristic "ум".  (1df02af)
        detect_task + best_for_task; auto-Brain expert now task-aware. MiniMax 28→94, Gemini→96.
- [ ] L3 reasoning dial: for models that IGNORE reasoning_effort (grok-nano, deepseek),
        try alternate params (reasoning:{effort}, thinking, extra_body); measure low-vs-high;
        store per-model which param actually deepens. Fall back to prompt-nudge + token floor.
- [~] L4a TIERS (Damir): BACKEND DONE (1a1ad02) — cost_tier(model) + best_for_task(task,tier) wired into
        auto + auto-Brain; tier_cost exposed per model. REMAINING: UI tier-selector chip (cheap/mid/top)
        on the main pad → send req.tier. "best CHEAP model for this code task" works (deepseek-v4 bench 95).
- [x] L4d Beam=Council merge: Council always uses fusion-critic synthesis; Beam absorbed.  (d02a073)
        VERIFIED taxonomy: Brain=triage/one-leads · Council=N deliberate→fuse · Heavy/Research=single-model.
- [ ] L4b Mode taxonomy cleanup (Damir-confirmed): Heavy = SINGLE-model max-intensity mode (NOT Brain);
        Research = single-model deep. Drop the separate "Слияние" UI button (now == Совет). Effort =
        Fast/Normal/Deep pure intensity; Fast suppresses auto-Brain (user authority).
- [x] L4e Multi-engine heads inherit main-pad spec + see chat memory (Damir).  (90daf3e)
        Council members/Brain-expert now get the FULL chat history (memory), inherit effort
        (deep→reasoning_effort, gated), scaled token budget, + optional per-head master prompt
        (memberPrompts). venice_complete += reasoning_effort. Heads work independent → then fuse.
- [ ] L4c BRAIN = 2× (Damir): Brain stays its own architecture (driver triages → ONE expert). Double
        master prompts (both editable), double tier-cost. On auto: pick the 2 best-for-task in the tier.
- [ ] L4f Multi-engine UI: SHOW which model each head uses (per Damir "needs to be shown"), per-head
        master-prompt editor, heads visibly obey the main pad (Auto/Deep/Fast/tier). "independent→together".
- [x] L17 Model-picker SORT: Мощнее (benchmark) / Новые (created) / Дешевле (per1k).  (fe 99ce78d / 58157dd)
        Picker already had the 4 layers as filters (type tabs Зрение/Код/Рассужд · uncensored/private/cheap
        toggles · 3 privacy groups). Code/Uncensored stay as mode buttons AND live as picker filters.
- [ ] L18 Picker categorization polish (Damir's "4 layers"): make type (uncensored/code/thinking/vision/voice)
        × cost × privacy fully browseable + label each model's layers clearly.
- [ ] L19 BRAIN output-count (Damir): req.brainExperts (1-3, default 1). =1 → current (driver→1 expert).
        >1 → driver triages, then runs the N best-for-task experts in parallel, fuses with BEAM_FUSION_PROMPT
        (reuse council fusion). UI: "выходных моделей" count selector in Brain controls. Each expert inherits
        pad spec + sees chat memory (L4e already wires venice_complete effort/context).
- [ ] L20 COUNCIL total-count (Damir): backend already reads req.n (2-5, default 3). Add frontend count
        selector (2-5) for AUTO council (when no explicit councilModels picked) → send req.n. UI: "всего
        моделей" stepper near the council members popover (chat.tsx ~3982).

## AGENTIC (from the harness repos — Damir: "main agentic feature", be a professor)
# walkinglabs/learn-harness-engineering: model smart, harness reliable. 5 subsystems = Instructions/
# State/Verification/Scope/Session-lifecycle. YennNing/Awesome-Code-as-Agent-Harness: code = executable
# stateful substrate; multi-agent = collaborative-synthesis/critique-repair/adversarial/debate.
- [ ] L15 Тайга Agent = "think like Council, act like agent", HARNESSED:
        THINK→multi-model deliberation (propose→critique-and-repair→adversarial→fuse) ·
        ACT→typed tools as code-as-action (inspectable/reversible) · VERIFY→run it, only passing checks=done ·
        STATE→memory layering (working/semantic/experiential/long-term) + resumable progress ·
        SCOPE→one sub-goal at a time, explicit done. Build on existing agent-mode + tools + council.
- [ ] L16 Harden MY build-loop with the 5 subsystems (LANES=feature-list, verify-before-commit, scoped).

## PRODUCT UI (backend + frontend, each needs a visible button)
- [ ] L6 ChatGPT-style thinking display: capture reasoning_content from stream → separate SSE
        channel → collapsible "Думает…→Подумал Nс" box (empty-safe for models w/o trace).
- [ ] L7 Verify-against-reality button: hallucination(vs web) + chat-drift + memory-vs-reality;
        verdict ✅/⚠️N/❌ + fixes. Reuse BEAM_FUSION_PROMPT + tool_web_search. (no name-stamp check)
- [ ] L8 Memory-write frequency: expose consolidation cadence as a user setting + UI slider.
- [ ] L9 User hooks per chat: chat-settings → create hook (trigger + action-prompt + AI-help btn).
- [ ] L10 Projects: group chats + shared files + instructions + memory (features.ts "soon"→live).
- [ ] L11 Voice hands-free mode: continuous listen→answer→speak loop on free stack (NanoGPT TTS +
        browser STT), dedicated voice UI; premium voice dropdown (Cartesia/ElevenLabs BYOK).
- [ ] L12 Skills→real: bundle runnable steps, auto-trigger skill search in normal chat, richer builder.

## NEW BIG (Damir-requested this session)
- [ ] L13 Parallel agents (Chad-like): spin N isolated agents (worktrees) → merge clean back.
        IN THE PRODUCT (studio/agents). Needs the agentic-harness repo link from Damir.
- [ ] L13 Parallel agents (Chad-like): BLOCKED — needs Damir's agentic-harness repo link. SKIP for now.
- [ ] L14 Ad-generator (Arcads-like): one product in → AI-avatar UGC video ads out, in Studio.
        Ref: github.com/krusemediallc/arcads-claude-code. Uses existing video/avatar catalog.

## EXPLORATORY (lower priority — Damir discussed as "can we")
- [ ] L21 Real-time screen co-pilot: getDisplayMedia() → periodic frames → vision → "press here" guidance
        bubble (+ optional voice). Build on existing vision + camera capture.
- [ ] L22 Store/reference web videos: fetch video → transcribe (whisper) + sample frames (vision) → RAG →
        reference later in chat. Pipeline on existing RAG + vision + whisper.

## Note: L13 appears twice intentionally (also in NEW BIG) — both BLOCKED on the repo link.
