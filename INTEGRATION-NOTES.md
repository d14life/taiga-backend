# INTEGRATION NOTES — handle at merge (coordinator, 2026-06-12)

Captured from Damir's live testing while the 4-worker fleet runs. Resolve these when merging lanes:

## agent-builder.tsx — relay/brain config ALREADY EXISTS
- `src/components/agent-builder.tsx` is the "Агент Тайга ИИ" builder with 🔻ведущий + 🔺эксперт model pickers (lines ~126/137). This IS the relay/brain configuration. The chat-core worker was asked to build "brain settings" — at merge, REUSE/extend this existing builder, do NOT duplicate. If both chat-core and panels touched agent-builder.tsx → resolve to one coherent version.
- **BUG (Damir screenshot):** the model-picker dropdown inside agent-builder is CLIPPED — "can't see the full list." Cause: dropdown rendered inside a modal with `overflow-hidden` (line ~66) / `overflow-y-auto` (line ~86). FIX per dropdown rule: render the dropdown via portal / `position: fixed` / native popover so it escapes the overflow container, OR make the list its own scroll area with a sane max-height that fits within the modal. Verify the FULL model list (Gemini/Mistral/Venice/Другие модели/…) is scrollable and visible.
- Surface a one-tap entry to this relay config from the composer "Мозг" toggle (so "change brain" is reachable without digging).

## LANE STATUS + DEFERRED WIRING (resolve at merge)
- ✅ `lane/memory` — MERGED to main.
- ✅ `lane/studio` (c9abe63) — image-studio.tsx only (music model picker, 3D down-state). Conflict-free.
- ✅ `lane/panels` (cb6ca26) — settings-panel.tsx + NEW theme-panel.tsx, voice-pref.ts. Added theme picker, MCP-in-settings, voice prefs, skills/auto-mem entries as OPTIONAL props.
  - **DEFERRED → must wire into chat.tsx at merge:**
    1. `<SettingsPanel onOpenSkills={() => { setSettingsOpen(false); setSkillOpen(true); }} />` (mirror onOpenMaster).
    2. `<SettingsPanel memAuto={memoryAuto} onMemAuto={toggleMemoryAuto} />` (existing state ~chat.tsx:1655).
    3. Voice consume: chat.tsx `loadVoicePref()` → pass `sttLang` into `useVoiceInput(onText, lang)` + if `autoSpeak` call `generateAudio` on completed replies.
  - **CONFLICT WATCH:** GAP-MAP fix #1 (brain config) was mapped to settings-panel.tsx but panels OWNS that file. If chat-core also edited settings-panel.tsx → resolve. (chat-core was scoped to chat.tsx; likely put brain config in chat.tsx instead — verify.)
- ⏳ `lane/chatcore` — running (chat.tsx: brain config, durable-delete tombstone, dead pills).
- ✅ `lane/sqlite` (3cf9d5d) — server.py: 12 JSON stores → SQLite (`BASE/db/taiga.db`, WAL, RLock), boot-migration idempotent, JSON kept as backup, tests green. Built on top of merged memory work.
  - **⚠️ RESTART RULE:** at final restart, STOP the old server first, THEN start new (clean single restart). Do NOT run old+new concurrently — old writes JSON, new writes SQLite; concurrent = lost writes. First boot migrates JSON→SQLite once (slightly slower boot).

## NEW QA DIRECTION (Damir): test USER behavior, not just SYSTEM
- Smoke (tsc/parse/curl) checks the system compiles/responds. Damir wants USER-level: does each feature actually DO what a person expects when they click. Build a ~200 user-case matrix (user action → expected behavior → verify) covering EVERY feature, then run each against the live app. This becomes the real "v1 done" gate (all user-cases green), replacing smoke-only.
