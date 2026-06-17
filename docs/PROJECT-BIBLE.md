# Тайга ИИ — PROJECT BIBLE (полный чертёж дома)

> Этот файл = всё, что нужно, чтобы человек или ИИ взял с нуля и построил продукт.
> Как чертёж дома: от фундамента до последней розетки.

---

## 1. VISION & POSITIONING

**Тайга ИИ** — приватный, uncensored, мульти-модельный AI-чат, позиционируемый как **агентная ОС**, а не чат-бот. Рынок: Россия/СНГ.

**Pitch:** "Один интерфейс ко всему интеллекту на планете" — 732+ моделей от множества провайдеров под одним брендом, приватно (no-logs/TEE), без цензуры, с агентными возможностями.

**Мот (competitive moat):**
- Единый доступ ко всем AI-моделям (не OpenAI-wrapper)
- Приватность (TEE/E2EE/no-logs) — user's data never seen by provider
- Uncensored — работает БЕЗ политических/моральных фильтров
- Russian-market UX (русский язык, СБП/крипто оплата)
- Агентный слой превращает чат в рабочее пространство

**Business model:** агрегатор — юзер платит нам, мы платим провайдерам, ~50% наценка. Оплата: СБП / крипто (NOWPayments/CoinGate/OxaPay).

**Founder:** Damir (solo), full stack, Russian-speaking.

---

## 2. GITHUB REPOS

### Main repos:
- **Backend:** `https://github.com/d14life/taiga-backend` — Python server + all docs
- **Frontend:** `https://github.com/d14life/taiga-web` — Next.js 16 app + shell.html

### Reference repos studied/borrowed patterns from:
- **LibreChat** (MIT) — multi-provider chat UI patterns, conversation tree, presets
- **Hermes/NousResearch** — agent loop, tool-use patterns
- **Claude Code** — skill system (SKILL.md format), permission ladder, agent-OS
- **RAG-Anything** — document parsing, chunking, hybrid retrieval
- **Open-Design** — design canvas concept (Apache license)
- **Ralph** (MIT) — verify/retry loops for agents

### Skills & Tools repos used:
- GitHub Claude-Code skills format (SKILL.md + scripts/)
- icons8 liquid-glass-color platform for icons
- Venice AI API (E2EE, uncensored)
- NanoGPT API (subscription model, free daily images)
- Chutes/Redpill/AIMLAPI — additional model providers

---

## 3. TECH STACK

### Backend (COMPLETE — don't rebuild)
```
Language:    Python 3.11+ (stdlib only — NO Flask/Django/FastAPI)
Server:      http.server.ThreadingHTTPServer on :8777
Database:    SQLite + FTS5 full-text search
Storage:     Per-user JSON + SQLite rows
Encryption:  Fernet (cryptography) for BYOK keys, cookies, MCP tokens
Auth:        Optional PBKDF2 signup/login + session tokens
Streaming:   Server-Sent Events (SSE)
Agent:       LangGraph (StateGraph) for orchestration
ML local:    MLX on Apple Silicon for RAG compression (:8791)
```

### Frontend
```
Framework:   Next.js 16 (App Router, Turbopack)
React:       19.2.4
TypeScript:  5.x
Styling:     Tailwind CSS 4 (dark theme, CSS variables)
Animation:   Motion (framer-motion) 12.x
Icons:       Lucide React + custom liquid-glass icon set (81 SVGs)
AI SDK:      @ai-sdk/react 3.x + ai 6.x (Vercel AI SDK)
3D:          Three.js + @react-three/fiber (for 3D viewer)
Markdown:    react-markdown + rehype-highlight + remark-gfm
Export:      docx, pptxgenjs, xlsx, jspdf, html2canvas
Diagrams:    Mermaid 11.x
```

### Infrastructure
```
Server:      Hetzner VPS (vpn.mostik.xyz / 217.160.174.8)
Processes:   launchd daemons (backend :8777, frontend :3000, MLX :8791)
Auto-update: GitHub pull + restart timer
Backup:      Auto-push to GitHub
```

