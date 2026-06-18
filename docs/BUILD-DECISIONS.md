# BUILD-DECISIONS — Damir-approved forks (2026-06-18)

Resolved in the ВОПРОСЫ gate before the build. Authoritative for the build phase. Source of truth for "what we agreed".

## Q1 — Shell/desks framing: REAL DESKS, each modeled on a best-in-class reference repo
NOT 5 flat pills. The product is **distinct desks/workspaces**, each patterned on a reference repo (ideas, not licensed code — see docs/REFERENCE-REPOS.md), built ON TOP of the existing working engines (strangler-fig, never regress):
| Desk | Reference repo(s) (idea donor) | Existing engine to build on |
|---|---|---|
| **Чат** | Hermes, LibreChat, Lobe-Chat, big-AGI, ChatGPT, Claude Code | chat.tsx + server.py:13501 chat() |
| **Студия** | ComfyUI, FLUX, Fooocus, AudioCraft, ACE-Step | studio image/video/music/tts engines |
| **Дизайн** | open-codesign (opendesign) "but better", shadcn/Radix | (new desk; design-canvas surfaces) |
| **Агент** | OpenHarness, agentic-os, personal-os, Ralph, claude-squad + "Jarvis" | agent_os.py, orchestrator.py |
| **Код** | bolt.diy, webcontainer, VS Code | E2B sandbox (already wired), browser_hub.py |
| **Ultra** | Damir's own — universal "one chat does everything" | universal-brain (additive flags) |
Approach: each desk is a real surface launched from the macOS dock, evolving existing engines toward its reference's UX. Reference repos = idea donors only.

## Q2 — Ultra conversational system-redesigner = DEFERRED (post-core)
The Ultra-exclusive "talk to rebuild the system" (Ultra chat generates 3D bg, changes layout/theme/buttons by conversation) is a later flagship demo. Build dock + windows + theming first so Ultra has surfaces to manipulate. Zero code today; do not build now.

## Q3 — Skill library = KEEP 358 for launch
Ship with the 358 already seeded (of ~868 available ECC). Do not seed the rest or source a 3000+ corpus now. "300+/3000+" is a post-launch content goal pending a named source.

## Q4 — Council everywhere + named length presets
- Council reachable from ALL modes via the "+" menu (was Ultra-only).
- Add named length presets **Fast (~300 words) / Medium / Long** on top of the existing eco/norm/max token chip.

---
Carry these into docs/UNIFIED-FEATURE-CHECKLIST.md build order. Build foundation (Shell+Chat) first; the macOS app-icon dock is the #1 gap AND the launcher for every desk above — first feature.
