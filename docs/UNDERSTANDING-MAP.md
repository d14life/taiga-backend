# Тайга ИИ — UNDERSTANDING-MAP (unified codebase understanding)

> Single entry point for a fresh session. Synthesizes 11 subsystem code-audits against the masters
> (FEATURE-LEDGER.md = 139 fich, GAPS-RECOVERED.md, FEATURE-INVENTORY.md, server.py self_manifest L14964).
> Companion file: `docs/UNIFIED-FEATURE-CHECKLIST.md` (the single master build-order checklist).
> Generated 2026-06-18 by the synthesis lead. Verdicts only marked **done** when a map cited wired code.

---

## 0. CANON FACTS (authoritative — do NOT re-open)

1. **Security MINE #0 is DONE.** `resolve_caller` / owner-spoof RCE / SSRF are closed and verified in code:
   `server.py:10013` (`def resolve_caller`), `:10043` (`def caller_is_owner`), `:10046`-region (`is_owner(resolve_caller(c))`),
   and all sandbox/RCE/money/identity/MCP gates (`:12249,:12257,:12275,:12297,:12301,:12307,:12318,:12640,:12656,:13539`)
   resolve the caller from a verified token, never the spoofable body `user` field. **Report DONE. Never flag as an open hole.**
2. **SCOPE / DEFERRED (gate before public launch, NOT now):**
   - MINE #1 — RU payment / YooKassa (PaymentProvider + webhook + idempotency). `/api/topup` is a correct 503 stub today (`server.py:12618`).
   - Phase D — scale to 10k (ASGI/Postgres/pgvector/object-storage/backups).
   Build everything else. Do not propose building payment now.
3. **DESIGN — exactly 2 canonical designs:**
   - NEW (build target) = `docs/design/design-v3-current-shell-jun17.html` — macOS windows + bottom dock.
   - OLD (reference / take features) = `docs/design/usertest-jun15/`.
   - v0/v1/v2 live in `docs/design/_donors/` (ignore unless told). `reference-mockup.html` was a dup, deleted.
4. **METHODOLOGY — feature-by-feature, foundation→walls.** Each feature: evaluate → build/clean → test →
   screenshot → **CRITIC-AGENT** (separate adversarial agent) → fix → perfect → only then next. A standing critic-agent
   is a permanent role. Build-layer order (LOVABLE-HANDOFF): **Shell+Chat → Modes → Studio → Agent → Memory → Code → Settings → Polish.**
5. **PATHS:** frontend = `taiga-web/src/components/*` (note the `src/`). `server.py` ≈ 15125 lines, `chat.tsx` ≈ 8157 lines.
   Both monolithic → decompose during build, **behavior byte-for-byte** (FEATURE-INVENTORY is the no-regress checklist).

---

## 1. Codebase shape at a glance

| Layer (build order) | Backend entry | Frontend entry | Health verdict |
|---|---|---|---|
| Shell+Chat | `server.py:13501 chat()` | `chat.tsx` (8157), `shell/taiga-sidebar.tsx`, `floating-window.tsx`, `feature-catalog.tsx` | **Strong core, shell incomplete** — chat fully wired; macOS **dock missing**, window resize/tiling/traffic-lights partial |
| Modes | `server.py:12848-13499` (relay/research/council/compare/brain) | `mode-pills.tsx`, `depth-slider.tsx`, `function-bar.tsx`, `route-intent.ts` | **Substantially built** — 6 mode methods, 5-level depth, council config; Ultra-redesign + 6-desk model missing |
| Studio | `server.py:10103-10542` (video/audio/music/3d/image/cinema) | `image-studio.tsx`, `cinema-studio.tsx`, `ad-generator.tsx`, `artifacts/*`, `export-doc.ts` | **Most complete** — only 3D gated by provider outage (one constant) |
| Agent | `agent_os.py`, `orchestrator.py`, `debate.py`, `screen_copilot.py` | `agent-os-panel.tsx`, `debate-panel.tsx`, `screen-copilot.tsx`, `agent-question-card.tsx` | **Backend strong** — harness/debate/question-gate/confidence done; Taiga-Coder + drag-builder + 10/40/50 lanes missing |
| Memory | `server.py:7972-9134`, `mlx_compressor.py`, `video_rag.py`, `mem_to_sandbox.py` | `chat-memory-panel.tsx`, `recall.ts`, `profile.ts`, `rag.ts` | **Substantially complete** — 3 gaps: consolidation-freq knob, memory fact-check, recall-only-on-backref |
| Code | `server.py:5528-5638, 11737-12303`, `skills_run.py`, `browser_hub.py` | `terminal-panel.tsx`, `run-sandbox.tsx`, `browser-panel.tsx`, `taiga-extension/` | **6/8 done** — BYOK base_url + KV/browser files partial; Daytona/Modal absent |
| Settings (cross-cut: routing+billing+catalog+security+automation) | `server.py:4051 route_model`, `:8406 billing`, `:2128 catalog`, `auth.py`, `guard.py`, `scheduler.py` | `settings-panel.tsx`, `custom-instructions.tsx`, `theme-panel.tsx`, `agent-automations.tsx` | **Substantially built** — tier-bug fixed, phantom self-heal, wallet/metering live; AA-bench wiring + TEE-weight + cross-provider mid-flight swap missing |
| Polish | (UI shell) | `mode-background.tsx`, `glass-filter.tsx`, `followup-chips.tsx`, `presets-menu.tsx`, `i18n.ts` | **~50%** — liquid-glass + per-mode bg + followups + presets done; dock, 3-stage hero, EN locale, custom-bg, audit-gallery missing |

