# SESSION B — ISOLATED WORKTREE (L13 pattern). 2026-06-13.

## ▶ YOU ARE HERE: /Users/damir12/Downloads/claude-sessions/2026-06-10/mostik-ai-B/  (an isolated git worktree)
Branches: `session-b` (parent: server.py etc.) · taiga-web on `session-b-fe`. node_modules is symlinked → tsc works.
Backend test: use `python3 -c "import ast;ast.parse(open('server.py').read())"` + import — do NOT run a 2nd
server on :8777 (the main one is there). PRODUCT frontend = taiga-web React. Read DAMIR-REQUESTS.md + ARCH-DECISIONS.md.

## ✅ FULL ISOLATION — edit ANY file here (server.py, chat.tsx, anything) without touching session A.
   This is YOUR copy. Session A works in the OTHER dir (.../mostik-ai/). You never see each other live.
   → To keep the eventual MERGE clean: stay on YOUR lanes (below) — different FEATURES than A
     (A = power-slider / Brain / Council / effort). Different features = different code regions = clean merge.
   → Avoid A's active areas: depth-slider, the effort/Brain/Council code paths.

## YOUR LANES (build end-to-end; full files OK since isolated):
- L18 PICKER POLISH — model-picker.tsx: 4-layer browse type×cost×privacy (fields exist: tier_cost, privacy, kind). FIRST.
- L7 VERIFY-AGAINST-REALITY button — new verify-panel.tsx + /api/verify (reuse BEAM_FUSION_PROMPT + tool_web_search):
    checks hallucination(vs web) · chat-drift · memory-vs-reality → ✅/⚠️N/❌ + fixes.
- L9 USER HOOKS per chat — hook-builder.tsx + /api/hooks (trigger + action-prompt + AI-help button).
- L11 VOICE hands-free — voice-mode.tsx (continuous listen→answer→speak; browser STT use-voice-input.ts + /api/tts).
- L10 PROJECTS — project store + projects-panel.tsx (group chats + shared files + instructions + cross-chat memory). BIG.
ORDER: L18 → L7 → L9 → L11 → L10.

## WORKFLOW (harness discipline):
1. Build a lane end-to-end. TEST: ast.parse + import for backend; `cd taiga-web && npx tsc --noEmit` for frontend.
2. Commit: backend → `git commit` on session-b; frontend → `cd taiga-web && git commit` on session-b-fe.
3. Casual line to WHATS-NEW.md. Next lane.
4. When ALL your lanes done → post "session-b done". Damir/A will MERGE.

## MERGE PLAN (for whoever merges, later):
   (from main .../mostik-ai): git merge session-b   (resolve server.py conflicts — small, different features)
   cd taiga-web && git merge session-b-fe ; then `git add taiga-web` + pointer commit in parent.
   Then `git worktree remove ../mostik-ai-B` (+ `cd taiga-web; git worktree remove ../../mostik-ai-B/taiga-web`).
