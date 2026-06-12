# ТАЙГА ИИ — USER-CASE TEST MATRIX (v1)

Comprehensive, USER-POV behaviour matrix. Each row is independently runnable by a human tester
or a browser-automation agent against the live app (`/app` route; landing at `/`).

**Columns:** ID · Area · User action (step by step) · Expected behaviour (user POV) · How to verify (observable UI/DOM signal) · Priority (P0 must / P1 should / P2 nice)

**Legend in notes:**
- ⚠️ **NOT BUILT / WILL FAIL** — feature is in the docs / planned but code shows it is absent or stubbed. Test it anyway; it documents the gap.
- 🟡 **PARTIAL** — present but not the full spec from PARITY-MATRIX.
- 🔒 **OWNER-GATED** — backend gates this to the owner identity; a normal user sees a soft block, not a crash.

**Cross-reference of what's actually built (from code, 2026-06-12):**
- Composer: `+` menu (PlusMenu, 16 items), EffortSelector (Fast/Auto/Expert/Heavy), ModelPicker (800-model search + privacy filter + brand groups), FunctionBar, MemoryWindow (memory slider), SpendCap, ghost/private/perm-mode toggles, mic (Web Speech STT), slash-commands (BUILTINS ~70).
- Brain/Relay: `relayOn`/`brainOn` real two-model backend pipelines (`/api/chat` with relay/brain); driver=ведущий, expert=эксперт; thinking steps via SSE (relay/ask_expert).
- Studio (image-studio.tsx): 8 sub-tabs — Картинки/Видео/Аудио/Аватар/Тулзы/Музыка/Кино/3D + Agents gallery. 3D `live:false` (provider down). FREE code-render (skill-render.ts: SVG→PNG diagrams, slides→MP4 with free Google TTS narration).
- Memory: chat-memory-panel (auto toggle, add/edit/lock/delete), memories-panel (cross-chat profile facts + style note), profile.ts, style-profile.ts.
- Skills: skill-builder (library by category + on/off toggles + search + custom), import-skill (by files/URL).
- MCP: mcp-panel (marketplace install / toggle / remove / add-by-URL) 🔒 owner-gated.
- Agents: agent-builder (brain/relay dual-model save-as-button), agent-gallery, orchestrator-panel.
- Commands: /pipeline (pipeline-builder), /uncensor, command-palette (slash discovery).
- Billing: money.ts (₽ from USD), balance display, SpendCap per-op limit, owner detection.
- Voice: STT via Web Speech (mic); studio Аудио tab = TTS (Kokoro/OpenAI). **No per-message read-aloud button.**
- Themes: theme.ts (midnight/slate/cyberpunk) + theme-panel.tsx picker, opened from Settings → «Тема и акцент» (BUILT). Font-by-mode NOT built.

**Known gaps that produce WILL-FAIL cases (see flagged rows):** ACE-Step free-music tier (only paid AIMLAPI), per-message cost display, per-message read-aloud, 3D `.glb` (provider triposr down), font-by-mode, native `.pptx` export, skill-install-by-URL (only file import exists), Mem0/Letta long-term auto-memory (backend not built per REMAINING-V1.md). MCP is owner-gated (expected, soft-block — not a fail).

---

## 1. Chat basics — send / stream / stop / retry / edit / copy / regenerate

| ID | Area | User action | Expected behaviour (user POV) | How to verify | Priority |
|---|---|---|---|---|---|
| CB-01 | Chat | Open `/app`, type «привет», press Enter | Reply streams in word-by-word within ~2s; trivial-greeting path keeps it short | Assistant bubble appears, text grows incrementally, no "беру запасную" banner | P0 |
| CB-02 | Chat | Type a real question «объясни, что такое VPN», send | Answer streams token-by-token, scroll auto-follows to bottom | `bottomRef` keeps view pinned; text length increases over time | P0 |
| CB-03 | Chat | While a long answer is streaming, click the Stop (■) button | Generation halts immediately; partial text stays; button reverts to ↑ | Send button icon flips Square→ArrowUp, network stream closes | P0 |
| CB-04 | Chat | After a reply, hover the user message, click «править» (pencil) | The user message becomes editable; resubmitting produces a fresh answer and forks the branch | Edit affordance appears; new sibling branch recorded in msg-tree | P0 |
| CB-05 | Chat | Hover an assistant reply, click «копировать» | Full reply text is copied to clipboard; brief confirmation | Clipboard contains message; (toast/checkmark) | P0 |
| CB-06 | Chat | Hover an assistant reply, click «заново» (regenerate) | A new answer replaces/branches from the same prompt; old one reachable via branch switcher | New assistant content; `<BranchSwitcher>` shows ≥2 siblings | P0 |
| CB-07 | Chat | Send a message, then click «ветка» (fork) on a reply | Conversation forks into a new chat; original stays intact | New chat in sidebar; original unchanged | P1 |
| CB-08 | Chat | Send 3 messages, reload the page | Whole conversation reappears exactly as left | Messages restored from storage on mount | P0 |
| CB-09 | Chat | Press Enter on an empty input | Nothing sends; send button stays disabled | Send button disabled state when `!input.trim()` | P1 |
| CB-10 | Chat | Type a multi-line message with Shift+Enter | Newline inserted, message NOT sent until Enter | Textarea grows; no submit on Shift+Enter | P1 |
| CB-11 | Chat | Use branch switcher arrows after an edit/regenerate | Can move between answer variants; each variant's text shown | BranchSwitcher prev/next changes rendered content | P1 |
| CB-12 | Chat | Send while offline / backend down | Clean error message, not a stack trace; can retry | Friendly RU error text in chat, no crash | P0 |