Stack: backend = Python stdlib `http.server` (no framework). Frontend = nested Next.js 16 / React 19 / Tailwind 4 in `taiga-web/`
(read `taiga-web/AGENTS.md`). Data in `~/.mostik-ai/` (SQLite `taiga.db`). Backend :8777, frontend :3000.

---

## 2. SHELL + CHAT (layer 1)

**Build-layer:** Shell+Chat (foundation).
**Entry points:** `server.py:13501 chat()` (main SSE dispatcher); `chat.tsx` (React monolith, all mode state);
`shell/taiga-sidebar.tsx` (7 nav groups, projects/folders); `floating-window.tsx:20` (drag + corner resize + traffic dots);
`window-rearrange.tsx:34` (3-zone detach); `resizable-shell.tsx:136` (column resize); `feature-catalog.tsx:24` (7-group button store);
`custom-bar.tsx` (pin/jiggle/drag-reorder/X-delete); `function-builder.tsx:112` (custom pills); `composer-plus-menu.tsx` (unified +);
`server.py:11939 /api/userconfig`, `:12032 /api/settings`, `:11951 /api/persona`.

**Health verdict:** Strong chat core; the **shell chrome is the single biggest build gap in the whole product**.

- **Done:** SSE streaming chat end-to-end; 7-group feature registry + FeatureCatalog; CustomBar (jiggle/drag/X-delete);
  FunctionBuilder custom pills; DevMode panel; preset-system; 8-group SettingsPanel; CustomInstructions; ThemePanel (font/accent/scheme);
  FollowupChips; PresetsMenu; FloatingWindow (drag + corner-br resize); WindowRearrange; ResizableShell; ModeBackground; ChatEmptyHero;
  userconfig/settings/persona endpoints; per-mode animated bg; liquid-glass SVG filter;
  **per-chat HOOKS** — trigger-substring → action-prompt injected into system prompt + "AI writes the action" button (`chat.tsx:3062` hooksBlock, `:6944` HooksPanel, `lib/chat-hooks.ts:1-48`); closes GAPS-RECOVERED #7 (donor `usertest-jun15/18-hooks.png`).
- **Stub/decorative:** macOS dock — `agent-dock.tsx:272` is a **run-monitor**, NOT the canonical app-icon dock; traffic-light yellow/green
  buttons render but have no onClick (`floating-window.tsx:93`); ChatEmptyHero is single-stage (not 3-stage hero).
- **Missing vs ledger (cat 2 + cat 11):** macOS **bottom dock** with pinned icons/jiggle/drag-to-dock (design `#dock` L238-326) — entirely absent;
  8-direction window resize (only corner-br); window tiling/snap; right-sidebar + inside-window as button surfaces; right-click remove button;
  i18n EN locale + language switch (i18n.ts is RU-only, 106 lines); `#audit-gallery`; custom-bg import + Ultra-generates-bg; per-font gradient/rounding;
  voice chat-to-chat; 3-stage hero progression.

