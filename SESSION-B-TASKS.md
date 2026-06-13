# SESSION B — task assignment (parallel to the active build session A). 2026-06-13.

Repo: /Users/damir12/Downloads/claude-sessions/2026-06-10/mostik-ai/ · PRODUCT = taiga-web React (:3000 /app).
Read DAMIR-REQUESTS.md + ARCH-DECISIONS.md first. Backend = server.py (:8777, shared). Test before commit
(tsc for frontend, ast.parse+import for backend). Casual line to WHATS-NEW.md per feature.

## ⛔ HARD COLLISION RULE — session A owns these, NEVER touch them:
   server.py · taiga-web/src/components/chat.tsx · depth-slider.tsx · LANES.md
   (A is building L4b power-slider + L4c/L19/L20/L4f/L6 in those files. Editing them = clobber.)
   → You work in NEW FILES ONLY. Backend logic → put in a NEW module (e.g. taiga_extras.py) with your
     endpoints/functions; leave a one-line "WIRE-ME" note at the bottom of SESSION-B-TASKS.md for A to
     import + route it later (A does the single server.py wiring line at a pause — not you).
   → Before each commit: `git log --oneline -2`; if A committed, `git pull`-equivalent (you're same repo,
     just re-read) and rebase your new files on top. New files don't conflict; just don't touch A's files.

## YOUR LANES (all NEW-file, isolated from A):
- L18 PICKER POLISH — taiga-web/src/components/model-picker.tsx is YOURS (A isn't on it). 4-layer browse:
    type (uncensored/code/thinking/vision/voice) × cost (tier_cost field exists) × privacy (privacy field).
    Label each model's layers clearly. Pure frontend, backend fields already exist. SAFE/CLEAN — do first.
- L7 VERIFY-AGAINST-REALITY button — NEW component verify-panel.tsx + NEW backend module verify_api.py
    (reuse BEAM_FUSION_PROMPT + tool_web_search ideas; checks: hallucination vs web · chat-drift · memory
    vs reality → ✅/⚠️N/❌ + fixes). Component is new; the button mount in chat.tsx = leave a WIRE-ME note.
- L9 USER HOOKS per chat — NEW hook-builder.tsx + NEW module hooks_api.py (trigger + action-prompt +
    AI-help button to co-write the prompt). New files only.
- L11 VOICE hands-free — NEW voice-mode.tsx (continuous listen→answer→speak; browser STT via existing
    use-voice-input.ts + existing /api/tts; premium voice dropdown later). New component; mount = WIRE-ME.
- L10 PROJECTS — NEW project store module + NEW projects-panel.tsx (group chats + shared files +
    instructions + shared cross-chat memory). Big; new files; sidebar mount = WIRE-ME note.

## ORDER: L18 (cleanest) → L7 → L9 → L11 → L10.
## A handles: L4b, L4c, L19, L20, L4f, L6, L3, L12, L15 (server.py/chat.tsx-heavy). NEW-1 kill :8777 = A (server.py).

## WIRE-ME (one-line server.py/chat.tsx hooks for A to add at a pause):
   (B appends here as it finishes each new module/component, e.g.:
    - import verify_api + route POST /api/verify
    - mount <VerifyPanel/> + <VoiceMode/> in chat.tsx)
