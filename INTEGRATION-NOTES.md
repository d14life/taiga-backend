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

## 🔴 NEXT WAVE (Damir, high-pri): MULTI-MODEL config for Brain + Council (not basic settings!)
Brain & Council are MULTI-model functions — their config windows must expose proper MODEL PICKERS, not the generic single-model/output basic settings currently shown. Compare already does it right (ComparePicker, up to 5) — COPY that pattern. Launch the moment chat.tsx (chat-polish) + server.py (be2) free up.
- **Brain config (chat.tsx brain popover):** add a **ведущий/lead model picker** (backend `driver`) + an **эксперт/expert model picker** (backend `model`/`expert`). Keep show-steps. Currently only a "выбранная/умная" toggle — replace/augment with explicit 2-model selection.
- **Council config:** replace basic settings with: **number of models (2–5)** + **WHICH models (multi-select, mirror ComparePicker)** + **synthesizer model**. Backend: add `councilModels` support to `chat_council` (mirror how `chat_compare` honors `compareModels`). Frontend: pass `councilModels` through dispatchSend→request body.
- **Research config (tailored, NOT generic):** depth (быстро/средне/глубоко) + number of sources + synthesis model. The research flow is WEB-SEARCH (Sonar/Exa/Brave/Linkup → facts+sources+synth), NOT multi-model — so its config must NOT look like Council's. Generic model/length/temp is wrong here.
- **PRINCIPLE:** each function's config window must be TAILORED to what the function does (Council=multi-model, Research=depth/sources, Brain=2-model lead+expert, Compare=already-right). Not a shared generic FuncConfigPopover for differentiated functions. Keep the generic one only for the plain effort modes (Fast/Expert/Heavy).
- Files: `chat.tsx` (brain+council+research popovers, owns), `server.py` (`chat_council` councilModels + research depth/sources params), `use-taiga-chat.ts` (pass councilModels/depth). All currently busy → queue.

## NEW QA DIRECTION (Damir): test USER behavior, not just SYSTEM
- Smoke (tsc/parse/curl) checks the system compiles/responds. Damir wants USER-level: does each feature actually DO what a person expects when they click. Build a ~200 user-case matrix (user action → expected behavior → verify) covering EVERY feature, then run each against the live app. This becomes the real "v1 done" gate (all user-cases green), replacing smoke-only.
