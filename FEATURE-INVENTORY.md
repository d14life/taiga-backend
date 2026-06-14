# FEATURE-INVENTORY.md — полный список фич Тайги

> Чек-лист для strangler-рефактора: при разборке монолита НИ ОДНА фича не должна потеряться.
> Отмечай [x] когда фича перенесена в чистый модуль и проверена зелёной.

**Всего областей: 12 · фич: 182**

## Chat core & model routing (19)
- [ ] Multi-provider uncensored chat across 5 OpenAI-compatible upstreams (Venice/NanoGPT/Chutes/Redpill/AIMLAPI) behind one brand; provider never exposed
- [ ] Streaming SSE responses with reasoning/thinking on a separate channel
- [ ] Auto model selection (__auto__): picks code/reason/vision/cheap/chat model from last message
- [ ] Price/cost tiers (off/cheap/mid/top) — best-benchmark model within a budget
- [ ] Native reasoning-depth dial (low/medium/high, 'Глубоко') + prompt-emulated depth for models that ignore reasoning_effort; depth slider 1-5
- [ ] Vision: auto-switch to a vision-capable model when images attached, with toast
- [ ] BYOK per-provider keys, encrypted at rest; owner sees free/hidden models
- [ ] Auto-continue on token-limit truncation (stitches up to 4 continuations)
- [ ] Silent provider failover before any visible text (retries next funded model)
- [ ] Graceful cost degradation: lower depth -> nearest cheaper same-family model -> honest warning instead of error (max_spend)
- [ ] NanoGPT subscription routing (free input tokens) + balance-aware token capping to avoid 402/402
- [ ] Per-user saved config per mode (model/maxTokens/systemPrompt/tools)
- [ ] Auto-compaction of long histories with image-context preservation
- [ ] Per-IP + per-user rate limiting and abuse filtering; phantom-model detection so routing never lands on a dead model
- [ ] Token-based billing with cost+markup, separate leader/expert metering, BYOK exempt, served_by reporting
- [ ] UI self-awareness: model told 'current interface state' so it can answer 'which model am I on'
- [ ] Live catalog with capability kind, privacy tier (e2ee/tee), context window, vision flag, censorship-test %, price-per-1k
- [ ] Image generation (Venice + NanoGPT) and voice-output, dispatched by model_kind
- [ ] Modes (hero word cycling), per-mode system prompts, master-prompt & custom-instructions

## Multi-engine chat modes (Brain / Council / Compare / Beam / Research / Relay) (14)
- [ ] Brain triage: cheap leader answers smalltalk itself, escalates substantive queries to a strong expert transparently
- [ ] Auto-Brain: on __auto__ + hard query, silently routes through cheap-leader->expert (toggle auto_brain=false)
- [ ] Explicit Brain mode with user-selectable driver and 1-3 experts
- [ ] Brain multi-expert orchestration: N best-for-task experts answer independently and are fused/cross-checked
- [ ] Council mode: N models deliberate in parallel; user-selectable synthesizer + per-member master prompts
- [ ] Beam-fusion mode (now mechanically == council): verifier/critic fuses, drops single-model hallucinations
- [ ] Compare mode: side-by-side raw answers from 2-5 models, no synthesis (weaker heads, bare completion)
- [ ] Deep/Ultra research: fast/balanced/deep presets -> plan -> web_search + page reads -> cited synthesis report; user source cap
- [ ] Relay / improve-prompt: cheap model fixes prompt, smart model answers
- [ ] Reasoning effort propagated to thinking-capable models across all modes
- [ ] Grounding/RAG/server-memory injected into council/expert/research heads with [N] citations
- [ ] Safe read-tools (web_search, super_search, fetch_url, wiki, rates, calc, now, search_skills, webhook) for every fan-out head
- [ ] Cross-provider resilience: leader fallback chain, expert pool on live providers, env-configurable council defaults
- [ ] Rich SSE timeline events per mode (council_plan/step, member_answer, research_step/plan/sources, tool/tool_done, meta, cost, done)

