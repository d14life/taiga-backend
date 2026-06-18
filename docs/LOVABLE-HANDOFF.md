# Тайга ИИ — Complete Handoff for Lovable Build

> ⚠️ СТАТУС-ПОПРАВКА (docs/MANIFEST.md + DECISIONS-LOG перевешивают): структура НЕ «8 фаз/Modes»,
> а **5 СТОЛОВ + Ultra** (Разговор/Студия/Дизайн/Агенты/Код + Ultra). Моды = «УСИЛЕНИЕ ответа», не
> отдельные экраны. Источник истины = эталон-репо стола (REFERENCE-REPOS.md) + design-v3. Порядок
> сборки — docs/TEST-WORKFLOW.md. API-контракт/SSE/токены ниже актуальны; читай как справочник по API.
>
> This document contains the API/SSE/design-token reference. Build order is the 5-стол plan, not the old phases.

## What is Тайга ИИ?

A **private, uncensored, multi-model AI chat product** for the Russian/CIS market. Think ChatGPT + Claude + Perplexity combined — but uncensored, multi-provider, with agent capabilities, and targeting Russian-speaking users.

**Positioning:** The most powerful AI interface money can buy — not another ChatGPT wrapper. Real multi-engine modes, agent orchestration, media studio, developer tools, and memory — all in one product.

**Live backend:** Python stdlib HTTP server at `https://ai.mostik.xyz:8777` (or localhost:8777). ALL API endpoints are already built and working. The frontend's ONLY job is to be a beautiful, functional client for this backend.

---

## The Design: macOS-Style Desktop App

**THE LOCKED DESIGN DECISION:** The UI looks like a macOS desktop application running inside a browser. NOT a generic chat interface. Think Apple's macOS + ChatGPT had a baby.

### Reference Files
- `docs/design/reference-mockup.html` — THE canonical design mockup (open in browser to see it). This is the single source of truth for how the app should look.
- `taiga-web/public/shell.html` — The live version with backend wiring (1977 lines). 14 JS modules in `public/shell/` wire features.
- `docs/screenshots/` — Screenshots of the current state.

### Design Language
- **Dark theme** (OLED black `#0d0d0d` base)
- **Single amber accent** `#FF9E64` for all interactive elements
- **macOS window chrome:** title bars, traffic lights (red/yellow/green dots), window shadows
- **Left sidebar** with 7 nav groups (collapsible)
- **Bottom dock** (macOS-style) with app shortcuts
- **Floating macOS-style windows** for panels (draggable, resizable, with traffic lights)
- **Glassmorphism** on overlays and panels (`backdrop-filter: blur`)
- **Font:** system -apple-system stack, clean and native-feeling
- **Icons:** Colored liquid-glass icons from icons8 (transparent backgrounds, NO squares behind them)
- **Language:** ALL user-facing text in Russian

### Layout Structure
```
┌─────────────────────────────────────────────────────┐
│  Top bar (app title + model label + user avatar)     │
├──────┬──────────────────────────────────────────────┤
│      │                                               │
│ Side │         Main Chat Area                        │
│ bar  │    (messages stream here)                     │
│      │                                               │
│ Nav  │    ┌─────────────────────────┐                │
│ Rail │    │  Composer (input bar)    │                │
│      │    │  + action row below     │                │
│ 7    │    └─────────────────────────┘                │
│ groups                                               │
│      │                                               │
├──────┴──────────────────────────────────────────────┤
│  ═══ macOS Dock (app shortcuts) ═══                  │
└─────────────────────────────────────────────────────┘
```

### Sidebar Nav Groups (7 groups, each expandable)
1. **Чаты** (Chats) — Recent chats, folders, projects, search
2. **Режимы** (Modes) — Chat/Code/Uncensored/Images/Ultra mode switcher
3. **Студия** (Studio) — Image/Video/Music/Voice/3D/Cinema generation
4. **Агенты** (Agents) — Agent builder, orchestrator, debate, tasks
5. **Код** (Code) — Terminal, skills, MCP connectors
6. **Память** (Memory) — Facts, RAG docs, grounding sources, episodic recall
7. **Настройки** (Settings) — Account, billing, theme, model catalog