## 2. Model selection & switching

| ID | Area | User action | Expected behaviour | How to verify | Priority |
|---|---|---|---|---|---|
| MS-01 | Model | Click the model pill in the composer | Dropdown opens showing «Авто» + brand groups; search box focused | ModelPicker panel opens, input autofocus, «Авто» row present | P0 |
| MS-02 | Model | In the picker, type «claude» | List filters live to matching models across providers | Filtered flat list under search; non-matches hidden | P0 |
| MS-03 | Model | Pick a specific model (e.g. a Claude model) | Pill label updates to that model name + brand icon; «Авто» no longer active | Pill text = chosen model name, BrandIcon shown | P0 |
| MS-04 | Model | Send a message after picking a model, then send another | The chosen model "sticks" for subsequent messages (per feature) | Override persists in `overrides[feature]`; pill unchanged across sends | P0 |
| MS-05 | Model | Expand a brand group (click chevron) | Group expands to show that brand's models with ум/контекст/свобода badges | Group rows render ModelRow children with stat badges | P1 |
| MS-06 | Model | Leave model on «Авто», send a coding question | Auto-router picks a strong model for the task; label shows «Авто · <model>» | Auto label includes resolved model name; reply produced | P0 |
| MS-07 | Model | Attach an image and ask «что на фото?» | A vision-capable model is auto-selected; image is described | Vision feature engaged; description references image content | P0 |
| MS-08 | Model | Pick a model that is currently down, then send | Either it's hidden from the list, or a fallback is used with a clear note | Unhealthy models filtered (`healthyOnly`); current selection kept visible | P1 |
| MS-09 | Model | Use the privacy filter «TEE» in the picker | List narrows to TEE/private models only | privFilter applied, only TEE-toned rows remain | P1 |
| MS-10 | Model | Switch model mid-chat, then regenerate an old reply | New model answers the regenerate; prior turns keep their original model | Regenerate uses current override; branch shows new content | P1 |
| MS-11 | Model | Open picker, clear search → see grouped-by-company view | Models grouped by brand with counts per brand | groupByBrand sections with count badges | P2 |
| MS-12 | Model | Run `/model claude` from the composer | Picker opens pre-focused (openSignal) for quick switch | `/model` bumps openSignal → dropdown opens | P1 |
| MS-13 | Model | Hover a model row | Shows ум score, context window, % свобода, privacy badge, capabilities | ModelRow badges visible (sp, fmtCtx, uncensored_pct, caps) | P2 |
| MS-14 | Model | Search a nonsense string «zzzzz» | «Ничего не нашлось» empty state, no crash | Empty-state text rendered | P2 |

## 3. Relay / Brain («Мозг») — change brain, lead vs expert, thinking steps

| ID | Area | User action | Expected behaviour | How to verify | Priority |
|---|---|---|---|---|---|
| BR-01 | Brain | From `+` menu pick «Улучшить · дешёвая правит → умная отвечает» | Relay toggles ON (pill highlighted); toast explains it | `relayOn=true`, item shows active state, toast shown | P0 |
| BR-02 | Brain | With relay ON, send a messy/short prompt | Two visible steps: «Причёсываю запрос» → «Спрашиваю эксперта»; final clean answer | SSE relay_craft → relay_crafted → expert answer; thinking step labels | P0 |
| BR-03 | Brain | Set Effort = Heavy, then send a hard question | Brain mode engages: driver triages → expert answers complex part | `brain=true` path; thinking steps incl. ask_expert | P0 |
| BR-04 | Brain | Run `/relay` slash command | Same as +menu relay toggle; toast «Улучшить вкл/выкл» | relay handler fires, toast text matches | P1 |
| BR-05 | Brain | Open Agent builder, choose «🧠 МОЗГ», pick ведущий (lead) model | Lead/driver model selectable via its own ModelPicker (uncensored feature) | driver ModelPicker renders with «🔻 ведущий» label | P0 |
| BR-06 | Brain | In Agent builder pick эксперт (expert) model | Expert model selectable via second ModelPicker (ultra feature) | expert ModelPicker renders with «🔺 эксперт» label | P0 |
| BR-07 | Brain | Save a МОЗГ agent, then press its Play button | Agent activates; next message routes through that driver→expert pair | activeAgent set; subsequent send uses brain override | P0 |
| BR-08 | Brain | During a brain answer, expand the thinking trace | Steps «думаю по шагам» are collapsible and readable | thinking-steps component toggles open/closed | P1 |
| BR-09 | Brain | Open the lead model dropdown inside agent builder | Dropdown shows the FULL model list and scrolls smoothly | Picker panel `max-h` scroll container; all healthy models reachable | P0 |
| BR-10 | Brain | Scroll the model dropdown to the bottom | Bottom models reachable; no clipped/cut list | overflow-y-auto reaches last group; no clipping | P0 |
| BR-11 | Brain | Verify the expert answer differs in depth from the lead's draft | Final expert answer is richer/cleaner than the raw prompt | Two-phase output; final answer is the polished one | P1 |
| BR-12 | Brain | Toggle relay OFF, send same prompt | Single-model normal answer, no «причёсываю» step | relayOn=false; no relay SSE steps | P1 |
| BR-13 | Brain | Choose МОЗГ with both models on «Авто» | Sensible defaults resolved (cheap uncensored lead, strong expert) | resolve() falls back to autoModelId; agent saved with concrete ids | P1 |
| BR-14 | Brain | Add a role instruction to the agent («отвечай как юрист РФ») | Role applied to expert's system prompt; answers in that persona | roleSystem/inst passed to backend; persona evident in reply | P1 |

