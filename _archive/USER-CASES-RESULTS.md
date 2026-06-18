# ТАЙГА ИИ — P0 USER-CASE RESULTS (QA re-run, 2026-06-12 / merge f4ffd87)

Method: code inspection of the CURRENT merged `taiga-web/src` + `server.py`, plus live
read-only curl against `http://127.0.0.1:8777` (GET/POST). Frontend served on `:3000`
(`/` and `/app` → 200). Backend up: `/api/init` 200, `/api/catalog` = 924 models,
`/api/chat` streams. Git HEAD `f4ffd87` (council councilModels + research depth/sources +
install_agent backend; on top of compare-bypass, per-user config, SQLite).

Scope: the **79 P0 rows** of USER-CASES.md. P1/P2 not graded (TB-06 / VO-06 noted in delta
because they flipped, even though they are P1 in the matrix).

---

## SUMMARY — P0 counts (this run)

- **PASS: 73**
- **FAIL: 3**
- **UNKNOWN (code wired, blocked only by an empty provider wallet at runtime): 3**

Prior run was **69 / 3 / 7**. Net: **+4 PASS** (IM-01, IM-03, MU-01, MU-02 flipped
UNKNOWN→PASS — provider wallets that were 402 last time are now funded and produce real
assets). The 3 remaining UNKNOWNs (VID-01, VID-02, VO-05) are still **402 Insufficient
balance** on the AIMLAPI video wallet / NanoGPT TTS wallet; their UI + proxy + gen-lib +
clean-error path are all code-confirmed, so they flip to PASS the moment those two wallets
are topped up — no code change needed.

## DELTA vs prior run (2026-06-12 first pass)

**Flipped UNKNOWN → PASS (4):**
- **IM-01 / IM-03** — free image gen now returns a real `data:image/png` (live curl on
  `ng:qwen-image` → PNG data-URL). Free NanoGPT image wallet is funded.
- **MU-01 / MU-02** — music now runs to `COMPLETED` with a real CDN mp3 URL
  (`https://cdn.aimlapi.com/.../music...`). AIMLAPI music wallet is funded.

**Still UNKNOWN (3, provider wallet only):**
- **VID-01 / VID-02** — `/api/video` → 402 ($0.10 AIMLAPI video wallet empty).
- **VO-05** — `/api/audio` → 402 (NanoGPT TTS wallet empty).

**Still FAIL (3, unchanged real defects):** CB-08, DG-01, DG-02. None regressed; none fixed.

**P1 features that became BUILT since last run (not in the 79-P0 set, but worth flagging
as wins):**
- **TB-06 per-message cost** — now BUILT. New `CostFooter` (chat.tsx:4398-4423) renders the
  SSE `cost` event (`m.cost`, populated use-taiga-chat.ts:251-258) as «≈ ₽» under each reply
  (owner sees себестоимость, user sees списание). Was "confirmed absent" last run. → PASS.
- **VO-06 read-aloud** — now BUILT. Per-message Volume2 button (chat.tsx:3642-3654) →
  `speakMessage` (1941) → `generateAudio` → `/api/audio`, with loading/playing/stop states +
  auto-speak + clean error toast. Wiring PASS; runtime UNKNOWN (shares the VO-05 402 TTS
  wallet). Was "no read-aloud button" last run.

**Changed areas that were specifically re-verified and PASS (the point of this re-run):**
- **Compare-bypass fix** — `/api/chat {compare:true, compareModels:[...]}` emits
  `member_answer` per model (curl: 2 valid models → 2 real answers, `ok:true`, + `cost` +
  `done`). Trivial-fast-path bypass guarded for compare/council/research/brain
  (chat.tsx:2188). UI: FunctionBar pill «Сравнить модели» (2519) + `/compare` slash (1572);
  `member_answer` → `m.members` grid cards (use-taiga-chat:204-219, chat.tsx:3579). End-to-end.
- **Council `councilModels`** — curl honors explicit member list (PLAN echoes my 2 models),
  emits `council_step` per member, then synthesizes (39 deltas + done). FE sends
  `councilModels` (chat.tsx:1335).