### Dock Apps (bottom bar)
Quick-launch icons for: Chat, Studio, Agent, Code, Memory, Settings, plus user-pinned custom entries.

---

## Tech Stack

### Frontend (what Lovable builds)
- **React 19** + **Next.js 16** (App Router)
- **Tailwind CSS 4** (dark theme, CSS variables)
- **Motion** (framer-motion) for animations
- **Lucide React** icons + custom glass icon set
- **AI SDK** (@ai-sdk/react) for streaming chat
- No database on frontend — ALL data from backend API

### Backend (ALREADY BUILT — don't rebuild)
- Python stdlib HTTP server on port 8777
- SQLite database
- All `/api/*` endpoints already working
- SSE streaming for chat responses
- OpenAI-compatible `/v1` proxy

**CRITICAL: Lovable builds ONLY the frontend. The backend is complete and running.**

---

## API Contract

### Base URL
```
http://localhost:8777   (dev)
https://ai.mostik.xyz:8777   (prod)
```

### Authentication
- User header: `X-User: <username>` (default: "default")
- Owner detection via server-side config
- Optional auth via `/api/auth` (PBKDF2)

### Core Chat Endpoint
```
POST /api/chat
Content-Type: application/json

{
  "user": "default",
  "model": "__auto__",       // or specific model ID
  "messages": [
    {"role": "user", "content": "привет"}
  ],
  "max_tokens": 2048,
  "system": "",              // optional system prompt override
  "mode": "chat",            // chat|code|uncensored|images|ultra
  "images": [],              // base64 images for vision
  "reasoning_effort": "medium", // low|medium|high
  "temperature": 0.7
}

Response: SSE stream
data: {"type":"delta","text":"Привет"}
data: {"type":"meta","model":"venice/llama-3.3-70b"}
data: {"type":"thinking","text":"..."}
data: {"type":"cost","input_tokens":50,"output_tokens":120,"cost_usd":0.001}
data: {"type":"done"}
```

### Key API Endpoints (all POST unless noted)

**Chat & Modes:**
- `POST /api/chat` — main chat (all modes)
- `GET /api/models` — full model catalog
- `GET /api/curated` — curated model list with brand groups
- `POST /api/council` — multi-model council mode
- `POST /api/compare` — side-by-side model comparison
- `POST /api/research` — deep research with web search

**Agent-OS:**
- `POST /api/orchestrate` — multi-agent task decomposition
- `POST /api/debate` — architect vs critic debate
- `GET /api/agent/status` — agent run status

**Studio (Media):**
- `POST /api/image` — text-to-image generation
- `POST /api/video` — text-to-video (SSE progress)
- `POST /api/music` — music generation (SSE)
- `POST /api/free-tts` — free text-to-speech
- `POST /api/audio` — paid TTS (NanoGPT voices)
- `POST /api/td3` — 3D mesh from photo
- `POST /api/upscale` — image upscale
- `POST /api/cinema` — multi-scene film export

**Memory & RAG:**
- `GET /api/memory?user=X` — get user's memory facts
- `POST /api/memory` — add/update memory fact
- `DELETE /api/memory` — remove fact
- `POST /api/memory_consolidate` — trigger consolidation
- `POST /api/rag/upload` — upload document for RAG
- `POST /api/rag/query` — query RAG knowledge base
- `POST /api/grounding` — add trusted source
- `GET /api/episodic?user=X&q=search` — search past chats

**Skills & MCP:**
- `GET /api/skills?user=X` — list installed skills
- `POST /api/skill/install` — install skill from GitHub
- `POST /api/skill/run` — run a skill script
- `GET /api/mcp` — list MCP connectors
- `POST /api/mcp` — install/remove/toggle connector