## 4. Effort modes — Fast / Auto / Expert / Heavy

| ID | Area | User action | Expected behaviour | How to verify | Priority |
|---|---|---|---|---|---|
| EF-01 | Effort | Click «Fast» in the effort selector, send | Fast non-thinking model, short reply, quick | active-effort pill on Fast; reply concise/fast path | P0 |
| EF-02 | Effort | Click «Auto», send | Router picks the model itself (default behaviour) | Auto highlighted; auto-route applied | P0 |
| EF-03 | Effort | Click «Expert», send a reasoning question | Step-by-step thinking visible, longer developed answer | Expert highlighted; thinking trace present | P0 |
| EF-04 | Effort | Click «Heavy», send a hard question | Council/brain-orchestrator engages (multiple models) | Heavy highlighted; brain path; toast «совет моделей» | P0 |
| EF-05 | Effort | Switch Fast→Heavy and observe the moving pill | Animated highlight slides between modes (layoutId) | motion `active-effort` animates between buttons | P2 |
| EF-06 | Effort | Reload after selecting Expert | Effort choice persists across reload | effort restored from storage (setEffortPersist) | P1 |
| EF-07 | Effort | Hover each effort button | Tooltip explains the mode («Быстро…», «Думает по шагам», etc.) | title attr text matches EFFORTS hints | P2 |
| EF-08 | Effort | Compare Fast vs Expert answer length on same prompt | Expert is visibly longer/deeper than Fast | Two answers differ in length/structure | P1 |

## 5. Memory

| ID | Area | User action | Expected behaviour | How to verify | Priority |
|---|---|---|---|---|---|
| MEM-01 | Memory | Open chat-memory panel (`/memory`), toggle Auto-memory ON | Toggle turns on; Тайга will record facts as you chat | auto=true; toggle visual on | P0 |
| MEM-02 | Memory | Toggle Auto-memory OFF | No new facts captured for this chat | auto=false; no new facts added after | P1 |
| MEM-03 | Memory | In chat-memory panel, click «+» and add a fact «меня зовут Дамир» | Fact appears in the list immediately | New Fact row rendered, persisted | P0 |
| MEM-04 | Memory | Edit an existing fact's text | Edited text saved and shown | commitEdit updates fact; storage updated | P0 |
| MEM-05 | Memory | Delete a fact (trash icon) | Fact removed from list and STAYS deleted after reload | onDelete removes; not present after reload | P0 |
| MEM-06 | Memory | Lock/pin a fact (lock icon) | Fact marked protected; not auto-pruned | onToggleLock sets locked; lock icon state | P1 |
| MEM-07 | Memory | Set the memory slider «контекст: N последних сообщений» | Only last N turns sent as context | MemoryWindow value changes; memWindow persisted | P0 |
| MEM-08 | Memory | Lower the slider to a small N, ask «что я говорил в начале?» | Тайга only "remembers" the last N messages | Earlier context absent from reply | P1 |
| MEM-09 | Memory | Open Memories panel (cross-chat profile), view profile facts | Facts known across ALL chats listed | memories-panel loads profile.facts | P0 |
| MEM-10 | Memory | Add a cross-chat profile fact, open a DIFFERENT chat | The fact applies in the new chat (after reload/open) | Profile loaded into new chat session | P0 |
| MEM-11 | Memory | Edit the «как ты пишешь (стиль)» style note | Style note saved; future replies adapt tone/slang | saveStyle persists; style applied to system | P1 |
| MEM-12 | Memory | Type with consistent slang, watch the style note | Тайга auto-notes your manner (slang/typos/mixed langs) | style-profile updates over time | P1 |
| MEM-13 | Memory | Delete a profile fact, reload | Deleted fact does NOT come back | persistFacts removes; gone after reload | P0 |
| MEM-14 | Memory | Run `/forget` in a chat | Тайга forgets everything for THIS chat after confirm | forget handler clears chat memory | P1 |
| MEM-15 | Memory | Clear all profile facts (clear-all button) | All cross-chat facts wiped | persistFacts([]) empties list | P1 |
| MEM-16 | Memory | Reload after adding 3 facts | All 3 facts persist | facts restored from profile storage | P0 |
| MEM-17 | Memory | ⚠️ Expect long-term AUTO-fact extraction (Mem0/Letta) — chat naturally, never opening memory | Тайга should auto-extract & reconcile facts (ADD/UPDATE/DELETE) so memory "grows smarter" | **WILL FAIL** — REMAINING-V1.md: Mem0/Letta backend NOT built (0 grep hits). Only manual + RAG today | P1 |
| MEM-18 | Memory | ⚠️ Contradict an earlier fact and expect reconciliation | Old fact updated/superseded, not duplicated | **WILL FAIL** — reconciliation (Mem0) not implemented | P2 |

## 6. Agents & skills