---

## 4. ALL 182 FEATURES (12 areas)

> See `FEATURE-INVENTORY.md` for the complete checklist.
> See `TAIGA-REQUIREMENTS.md` for status (✅/🔴/🟡) per feature.
> See `USER-CASES.md` for 381-line user test matrix.

### Summary by area:
| # | Area | Features | Status |
|---|------|----------|--------|
| 1 | Chat Core & Model Routing | 19 | 95% built |
| 2 | Multi-Engine Modes (Brain/Council/Compare/Research/Relay) | 14 | 90% built |
| 3 | Agent-OS (orchestration, debate) | 18 | 85% built |
| 4 | MCP Connectors | 11 | 80% built |
| 5 | Skills (GitHub-imported) | 15 | 90% built |
| 6 | Memory, RAG & Grounding | 18 | 75% built |
| 7 | Studio / Media Generation | 16 | 70% built |
| 8 | Billing / Balance / Pricing | 15 | 60% built |
| 9 | Accounts, Auth & Security | 16 | 85% built |
| 10 | Storage / Persistence | 11 | 80% built |
| 11 | Web Chat UI | 19 | 60% built |
| 12 | Routines & Automations | 10 | 50% built |

---

## 5. DESIGN LANGUAGE

### The Decision (LOCKED)
The UI looks like a **macOS desktop application** running inside a browser. NOT a generic chat interface. Think Apple's macOS + ChatGPT combined.

### Reference:
- `docs/design/reference-mockup.html` — THE canonical mockup (337KB single HTML file)
- `taiga-web/public/shell.html` — live version with backend wiring (1977 lines)
- `docs/screenshots/` — 14 screenshots of current state

### Design tokens:
- **Base:** OLED black `#0d0d0d`
- **Surfaces:** `#1a1a1a`, `#222`
- **Single accent:** `#FF9E64` (amber) — ONLY accent color
- **Text:** `#e5e5e5` primary, `#888` secondary, `#555` muted
- **Window chrome:** macOS-style title bars with traffic lights (red/yellow/green)
- **Glass:** `backdrop-filter: blur(20px)` on overlays
- **Icons:** Colored liquid-glass from icons8, transparent backgrounds
- **Font:** -apple-system stack
- **Radius:** 8/12/16px
- **Language:** ALL Russian

### Layout:
- Left sidebar (260px) with 7 collapsible nav groups
- Main chat area center
- Bottom dock (64px) with app shortcuts
- Floating macOS-style windows for panels (draggable, resizable, traffic lights)

---

## 6. ARCHITECTURE (current)

### Backend monolith
`server.py` (~14,729 lines, 541 functions, 47+ API endpoints)

One file holds EVERYTHING:
- HTTP router + all `/api/*` handlers
- Model routing (auto-select, cost tiers, fallback chains)
- Chat engine (streaming, modes, Brain/Council/Compare/Research)
- Agent-OS (orchestrator, debate, workers)
- Tool registry + permission gating
- Memory + RAG + grounding
- Studio (image/video/music/TTS/3D/cinema)
- Billing + metering + balance
- Skills (install/run/auto-trigger)
- MCP client + connector management
- Search (FTS5)
- Auth + security + rate limiting

**Extracted modules:** `agent_os.py`, `orchestrator.py` (LangGraph), `debate.py`, `scheduler.py`, `skills_run.py`, `skill_caps.py`, `auth.py`, `guard.py`, `browser_hub.py`, `ad_gen.py`, `video_rag.py`, `screen_copilot.py`

### Frontend
`taiga-web/src/components/chat.tsx` (~8,157 lines) — god component
`taiga-web/public/shell.html` (1,977 lines) — macOS-style UI
14 JS modules in `public/shell/` wire features to backend

133 React components total in `src/components/`.

### See `ARCHITECTURE-MAP.md` for the full map with coupling analysis.

---

## 7. API CONTRACT

> See `docs/LOVABLE-HANDOFF.md` section "API Contract" for the full endpoint list.