## Agent-OS (multi-agent orchestration & debate) (18)
- [ ] Multi-agent orchestration: auto-decompose a task into 2-4 subtasks -> parallel/sequential workers -> single synthesized answer
- [ ] Live agent timeline (SSE): decomposition, per-worker running/thinking/searching/verifying/done/timeout, synthesis
- [ ] 17 selectable skill personas per worker (general, researcher, coder, critic, writer, planner, architect, security, reviewer, debugger, optimizer, analyst, marketer, summarizer, translator, devops, qa)
- [ ] Per-worker model choice (TaskPacket); non-owners gated to their visible catalog
- [ ] BYOK per worker (own key/base)
- [ ] Parallel mode with 110s budget (late workers get placeholder); sequential mode (each worker sees prior results)
- [ ] Researcher workers web-search & ground in sources with honest empty-result signaling
- [ ] Worker-as-full-chat: long-term memory + RAG + grounding + safe read-tools + tool-loop
- [ ] Worker thinking mode: normal / council (worker + up to 2 pool models) / brain (strong expert)
- [ ] Worker depth: light / full / auto
- [ ] Worker autonomy directive (act, don't ask back)
- [ ] Grounded mode (strip web tools, answer strictly from sources)
- [ ] Per-subtask acceptance criteria verified by a cheap LLM judge, surfaced in timeline
- [ ] Chat-to-Agent seed context (text only, anti-RCE)
- [ ] Anti-hallucination synthesis
- [ ] Scheduled/cron orchestration runs with balance gating
- [ ] Architect<->Critic debate (/api/debate): convergence detection (verdict agreed / no new issues / N rounds), SSE round stream
- [ ] Debate human-in-the-loop: 'ВОПРОС:' fork with 2-3 tappable answer options

## MCP (Model Context Protocol connectors) (11)
- [ ] Built-in connector marketplace (7: DeepWiki, Context7, Hugging Face, Microsoft Learn, GitHub, Notion, ComfyUI) with category/auth/description
- [ ] One-click install a marketplace connector by id
- [ ] Add a custom MCP server by name + http(s) URL (+ optional custom headers)
- [ ] Remove / enable-disable (toggle, without delete) / refresh (re-probe) an installed server
- [ ] Attach a personal auth token stored encrypted, with configurable header name
- [ ] Per-server UI status: enabled, ok/reachable, has_token, tool/resource/prompt lists
- [ ] Connected MCP tools become live callable tools in agent and normal chat (GitHub/Notion/ComfyUI work in chat)
- [ ] Self-hosted connector support (paste own MCP URL)
- [ ] Skill/agent builders can declaratively auto-connect a required connector idempotently
- [ ] Capabilities surface reports installed connectors + catalog
- [ ] SSE & plain-JSON MCP transport, session-id continuity, automatic re-init on expiry

## Skills (GitHub-imported Claude-Code-style) (15)
- [ ] Import a whole skill folder from a GitHub repo/subfolder (SKILL.md + scripts/ + resources/), 2MB/60-file/512KB caps, idempotent reinstall
- [ ] Import single SKILL.md via direct/blob/tree GitHub link (auto blob->raw, tree->SKILL.md)
- [ ] Mass-import every SKILL.md from a whole repo as text instruction-skills (~200-file cap, symlink resolution)
- [ ] Static compatibility badge per skill (full / partial / instruction-only / needs-server / unsupported)
- [ ] Capability summary tooltip: language, third-party packages, needs[], media verbs, claude-authored flag
- [ ] List installed personal skills; enable/disable toggle (disabled never auto-trigger or inject)
- [ ] Run a bundled skill script with STDIN and CLI args
- [ ] Owner runs scripts natively on the server (real cwd, argv, __file__, sibling-resource reads)
- [ ] Non-owner pure/Pyodide scripts return a browser-wasm marker for front-end Pyodide/WebContainer execution
- [ ] Non-owner needs-server scripts auto-run in a one-shot E2B cloud sandbox (if key set), else needs-native-bridge marker
- [ ] Persistent per-chat E2B sandbox shared between the AI's run_code/shell and the user's terminal
- [ ] Auto-trigger: keyword/token-overlap match injects up to 2 skills' SKILL.md so ANY model follows the skill
- [ ] run_skill_script tool exposed to the model in agent & normal chat
- [ ] Model-pin: claude-authored skill auto-pins the chat to a recommended Claude model
- [ ] Personal skills merged into global skill library search

## Memory, RAG & Grounding (context injection) (18)
- [ ] Persistent long-term memory of facts auto-extracted from conversation (name, prefs, projects, style)
- [ ] Contradiction-aware memory updates (Mem0 reconcile: KEEP/ADD/UPDATE/DELETE)
- [ ] 'Forget X' that sticks across future extractions (tombstones); 'remember X again' lifts the tombstone
- [ ] Model-driven self-editing memory tools (save_note/remember/forget)
- [ ] Relevance- & style-aware memory injection (style prefs framed as soft advice)
- [ ] Per-user memory budget knobs (protected_recent, memory_max_chars)
- [ ] Sleep-time background consolidation (dedup, near-dup merge, quantize/compress) for idle users + owner manual trigger
- [ ] Full-text search over remembered facts (via search_chats kind=memory)
- [ ] Document RAG: upload docs incl. DOCX/PDF/images (VLM captioning) -> structure-aware chunking -> per-user vector store with workspace/chat scoping
- [ ] Hybrid retrieval by default (dense + keyword + RRF); premium smart-search (MultiQuery + LLM rerank)
- [ ] RAG context injection with [source] citations and prompt-injection-safe delimiters
- [ ] Semantic compression of retrieved chunks (local MLX -> cheap LLM)
- [ ] Grounding / source-of-truth mode: answer ONLY from trusted sources, [N] footnotes, explicit 'не подтверждено источниками', clickable used-sources
- [ ] Add trusted sources by URL (SSRF-safe), pasted text, or file
- [ ] Episodic recall: keyword search across past chats (/recall, /api/episodic)
- [ ] Style note: running per-user note of HOW the user writes
- [ ] Anti-echo loop breaking + post-response hallucination/degradation verification (/api/verify)
- [ ] All of memory+RAG+grounding also injected into council/beam advisors and worker/orchestrate runs

## Studio / Media generation (16)
- [ ] Text-to-image (Venice + NanoGPT) with seed, steps, cfg_scale, negative_prompt, width/height
- [ ] NanoGPT subscription free-image path for owner (hidream/qwen-image)
- [ ] Image upscale (2x-4x) and image edit / img2img by prompt
- [ ] Text-to-video (t2v) across NanoGPT + AIMLAPI with live catalog + curated fallback
- [ ] Animate-a-photo (i2v), talking-head avatar video, lip-sync, reference-video-to-video (r2v)
- [ ] Video tools: face-swap, extend, video upscale
- [ ] Live SSE video progress with elapsed time, WAITING heartbeats, poll watchdog
- [ ] Per-clip price reservation with auto-refund on failure/timeout (video & music)
- [ ] Music generation from prompt + optional lyrics (SSE progress)
- [ ] 3D .glb mesh from a single photo
- [ ] Paid TTS voiceover (NanoGPT) with voice/model/speed/language; FREE TTS via Google translate_tts
- [ ] Cinema/film export: concatenate mixed image+video scenes with per-scene narration into one MP4 (ffmpeg, 720p30)
- [ ] UGC video-ad script writer (N angle-varied scripts) + avatar-model recommender
- [ ] Brand-brief -> design-token system; reference-image -> design tokens (vision)
- [ ] Image-intent classifier (free code-render vs paid generation)
- [ ] Media discovery endpoints (video/music/3d model lists); non-generative web media search (YouTube + DDG images)

## Billing / Balance / Pricing (15)
- [ ] Prepaid USD wallet per user (balance, lifetime spent, 200-entry ledger)
- [ ] Pay-as-you-go text billing: real input/output tokens x provider price x markup, deducted live
- [ ] Live balance readout in UI after each answer
- [ ] Media billing: images, video clips, music, audio/TTS, 3D, each at real cost x markup
- [ ] Reserve-then-refund for long media jobs
- [ ] Per-feature flat fees (search $0.02, RAG vision per page, agent-OS $0.05, fan-out $0.05*N, orchestrate/debate $0.05, screen copilot $0.01, video-RAG $0.06, terminal $0.002, scheduled $0.05)
- [ ] Insufficient-funds gating with a Russian top-up message and a ~$need estimate
- [ ] Owner free tier (never charged — but leaky per call-site)
- [ ] User self-service top-up slider (RUB->USD, est. messages) — currently 503-blocked pending payment processor
- [ ] Owner billing console: view all balances, credit any user, toggle billing, set markup %, set manual RUB/USD rate, set avg msg price, toggle test top-up
- [ ] Live RUB pricing via real-time USDT->RUB (CoinGecko, CBR fallback, 95.0 hard fallback)
- [ ] Estimated-messages-remaining indicator
- [ ] Provider credit dashboard (Mostik's own funds at Venice/OpenRouter/NanoGPT/Chutes)
- [ ] NanoGPT subscription optimization (free daily image quota, auto-capped max_tokens)
- [ ] Resale-as-API: mint Mostik API keys, hit an OpenAI-compatible /v1 proxy metered against balance

## Accounts, Auth & Security (16)
- [ ] Multi-user accounts (create/rename/delete) with display name/emoji/owner flag
- [ ] Optional PBKDF2 signup/login + session tokens (/api/auth)
- [ ] Owner vs regular-user distinction (owner untaxed, manages balances, sees hidden models, runs admin routes)
- [ ] BYOK keys, cookies, MCP tokens, opt-in user files — all Fernet-encrypted at rest
- [ ] Per-IP rate limiting (owner exempt) on all expensive endpoints
- [ ] CSAM-style content blocking (minor+sexual) with abuse logging + per-user counter
- [ ] Brand-identity scrubbing (strips Venice/NanoGPT/Chutes/RedPill self-references)
- [ ] Owner-only dev tools in chat: shell, run_code (python/js/bash sandbox), list_dir, read_file, write_file, edit_file (Aider-style), revert_file
- [ ] Permission ladder for agent tool use (plan/auto/full)
- [ ] Interactive per-tool approval UI (allow_once/always/deny) + open-ended agent question/answer gate
- [ ] Destructive-command safety net (blocks rm -rf /, mkfs, dd, fork-bombs, curl|sh, sudo rm, etc.)
- [ ] Anti-SSRF for outbound fetches incl. redirect-hop revalidation
- [ ] GitHub skill install guarded by SSRF check
- [ ] Per-request resource caps (message count, chars, RAG bytes, workers, steps, cinema scenes, userfile size/count)
- [ ] Owner admin ops: live catalog rebuild, /sprint self-test, sleep-time memory consolidation
- [ ] Worker-model owner-gating (non-owner can't smuggle a model outside their catalog)

## Storage / Persistence (11)
- [ ] Multi-user accounts with stable ordering, per-user settings
- [ ] Long-term memory + tombstones, personal notes (capped 200)
- [ ] Per-user balance/spend ledger
- [ ] BYOK keys encrypted at rest; per-user custom config (sub-modes + custom functions, server-validated)
- [ ] RAG knowledge base (docs, per-chunk vectors, workspaces, vision-sourced chunks)
- [ ] Chat history (full objects, recent-chats list, episodic recall)
- [ ] Full-text search across all chats + memory (owner searches everyone), bm25 ranking + snippets, LIKE fallback
- [ ] Encrypted cookie storage (browser tool acts logged-in)
- [ ] Opt-in encrypted server-side file storage (25MB/file, 200 files/user)
- [ ] Personal skills import, trusted sources list, scheduled routines
- [ ] Global stores: billing config, Mostik API keys, MCP server list, assistant identity/persona override

## Web chat UI (front door) (19)
- [ ] Streaming chat with branch/edit tree, regenerate, message export to PDF/DOCX/MD, copy, bookmark
- [ ] Model picker across ~800 models with funding/cost/effort routing + per-feature overrides
- [ ] Trivial-message fast lane (cheap non-thinking model)
- [ ] Slash-commands + Cmd-K command palette + inline command autocomplete
- [ ] Custom pills/functions (builder, config popovers, marketplace); pipelines model->model (builder, presets, /loop)
- [ ] Compare grid, council config, research config popovers; auto-verify + manual verify
- [ ] Composer: attachments (images/files), camera capture, screen capture, drag-drop, paste, morph build-intent chip, followup chips
- [ ] Voice input (dictation) + hands-free conversation loop + TTS auto-speak
- [ ] Budget (eco/norm/max) and cost-tier controls; spend cap + spend-confirm gating
- [ ] Message branching/forking, checkpoint branching, branch switcher, regenerate
- [ ] Chat folders/projects with shared instructions; merge chats; presets save/apply/delete
- [ ] Ghost chat (nothing on disk), privacy mode (local/server), TEE private-model routing
- [ ] Permissions ladder UI + permission modal + decision cards; dev mode (file/terminal) for owner
- [ ] Big-tab panels: design studio, agent OS dashboard, terminals (visual/dual/E2B), workspace, browser panel, orchestrator, team, loop studio
- [ ] Agent-OS dashboard: overview, modes, automations, tasks (kanban+deps+inbox), runs, ralph monitor, source-of-truth, sandbox, tools, evals
- [ ] Marketplaces: skills, tools/MCP, agents, commands, models catalog
- [ ] Characters/persona gallery + temperament; capability tour; onboarding; feature catalog/visibility
- [ ] Cost & served-by footers, sources panel, thinking-steps timeline, balance + provider-balance display + RUB conversion
- [ ] MCP panel, jobs panel, cookies panel, knowledge panel, screen co-pilot, design-system studio, slides canvas, cinema studio, ad-generator

## Routines, Scheduler & Automations (10)
- [ ] Per-user saved-prompt routines on time schedules (hourly/daily/weekdays/weekly at HH:MM, per-routine timezone), max 50, idempotent once-per-window firing
- [ ] Event routines on_run_done / on_chat_match (UI-exposed; backend handler exists but NEVER fires — no producer wired)
- [ ] Per-routine run history (last 25 records, status, output capped) + lastRunTs
- [ ] Background auto-run engine (owner-only by default; all users if MOSTIK_ROUTINES_ALL=1), 8 runs/hour/user, LLM-only
- [ ] Scheduled orchestration jobs (/api/jobs): owner cron, interval or time-of-day with weekday tokens, balance-gated $0.05/run
- [ ] Sleep-time nightly memory consolidation + quantization (env-gated OFF by default)
- [ ] Manual memory consolidation (/api/memory_consolidate, one user or all)
- [ ] Workflow templates (/api/workflow): research-brief, image-from-idea, doc-qa, rewrite-polish + custom step arrays
- [ ] Invisible housekeeping: live catalog auto-refresh, phantom-model self-healing probe, WAL auto-checkpoint, FTS backfill
- [ ] /sprint backend self-test (owner) incl. scheduler-liveness check