| ID | Area | User action | Expected behaviour | How to verify | Priority |
|---|---|---|---|---|---|
| AG-01 | Agents | Run `/agent`, fill name + lead + expert, click «Сохранить агента» | Agent saved; appears in «твои агенты» list as a button | onAdd adds TaigaAgent; row with name + MODE badge | P0 |
| AG-02 | Agents | Press an agent's Play button | Agent activates for the chat; chip/indicator shows it's on | activeAgent set; subsequent send uses its config | P0 |
| AG-03 | Agents | Delete an agent (trash) | Agent removed from the list | onDelete removes row | P1 |
| AG-04 | Agents | Open «Навыки · библиотека» from `+` menu | Skills library opens with categories + search + on/off toggles | SkillBuilder modal; SKILL_PRESETS grouped by category | P0 |
| AG-05 | Skills | Toggle a skill (e.g. «Юрист») ON | Skill activates; ИИ follows its instruction every message | onToggle sets enabled; skillsBlock injected into system | P0 |
| AG-06 | Skills | Search skills for «sql» | Library filters to matching skills | Filtered preset list | P1 |
| AG-07 | Skills | Filter skills by a category tab | Only that category's skills shown | cat filter applied | P1 |
| AG-08 | Skills | Create a custom skill (name + instruction), save | New skill appears and is toggleable | newSkill added; row toggle works | P1 |
| AG-09 | Skills | Enable a "slang" / persona skill, then chat | Replies take on that slang/voice | Skill instruction visible in tone of replies | P1 |
| AG-10 | Skills | ⚠️ Install a skill BY URL (skill-autoinstaller) | Paste a skill URL → it's fetched and added | **WILL FAIL** — only `importSkillFiles` (file import) exists; no URL installer (the Link2 field is a webhook). MASTER-PLAN lists this as NEW | P1 |
| AG-11 | MCP | Open «Подключить инструменты (MCP)» (`/connect`) | MCP marketplace opens: named connectors + add-by-URL | mcp-panel marketplace list renders | P0 |
| AG-12 | MCP | Click Install on a marketplace connector (e.g. GitHub) | Connector installs one-click; shows installed + a toggle | installConnector → server appears with enable toggle | P0 |
| AG-13 | MCP | Toggle an installed connector OFF then ON | Enable/disable flips; its tools (un)available to agent | toggleMcp updates `enabled` | P1 |
| AG-14 | MCP | Remove an installed connector | Connector removed from list | removeMcp deletes row | P1 |
| AG-15 | MCP | Add a custom MCP by name + URL | Custom server added to list | addMcp adds; success message | P1 |
| AG-16 | MCP | 🔒 As a NON-owner, open MCP and try to install | Soft block / owner-gated message, NOT a crash | Backend gates to owner; clean refusal in UI | P0 |

## 7. Diagrams / schemes / flowcharts (FREE code-render)

| ID | Area | User action | Expected behaviour | How to verify | Priority |
|---|---|---|---|---|---|
| DG-01 | Diagram | Type «нарисуй схему авторизации по токену» and send | A rendered flowchart/scheme image appears inline within ~Xs (free SVG→PNG), downloadable | skill-render looksLikeCodeRender→true; img rendered; download link | P0 |
| DG-02 | Diagram | Ask «сделай блок-схему процесса оплаты» | Block diagram renders inline as an image | SVG generated & rasterized to PNG; inline image | P0 |
| DG-03 | Diagram | Ask «нарисуй mind-map по теме маркетинг» | Mind-map renders inline | code-render regex matches «mind map/майнд»; image shown | P1 |
| DG-04 | Diagram | Ask «организационную диаграмму компании» (orgchart) | Org chart renders as a scheme image | regex matches «организац/orgchart»; image | P1 |
| DG-05 | Diagram | Ask «таймлайн запуска продукта» | Timeline diagram renders inline | regex «timeline/таймлайн»; image | P2 |
| DG-06 | Diagram | Ask «воронку продаж» (funnel) | Funnel diagram renders | regex «воронк»; image | P2 |
| DG-07 | Diagram | Download the rendered diagram | PNG downloads with a sensible filename | download button saves taiga-*.png | P1 |
| DG-08 | Diagram | Give an impossible/garbage diagram prompt | Clean «модель не вернула SVG — попробуй переформулировать» message, not a crash | error string from skill-render rendered | P1 |
| DG-09 | Diagram | Ask for a Venn diagram «диаграмма Венна A и B» | Venn renders inline | regex «venn/венн»; image | P2 |
| DG-10 | Diagram | Verify diagram is FREE (no balance charge) | No paid-image charge; produced via code-render tier | No image-provider spend; balance unchanged | P1 |

## 8. SVG / vector graphics

| ID | Area | User action | Expected behaviour | How to verify | Priority |
|---|---|---|---|---|---|
| SV-01 | SVG | Ask «сделай SVG иконку тигра» | Vector graphic renders inline (SVG→PNG) | extractSvg returns svg; rendered image | P1 |
| SV-02 | SVG | Ask «векторный постер тайга, минимализм» | Poster-style SVG renders | regex «постер/poster/svg»; image | P1 |
| SV-03 | SVG | Download/export the SVG result | PNG (and/or SVG) downloadable | download writes PNG; svg present in result object | P1 |
| SV-04 | SVG | Ask «логотип-схема для VPN-сервиса» | Logo-scheme vector renders | regex «логотип-схем»; image | P2 |
| SV-05 | SVG | Ask «wireframe лендинга» | Wireframe vector renders | regex «wireframe/вайрфрейм/макет-схем»; image | P2 |
| SV-06 | SVG | Give a prompt that yields invalid SVG | Friendly retry message, no broken image icon | error branch when no `<svg>` | P1 |

## 9. Charts / data viz

| ID | Area | User action | Expected behaviour | How to verify | Priority |
|---|---|---|---|---|---|
| CH-01 | Charts | Ask «построй график роста выручки по кварталам» | A chart image renders inline (free code-render) | regex «график/чарт/chart»; image | P1 |
| CH-02 | Charts | Ask «инфографику по статистике VPN в РФ» | Infographic renders inline | regex «инфограф/infograph»; image | P1 |
| CH-03 | Charts | Ask «столбчатую диаграмму продаж» | Bar-chart-style image renders | regex «диаграмм»; image | P1 |
| CH-04 | Charts | Provide explicit numbers, ask to chart them | Chart reflects the given data values | Values appear in rendered chart text/bars | P2 |
| CH-05 | Charts | Download the chart | PNG downloads | download button works | P2 |
| CH-06 | Charts | Ask for a comparison table «таблицу сравнения 3 тарифов» | Table/scheme renders inline | regex «таблиц»; image | P2 |