**Top shell priorities (decide-yourself, technical):** build the real macOS dock as a distinct component; wire traffic-light minimize/maximize;
add 8-direction resize + tiling; add right-sidebar button surface.

---

## 3. MODES (layer 2)

**Build-layer:** Modes.
**Entry points:** `server.py:13501 chat()` dispatch → `:12848 chat_relay`, `:12964 chat_research`, `:13117 chat_council` (also `beam=True`),
`:13386 chat_compare`, `:13332 chat_agent_os`, brain flag inside `chat()` (`:13947`); `mode-pills.tsx:7` (5 pills: chat/code/uncensored/image/ultra);
`depth-slider.tsx:21` (5-level DEPTH_LEVELS, the live effort dial); `effort-selector.tsx:12` (4-state, **legacy/likely-dead** — replaced by depth slider per `chat.tsx:1435`);
`function-bar.tsx:34` (per-mode buttons); `route-intent.ts:24 classifyIntent()` (auto-router); `debate.py`, `orchestrator.py`.

**Health verdict:** Substantially built. The 6 mode methods are distinct and wired; the depth/effort dials are real.

- **Done:** universal-brain (all tools any mode for owner, `server.py:13704`); 5-level depth slider end-to-end with native `reasoning_effort` +
  L3 prompt-emulation fallback (`server.py:349-416, 13806`) + `reasoning_token_floor`; auto-depth client+server (`depth-slider.tsx:48`, `query_is_hard 4262`);
  council config popover (members 2-5 + synth + per-member prompts, `chat.tsx:7577`); brain driver+expert (1-3 experts); compare fan-out;
  relay 2-step; research 3-depth; debate engine (`debate.py`) + panel; auto-router `classifyIntent`; tier/cost presets cheap/mid/top; confidence badge.
- **Partial:** the two dials are right-shaped but the **response-length dial is a 3-state token toggle** (eco/norm/max), not a named "Fast ~300 words" preset;
  token floor is **flat** (4000/3000), not per-model tuned; beam/fusion removed from front (`chat.tsx:624`) but server `chat_council(beam=True)` path remains;
  fusion-critic verify exists (`verifyById`) but no standalone "check hallucination" button.
- **Missing vs ledger (cat 1, 3, 4):** Ultra-exclusive conversational system-redesign (3D-bg/layout via chat) — zero code;
  6-desk model (Чат/Дизайн/Студия/Агент/Код/Ultra) collapses to 5 pills (no separate Дизайн/Студия/Агент desks);
  "Fast ~300 words" named preset in general path; per-model token-cap tuning; standalone fusion-critic button.

---

## 4. STUDIO (layer 3)

**Build-layer:** Studio.
**Entry points:** `image-studio.tsx` (1719 lines, 11 sub-tabs); `cinema-studio.tsx` (607); `ad-generator.tsx`; `studio-skills.tsx`;
`design-studio.tsx`; `artifacts/*` (three/chart/anim/mermaid/sheet/web-preview); `export-doc.ts` (md/pdf/docx/xlsx/csv);
`server.py:10103 api_video, :10239 api_audio, :10279 api_free_tts, :10296 api_music, :10391 api_td3, :10423 api_image, :10506 api_image_tool, :10542 api_cinema_export`;
`server.py:12137 /api/ad_gen, :12176 /api/video_rag`; `ad_gen.py`, `video_rag.py`.

**Health verdict:** **Most complete subsystem.** Generation pipeline image/video(t2v/i2v/r2v/avatar)/audio/music/cinema/ads/photo-tools wired
backend→frontend; artifact viewers are real (Three.js, Mermaid, Chart.js, sheet, anim, web); exports use real lazy-loaded libs.

- **Done:** all artifact types; export buttons (PDF/Word/Markdown/Excel/CSV) + model knows it can do files; image (t2i/img2img/upscale/seed/steps/cfg/neg);
  video t2v/i2v/r2v/avatar; voiceover (paid NanoGPT + free Google); music (AIMLAPI + lyrics); cinema/storyboard + ffmpeg; studio-skills;
  photo tools (upscale/edit/faceswap/extend); video-RAG ingest; **featured-star sort, price-before-generation, real-price video/audio/music metering**
  (these 3 are ledger `[GAP]` but the code disagrees — mark done).