**Billing:**
- `GET /api/balance?user=X` — user balance
- `GET /api/billing` — billing config (owner)
- `POST /api/topup` — top up balance (needs payment processor)

**Account:**
- `GET /api/users` — list users
- `POST /api/user/create` — create user
- `POST /api/user/rename` — rename user
- `POST /api/settings` — save user settings
- `GET /api/settings?user=X` — load user settings

**Search:**
- `GET /api/search?user=X&q=query` — full-text search chats
- `GET /api/chats?user=X` — chat history list

**Misc:**
- `GET /api/capabilities` — full system capabilities report
- `POST /api/verify` — verify last AI answer
- `POST /api/compact` — compact long chat history

---

## Feature Map: 12 Areas, 182 Features

### 1. Chat Core & Model Routing (19 features)
The heart of the product. Multi-provider uncensored chat across 5 upstreams (Venice/NanoGPT/Chutes/Redpill/AIMLAPI) behind one brand. Users never see provider names.

**Key features:**
- Streaming SSE responses with word-by-word rendering
- Auto model selection (`__auto__`): picks best model for code/reason/vision/cheap/chat
- Price/cost tiers (off/cheap/mid/top)
- Reasoning depth dial (low/medium/high) — "Глубоко" slider
- Vision: auto-switches to vision model when images attached
- Auto-continue on token-limit truncation (stitches up to 4 parts)
- Silent provider failover (retries next funded model before showing error)
- Per-user saved config per mode
- Model picker with ~800 models, brand groups, search, capability badges

### 2. Multi-Engine Modes (14 features)
What makes Тайга unique — multiple AI models working together.

- **Мозг (Brain):** Cheap leader triages → strong expert answers hard questions
- **Совет (Council):** N models deliberate in parallel, synthesizer fuses
- **Сравнение (Compare):** Side-by-side raw answers from 2-5 models
- **Ультра (Ultra/Research):** Deep research with web search, plan, cited report
- **Связка (Relay):** Cheap model fixes prompt, smart model answers
- Rich SSE timeline events showing thinking steps per mode

### 3. Agent-OS (18 features)
Multi-agent orchestration — decompose tasks, parallel workers, synthesis.

- Auto-decompose task into 2-4 subtasks → parallel workers → synthesized answer
- Live timeline (SSE): per-worker status, thinking, searching, verifying
- 17 skill personas per worker
- Architect↔Critic debate with convergence detection
- Scheduled/cron agent runs

### 4. MCP Connectors (11 features)
Connect to external tools via Model Context Protocol.

- Built-in marketplace (DeepWiki, Context7, HuggingFace, GitHub, Notion, ComfyUI)
- One-click install, toggle, remove
- Custom MCP server by URL
- Connected tools become callable in chat

### 5. Skills (15 features)
GitHub-imported Claude-Code-style skills.

- Import skill folders from GitHub
- Auto-trigger: keyword matching injects skill instructions
- Run scripts natively (owner) or in E2B sandbox
- Skill library with categories, search, enable/disable

### 6. Memory, RAG & Grounding (18 features)
Long-term memory and knowledge injection.

- Auto-extracted facts from conversation
- Contradiction-aware updates
- Forget/remember commands
- Document RAG: upload docs → chunked vector search
- Grounding mode: answer ONLY from trusted sources with citations
- Episodic recall: search past chats

### 7. Studio / Media (16 features)
Creative media generation.

- Text-to-image with seed, steps, negative prompt
- Text-to-video with live SSE progress
- Music generation from prompt + lyrics
- TTS voiceover (free + paid)
- 3D mesh from photo
- Cinema: concatenate scenes into MP4
- Design system generator from brand brief

### 8. Billing (15 features)
Prepaid USD wallet per user.

- Pay-as-you-go text billing (tokens × price × markup)
- Media billing per-item
- Live balance display after each answer
- Top-up slider (RUB→USD)
- Owner billing console