## 10. PowerPoint / slides / presentations

| ID | Area | User action | Expected behaviour | How to verify | Priority |
|---|---|---|---|---|---|
| PP-01 | Slides | Ask «сделай презентацию из 5 слайдов про Тайгу» | A multi-slide deck is generated (titles + bullets per slide) | skill-render slides JSON (4-6 slides) parsed & rendered | P1 |
| PP-02 | Slides | View the generated slides | First slide is title, last is conclusion; 2-4 bullets each | Slide structure matches SLIDE_SYS contract | P1 |
| PP-03 | Slides | Export / render slides to video (slides→MP4) | Slides become a narrated MP4 (cinema-export stitches frames) | renderSkillVideo → cinema-export MP4; download | P1 |
| PP-04 | Slides | Verify free TTS narration on slides | Each slide with narration gets a Google-TTS voice-over | freeTts called per slide; audio in export | P1 |
| PP-05 | Slides | Download the slide deck / video | File downloads (MP4 for video, or images) | download path works | P1 |
| PP-06 | Slides | ⚠️ Ask to export as a real .pptx file | A .pptx download | **LIKELY FAIL** — only SVG-slide→MP4/PNG path exists; no native PPTX export found | P2 |
| PP-07 | Slides | Give a 1-line topic, expect sensible auto-outline | Model auto-expands into a coherent deck | Logical 4-6 slide outline produced | P2 |
| PP-08 | Slides | Verify slides are FREE tier (code-render) | No paid charge for slide/video code-render | No media-provider spend | P1 |

## 11. Images — generate / i2i / gallery / errors

| ID | Area | User action | Expected behaviour | How to verify | Priority |
|---|---|---|---|---|---|
| IM-01 | Images | Open Studio → Картинки, prompt «неоновый тигр в тайге, 8k», generate | Photoreal image generates and shows in result area | generateImage → GenResult.url; ResultCard image | P0 |
| IM-02 | Images | Verify default model is the FREE subscription model | Default = ng:hidream / ng:qwen-image (free, $0) | defaultModel = free NanoGPT id | P0 |
| IM-03 | Images | In chat, type «нарисуй кота» (no studio) | Inline image generated in the chat thread | mode→image or /draw; inline image bubble | P0 |
| IM-04 | Images | Distinguish FREE vs PAID: a diagram prompt vs a photoreal prompt | Diagram → free SVG render; photoreal → paid image model | code-render for scheme; paid model for photoreal | P1 |
| IM-05 | Images | Upload a reference photo, ask image-to-image / variation | New image generated from the reference | ref image passed; result reflects reference | P1 |
| IM-06 | Images | Open the gallery of generated images | Past generations shown as thumbnails, re-openable | Gen[] list renders ResultCards | P1 |
| IM-07 | Images | Trigger an image error (provider busy) | Clean «не вышло, попробуй ещё» message + retry, not raw error | onSoon error string; retry available | P0 |
| IM-08 | Images | Retry a failed image generation | Re-runs generation; new attempt | retry path re-calls generate | P1 |
| IM-09 | Images | Switch image model via picker (search + sort by ум) | Model list searchable/sortable; selection applies | imageModels sorted by smart; selection used | P1 |
| IM-10 | Images | Choose aspect ratio (1:1 / 16:9) and generate | Output matches chosen aspect | aspect class applied to result card | P1 |
| IM-11 | Images | Download a generated image | PNG downloads (taiga-*.png) | download() writes png | P1 |
| IM-12 | Images | Generate while balance is empty (non-owner) | Soft message about funds, not a crash | gate / clean error; no stack trace | P0 |

## 12. Video — t2v / i2v / r2v / code-video / TTS / progress / errors

| ID | Area | User action | Expected behaviour | How to verify | Priority |
|---|---|---|---|---|---|
| VID-01 | Video | Studio → Видео, prompt «дрон над тайгой», generate | Video job submits, progress shown, MP4 appears | generateVideo submit→poll; progress; video result | P0 |
| VID-02 | Video | See live progress while video renders | Progress/elapsed updates; not a frozen spinner | SSE progress events update UI | P0 |
| VID-03 | Video | Cancel a video render mid-way | Job cancels cleanly; can start a new one | abort signal stops poll; no zombie state | P1 |
| VID-04 | Video | Image-to-video: upload a start frame, animate it | Uploaded image animates into a clip | i2v kind; start frame used | P1 |
| VID-05 | Video | Video-by-reference (r2v): provide a reference | Output guided by the reference | r2v kind path exercised | P1 |
| VID-06 | Video | Code-video (free): «объясняющее видео про X слайдами» | Free slide-video renders with narration (no paid model) | renderSkillVideo; free tier; MP4 | P1 |
| VID-07 | Video | Free TTS narration on the code-video | Russian voice-over present on slides | freeTts audio attached per slide | P1 |
| VID-08 | Video | Trigger a video scene error («не вышло») | Clean retry/error UI per scene, not a raw failure | prettyMediaError; scene retry; no crash | P0 |
| VID-09 | Video | Cinema studio: build a multi-scene storyboard, export | Scenes (video/image/animate/avatar) compose into one MP4 | exportCinema stitches; download MP4 | P1 |
| VID-10 | Video | Avatar / talking-head mode with a face image | Talking-head clip generated | avatar kind; face image input | P2 |
| VID-11 | Video | Choose duration / aspect for a clip | Output respects duration + aspect | params sent; result matches | P1 |
| VID-12 | Video | Download the finished video | MP4 downloads | download taiga-*.mp4 | P1 |
| VID-13 | Video | Pick a video model from the marketplace (price per clip shown) | Per-clip ~$ price visible on each model | title `~$ за клип`; price shown | P1 |
| VID-14 | Video | Generate video with empty balance (non-owner) | Soft funds message, no crash | clean error; no stack trace | P0 |