- **Partial:** 3D from photo — backend `api_td3` + frontend `generate3D` fully coded but gated by `TD3_AVAILABLE=false` (provider down, flip one constant);
  ads/UGC — script-gen + our-own avatar pipeline wired, no real Arcads API.
- **Deferred (security):** face-swap guard on real people (tool live, no consent/detection layer — ledger "позже").

---

## 5. AGENT OS (layer 4)

**Build-layer:** Agent.
**Entry points:** `agent_os.py` (Harness L239: scope/think/act/verify/run, fan_out L531, resume L500);
`orchestrator.py:112 run_orchestration` (LangGraph, ThreadPool max 4-5, 110s budget); `debate.py:101 run_debate`; `screen_copilot.py:30`;
`server.py:11091 /api/agent_os, :11135 /api/agent_fanout, :12154 /api/screen_copilot, :12463 /api/debate, :12433 /api/agent_permit,
:12449 /api/agent_answer, :13332 chat_agent_os, :5373 install_agent_from_url, :6162 _agent_question_wait`;
`agent-os-panel.tsx`, `debate-panel.tsx`, `screen-copilot.tsx`, `agent-question-card.tsx`, `agent-os.ts`.

**Health verdict:** Backend substantially built and wired. Several ledger "gaps" are actually done.

- **Done:** L15 harness (think→act→verify→state, multi-model deliberation, resumable disk state, SSE timeline);
  Architect↔Critic debate loop with convergence + budget + human-approve (ledger `[partial GAP]` — actually done);
  open-question gate (SSE question + option buttons + free-text + skip, ledger `[partial GAP]` — done);
  confidence badge (3-tier, ledger `[GAP]` — done); screen copilot (getDisplayMedia→vision→tip/target/done);
  17 worker personas; per-worker model + BYOK; worker think-mode normal/brain/council; acceptance-criteria LLM judge.
- **Partial:** Jules-like non-stop autonomy (request-response, no persistent daemon / 10h build); parallel isolation (logical per-run, **no git worktrees**, cap 4-5);
  session-coordinator (locks + resumable state, but no smoke-gate / binary-DoD field to frontend); watchdog self-wake (`resume()` exists, no endpoint, no cron);
  harness-repo install-by-URL works but no Ralph/Paperclip/guild catalogue.
- **Missing vs ledger (cat 8):** Taiga-Coder 4 modes (cloud/BYO/daemon/ephemeral) — zero code; drag-and-drop workflow builder — zero code;
  10/40/50 lanes (git worktrees); self-wake cron for 10h crash-resume; exposed `/api/agent_os_resume`.

---

## 6. MEMORY / RAG / GROUNDING (layer 5)

**Build-layer:** Memory.
**Entry points:** `server.py:7972 load/save_memory, :1131 _rag_embed, :1413 rag_ingest, :1459 rag_query (hybrid BM25+RRF default-on),
:1717 rag_query_smart, :1820 rag_context, :8623 extract_memory_facts, :8748 episodic_recall, :8805 reconcile_memory (Mem0),
:8902 quantize_memory, :8934 consolidate_memory (Letta), :9067 consolidate_active_users, :9134 memory_block, :2082 grounding_context,
:7677 _fts_index_memory, :7987 tombstones`; endpoints `:12079 /api/remember, :12081 /api/forget, :10742 /api/recall, :11052 /api/memory_consolidate,
:12238 /api/mem_extract, :12550 /api/export_memory`; `mlx_compressor.py:35` (sidecar :8791, Qwen2.5-3B), `mem_to_sandbox.py:104`, `video_rag.py:129`;
`chat-memory-panel.tsx`, `recall.ts`, `profile.ts`, `chat-memory.ts`, `rag.ts`, `style-profile.ts`.

**Health verdict:** Substantially complete. All core pillars wired.

- **Done:** per-chat + cross-chat fact accumulation; auto-extract OFF by default + skip in uncensored; Mem0 reconcile; Letta sleep-consolidation;
  hybrid BM25+RRF (default-on) + MultiQuery+LLM-rerank; grounding/source-truth `[N]` footnotes; tombstone forget; mem→sandbox MEMORY.md;
  video-RAG; episodic recall; style-note; FTS5 memory index; memory export; per-chat master prompts.
