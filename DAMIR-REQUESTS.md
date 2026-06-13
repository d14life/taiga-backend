# Damir's requests — authoritative record (for the build session). 2026-06-13.

PRODUCT = taiga-web React on :3000 (route /app). index.html (:8777) = LEGACY, to be killed (see NEW-1).
Backend server.py is SHARED. Most items below are ALREADY in LANES.md as lanes + being built. This file
consolidates EVERY request Damir made + adds the new ones. Cross-refs to LANES lane IDs.

## ✅ ALREADY BUILT (confirmed in code)
- Agent S identity + name-stamp fix + default-leak fix (L0)
- Phantom-guard: never auto-pick a dead model, probe-by-calling, self-heal (L0)
- Native "Deep" dial (real reasoning_effort on GPT/Gemini) + per-model token budget (L1)
- Benchmark "ум" matrix + best-model-per-task auto-routing (MiniMax 28→94) (L5)
- Cost-tiers cheap/mid/top + "цена" chip + best-in-budget (L4a)
- Beam = Council merge (fusion-critic, dehallucinate) (L4d)
- Multi-engine heads inherit pad + see chat memory + per-head master prompt (L4e)
- Model-picker sort (Мощнее/Новые/Дешевле) (L17)
- No mid-answer truncation (auto-continue) + budget-aware routing (L23) — shipped by build session
- Temperature forwards on main path (fixed)
- MEMORY (verified built): caching, auto_compact, sleep-time consolidate, RAG (per-chat workspace),
  episodic recall (search past chats /api/recall), granular facts + tombstones + budget knobs
- PER-CHAT CUSTOMIZATION (verified built): chat-memory, master-prompt-panel, prompts-panel, artifacts
- MCP CONNECTORS (verified built): full client + catalog + mcp-panel UI + agent integration

## 🔨 REMAINING — Damir's requests, mapped to lanes (build these)
- L4b POWER SYSTEM (HIGH): 5-level effort slider (Faster↔Smarter, screenshot) + Fast/Heavy/Deep presets.
    TWO dials: thinking-depth (slider; Fast=1, Deep=5; Fast/Deep are slider shortcuts) × output-length
    (Heavy lives here). Mode (Solo/Brain/Council) = how MANY models, separate. Heavy ≠ Brain. Each preset
    controls output too; caps are user-overridable defaults. Deep routes to native-thinking models.
- L4c BRAIN = ORCHESTRATOR: lead directs MULTIPLE models like the agent (hierarchical), not 1 expert.
- L19 BRAIN output-count (choose # of output/expert models) · L20 COUNCIL total-count (choose # members).
- L4f MULTI-ENGINE UI: SHOW which model each head uses + per-head master-prompt editor.
- L18 PICKER 4-layer browse: type(uncensored/code/thinking/vision) × cost × privacy, labeled.
- L6 ChatGPT-style THINKING DISPLAY (live collapsible "Думает…→Подумал Nс").
- L7 VERIFY-AGAINST-REALITY button (hallucination vs web + chat-drift + memory-vs-reality).
- L8 MEMORY-WRITE FREQUENCY user setting (mechanism exists at 6h; expose the knob).
- L9 USER HOOKS per chat (trigger + action-prompt + AI-help button).
- L10 PROJECTS (group chats + shared files + instructions + shared cross-chat memory). BIG.
- L11 VOICE hands-free mode (continuous listen→answer→speak; free stack NanoGPT TTS + browser STT).
- L12 FULL SKILLS (HIGH differentiator): paste a GitHub Claude-Code skill → import WHOLE folder
    (SKILL.md + scripts + resources) → RUN scripts sandboxed (see ARCH-DECISIONS) → auto-trigger in
    normal chat → works for ANY model (GPT/Gemini/DeepSeek use Claude-format skills). Store server-side.
- L15 AGENTIC HARNESS (HIGH differentiator): "think like Council, act like agent" across REAL ENVS —
    BROWSER (/api/browser) + TERMINAL/CODING (sandbox) + STUDIO (image/video/music/3D). Verify-loops,
    memory layering, + SESSION-LEVEL agent mode (a new chat can START as a full agent per settings).
- L13 MULTI-AGENT (Chad-style): spin N isolated agents (git worktrees) → merge clean back. In product.
- L14 AD-GENERATOR (Arcads-style): one product in → AI-avatar UGC video ads out, in Studio.
- L16 harden build-loop · L3 reasoning-params for stubborn models · L21 screen co-pilot · L22 web-video RAG

## 🆕 NEW REQUESTS (this turn)
- NEW-1 KILL :8777 / index.html (Damir: ":3000 main one, other kill"). taiga-web(:3000) is the product.
    server.py _do_GET_inner: `if path == "/": serve index.html` (~line 9331). CHANGE to a 307 redirect to
    the taiga-web origin (or stop serving index.html / show "use the app"). DO NOT delete the backend API.
    Then ONE app, no more frontend mix-up. Confirm production deploy serves BUILT taiga-web, not index.html.

## ARCH DECISIONS (Damir-approved, see ARCH-DECISIONS.md)
- Exec hosting = HYBRID: browser-WASM (free, light) + cloud sandbox-per-user (paid, heavy). Never on bare server.
- Skill storage = SERVER-SIDE per account (syncs all devices). Not the Chrome extension.

## ⚠️ OPERATIONAL
Two Claude sessions on one repo = collision risk (already caused the :8777 scare). ONE driver on
LANES.md/server.py at a time. The build session is currently active + productive — let it own the repo.