### 9. Accounts & Security (16 features)
Multi-user with owner/regular distinction.

- Create/rename/delete accounts
- Optional password auth
- BYOK keys encrypted at rest
- Rate limiting, abuse filtering
- CSAM blocking
- Permission ladder for agent tools (plan/auto/full)
- Destructive command safety net

### 10. Storage (11 features)
All server-side, SQLite-backed.

- Chat history with full-text search
- Memory facts, RAG chunks, grounding sources
- Encrypted file storage (25MB/file)
- Skill library, MCP configs, routines

### 11. Web UI (19 features)
The frontend — what Lovable builds.

- Streaming chat with branch/edit tree, regenerate, copy
- Model picker (800+ models)
- Slash-commands + Cmd-K command palette
- Composer: attachments, camera, screen capture, voice input
- macOS-style floating windows for panels
- Agent-OS dashboard
- Studio panels
- Marketplaces (skills, tools, agents, commands)

### 12. Routines & Automations (10 features)
Scheduled prompts and workflows.

- Per-user saved-prompt routines on time schedules
- Event routines (on completion, on pattern match)
- Workflow templates (research-brief, image-from-idea, doc-qa)

---

## Build Order (Phase by Phase)

### Phase 1: Shell + Chat (SHIP THIS FIRST)
Build the macOS-style shell with working chat.
- Dark theme layout (sidebar + main area + dock)
- Sidebar with 7 nav groups
- Bottom dock with app icons
- Chat composer (text input, send button, stop button)
- SSE streaming chat connected to `/api/chat`
- Message rendering with markdown
- Model picker dropdown connected to `/api/curated`
- Basic chat history in sidebar
- Auto-scroll, loading states

### Phase 2: Modes + Brain
- Mode switcher (Chat/Code/Uncensored/Images/Ultra)
- Per-mode hero text cycling
- Brain/Relay toggle in composer actions
- Thinking steps display (collapsible timeline)
- Council mode panel
- Compare mode (side-by-side grid)
- Research mode with cited output

### Phase 3: Studio
- Image generation panel (prompt, negative, seed, size, model picker)
- Image gallery/history
- Video generation with SSE progress bar
- Music generation
- TTS/voice panel
- 3D viewer

### Phase 4: Agent-OS
- Orchestrator panel (task input → worker timeline)
- Debate panel (architect vs critic rounds)
- Agent builder (brain mode config: lead + expert model)
- Task kanban board
- Agent gallery/marketplace

### Phase 5: Memory & RAG
- Memory panel (view/add/edit/delete facts)
- Style note editor
- RAG upload (drag-drop docs)
- Grounding sources panel
- Episodic recall search

### Phase 6: Code & Skills
- Terminal panel (owner-only)
- Skills library panel
- Skill install from GitHub URL
- MCP connector marketplace
- MCP toggle/config panel

### Phase 7: Settings & Account
- Account management (users list, create, rename)
- Billing panel (balance, top-up, ledger)
- Theme picker
- Model catalog (full browsable list)
- Master prompt editor
- Custom instructions

### Phase 8: Polish
- macOS window management (drag, resize, minimize, close)
- Cmd-K command palette
- Keyboard shortcuts
- Mobile responsive
- Animations and transitions
- Error states and empty states

---

## Design Tokens