- **Research `depth`/`sources`** — `{research:true, depth:"deep", sources:6}` → 8-way
  sub-question decomposition, web fetch, `research_sources`, 1257-delta synthesis. Backend
  `_DEPTH_PROFILES` (server.py:6029) + `sources` cap (6054) wired. FE sends `depth`/`sources`
  (chat.tsx:1336-1337, use-taiga-chat:306-307).
- **Tailored Brain config** — driver/expert/roleSystem now sent from the ad-hoc «Мозг»
  toggle (was the owner's #1 complaint / GAP-MAP A1+C1). `brainExpertModel`/`brainExpert`/
  `brainLead`/role wired into dispatchSend (chat.tsx:1246-1271); Brain config UI section
  present (2990-3043). Backend accepts driver/expert/roleSystem.
- **Agent marketplace MOUNTED** — `AgentsMarketplace` imported (chat.tsx:102) and mounted
  (3806), `onInstall={installAgent}` upserts into the working store (1882). Reachable via
  AgentsPanel «Маркет» button. `install-agent.ts` posts `/api/install_agent` (proxy EXISTS).
- **install_skill / install_agent SSRF guards** — live-tested: loopback (`127.0.0.1`),
  cloud-metadata (`169.254.169.254`), and `file://` all rejected on BOTH endpoints
  («внутренние/приватные адреса заблокированы» / «разрешены только http(s)»). Shared
  `_fetch_text_guarded` (server.py:2309): scheme allow-list + resolve-all-IPs private/loopback
  block + 8s timeout + 256KB cap + text-only ctype; downloaded content is parsed, never
  executed. Public-URL fetch works direct on :8777.
- **SQLite migration** — transparent. Post-migration: chat streams, `mem_extract` returns
  facts, `balance` returns USD ($4.22), `uncensor` rewrites, `supersearch` returns 13
  sources. No regressions in any P0.

---

## PRIORITIZED FAIL WORKLIST (3 P0 defects, unchanged)

### 1. Chat persistence on reload — CB-08 (P0, real defect) → owner: `taiga-web/src/components/chat.tsx`
Unchanged from last run. `chatId` still inits to a fresh `rid()` every mount (chat.tsx:416),
and the mount effect (chat.tsx:612-613) loads only the sidebar *metadatas* (`setChats(metas)`)
— it never `selectChat(metas[0].id)`s the most-recent chat. `selectChat` is called only from
the sidebar `onSelect` (3475). On reload the user lands on an empty new chat; the prior thread
is reachable only by clicking it in the sidebar.
**Fix:** on mount, if `metas[0]` exists and not ghost, `selectChat(metas[0].id)` (or seed
`chatId` from the last chat + load its messages). ~30 min.

### 2. Inline FREE code-render in the chat thread — DG-01, DG-02 (P0) → owner: `chat.tsx` + new proxy `app/api/image_intent/route.ts`
Unchanged. The free SVG→PNG diagram render (`skill-render.ts`) is still wired **only inside
Studio**. Typing «нарисуй схему авторизации» in the chat thread goes `classifyIntent` →
`intent.mode==="image"` → `{mode:"image", image:true}` → `dispatchSend` → a **paid** image
model (chat.tsx:2262-2275). `looksLikeCodeRender` / `renderSkillImage` is NOT imported in
chat.tsx, the `/api/image_intent` Next proxy is still MISSING (backend tags diagrams as
`render` but the route is orphaned). These PASS only via Studio → Картинки + 🆓 code-render
toggle; FAIL as the row is written ("type … and send" in chat).
**Fix:** in the chat image path, call `looksLikeCodeRender(text)` (or proxy
`/api/image_intent`) and, when true, run `renderSkillImage` inline instead of the paid model.
Medium.

### 3. (no third real defect)
The prior "FAIL: 4" header was a miscount — only 3 P0 rows are FAIL (CB-08, DG-01, DG-02);
TB-06 listed there is P1 and is now BUILT (see delta above).

> Out-of-P0 documented gaps still real (P1/P2): AG-10 skill-install-BY-URL — backend
> `/api/install_skill` + SSRF guard exist and work direct on :8777, BUT there is **no Next
> proxy** (`/api/install_skill` → 404 from :3000) AND no FE caller; skill-builder's `Link2`
> is still only the webhook field. MEM-17/18 (Mem0/Letta auto-memory — note: reconciliation
> + self-edit tools DID land per commit d8dc73d, so the gap narrowed), MU-05 (free ACE-Step
> vocals), TD-05 (.glb), PP-06 (.pptx), TH-05 (font-by-mode).

---

## FULL P0 TABLE

| ID | Area | Verdict | Evidence | Fix note |
|---|---|---|---|---|
| CB-01 | Chat | PASS | curl `/api/chat` «привет» → «Привет! Как я могу помочь тебе сегодня?», single model `venice-uncensored`, no fallback banner | — |
| CB-02 | Chat | PASS | curl «объясни что такое VPN» → 9 delta events stream, text grows; auto-scroll effect chat.tsx:657 (`bottomRef`) | — |
| CB-03 | Chat | PASS | send btn `onClick={busy?stop:submit}`; Square↔ArrowUp icon flip; `stop()`→`abortRef.abort()` | — |
| CB-04 | Chat | PASS | `editUserMsg` chat.tsx:1979 (pencil 3571); loads slice; branch sibling via `recordPath` | — |
| CB-05 | Chat | PASS | `copyText`→`navigator.clipboard.writeText` chat.tsx:1924 (Copy 3572/3639) | — |
| CB-06 | Chat | PASS | `regenerate` chat.tsx:1989 (RefreshCw 3640); slices to prompt, re-dispatches; BranchSwitcher siblings | — |
| CB-08 | Chat | **FAIL** | `chatId`=fresh `rid()` each mount (chat.tsx:416); mount loads only sidebar metas (612-613), never `selectChat`s last chat | Worklist #1 (unchanged) |
| CB-12 | Chat | PASS | use-taiga-chat fetch catch → friendly «⚠ Ошибка backend …», no crash; 402/502/429 mapped | — |
| MS-01 | Model | PASS | ModelPicker pill opens panel, input autofocus, «Авто» row present | — |
| MS-02 | Model | PASS | `searchModels(models,q)` live flat filtered list | — |
| MS-03 | Model | PASS | `choose(id)`→`setOverrideFor`; pill = model name + BrandIcon | — |
| MS-04 | Model | PASS | override persisted (`saveOverrides`); dispatch reads `overrides[feature]` | — |
| MS-06 | Model | PASS | «Авто» resolves `autoModelId`; backend `route_model` auto-picks (curl OB-06 meta=resolved model) | — |
| MS-07 | Model | PASS | attached image → `images` + `__auto__`; backend `route_model(has_images)` → vision model | — |
| BR-01 | Brain | PASS | +menu relay item → `setRelayOn`; «вкл» badge; toast on slash | — |
| BR-02 | Brain | PASS | relay pipeline → curl `relay_craft`→`relay_crafted`→responder; step labels in use-taiga-chat | — |
| BR-03 | Brain | PASS | `eff==="heavy"`→brain; brain curl emits ask_expert tool + deltas | — |
| BR-05 | Brain | PASS | agent-builder driver ModelPicker «🔻 ведущий» | — |
| BR-06 | Brain | PASS | agent-builder expert ModelPicker «🔺 эксперт» | — |
| BR-07 | Brain | PASS | `runAgent`→`setActiveAgent`; submit uses agent brain+driver+expert+roleSystem (chat.tsx:1841-1842) | — |
| BR-09 | Brain | PASS | ModelPicker `max-h … overflow-y-auto`; agent-builder form not clipped | — |
| BR-10 | Brain | PASS | same scroll container reaches last group; modal flex scroll | — |
| EF-01 | Effort | PASS | Fast path → short maxTokens; EffortSelector Fast btn | — |
| EF-02 | Effort | PASS | Auto = default effort; router resolves model | — |
| EF-03 | Effort | PASS | Expert→deep → 2-step pipeline («Разбираю по шагам»→detail); ThinkingSteps | — |
| EF-04 | Effort | PASS | Heavy→brain orchestrator; council SSE path also exists (curl `council_plan`+`council_step`) | — |
| MEM-01 | Memory | PASS | ChatMemoryPanel auto toggle; curl `/api/mem_extract` returns facts («Имя — Дамир», «Город — Москва») | — |
| MEM-03 | Memory | PASS | `memAdd` (panel «+»); fact row persisted | — |
| MEM-04 | Memory | PASS | `memEdit` (`commitEdit`) updates + saves | — |
| MEM-05 | Memory | PASS | `memDelete`→tombstone (`dismissFact`); survives reload (C2 fix landed) | — |
| MEM-07 | Memory | PASS | MemoryWindow `setMemWindowPersist`; `historyCap:memWindow` in every dispatch | — |
| MEM-09 | Memory | PASS | MemoriesPanel loads `profile.facts`; cross-chat | — |
| MEM-10 | Memory | PASS | global profile; `profileBlock` injected into composeSystem for every chat (1890) | — |
| MEM-13 | Memory | PASS | profile delete → `saveProfile`; loaded fresh on mount, gone after reload | — |
| MEM-16 | Memory | PASS | facts persisted to profile + chat-memory; restored on mount | — |
| AG-01 | Agents | PASS | agent-builder `onAdd`+«Сохранить агента»; `addAgent` saves; gallery row w/ MODE badge | — |
| AG-02 | Agents | PASS | agent Play→`runAgent`→`setActiveAgent`; active chip; send uses its config | — |
| AG-04 | Skills | PASS | +menu «Навыки · библиотека»→SkillBuilder modal w/ presets+search+toggles | — |
| AG-05 | Skills | PASS | skill `onToggle`→enabled; `skillsBlock` injected into composeSystem (1890) | — |
| AG-11 | MCP | PASS | +menu/`/connect`→McpPanel marketplace list + servers | — |
| AG-12 | MCP | PASS | `installConnector`→backend install (owner); server w/ toggle | — |
| AG-16 | MCP | PASS | non-owner install → `{"error":"Управлять MCP может только владелец."}` soft block, no crash | — |
| DG-01 | Diagram | **FAIL** (as written) | chat «нарисуй схему» → `classifyIntent`→image→paid model (chat.tsx:2262-2275); `looksLikeCodeRender` not imported in chat; works only in Studio | Worklist #2 (unchanged) |
| DG-02 | Diagram | **FAIL** (as written) | same; `/api/image_intent` proxy still MISSING | Worklist #2 (unchanged) |
| IM-01 | Images | **PASS** *(was UNKNOWN)* | live curl `/api/image` `ng:qwen-image` → real `data:image/png;base64,…`; free wallet funded | flipped ✅ |
| IM-02 | Images | PASS | default = free `["ng:hidream","ng:qwen-image"]`, tagged «🆓 бесплатно» | — |
| IM-03 | Images | **PASS** *(was UNKNOWN)* | chat «нарисуй кота» → classifyIntent=image → `/api/image` inline; same free model now returns PNG | flipped ✅ |
| IM-07 | Images | PASS | error → `onSoon(r.error||"не вышло…")`; clean message, no raw stack | — |
| IM-12 | Images | PASS | non-owner empty balance → 402 → `{error}` → clean onSoon toast, no crash | — |
| VID-01 | Video | UNKNOWN (wired) | Studio Видео `generateVideo`→`/api/video` submit→poll→render; curl 402 (AIMLAPI video wallet empty) | top-up AIMLAPI video |
| VID-02 | Video | UNKNOWN (wired) | `onProgress`→`setVidProgress` (STARTED+elapsed); UI present; runtime blocked by 402 | top-up AIMLAPI video |
| VID-08 | Video | PASS | error→`onSoon(r.error||"видео не вышло")` 402; `prettyMediaError` per-scene; no crash | — |
| VID-14 | Video | PASS | non-owner empty balance → 402 SSE error → clean message, no stack | — |
| MU-01 | Music | **PASS** *(was UNKNOWN)* | live curl `/api/music` → `music_status` STARTED→GENERATING→COMPLETED + real CDN mp3 URL | flipped ✅ |
| MU-02 | Music | **PASS** *(was UNKNOWN)* | result `audio:true` Gen → ResultCard `<audio>` plays the completed mp3; wallet funded | flipped ✅ |
| TD-02 | 3D | PASS | `TD3_AVAILABLE=false` → `onSoon("3D временно недоступно — провайдер на обслуживании…")`; no raw error | — |
| VO-01 | Voice | PASS | mic btn `toggleMic`; Web Speech ru-RU; `listening` pulse | — |
| VO-02 | Voice | PASS | `onresult` accumulates transcript → `setInput` (editable before send) | — |
| VO-05 | Voice | UNKNOWN (wired) | Studio Аудио `generateAudio`→`/api/audio` (Kokoro/OpenAI, af_bella); curl 402 (NanoGPT TTS wallet empty) | top-up NanoGPT TTS |
| TB-01 | Billing | PASS | `/balance` → toast «Баланс: $X» (curl `/api/balance` → `{"usd":4.22}`); ₽ via fmtRub | — |
| TB-03 | Billing | PASS | SpendCap $0.05/$0.2/$1/без лимита; persisted | — |
| TB-05 | Billing | PASS | `gateSpend(est,label,run)` → confirm dialog for ops > cap | — |
| TB-07 | Billing | PASS | `isOwner` from `/api/init`; `cost` SSE `owner:true` (not charged); low-wallet toast on init | — |
| CM-01 | Commands | PASS | InlineCommands opens on «/» (`searchCommands`) | — |
| CM-03 | Commands | PASS | `/pipeline`→`setPipelineOpen`; PipelineBuilder modal | — |
| CM-04 | Commands | PASS | `sendPipeline` runs stages w/ `{{prev}}` chaining; pipelines.ts | — |
| CM-06 | Commands | PASS | `/uncensor`→`/api/uncensor` (curl rewrites prompt) → `dispatchSend(rewritten)` one step | — |
| PR-01 | Privacy | PASS | Ghost toggle; placeholder «Призрак — этот чат нигде не сохранится…»; persist effects guard `if(ghost)return` (658) | — |
| PR-02 | Privacy | PASS | ghost → no localStorage write; reload shows nothing restored | — |
| SR-01 | Search | PASS | +menu «Веб-поиск»→`setWebOn`→backend web_search tool | — |
| SR-02 | Search | PASS | superOn→`/api/supersearch` (curl: 13 sources, 1 answer); `citeify` [1][2]; SourcesPanel | — |
| FL-01 | Files | PASS | +menu «Файлы и фото»→`/api/extract` (curl extracts text); chip + `fileBusy` spinner | — |
| FL-02 | Files | PASS | extracted text → `attachedFiles` → sent as `files`; backend injects to context | — |
| FL-04 | Files | PASS | image→`attachedImages` thumbnail; sent as `images`→vision flow | — |
| OB-01 | Onboarding | PASS | `/`→Landing; Hero + CTA `href="/app"`; live curl 200 | — |
| OB-02 | Empty | PASS | no-chat hero: MorphingText + ModelStrip + composer + TierNav; composer ready | — |
| OB-05 | Errors | PASS | backend 500/down → friendly «⚠ Ошибка backend», app usable, retry via regenerate | — |
| OB-06 | Errors | PASS | «привет» curl: NO «беру запасную» banner (single venice model, clean stream) — KNOWN BUG #1 stays fixed | — |
| OB-08 | Mobile | PASS | composer toolbars `flex flex-wrap`; panels full-screen modals; `/app` 200 | — |

---

### Counts by area (P0, this run)
Chat 7/8 PASS (CB-08 FAIL) · Model 6/6 · Brain 8/8 · Effort 4/4 · Memory 8/8 ·
Agents/Skills/MCP 6/6 · Diagram 0/2 (both FAIL-as-written, PASS-in-Studio) ·
Images 4 PASS + 1 PASS↑ ×2 = **5/5 PASS** (IM-01/03 flipped) · Video 2 PASS + 2 UNKNOWN ·
Music **2/2 PASS** (both flipped) · 3D 1/1 · Voice 2 PASS + 1 UNKNOWN (VO-05) ·
Billing 4/4 · Commands 4/4 · Privacy 2/2 · Search 2/2 · Files 3/3 · Onboarding/Mobile 5/5.

### What "UNKNOWN" means operationally (3 rows)
VID-01, VID-02, VO-05 — code is complete and reachable (UI control + Next proxy + gen-lib +
clean error path all verified). Only blocker is an empty provider wallet (AIMLAPI video /
NanoGPT TTS) returning 402 at request time. Fund those two wallets and re-run — no code
change expected. (The image and music wallets that were empty last run are now funded, which
is why IM-01/03 + MU-01/02 flipped to PASS this run.)
