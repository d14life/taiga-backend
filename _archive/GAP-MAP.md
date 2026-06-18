# UI GAP MAP — Тайга ИИ (from UI-audit agent, 2026-06-12)

## 🔴 ROOT CAUSE of "dead buttons" — the proxy layer
The frontend NEVER calls the Python backend directly. Every `fetch("/api/X")` is served by a Next.js proxy at `taiga-web/src/app/api/X/route.ts` → forwards to `http://127.0.0.1:8777`.
**52 Python routes exist, but only 30 Next proxies.** A route the FE fetches but that has NO proxy = silent 404 (swallowed). That is the mechanical reason many features look dead. **Fix discipline: every backend capability we surface needs (a) a proxy route AND (b) a UI control.**

## A. BUILT-BUT-NOT-SURFACED (capability exists, no reachable UI)
- A1 **Brain driver/expert selection** for ad-hoc "Мозг" toggle & Heavy — backend accepts `req.driver`/`expert`/`roleSystem` (server.py:5319-5335), but the toggle only sends hardcoded `cheap`/`BRAIN_DRIVER`. Only configurable inside saved agents (agent-builder.tsx). = owner's #1 complaint.
- A2 `/api/recall` episodic memory — built, no proxy, never called.
- A3 `/api/improve` prompt polisher — built, no proxy, never called.
- A4 `/api/image_intent` free diagram/poster auto-route — built, no proxy, orphaned.
- A5 `/api/skills` 358-skill marketplace — only the agent can reach it; no browse/import UI.
- A6 `/api/identity` server persona editor — FE persona is localStorage only.
- A7 `/api/billing` + `/api/topup` — built, no proxy, no caller (see B1).
- A8 `/api/userkeys` BYOK provider keys — built, no UI to paste a provider key.
- A9 `/api/websearch` media search — built, no caller.
- A10 server-side persistence (`/api/save /chats /delete /users /settings /remember /forget`) — intentionally bypassed (localStorage), BUT "Открыто — на сервере" privacy mode does nothing as a result.
- A11 dead export `assessRisk` (decision.ts).

## B. DEAD / BROKEN CONTROLS (clickable but no-op)
- B1 **"Пополнить" top-up** (sidebar.tsx:376) — toast only; `/api/topup` never called.
- B2 **Style-learning silently 404s** (style-profile.ts:40 → `/api/extract_style`) — NO proxy exists; dev returns 404, caught & swallowed. "Learns how you write" is broken end-to-end.
- B3 `/video` slash (builtins.ts:137) — toast "soon" though full video studio is built & reachable via image mode.
- B4 `/vision` slash — toast "soon" though vision works via attach.
- B5 `/projects` slash — toast; feature doesn't exist.
- B6 `/agents` slash (marketplace dup) — toast; `/orchestrate` & `/agent` DO work.
- B7 `/checkpoint` slash — toast; no checkpoint.
- B8 **FunctionBar pills `worker/diff/terminal/run/video`** — all collapse to the same `agentOn=true`; look distinct, aren't. `video` pill does NOT open studio.
- B9 "Открыто — на сервере" radio (settings-panel.tsx:16) — no backend effect.

## C. MISSING CONFIG / SECTIONS
- C1 **Brain config absent** — composer "Мозг" is a binary toggle, zero config. Relay ("Улучшить") HAS a full editable craft section (settings-panel.tsx:396-414); Brain has nothing. Backend already accepts driver+expert+roleSystem. Fix: a "Мозг" section mirroring relay → driver picker + expert picker + role text, feeding `dispatchSend ov.driver/ov.expert/ov.roleSystem` (already exist, chat.tsx:988-991).
- C2 **Memory delete not durable when auto-memory ON** — re-extraction (chat.tsx:595-624) re-adds deleted facts because `mergeFacts` dedups only vs current facts (no tombstone). Durable only while memoryAuto OFF (default). Fix: per-chat `deletedFactTexts` set filtered inside mergeFacts.
- C3 BYOK key entry missing; top-up fake; skill marketplace not browsable. (MCP marketplace is GOOD — the model for how skills/brain should look.)

## PRIORITIZED FIX LIST (impact-ranked)
1. **Brain config section** — settings-panel + chat.tsx wire ov.driver/expert/roleSystem. (real ~2-3h) → CHAT-CORE lane
2. **Proxy for extract_style** — add `app/api/extract_style/route.ts`. (quick) → PANELS lane
3. **Top-up works** — sidebar + new topup/billing proxies + modal. → deferred (real payment is ⛔ until uncensor per MASTER-PLAN; do proxy+stub only)
4. **Durable memory delete** (tombstone set) — chat-memory.ts + chat.tsx. (quick ~30m) → CHAT-CORE lane
5. **BYOK provider-key UI** — settings + userkeys proxy. (real) → PANELS lane
6. **Un-"soon" /video & /vision** — builtins.ts + slash switch. (quick) → CHAT-CORE lane
7. **Skill marketplace browse UI** — new panel + skills proxy, mirror mcp-panel. (real) → PANELS lane
8. **Server identity editor** — wire system-prompt textarea → /api/identity proxy. (quick) → PANELS lane
9. **Fix/remove dead FunctionBar pills** (diff/worker/video). → CHAT-CORE lane
10. **"Открыто на сервере" real-or-hide.** → defer/hide
11. **/api/improve "polish prompt" button.** (quick) → CHAT-CORE lane
12. **/api/recall wire-or-delete.** → CHAT-CORE
13. **image_intent free diagram auto-route** — gen-image + proxy. (real) → STUDIO lane
14. **Remove /projects /agents(dup) /checkpoint stubs.** (quick) → CHAT-CORE
15. **Remove dead assessRisk export.** (trivial) → CHAT-CORE

## INTEGRATION RULE
The 4 running lane-workers cover most of these by area. At merge, use THIS list as the checklist; whatever no lane covered (esp. cross-cutting MISSING PROXIES), coordinator does in a cleanup pass. Then run USER-CASES.md against the live app.