## 13. Music — generate (free vs paid) / play / download

| ID | Area | User action | Expected behaviour | How to verify | Priority |
|---|---|---|---|---|---|
| MU-01 | Music | Studio → Музыка, prompt «лоу-фай для работы», generate | Track generates (MiniMax/Lyria), shows progress | generateMusic submit→poll; music_status; mp3 | P0 |
| MU-02 | Music | Play the generated track | Audio plays inline | audio element plays the mp3 | P0 |
| MU-03 | Music | Download the track | MP3 downloads (taiga-*.mp3) | download writes mp3 | P1 |
| MU-04 | Music | Generate music WITH VOCALS | Track with sung vocals returned | Vocal track produced (paid AIMLAPI) | P1 |
| MU-05 | Music | ⚠️ Use the FREE music tier (ACE-Step) with vocals | A free vocal track via ACE-Step | **WILL FAIL** — only paid AIMLAPI MiniMax/Lyria in code; ACE-Step free tier NOT built (MASTER-PLAN planned) | P1 |
| MU-06 | Music | See progress/elapsed while music renders | Live status updates | onProgress music_status + elapsed | P1 |
| MU-07 | Music | Trigger a music error | Clean error message + retry | error path; no crash | P1 |
| MU-08 | Music | Generate music with empty balance (non-owner) | Soft funds message | clean gate; no crash | P1 |

## 14. 3D

| ID | Area | User action | Expected behaviour | How to verify | Priority |
|---|---|---|---|---|---|
| TD-01 | 3D | Studio → 3D tab | Tab opens; clearly marked as currently unavailable, not broken | SUBS td3 `live:false`; teaser state | P1 |
| TD-02 | 3D | Upload a photo and request a 3D model | Clean «временно недоступно / провайдер на обслуживании» message, NOT a raw error | toast «провайдер 3D сейчас на обслуживании»; no stack trace | P0 |
| TD-03 | 3D | Attempt 3D without a photo | Prompt «Загрузи фото — 3D делается из картинки» | onSoon guidance message | P1 |
| TD-04 | 3D | Verify the unavailable state is graceful (no console error spam) | No uncaught exceptions; UI stays usable | No red console errors; rest of studio works | P1 |
| TD-05 | 3D | ⚠️ Expect a working .glb 3D download | A .glb downloads and previews | **WILL FAIL** — provider down (triposr); generate3D returns error today | P2 |

## 15. Voice — TTS read-aloud / STT mic

| ID | Area | User action | Expected behaviour | How to verify | Priority |
|---|---|---|---|---|---|
| VO-01 | Voice | Click the mic button in the composer | Mic listens (pulsing), speech transcribes into the input | listening=true (pulse); Web Speech text fills textarea | P0 |
| VO-02 | Voice | Speak a Russian sentence, stop | Transcribed RU text appears in the input, editable before send | onText inserts recognized text | P0 |
| VO-03 | Voice | Click mic again to stop listening | Listening stops; pulse ends | listening=false; mic style reverts | P1 |
| VO-04 | Voice | Use mic in a browser without Web Speech support | Graceful unsupported message, mic doesn't crash | supported=false handled | P1 |
| VO-05 | Voice | Studio → Аудио, type text, pick a voice, generate | TTS audio generated and playable (Kokoro/OpenAI voices) | /api/audio returns audio data-URL; plays | P1 |
| VO-06 | Voice | ⚠️ Click a "read aloud" button on an assistant reply | The reply is spoken via TTS | **LIKELY FAIL** — no per-message read-aloud button in chat (only studio Аудио tab); confirm gap | P1 |

## 16. Tokens / billing / balance

| ID | Area | User action | Expected behaviour | How to verify | Priority |
|---|---|---|---|---|---|
| TB-01 | Billing | Run `/balance` | Current balance shown in ₽ (toast «Баланс: $X» + ₽ display) | balance fetched; ₽ via money.fmtRub | P0 |
| TB-02 | Billing | Verify the ₽ display uses the live USD→₽ rate | Amounts shown in rubles, converted from USD | setRate from /api/init billing.rub_per_usd | P1 |
| TB-03 | Billing | Open the spend-cap control, pick a per-op limit ($0.05/$0.2/$1) | Limit set; expensive ops above it ask confirmation | SpendCap value set; gateSpend triggers confirm | P0 |
| TB-04 | Billing | Set spend cap to «без лимита» | No per-op confirmation prompts | value=0; gate skipped | P1 |
| TB-05 | Billing | Trigger an op above the spend cap | Confirmation dialog before spending | gateSpend(estUsd) confirm dialog | P0 |
| TB-06 | Billing | ⚠️ Look for per-MESSAGE cost shown under each reply | Each reply shows its ₽ cost / tokens | **LIKELY FAIL** — message footer has copy/regen/fork only; no per-msg cost render found | P1 |
| TB-07 | Billing | As OWNER, send messages | No charges; owner-free; low-wallet warnings only | isOwner=true; «Кошелёк кончается» warning only | P0 |
| TB-08 | Billing | As OWNER, see low-wallet warning | Toast «⚠️ Кошелёк кончается: <provider> — пополни…» | low-balance toast on init | P1 |
| TB-09 | Billing | As NON-owner, hit a top-up gate | Top-up gate / soft block (payment is owner-gated/off) | ⛔ payment deferred per MASTER-PLAN; clean message | P1 |
| TB-10 | Billing | Run `/budget` and cycle эконом → норма → макс | Response length/cost tier changes visibly | cycleBudget; BUDGET_RU label flips; reply length changes | P1 |