### Quick reference — most important endpoints:
```
POST /api/chat        — main chat (SSE streaming)
GET  /api/models      — full 732+ model catalog
GET  /api/curated     — curated list with brand groups
POST /api/council     — multi-model council
POST /api/compare     — side-by-side comparison
POST /api/research    — deep research with web search
POST /api/orchestrate — multi-agent task decomposition
POST /api/debate      — architect vs critic debate
POST /api/image       — text-to-image
POST /api/video       — text-to-video (SSE progress)
POST /api/music       — music generation
POST /api/free-tts    — free TTS
POST /api/audio       — paid TTS
GET  /api/memory      — user memory facts
GET  /api/balance     — user balance
GET  /api/search      — full-text search chats
GET  /api/capabilities — system capabilities report
```

---

## 8. GRAND PLANS (evolution)

### GRAND-PLAN.md (v1) — A-Z feature map
All features from Chat to Studio to Agent-OS to UI customization to Infra. Built in waves of parallel agents.

### GRAND-PLAN-V2.md — Batches 0-8
Strangler refactor pattern. Focus on parity + production hardening.

### GRAND-PLAN-V3.md — Batches 9-21 (COMPLETED)
All 13 batches done. Added: smart RAG, multimodal ingest, agent timeline + permissions, workflow runner, hands-free voice, OOXML export, per-model playground, mobile polish, i18n, security hardening, performance, observability, test suite (16 endpoint + 73 vitest).

### Current state: ALL grand plan batches COMPLETE.
Next phase: macOS shell redesign + Lovable rebuild.

---

## 9. IDEAS & FEATURES (complete list)

### Built & working:
- Multi-provider uncensored chat (5 upstreams)
- Auto-model selection by task type
- Brain (cheap→expert), Relay (clean→answer), Council (parallel→fuse), Compare (side-by-side), Research (web+cited)
- Agent-OS with LangGraph orchestration
- Architect↔Critic debate
- 17 worker skill personas
- Full skill import from GitHub (SKILL.md format)
- Memory with auto-extraction + tombstones + consolidation
- RAG with hybrid retrieval (FTS + dense + RRF)
- Studio: images, video, music, TTS, 3D, cinema, ads
- MCP connector marketplace
- Billing with cost tracking
- Voice input (Web Speech)
- Canvas/Artifacts (live HTML/React/SVG sandbox)
- Privacy modes (local/E2EE/server)
- TEE routing preference
- Command palette (50+ slash commands)
- Custom commands + pipelines
- Thinking display (collapsible)
- Verify-against-reality button
- Auto-continue on token limit
- Cost tier routing (cheap/mid/top)
- Chat projects with shared instructions

### Designed but not fully wired in UI:
- Full agent step timeline with permission ladder
- Subagents (isolated context + parallel)
- Background/scheduled agents
- Skills marketplace (thousands browsable)
- MCP OAuth flow
- Full payment processing (СБП/crypto)
- Cross-chat user profile
- Notes app (Apple-style window)
- Files app (Apple-style window)
- App Store of all features

### Deferred / future:
- CLaRa-7B (latent RAG model — waiting for MLX release)
- g-brain graph memory visualization
- Voice personas (18+)
- Obsidian integration
- JSON→Postgres migration
- YooKassa billing
- Desktop Tauri app
- GPU self-hosting (Qwen3.6-35B-A3B abliterated)
- Social publishing
- Deepfake guard

---

## 10. INSTALLED SKILLS (Claude Code format)

### User skills (~40 installed):
```
brandkit, ckm-banner-design, ckm-brand, ckm-design, ckm-design-system,
ckm-slides, ckm-ui-styling, design-md, design-taste-frontend,
design-taste-frontend-v1, emil-design-eng, enhance-prompt, find-skills,
framer-motion, full-output-enforcement, gpt-taste, high-end-visual-design,
image-to-code, imagegen-frontend-mobile, imagegen-frontend-web, impeccable,
industrial-brutalist-ui, minimalist-ui, pick-skills, react-components,
redesign-existing-projects, refero-design, remotion, shadcn-ui,
stitch-code-to-design, stitch-design-taste, stitch-extract-design-md,
stitch-extract-static-html, stitch-generate-design, stitch-loop,
stitch-manage-design-system, stitch-react-native, stitch-upload-to-stitch,
supabase, supabase-postgres-best-practices, taste-design, ui-ux-pro-max
```

