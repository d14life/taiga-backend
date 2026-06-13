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
Priority: L4a-ui · L23 (no-truncation/budget-routing) · L4b · L4c · L19 · L20 · L4f · L6 · L7 · L8 · L9 · L10 · L11 · L12 · L18 · L15 · L16 · L14 · L3 · L21 · L22

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
- [ ] L23 NO MID-ANSWER TRUNCATION + budget-aware routing (Damir — HIGH priority, core output UX).
        PRINCIPLE: a cap shapes the PLAN (which model / continue-or-not), it NEVER chops the output.
        (a) AUTO-CONTINUE: capture finish_reason in venice_stream; if "length" (answer cut), auto-issue a
            continuation (append assistant partial + "продолжи ровно с места обрыва") and stitch seamlessly
            → user NEVER sees a cut sentence. 16k stays a per-CHUNK ceiling, not an answer limit.
        (b) GRACEFUL COST DEGRADATION: sendEstimate already estimates cost pre-flight. If it would exceed the
            user's spend-cap/balance, DON'T cut/block — route to a cheaper model that fits (cost_tier via
            best_for_task, the L4a backend) and answer FULLY but cheaper, told transparently
            ("большой запрос — отвечаю моделью X в рамках бюджета"). No truncation, ever.
- [~] L4a TIERS (Damir): BACKEND DONE (1a1ad02) — cost_tier(model) + best_for_task(task,tier) wired into
        auto + auto-Brain; tier_cost exposed per model. REMAINING: UI tier-selector chip (cheap/mid/top)
        on the main pad → send req.tier. "best CHEAP model for this code task" works (deepseek-v4 bench 95).
- [x] L4d Beam=Council merge: Council always uses fusion-critic synthesis; Beam absorbed.  (d02a073)
        VERIFIED taxonomy: Brain=triage/one-leads · Council=N deliberate→fuse · Heavy/Research=single-model.
- [ ] L4b POWER SYSTEM = 5-level slider + Fast/Heavy/Deep presets (Damir, updated — HIGH).
        CURRENT muddle (verified): Expert = deep single model; Heavy = secretly Brain (2 models), mislabeled
        "совет". Replace with this clean design:
        • EFFORT/OUTPUT = a 5-LEVEL slider (Claude-Code cheap/mid/max idea but 5 steps; screenshot's 5 dots),
          chip next to model ("Opus 4.8 · Medium"). Maps to reasoning_effort (low/med/high→native dial,
          backend-ready) + token/output budget.
        • QUICK PRESETS Fast · Heavy · Deep — one-tap, each bundles effort + OUTPUT + routing:
            Fast  = fast, SHORT output preset (~300 words, request-dependent), cheap/fast model.
            Heavy = thorough, more compute + longer output.
            Deep  = deep thinking, ROUTED to models that natively accept it (GPT/Gemini — measured to honor
                    reasoning_effort) using their REAL native reasoning (use best_for_task + model_reasons).
        • Each preset ALSO controls output length (presets carry output caps). Native routing: Deep/thinking
          → only reasoning-capable models, real dial not faked.
        Also: drop separate "Слияние" button (== Совет); "more engines" (Brain/Council) = MODE, not effort.
        CRITICAL (Damir asked twice): Heavy ≠ Brain. TWO INDEPENDENT AXES:
          • EFFORT axis = Fast/Heavy/Deep + 5-slider → how hard ONE model works + output length (single model).
          • MODE axis   = Solo/Brain/Council → how MANY models + how they combine.
          Today Heavy SECRETLY turns on Brain (===, the bug). Fix: Heavy stays ONLY on the effort axis
          (1 model, thorough, long). Brain is the MODE. They must be combinable (Brain+Heavy = 2 models each
          working hard). Output caps per preset are DEFAULTS — user can override them.
        NOTE: temperature already forwards main path (comment fixed 63fc8b8); pipeline-step temp = todo.
- [x] L4e Multi-engine heads inherit main-pad spec + see chat memory (Damir).  (90daf3e)
        Council members/Brain-expert now get the FULL chat history (memory), inherit effort
        (deep→reasoning_effort, gated), scaled token budget, + optional per-head master prompt
        (memberPrompts). venice_complete += reasoning_effort. Heads work independent → then fuse.
- [ ] L4c BRAIN = ORCHESTRATOR (Damir, updated): Brain's lead doesn't just delegate to ONE expert — it
        ORCHESTRATES MULTIPLE models like the agent feature (manager → directs N specialists, hierarchical).
        This is the clean split vs Council (Council = N equals deliberate→fuse, flat). Lead breaks the task,
        routes pieces to best-for-task models (in the chosen tier), combines. Editable lead + per-model
        master prompts; count = L19 (how many models it orchestrates). Each model inherits pad + chat memory.
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
        SESSION-LEVEL (Damir): a NEW chat can START as a full agent session depending on SETTINGS (setting
        "new chats = agent mode" → the whole session orchestrates models+tools multi-step from msg 1, not
        just per-message). Brain-orchestrator (L4c) is the per-turn version; this is the whole-session version.
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