```css
:root {
  /* Core */
  --bg-base: #0d0d0d;
  --bg-surface: #1a1a1a;
  --bg-elevated: #222;
  --bg-overlay: rgba(30,30,30,0.85);
  
  /* Text */
  --text-primary: #e5e5e5;
  --text-secondary: #888;
  --text-muted: #555;
  
  /* Accent — ONLY ONE */
  --accent: #FF9E64;
  --accent-hover: #FFB080;
  --accent-dim: rgba(255,158,100,0.15);
  
  /* Borders */
  --border-subtle: rgba(255,255,255,0.06);
  --border-medium: rgba(255,255,255,0.1);
  
  /* Window chrome */
  --titlebar-bg: rgba(30,30,30,0.7);
  --traffic-red: #ff5f57;
  --traffic-yellow: #febc2e;
  --traffic-green: #28c840;
  
  /* Sidebar */
  --sidebar-width: 260px;
  --sidebar-bg: rgba(15,15,15,0.95);
  
  /* Dock */
  --dock-bg: rgba(30,30,30,0.8);
  --dock-height: 64px;
  
  /* Glassmorphism */
  --glass-bg: rgba(30,30,30,0.6);
  --glass-blur: 20px;
  --glass-border: rgba(255,255,255,0.08);
  
  /* Radius */
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-window: 12px;
  
  /* Shadows */
  --shadow-window: 0 20px 60px rgba(0,0,0,0.5);
  --shadow-dock: 0 -4px 30px rgba(0,0,0,0.3);
}
```

---

## Key Technical Notes

1. **ALL text must be in Russian.** Button labels, placeholders, error messages, tooltips — everything in Russian. The product is for RU/CIS market.

2. **Backend is OpenAI-compatible.** The `/v1/chat/completions` endpoint works like OpenAI's API. You can use `@ai-sdk/openai-compatible` to connect.

3. **SSE streaming format:**
   ```
   data: {"type":"delta","text":"word "}
   data: {"type":"meta","model":"venice/llama-3.3-70b","served_by":"venice"}
   data: {"type":"thinking","text":"reasoning step..."}
   data: {"type":"tool","name":"web_search","args":{"q":"query"}}
   data: {"type":"tool_done","name":"web_search","result":"..."}
   data: {"type":"cost","input_tokens":50,"output_tokens":200,"cost_usd":0.002}
   data: {"type":"done"}
   ```

4. **Model catalog structure** (from `/api/curated`):
   ```json
   {
     "models": [
       {
         "id": "venice/llama-3.3-70b",
         "name": "Llama 3.3 70B",
         "provider": "venice",
         "brand": "Meta",
         "brand_icon": "meta",
         "kind": "chat",
         "context": 131072,
         "vision": false,
         "uncensored_pct": 95,
         "price_in": 0.0003,
         "price_out": 0.0008,
         "sp": 87
       }
     ],
     "groups": { "Meta": [...], "Anthropic": [...] }
   }
   ```

5. **Chat history format** (from `/api/chats`):
   ```json
   {
     "chats": [
       {
         "id": "abc123",
         "title": "Привет мир",
         "ts": 1718000000,
         "preview": "Первое сообщение...",
         "model": "venice/llama-3.3-70b",
         "msg_count": 5
       }
     ]
   }
   ```

6. **No authentication needed for dev.** Just send `X-User: default` header. Auth is optional.

---

## File Structure in This Repo

