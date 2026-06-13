# Тайга — build backlog (Damir drives; this file = source of truth, resume from here)

## ▶ START HERE (fresh session)
Repo: /Users/damir12/Downloads/claude-sessions/2026-06-10/mostik-ai/ · backend: `python3 server.py` :8777
State (2026-06-13): 11 commits landed (Agent S identity, phantom-guard, native dial+token budget,
benchmark "ум" matrix + per-task routing, Beam=Council merge, multi-engine memory/effort inheritance,
model-picker sort, cost-tiers backend). WHATS-NEW.md = the casual changelog. Read it + this file, then grind.
ALSO read ARCH-DECISIONS.md — Damir-approved exec-hosting (HYBRID: browser-WASM free + cloud sandbox-per-user
paid), full-skills spec (L12: import folder+scripts, run sandboxed, auto-trigger, model-agnostic), agent-envs (L15).
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
Priority: L12 · L18 · L15 · L16 · L14 · L3 · L21 · L22

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
- [x] L23 NO MID-ANSWER TRUNCATION + budget-aware routing — DONE (server.py + taiga-web f150c54).
        PRINCIPLE: a cap shapes the PLAN (which model / continue-or-not), it NEVER chops the output.
        (a) AUTO-CONTINUE: capture finish_reason in venice_stream; if "length" (answer cut), auto-issue a
            continuation (append assistant partial + "продолжи ровно с места обрыва") and stitch seamlessly
            → user NEVER sees a cut sentence. 16k stays a per-CHUNK ceiling, not an answer limit.
        (b) GRACEFUL COST DEGRADATION: sendEstimate already estimates cost pre-flight. If it would exceed the
            user's spend-cap/balance, DON'T cut/block — route to a cheaper model that fits (cost_tier via
            best_for_task, the L4a backend) and answer FULLY but cheaper, told transparently
            ("большой запрос — отвечаю моделью X в рамках бюджета"). No truncation, ever.
        VERIFIED: (a) venice_stream auto-continues on finish_reason=='length' → 64-tok chunk cap produced a
        6239-char answer — BUT that run didn't truly test continue (model ignored the cap); FIXED a latent
        NameError (_max_continues was undefined) in commit w/ L6 and RE-VERIFIED PROPERLY: cap=120 → 1164-char
        COMPLETE answer via multi-round continue, clean ending, no error. (b) non-owner max_spend=0.003 → opus→deepseek-v4-
        pro-cheaper + transparent meta.note (shown in UI). (a) live for ALL; (b) for billed users only
        (owner = free opus → not budget-limited; taiga-web currently sends user=default=owner → (b) dormant).
- [x] L4a TIERS (Damir): BACKEND (1a1ad02) + UI CHIP (taiga-web 3bcc8eb). cost_tier(model) +
        best_for_task(task,tier) wired into auto + auto-Brain; tier_cost per model. UI: cycling "цена:"
        chip (любая/дёшево/средне/топ) on the pad next to "ответ:" → req.tier (SendOpts→baseBody→proxy
        allow-list). VERIFIED via proxy: cheap+code → deepseek-v4-pro-cheaper, mid → grok, top → opus.
- [x] L4d Beam=Council merge: Council always uses fusion-critic synthesis; Beam absorbed.  (d02a073)
        VERIFIED taxonomy: Brain=triage/one-leads · Council=N deliberate→fuse · Heavy/Research=single-model.
- [x] L4b POWER SYSTEM — CORE DONE (taiga-web b094267): 5-dot ГЛУБИНА-slider replaces Fast/Auto/Expert/Heavy
        pills; maps to effort + NATIVE reasoning_effort (L1 fast…L5 max). Heavy/Brain DECOUPLED (the CRITICAL
        bug), Solo/Brain/Council = mode axis, "ответ:" chip = output length, Слияние button dropped. VERIFIED
        live (5 dots, persists, proxy forwards reasoning_effort, no console errors). (Optional polish left:
        discrete one-tap Fast/Heavy/Deep chips — slider ends already ARE Fast/Deep; Heavy = output «ответ: макс».)
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
        CRITICAL (Damir, resolved): there are only TWO power dials + the mode axis — DON'T make 3 overlapping:
          • DIAL 1 THINKING DEPTH = the 5-level slider (Faster←→Smarter). Fast = level 1, DEEP = level 5.
            So Fast/Deep are NOT separate controls — they're SHORTCUTS that jump the slider (redundant otherwise).
          • DIAL 2 OUTPUT LENGTH = short←→long. HEAVY lives here (long/thorough output). Different dimension
            than thinking. Combinable: Deep+Heavy = thinks hard AND writes long.
          • MODE axis = Solo/Brain/Council (how MANY models). Heavy ≠ Brain. Today Heavy SECRETLY === Brain
            (the bug). Fix: Heavy = output dial only; Brain = mode. All axes combinable.
          Preset caps (Fast≈300w etc.) are DEFAULTS the user can override.
        NOTE: temperature already forwards main path (comment fixed 63fc8b8); pipeline-step temp = todo.
- [x] L4e Multi-engine heads inherit main-pad spec + see chat memory (Damir).  (90daf3e)
        Council members/Brain-expert now get the FULL chat history (memory), inherit effort
        (deep→reasoning_effort, gated), scaled token budget, + optional per-head master prompt
        (memberPrompts). venice_complete += reasoning_effort. Heads work independent → then fuse.