### Plugin skills (superpowers + vercel + codex + anthropic):
```
brainstorming, dispatching-parallel-agents, executing-plans,
finishing-a-development-branch, receiving-code-review, requesting-code-review,
subagent-driven-development, systematic-debugging, test-driven-development,
using-git-worktrees, verification-before-completion, writing-plans,
writing-skills
```

### Vercel ecosystem skills:
```
ai-gateway, ai-sdk, auth, bootstrap, chat-sdk, deployments-cicd, env-vars,
marketplace, microfrontends, next-cache-components, next-forge, next-upgrade,
nextjs, react-best-practices, routing-middleware, runtime-cache, shadcn,
turbopack, vercel-agent, vercel-cli, vercel-firewall, vercel-functions,
vercel-sandbox, vercel-storage, verification, workflow
```

### Key skill: agent-elements
Agent Elements — shadcn registry for chat/agent UIs. Components: AgentChat, MessageList, InputBar, tool cards (Bash, Edit, Search, Todo, Plan, Subagent, MCP, Thinking, Generic), suggestions, model picker, mode selector. Works with Vercel AI SDK useChat().

---

## 11. KEY DECISIONS (LOCKED)

1. **macOS desktop aesthetic** — NOT a generic web app. Windows, dock, sidebar, traffic lights.
2. **Dark theme only** — no light mode (yet)
3. **Single amber accent #FF9E64** — one accent color, everywhere
4. **Russian language** — ALL UI text in Russian
5. **No emoji in UI** — SVG/line icons only
6. **Backend = source of truth** — frontend is a client only
7. **Provider names hidden** — user sees "Тайга ИИ" brand
8. **SSE streaming** — word-by-word, not load-then-display
9. **Privacy-first** — TEE/E2EE preferred, no-logs default
10. **Uncensored** — no political/moral filters, only clearly-illegal blocked
11. **shell.html as THE app** — the macOS mockup IS the product (not React approximation)

---

## 12. CONVERSATION HISTORY (key decisions & pivots)

### Timeline of major decisions:

**Week 1 (June 10-11):** Initial build. Established multi-provider backend, chat streaming, mode switching. Built 133 React components. Chat.tsx grew to 8K+ lines (god component).

**Week 1-2 (June 11-13):** Grand Plan V1-V3 executed. 21 batches of parallel agent builds. Added RAG, agent timeline, permissions, voice, workflow runner, security hardening, performance, observability. 16 endpoint tests + 73 vitest passing.

**Week 2 (June 13-14):** Damir discovered React app "used old design this whole time." Critical pivot: took the EXACT macOS-perfect HTML mockup and made IT the real app (shell.html), NOT a React approximation. Mounted via iframe at /app route.

**Week 2-3 (June 14-17):** Shell wiring phase. 14 JS modules written to wire shell.html to live backend. Modes, studio, agent, code, memory, chats, account, store, tools, design, automations, desktop, ultra — all partially wired. Glass icons replaced (81 SVGs, transparent backgrounds). Dock and sidebar polished.

**Week 3 (June 17):** Final functionality gate attempted. 9/10 test areas hit API rate limits. 6 bugs found in search-chats area (3 HIGH: ghost-chat 405, window.* scoping for compact/followups; 3 MED: presets, static folders, missing branches/regenerate).

**June 17 (now):** Damir decided to try Lovable for the frontend build. This handoff package prepared.

### Key frustrations & rules (from Damir):
- "Don't tell me to sleep/rest/take a break"
- "Don't pile multi-choice technical questions"
- "Make decisions yourself when I say go/drive"
- "No emoji, no jargon"
- "Status = binary per-deliverable lines"
- "The design mockup IS the product, not a React approximation"