- **Partial:** "slider N-сообщений" — frequency-of-extraction slider exists (`chat-memory-panel.tsx:149`); injected-fact cap is server cfg, not a UI slider (ambiguous — see open Q);
  recall fires on **every** non-trivial message (ledger says only-on-backref) with **no inject-once guard**; CLaRa-7B is actually Qwen2.5-3B (model-agnostic via env).
- **Missing vs ledger (cat 5, 13):** user-facing consolidation-frequency knob (6h hardcoded); memory fact-check against live web; recall back-reference gating + inject-once.
- **Deferred (Phase D):** CLaRa-7B MLX (specific model), pgvector+HNSW.

---

## 7. CODE / SANDBOX / TERMINAL / BROWSER (layer 6)

**Build-layer:** Code.
**Entry points:** `server.py:5549 run_code_lang, :5638 tool_run_code, :5528 tool_shell, :12247 /api/run (owner-only Canvas),
:12252 /api/terminal (persistent E2B per-chat), :12286 /api/files, :11737 api_browser, :11767 api_browser_act, :12154 /api/screen_copilot,
:13740 _sess_code/_sess_shell`; `skills_run.py:413 sandbox_session_run, :345 run_in_cloud_sandbox`; `browser_hub.py` (Playwright);
`screen_copilot.py`; `taiga-extension/` (MV3: manifest+content+background); `terminal-panel.tsx`, `run-sandbox.tsx` (774), `browser-panel.tsx`, `screen-copilot.tsx`, `dual-terminal.tsx`.