- [x] L4c BRAIN = ORCHESTRATOR — DONE (server.py best_n_for_task + taiga-web 6c44231; VERIFIED experts=2 →
        opus+deepseek-v4-pro ran as council_step then fused). Brain's lead doesn't just delegate to ONE expert — it
        ORCHESTRATES MULTIPLE models like the agent feature (manager → directs N specialists, hierarchical).
        This is the clean split vs Council (Council = N equals deliberate→fuse, flat). Lead breaks the task,
        routes pieces to best-for-task models (in the chosen tier), combines. Editable lead + per-model
        master prompts; count = L19 (how many models it orchestrates). Each model inherits pad + chat memory.
- [x] L4f Multi-engine UI — DONE (taiga-web b23a797): per-head master-prompt textarea in Совет popover
        (→ memberPrompts[], backend applies per head); each head's MODEL shown as "Совет: <model>" steps
        (covers brain-orchestrator experts too via L4c council_step). SHOW which model each head uses, per-head
        master-prompt editor, heads visibly obey the main pad (Auto/Deep/Fast/tier). "independent→together".
- [x] L17 Model-picker SORT: Мощнее (benchmark) / Новые (created) / Дешевле (per1k).  (fe 99ce78d / 58157dd)
        Picker already had the 4 layers as filters (type tabs Зрение/Код/Рассужд · uncensored/private/cheap
        toggles · 3 privacy groups). Code/Uncensored stay as mode buttons AND live as picker filters.
- [ ] L18 Picker categorization polish (Damir's "4 layers"): make type (uncensored/code/thinking/vision/voice)
        × cost × privacy fully browseable + label each model's layers clearly.
- [x] L19 BRAIN output-count — DONE (taiga-web 6c44231: "Сколько экспертов" 1/2/3 selector in Brain popover →
        req.brainExperts). req.brainExperts (1-3, default 1). =1 → current (driver→1 expert).
        >1 → driver triages, then runs the N best-for-task experts in parallel, fuses with BEAM_FUSION_PROMPT
        (reuse council fusion). UI: "выходных моделей" count selector in Brain controls. Each expert inherits
        pad spec + sees chat memory (L4e already wires venice_complete effort/context).
- [x] L20 COUNCIL total-count — DONE (taiga-web a0f6234): «всего N» stepper next to Совет (auto, no explicit
        members) → req.n; persisted. VERIFIED live (steps 3→4, persists). backend already reads req.n (2-5, default 3). Add frontend count
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
- [x] L6 ChatGPT-style thinking display — DONE (server.py reasoning_cb + taiga-web 7ffe7ae): venice_stream
        surfaces reasoning_content on a SEPARATE channel → SSE {type:"reasoning"} → collapsible «Думает…/
        Подумал Nс» box, not mixed into the answer. VERIFIED: thinking model → 172 reasoning events. Original ask:
        capture reasoning_content from stream → separate SSE
        channel → collapsible "Думает…→Подумал Nс" box (empty-safe for models w/o trace).
- [x] L7 Verify-against-reality button — DONE (taiga-web b075d9a): per-answer «проверить» → web-search the
        question + strict fact-checker model → verdict ✅/⚠️N/❌ + fixes (reuses super-search + ultra). Covers:
        hallucination(vs web) + chat-drift + memory-vs-reality;
        verdict ✅/⚠️N/❌ + fixes. Reuse BEAM_FUSION_PROMPT + tool_web_search. (no name-stamp check)
- [x] L8 Memory-write frequency — DONE (taiga-web f3290d0): 1-8 slider «как часто запоминать» in memory
        panel → раз в N ответов (taiga.mem.every); extraction effect gates on it + widens window. Verified cold.
        Original: expose consolidation cadence as a user setting + UI slider.
- [x] L9 User hooks per chat — DONE (taiga-web dd3ad40): «хуки» button → HooksPanel (trigger substring +
        action-prompt, ✨ AI-help via /api/improve, per-chat taiga.hooks.<id>); matched hooks inject into
        system via composeSystem. VERIFIED live (add hook → persists). chat-settings → create hook (trigger + action-prompt + AI-help btn).
- [x] L10 Projects — CORE DONE (taiga-web 871a26a + a519b36): folders = ПРОЕКТЫ с общими instructions
        (folderInstrBlock → composeSystem грунтует все чаты папки); «проект» кнопка+модалка когда чат в папке;
        features.ts soon→live. VERIFIED live (сейв персистит в taiga.folders). Group chats✓ + instructions✓;
        shared FILES + shared MEMORY проекта = следующий слой (на существующих files/RAG + memory).
- [x] L11 Voice hands-free — DONE (taiga-web 2c98677): continuous loop ALREADY built (handsfree→autoSpeak,
        onSpeechEnd→submit, rearmMic on TTS end; free Google TTS + browser STT + paid nanogpt). ADDED premium
        voice dropdown: ElevenLabs BYOK (key in settings, direct browser call, graceful fallback to free).
        (Cartesia addable identically.) continuous listen→answer→speak loop on free stack (NanoGPT TTS +
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