## 17. Commands — /pipeline, /uncensor, slash discovery

| ID | Area | User action | Expected behaviour | How to verify | Priority |
|---|---|---|---|---|---|
| CM-01 | Commands | Type «/» in the composer | Inline command menu appears with matching commands | InlineCommands list opens | P0 |
| CM-02 | Commands | Type «/pip» | Autocompletes toward /pipeline | filtered command list | P0 |
| CM-03 | Commands | Run `/pipeline` | Pipeline builder opens to chain model→model→model | pipeline-builder modal opens | P0 |
| CM-04 | Commands | Build a 2-stage pipeline and run a query | Query flows stage→stage; final combined answer | pipelines.ts runs stages; {{prev}} chaining | P0 |
| CM-05 | Commands | Run the built-in `/duo` pipeline | «Мозг думает → Редактор шлифует» two-stage run | duo pipeline executes both stages | P1 |
| CM-06 | Commands | Run `/uncensor <запрос>` | Request rewritten without moralizing, then answered directly in one step | uncensor handler; /api/uncensor; direct answer | P0 |
| CM-07 | Commands | Open command palette (Cmd/Ctrl-K style) | Full searchable command registry | CommandPalette opens with visibleRegistry | P1 |
| CM-08 | Commands | Run a prompt-command like `/tldr <текст>` | Text summarized into 5 bullets | template applied; bulleted summary | P1 |

## 18. Privacy modes — ghost / private / full

| ID | Area | User action | Expected behaviour | How to verify | Priority |
|---|---|---|---|---|---|
| PR-01 | Privacy | Toggle Ghost (призрак) on | Placeholder changes to «Призрак — этот чат нигде не сохранится…»; nothing persisted | ghost=true; placeholder text; no storage writes | P0 |
| PR-02 | Privacy | Chat in Ghost, then reload | The ghost conversation is gone (not saved) | No chat restored after reload | P0 |
| PR-03 | Privacy | Toggle «приватно» (TEE routing) | Router prefers TEE/encrypted models; toast confirms | privatePref=true; toast; TEE models preferred | P1 |
| PR-04 | Privacy | Turn «приватно» off | Best-quality models used regardless of privacy | privatePref=false; toast | P1 |
| PR-05 | Privacy | Verify ghost disables memory writes | No facts captured during ghost chat | auto-memory suppressed in ghost | P1 |
| PR-06 | Privacy | Cycle agent permission mode (план → авто → полный) | Permission badge changes; agent autonomy gated accordingly | cyclePermMode; PERM_MODES label flips | P1 |

## 19. Search / research / web / co-browse

| ID | Area | User action | Expected behaviour | How to verify | Priority |
|---|---|---|---|---|---|
| SR-01 | Search | Toggle «Веб-поиск» in `+` menu, ask «что нового про ИИ сегодня?» | Answer grounded in fresh web results | webOn=true; reply cites current info | P0 |
| SR-02 | Search | Toggle «Супер-поиск», ask a factual question | Answer with numbered source citations [1][2] | superOn; /api/supersearch; SourcesPanel | P0 |
| SR-03 | Search | While searching, see «Ищу в сети…» indicator | Live searching banner with a Stop button | searchingWeb banner + стоп button | P1 |
| SR-04 | Search | Stop an in-flight web search | Search aborts cleanly | searchAbortRef.abort() | P1 |
| SR-05 | Research | Run `/research <тема>` (deep research) | Deep multi-source research with sources | research handler; sources rendered | P1 |
| SR-06 | Search | Click a citation in the SourcesPanel | Opens the source link | SourcesPanel link opens URL | P1 |
| SR-07 | Co-browse | Run `/browse <url>` or pick Браузер-в-чате | In-chat browser opens; AI and user share one screen | browser-panel opens with URL | P1 |
| SR-08 | Co-browse | Use cookies login for co-browse (`/cookies`) | Agentic browser uses your session (owner) | cookies-panel; co-browse under session | P2 |

## 20. Files — upload PDF/DOCX/image, extract text

| ID | Area | User action | Expected behaviour | How to verify | Priority |
|---|---|---|---|---|---|
| FL-01 | Files | Click `+` → «Файлы и фото», upload a PDF | File chip shows «читаю файл…» then attaches; text extracted | attachedFiles chip; /api/extract; fileBusy spinner | P0 |
| FL-02 | Files | Ask «выпиши главное из этого PDF» after upload | Answer references the PDF's actual content | extracted text in context; reply on-topic | P0 |
| FL-03 | Files | Upload a DOCX | Text extracted and usable | /api/extract DOCX path | P1 |
| FL-04 | Files | Upload an image | Image attached as a thumbnail; vision model can read it | attachedImages thumbnail; vision flow | P0 |
| FL-05 | Files | Remove an attached file before sending | Chip removed; file not sent | X removes from attachedFiles | P1 |
| FL-06 | Files | Upload an unsupported / huge file | Clean «Не вышло прочитать <file>» message, no crash | error toast; no stack trace | P1 |

## 21. Themes / appearance / fonts / backgrounds