**Health verdict:** 6/8 done, 2 partial, security gate correctly applied everywhere (MINE #0).

- **Done:** AI-live terminal (tool_result→terminal); persistent E2B session per chat shared AI+user; owner-only `/api/run`; `/api/files` tree;
  MV3 browser copilot (read/click/type/scroll via content.js + Playwright server-side); screen copilot; sandbox-gate for non-owners (anti-RCE, `caller_is_owner`).
- **Partial:** files-not-on-server — E2B + opt-in Fernet server files only (no KV / browser-local paths); BYOK — keys done, **custom base_url/own-server absent**
  (storage ready, URL field missing); real-time browser video capture (only URL-based video-RAG ingest).
- **Missing vs ledger (cat 10):** Daytona + Modal sandbox providers (only E2B exists).

---

## 8. SETTINGS / CROSS-CUT — ROUTING + CATALOG + BILLING (layer 7, cat 6)

**Build-layer:** Settings (cross-cut).
**Entry points:** `server.py:4051 route_model, :4136 best_for_task, :4074 detect_task, :711 _tier, :865 bench, :2128 load_rich_catalog,
:2344 visible_catalog_for, :14894 refresh_catalog_live, :14918 _maybe_bg_refresh_catalog, :3462 get_balance, :3712 get_balances,
:3511 nano_sub_status, :8406 load_billing, :8459 user_balance, :8541 meter, :8564 charge_media, :12618 api_topup, :12653 api_billing,
:3956 _prov_has_funds, :3653 budget_degrade, :4010 probe_model_live, :3774 is_phantom`; `adapter_config.toml`, `auto_update.py:68/104`.

**Health verdict:** Substantially implemented.

- **Done:** show-only-live + phantom-detect + 6h self-heal cron; auto-downgrade ladder (depth→cheaper-model→token-cap, NanoGPT); live catalog auto-refresh 30min
  with flap-protection; per-provider balance (Venice/NanoGPT/Chutes) + live total; categorization speed/type/price/privacy/power; **tier substring bug fixed**
  (`server.py:724` `\b(mini|nano|tiny|micro)\b`); Opus-NOT-default routing; image/video/audio provider+price; per-user USD wallet with atomic meter + markup + ledger;
  billing config (markup/rate/RUB-USD live/avg-msg); video/audio/music real-price metering; structured adapter routing (`adapter_config.toml`).
- **Partial:** balance-aware cross-provider routing — gates by provider funds at selection, **no mid-flight swap** if a provider drains during a stream;
  NanoGPT "do-not-fund" is a comment not enforced (it IS the primary provider); benchmarks — `auto_update.py` fetches AA to disk but **WIRE into `bench()` is explicitly deferred**
  (static `_BENCH` only); TEE/privacy — 5-6 labels computed but **no routing weight**; `auto_update.py` snapshot never read by server.
- **Stub:** `api_topup` — owner-gated `test_topup`, else 503 (the correct DEFERRED MINE #1 stub).
- **Missing vs ledger (cat 6):** live AA-benchmark wiring into router; TEE routing weight (3 groups); real-time cross-provider swap on mid-flight balance exhaustion;
  phantoms filtered from `/api/catalog` payload (currently only excluded from auto-routing, still visible in catalog list).

---

## 9. SKILLS + MARKETPLACE + MCP (layer 6, cat 7) — most complete

**Build-layer:** Code / Agent.
**Entry points:** `skill_caps.py:443 detect_skill_caps/compute_badge/analyze_skill`; `skills_run.py:96 import_skill_folder, :468 run_skill_script,
:595 match_skills/build_skill_injection, :652 make_run_skill_tool`; `skills_lib.py:88 search_skills`;
`server.py:10756 api_skills, :10788 api_install_skill, :10816 api_import_skill_repo, :10830 api_skill_folder, :11953 GET /api/mcp,
:12315 POST /api/mcp, :5958 tool_search_skills/tool_load_skill, :13643 auto-trigger injection`;
`skills-marketplace.tsx`, `full-skills-panel.tsx`, `tool-marketplace.tsx` (1061), `mcp-panel.tsx`, `skill-badge.tsx`, `skill-builder.tsx`,
`studio-skills.tsx`; `lib/skills/skill-caps.ts` (Pyodide runner), `full-skills.ts`, `unified.ts`.

**Health verdict:** **Most complete** — 8/10 ledger features done.

- **Done:** full GitHub-folder skill import; SKILL.md multi-step injection; media-verb skills as free alternative; skill persistence per-user;
  agent+skill marketplace + install-by-link + unified registry; MCP connectors (7-catalog, SSRF-guarded, encrypted token, agent-tool exposure, add/remove/toggle/refresh/ensure);
  skill-transform compatibility layer (static analysis → Pyodide split → badge full/partial/instruction-only/needs-server/unsupported → runtime routing server/browser-wasm/E2B).
- **Partial:** library scale — 358 ECC skills seeded (ledger wants 300+/3000+; 868 available in lib but only 358 imported).
- **Missing vs ledger (cat 7):** guild/community-packs — zero code anywhere.

---

## 10. VOICE / CONTINUOUS CONVERSATION (Studio / Polish, cat 11 voice items)

**Build-layer:** Studio / Polish.
**Entry points:** `server.py:10239 api_audio (paid NanoGPT TTS), :10279 api_free_tts (Google)`; `use-voice-input.ts:28` (Web Speech STT);
`audio-gen.ts:24` (free/nanogpt/elevenlabs); `voice-pref.ts:31`; `chat.tsx:736` (STT in composer), `:3153 speakMessage/stopAudio`,
`:3983 toggleHandsfree`; `settings-panel.tsx:900` (voice settings).

**Health verdict:** Substantially complete.

- **Done:** STT (Web Speech, ru-RU default, 8 langs); paid TTS (NanoGPT) + free TTS (Google) + ElevenLabs BYOK; provider selection + persistence;
  auto-speak; per-message speak/stop; markdown cleanup before TTS; **hands-free continuous loop**; STT language select; **audio billing** (`server.py:10275 charge_media kind=audio`
  — GAPS-RECOVERED claims it doesn't debit, code shows it does → verify once in DB, code looks correct); voice-model catalog classification; cinema scene TTS.
- **Missing vs ledger:** voice chat-to-chat (no impl); server-side STT/Whisper endpoint (STT is browser-only → breaks on Safari/iOS — coverage hole for CIS mobile).

---

## 11. ACCOUNTS / SECURITY / IDENTITY (cross-cut, cat 12)

**Build-layer:** cross-cut (Settings).
**Entry points:** `auth.py` (signup/login/make_token/uid_from_token); `guard.py` (redact_secrets/injection_score/wrap_untrusted);
`server.py:10013 resolve_caller, :10043 caller_is_owner, :7237 is_owner, :10725 api_auth, :12804 api_users, :12304 /api/identity,
:12618 api_topup, :12653 api_billing, :8608 _safe_fact, :2419 TRUST_BOUNDARY, :2477 scrub_identity, :61 _cors_allowlist, :9977 _cors_headers`.

**Health verdict:** Substantially solid. **MINE #0 confirmed DONE** (see CANON FACTS).

- **Done:** MINE #0 resolve_caller / owner-spoof RCE (all gates token-resolved); CORS allowlist; PBKDF2-600k auth + HMAC session tokens; /api/users CRUD owner-gate;
  TRUST_BOUNDARY in every prompt; RAG fenced as untrusted; anti-memory-poisoning `_safe_fact`; Agent-S identity + engine-reveal scrub (Claude/Anthropic intentionally not hidden);
  thin system prompt (self-knowledge on-demand via tool_self); SSRF guard incl. redirect-hop; secret redaction (12 patterns); per-user + per-IP rate limit; input caps;
  file-edit denylist; owner-only persona write; test_topup default OFF.
- **Stub:** `guard.py wrap_untrusted` defined but **never called** — web tool results enter context with only TRUST_BOUNDARY (no per-source fence).
- **Deferred:** YooKassa billing (MINE #1); face-swap real-person guard ("позже"); `authz.py` extraction (refactor only, no functional impact).

---

## 12. AUTOMATION / SCHEDULER / ROUTINES (layer 7, cat 13)

**Build-layer:** Settings.
**Entry points:** `scheduler.py` (interval+time engine, add/list/delete/toggle, compute_next_run, min 600s); `server.py:14519-14873 _routine_*,
:10937 api_jobs, :11472 api_routines, :11504 api_routine_event, :14500 event producer, :14849 _start_routine_scheduler, :15068 main wiring,
:14964 self_manifest`; `agent-automations.tsx` (full UI); `auto_update.py` (standalone, not wired).

**Health verdict:** Substantially complete. Two parallel schedulers.

- **Done:** `scheduler.py` daemon (interval+time-of-day, owner cron via `/api/jobs`, balance-gated); per-user routine system (`/api/routines`) +
  full `agent-automations.tsx` UI (create/edit/toggle/delete/run-now, 6 templates, 4 schedule kinds, 3 trigger types, localStorage mirror + server sync);
  **event routines on_run_done / on_chat_match now FIRE** (producer wired `server.py:14500` — previously-noted gap CLOSED);
  internal sleep-time consolidation (env-gated OFF); routine rate-limit 8/hr; `/sprint` self-test incl. scheduler-liveness; catalog auto-refresher (6h).
- **Stub:** `auto_update.py` — complete standalone script, NOT imported by server, no launchd plist, snapshot never read back.
- **Missing vs ledger (cat 13):** launchd plist for `auto_update.py` (Cron на Mac) + read-back into `bench()`; `/api/jobs` frontend panel; unify the two scheduler systems.

---

## 13. Self-knowledge anchor

`server.py:14964 self_manifest()` introspects registries → manifest dict, computed once at startup (`:15056 SELF_MANIFEST = self_manifest()`),
served via `tool_self` / `full=True` (NOT injected into every message — the ~1200-1500-token static manifest was correctly removed). This is the live
source-of-truth for "what can Тайга do" and should feed the in-app feature store / capability tour.

---

## 14. Cross-cutting truths a new session must internalize

1. **Ledger is stale in Studio + Agent.** Several `[GAP]` items (price-before-gen, real-price metering, video-by-reference, confidence badge,
   debate loop, question-gate) are **already wired**. Trust the code citation over the ledger marker.
2. **The macOS dock is the single largest missing UI piece.** `agent-dock.tsx` is a run-monitor, not the canonical app-icon dock.
3. **Two schedulers, two routers-of-sorts, two memory-recall paths** (server + client) exist in parallel — decompose carefully, behavior byte-for-byte.
4. **`effort-selector.tsx` is likely dead** (replaced by `depth-slider.tsx`); confirm and tombstone during the Modes layer.
5. **MINE #0 is closed; MINE #1 (payment) + Phase D (scale) are the only true deferrals.** Everything else is build-now, feature-by-feature, with a standing critic-agent.