---

## 13. KNOWN BUGS (as of June 17)

From `BUGS-FOUND.md`:
1. **HIGH:** Ghost-chat (openGhostChat) uses GET → route.ts is POST-only → 405
2. **HIGH:** Compact never works — window.taigaMessages/window.convo undefined
3. **HIGH:** Followups dead — same window.* binding root cause
4. **MED:** Presets save/apply broken vs backend's ALLOWED_CONFIG_MODES whitelist
5. **MED:** Sidebar folders/projects are static mock — no API, fake drag-drop
6. **MED:** Branches/regenerate/edit-message missing — palette commands are toast-only

---

## 14. BUILD ORDER FOR NEW BUILDER (Lovable or other)

### Phase 1: Shell + Chat (MVP — SHIP THIS)
- macOS shell layout (sidebar, main area, dock)
- Chat with SSE streaming to /api/chat
- Model picker from /api/curated
- Basic chat history from /api/chats
- Send/stop/copy/markdown rendering

### Phase 2: Modes
- Mode switcher (Chat/Code/Uncensored/Images/Ultra)
- Brain/Relay toggle
- Thinking steps display
- Council + Compare panels
- Research with citations

### Phase 3: Studio
- Image generation + gallery
- Video with SSE progress
- Music + TTS
- 3D viewer

### Phase 4: Agent-OS
- Orchestrator panel
- Debate panel
- Agent builder
- Task board

### Phase 5: Memory & Knowledge
- Memory panel (CRUD)
- RAG upload
- Grounding sources
- Search across chats

### Phase 6: Code & Skills
- Terminal (owner)
- Skills library + install
- MCP connectors

### Phase 7: Settings & Account
- User management
- Billing + balance
- Theme picker
- Master prompt editor

### Phase 8: Polish
- Window management (drag/resize/minimize)
- Cmd-K command palette
- Keyboard shortcuts
- Mobile responsive
- Animations

---

## 15. FILES INDEX

### Backend (mostik-ai/):
```
server.py              — 14K+ lines, ALL API endpoints
agent_os.py            — Agent orchestration
orchestrator.py        — LangGraph task decomposition
debate.py              — Architect-Critic debate
scheduler.py           — Cron/routine runner
skills_run.py          — Skill script executor
skill_caps.py          — Skill capability scanner
auth.py                — Auth module
guard.py               — Security guards
browser_hub.py         — Browser automation
ad_gen.py              — UGC ad script generator
video_rag.py           — Video RAG
screen_copilot.py      — Screen co-pilot
```

### Frontend (taiga-web/):
```
public/shell.html      — THE live macOS-style app (1977 lines)
public/shell/*.js      — 14 modules wiring features
public/icons/glass/    — 81 liquid-glass SVG icons
src/components/        — 133 React components
src/app/app/page.tsx   — /app route (iframe → shell.html)
src/app/api/           — Next.js API routes
```

### Documentation:
```
docs/LOVABLE-HANDOFF.md     — Complete Lovable build spec
docs/PROJECT-BIBLE.md       — THIS FILE
docs/design/                — Reference mockup + design docs
docs/screenshots/           — 14 current state screenshots
FEATURE-INVENTORY.md        — All 182 features checklist
TAIGA-REQUIREMENTS.md       — Full requirements + status
USER-CASES.md               — 381-line user test matrix
ARCHITECTURE-MAP.md         — System architecture map
GRAND-PLAN.md               — Feature roadmap v1
GRAND-PLAN-V2.md            — Batches 0-8
GRAND-PLAN-V3.md            — Batches 9-21 (done)
TAIGA-RESEARCH-BRIEF.md     — Architecture research prompts
TAIGA-SESSION-DIRECTIVES.md — Multi-session coordination
REBUILD-BRIEF.md            — Rebuild brief
WIRING-PLAN.md              — Feature → endpoint mapping
BUGS-FOUND.md               — Known bugs
DESIGN-APPLY-QUEUE.md       — Design fixes queue
WHATS-NEW.md                — User-facing changelog
```