```
mostik-ai/                          # Backend (Python)
├── server.py                       # Main server (14K+ lines, ALL endpoints)
├── agent_os.py                     # Agent orchestration
├── orchestrator.py                 # LangGraph-based task decomposition
├── debate.py                       # Architect-Critic debate
├── scheduler.py                    # Cron/routine runner
├── skills_run.py                   # Skill script executor
├── skill_caps.py                   # Skill capability scanner
├── auth.py                         # Auth module
├── guard.py                        # Security guards
├── browser_hub.py                  # Browser automation
├── ad_gen.py                       # UGC ad script generator
├── video_rag.py                    # Video RAG
├── screen_copilot.py               # Screen co-pilot
│
├── taiga-web/                      # Frontend (Next.js 16)
│   ├── public/
│   │   ├── shell.html              # THE live macOS-style app (1977 lines)
│   │   ├── shell/                  # 14 JS modules wiring features
│   │   │   ├── api.js              # window.Taiga API client
│   │   │   ├── modes.js            # Mode switching
│   │   │   ├── chats.js            # Chat history, search, folders
│   │   │   ├── studio.js           # Studio media panels
│   │   │   ├── agent.js            # Agent-OS panels
│   │   │   ├── code.js             # Code/skills/MCP panels
│   │   │   ├── memory.js           # Memory/RAG panels
│   │   │   ├── account.js          # Account/billing
│   │   │   ├── store.js            # App store / marketplace
│   │   │   ├── tools.js            # Tool management
│   │   │   ├── design.js           # Design system
│   │   │   ├── automations.js      # Routines/automations
│   │   │   ├── desktop.js          # macOS window management
│   │   │   └── ultra.js            # Ultra/research desk
│   │   └── icons/glass/            # Liquid glass icon set (81 SVGs)
│   ├── src/
│   │   ├── app/
│   │   │   ├── app/page.tsx        # /app route → iframe to shell.html
│   │   │   └── api/                # Next.js API routes (proxy to backend)
│   │   └── components/             # 133 React components
│   │       └── chat.tsx            # Main chat component (8157 lines)
│   └── package.json
│
├── docs/
│   ├── LOVABLE-HANDOFF.md          # THIS FILE
│   ├── design/
│   │   ├── reference-mockup.html   # THE macOS mockup (open in browser)
│   │   ├── FEATURE-LEDGER.md       # Feature status ledger
│   │   ├── STATE-MODEL.md          # Frontend state model
│   │   ├── PORT-COVERAGE.md        # Port coverage analysis
│   │   ├── ICON-MAP.md             # Icon assignments
│   │   ├── PRODUCTION-ROADMAP.md   # Production roadmap
│   │   └── GAPS-RECOVERED.md       # Gaps analysis
│   └── screenshots/                # Current state screenshots
│
├── FEATURE-INVENTORY.md            # All 182 features checklist
├── TAIGA-REQUIREMENTS.md           # Full requirements spec
├── USER-CASES.md                   # User test cases (381 lines)
├── ARCHITECTURE-MAP.md             # System architecture
├── WIRING-PLAN.md                  # Feature → endpoint mapping
├── BUGS-FOUND.md                   # Known bugs
└── REBUILD-BRIEF.md                # Rebuild brief
```

---

## What's Working vs What's Not

### Backend: 95% complete
All API endpoints built and tested. Working:
- Chat streaming (all modes)
- Model routing and catalog
- Brain/Council/Compare/Research modes
- Agent-OS orchestration + debate
- Image/Video/Music/TTS generation
- Memory CRUD + RAG
- Skills install + run
- MCP connectors
- Billing/balance
- Search
- User accounts

### Frontend: 60% wired
The shell.html + 14 JS modules have the UI built but many features are either:
- Toast-only (button exists but shows "coming soon" toast)
- Partially wired (UI renders but backend call is missing or broken)
- Fully working (chat, ultra desk, mode switching, some studio functions)

**The Lovable build should START FRESH from the design mockup, not try to fix the existing shell.html.** Build clean React components that call the backend API directly.

---

## User Personas

1. **Power user (main target):** Russian tech-savvy user who wants uncensored AI, multiple models, and agent capabilities. Uses Brain mode, custom skills, terminal.

2. **Casual user:** Wants a better ChatGPT in Russian. Uses basic chat, image generation, voice input.

3. **Developer:** Wants the agent-OS, terminal, skills, MCP connectors. Builds custom workflows.

4. **Owner (admin):** Manages the instance — billing, users, model catalog, server config.

---

## Non-Negotiables

1. **Russian language everywhere** — ALL UI text in Russian
2. **Dark theme** — No light mode (yet)
3. **macOS desktop aesthetic** — Window chrome, dock, sidebar, traffic lights
4. **Single amber accent #FF9E64** — No other accent colors
5. **No emoji in UI** — Only SVG/line icons
6. **Provider names hidden** — User sees "Тайга ИИ", never "Venice" or "NanoGPT"
7. **Backend is the source of truth** — Frontend is just a client, no frontend DB
8. **SSE streaming** — Responses must stream word-by-word, not load-then-display