| ID | Area | User action | Expected behaviour | How to verify | Priority |
|---|---|---|---|---|---|
| TH-01 | Themes | Settings → «Тема и акцент», pick a theme (midnight/slate/cyberpunk) | Accent colors + background change app-wide instantly | ThemePanel lists THEMES; applyTheme sets data-theme + CSS vars; visible recolor | P1 |
| TH-02 | Themes | Reload after picking a theme | Theme persists | loadThemeId restores from storage | P1 |
| TH-03 | Themes | Open the theme picker from settings | A swatch grid of themes with accent previews opens | ThemePanel modal opens with THEMES.map swatches | P1 |
| TH-04 | Appearance | Toggle the animated background / mode background | Background reacts to mode (chat/uncensored/ultra/image) | mode-background swaps per mode | P2 |
| TH-05 | Appearance | ⚠️ Change the font / font-by-mode | Font changes per mode/setting | **LIKELY FAIL** — fonts-by-mode listed as NEW/🅝; confirm not built | P2 |
| TH-06 | Appearance | Verify contrast on the studio/cinema neon background | Controls remain readable (no rainbow-glitch bleed) | KNOWN BUG (PARITY #2): rainbow neon leak — verify fixed; controls legible | P1 |

## 22. Prompts / bookmarks / presets libraries

| ID | Area | User action | Expected behaviour | How to verify | Priority |
|---|---|---|---|---|---|
| PB-01 | Prompts | Open «Библиотека промптов» from settings | Prompt templates by category + search | prompts-panel; PROMPT presets grouped | P1 |
| PB-02 | Prompts | Insert a prompt template into the composer | Template text inserted into input (or copied) | onInsert fills textarea | P1 |
| PB-03 | Prompts | Create and save a custom prompt | Custom prompt saved and reusable | saveCustomPrompts persists | P1 |
| PB-04 | Prompts | Search prompts for a keyword | List filters | q filter applied | P2 |
| PB-05 | Bookmarks | Star/bookmark an assistant reply | Reply saved to bookmarks panel | addBookmark; BOOKMARKS_EVENT; row appears | P1 |
| PB-06 | Bookmarks | Open bookmarks panel, copy a saved snippet | Snippet copied to clipboard | copy button works | P1 |
| PB-07 | Bookmarks | Delete a bookmark | Removed from list | removeBookmark | P2 |
| PB-08 | Presets | Open presets menu and apply a preset | Mode/model/flags applied from the preset | presets-menu applies PresetState | P2 |

## 23. Onboarding / empty states / errors / mobile

| ID | Area | User action | Expected behaviour | How to verify | Priority |
|---|---|---|---|---|---|
| OB-01 | Onboarding | Visit `/` (landing) for the first time | Landing hero loads; clear CTA into the app | landing.tsx Hero renders; CTA to /app | P0 |
| OB-02 | Empty | Open `/app` with no chats | Friendly empty state / starter prompt, not a blank screen | Empty chat state visible; composer ready | P0 |
| OB-03 | Onboarding | Open the `+` menu first time | 16 modes listed with example prompts each | plusItems render with `example` hints | P1 |
| OB-04 | Empty | Click a starter example | The example seeds a prompt/mode | setModeHint sets placeholder example | P2 |
| OB-05 | Errors | Force backend 500 on send | Clean RU error in chat, retry possible, no crash | friendly error; app still usable | P0 |
| OB-06 | Errors | Verify NO «Основная модель недоступна — беру запасную» on a plain «привет» | Trivial greeting must NOT trigger fallback banner spam | KNOWN BUG (PARITY #1): confirm fixed — no fallback banner on greeting | P0 |
| OB-07 | Errors | Verify no hallucinated model names (e.g. «grok-4.20») in pickers/toasts | Only real catalog model names shown | KNOWN BUG (PARITY #5): confirm fixed; names match catalog | P1 |
| OB-08 | Mobile | Open `/app` on a phone-width viewport | Layout is responsive; composer + toolbar usable, no overflow off-screen | Composer wraps (flex-wrap); panels full-screen on mobile | P0 |
| OB-09 | Mobile | Open a side panel (memory/skills/MCP) on mobile | Panel is reachable and dismissable on small screens | Modal fits viewport; close works | P1 |
| OB-10 | Mobile | Long-press / tap message actions on mobile | Copy/regenerate reachable on touch | MsgAction tappable; group-hover fallback on touch | P1 |

---

## SUMMARY OF COUNTS

- **Total cases: 219**
- Chat basics: 12 · Model selection: 14 · Relay/Brain: 14 · Effort: 8 · Memory: 18 · Agents & skills: 16 · Diagrams: 10 · SVG: 6 · Charts: 6 · Slides/PPT: 8 · Images: 12 · Video: 14 · Music: 8 · 3D: 5 · Voice: 6 · Billing: 10 · Commands: 8 · Privacy: 6 · Search/co-browse: 8 · Files: 6 · Themes: 6 · Prompts/bookmarks: 8 · Onboarding/errors/mobile: 10
- Priority mix: **P0 = 79 · P1 = 115 · P2 = 25**

## CASES MOST LIKELY TO FAIL TODAY (documented gaps)

- **MEM-17 / MEM-18** — long-term auto-memory (Mem0/Letta) NOT built (REMAINING-V1.md).
- **MU-05** — FREE music-with-vocals (ACE-Step) NOT built; only paid AIMLAPI.
- **TB-06** — per-message cost display missing in chat footer.
- **VO-06** — per-message read-aloud button missing.
- **TD-05** — 3D `.glb` output (provider triposr down).
- **PP-06** — native `.pptx` export missing (only SVG→MP4/PNG).
- **TH-05** — font-by-mode not built (theme picker itself IS built — see TH-01/03).
- **AG-10** — skill-install-by-URL NOT built: only `importSkillFiles` (file import) exists; the Link2 field in skill-builder is a webhook, not a URL installer.
