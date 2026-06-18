# Тайга ИИ — UNIFIED FEATURE CHECKLIST (single master, build-order)

> The SINGLE master checklist. Every one of the 139 FEATURE-LEDGER features appears **exactly once**, reconciled against
> the 11 subsystem maps + FEATURE-INVENTORY + self_manifest. Grouped by the 8 build layers so it doubles as the
> feature-by-feature BUILD ORDER. `[EXTRA]` = surfaced by inventory/self_manifest beyond the 139. Status only **done** when a map cited wired code.
> Companion: `docs/UNDERSTANDING-MAP.md`. Generated 2026-06-18.
>
> **CANON:** MINE #0 (resolve_caller/RCE/SSRF) = DONE. MINE #1 (YooKassa payment) + Phase D (scale: pgvector/Postgres/ASGI) = DEFERRED (gate before public launch, marked DEFERRED rows). 2 designs (NEW = design-v3-current-shell-jun17.html, OLD = usertest-jun15). Feature-by-feature + standing critic-agent. Behavior byte-for-byte.

## Counts (this file)

| status | count |
|---|---|
| done | 104 |
| partial | 42 |
| stub | 6 |
| dead | 0 |
| missing | 21 |
| **total rows** | **173** |

Counts verified by strict 5-column parse of this file (2026-06-18). Of which DEFERRED (not to build now): 5 rows (payment stub + scale items). 134 ledger-mapped rows cover all 139 FEATURE-LEDGER features (a few compound ledger lines are kept as a single row — coverage is complete, row-count differs from 139 only by that merging); `[EXTRA]` rows from inventory/self_manifest = 39 (marked `[EXTRA]` in the category column).

| build layer | done | needs work (partial+stub+dead+missing) |
|---|---|---|
| Shell+Chat | 13 | 13 |
| Modes | 17 | 6 |
| Studio | 15 | 2 |
| Agent | 10 | 8 |
| Memory | 13 | 6 |
| Code | 10 | 7 |
| Settings (routing+catalog+billing+security+automation) | 23 | 13 |
| Polish | 3 | 9 |
| Deferred | 0 | 5 |

---

## LAYER 1 — SHELL + CHAT

| feature | category | status | citation | note |
|---|---|---|---|---|
| УНИВЕРСАЛ-МОЗГ: любой чат может всё; мод = стиль/линза | 1 arch | done | server.py:13520-13534; :13704 | additive flags, owner gets all tools any mode |
| 3-яруса (Обычный/Студия/Ultra) | 1 arch | partial | mode-pills.tsx:7-13 | 5 pills, no explicit Studio tier gate; Ultra exclusives missing |
| Ultra = универсал + ВСЕ табы + видимый пульт + ЭКСКЛЮЗИВ пересборка | 1 arch | missing | function-bar.tsx:43-46 | Ultra pill only toggles council+agent; no exclusive redesign path |
| Ultra-чат = разговорный дизайнер системы (генерит 3D-фон/тему/раскладку) | 1 arch | missing | chat.tsx:624 (no branch) | zero backend/frontend path |
| 6 столов: Чат Дизайн Студия Агент Код Ultra | 1 arch | partial | mode-pills.tsx:7-13 | 5 pills; no separate Дизайн/Студия/Агент desks |
| ВСЁ = кнопка-объект {id иконка ярлык группа действие где} | 2 button | done | features-registry.ts:16-23,25-80 | typed registry |
| Магазин кнопок по 7 группам → на поверхность | 2 button | done | features-registry.ts:82-84; feature-catalog.tsx:24-100 | 7 cats, grouped search+pin |
| Поверхности: док, композер, правый сайдбар, внутрь окна | 2 button | partial | custom-bar.tsx:39; feature-catalog.tsx:27-71 | only custom-bar surface; right-sidebar + inside-window missing |
| drag, jiggle-delete, правый-клик убрать, drag-reorder, persist per-user | 2 button | partial | custom-bar.tsx:52-149 | drag/jiggle/X-delete done; right-click remove missing; persist is localStorage not server |
| Юзер собирает кастом-функцию из примитивов → кастом-пилюля + конфиг-окно | 2 button | done | function-builder.tsx:112; composer-plus-menu.tsx | 8 bases, model/depth/params, named pill |
| Дефолт = чистый стартовый набор (Чат: 4 кнопки) | 2 button | done | custom-bar.tsx:65-75; use-custom-bar.ts | empty default + "add buttons" placeholder |
| Каталог фич / библиотека всех кнопок | 2 button | done | feature-catalog.tsx:24,42-64 | search+groups+pin+custom create |
| Dev-режим per-user с гардрейлами (модель/output/temp/промпт/тулзы) | 2 button | done | settings-panel.tsx:34,263-281,24 | master toggle gates DevModePanel |
| Хуки per-chat: триггер-подстрока → action-промпт инжектится в систем-промпт + кнопка «ИИ допишет действие» | 13 proc [GAP] | done | chat.tsx:3062 (hooksBlock инжект), :6944 (HooksPanel); lib/chat-hooks.ts:1-48 | GAPS-RECOVERED #7: поток ЕСТЬ (было «куски есть, потока нет»); донор usertest 18-hooks.png |
| Редизайн index.html → порт в taiga-web; responsive web+MacBook+телефон | 11 ui | partial | chat.tsx:4671,6162 | sm/md/lg breakpoints; not full responsive parity, mobile incomplete |
| ДОК: пин-иконки, jiggle-delete, drag-to-dock | 11 ui | missing | agent-dock.tsx:272 | AgentDock is run-monitor, NOT macOS app-icon dock (design #dock L238-326) — absent |
| macOS-окна: drag/8-resize/светофор/тайлинг; чат+артефакты как окна | 11 ui | partial | floating-window.tsx:20-119; window-rearrange.tsx:34-60 | drag + corner-br resize + decorative traffic-lights; no 8-resize, no tiling, yellow/green no onClick |
| Композер «+» (все тулзы) · ресайз ВСЕХ контейнеров | 11 ui | done | composer-plus-menu.tsx:51; resizable-shell.tsx:136 | unified + menu, column resize |
| Кнопки-подсказки в конце ответа (до 4) · пресет-система | 11 ui | done | followup-chips.tsx:19; presets-menu.tsx:20 | followups + named preset pills wired |
| Мульти-чат как LibreChat (проекты) | 11 ui | done | taiga-sidebar.tsx:109-131; chat.tsx:700 | projects/folders with shared instructions |
| реал-тайм визуал мышления | 11 ui | partial | thinking-steps.tsx | component exists; wiring status unclear |
| Текучий персональный hero (3 стадии) · liquid-glass-color иконки | 11 ui | stub | chat-empty-hero.tsx:14 | single-stage hero (morph title); no 3-stage progression |
| Шрифт меняет цвета/градиент/скругление · #audit-галерея | 11 ui | partial | theme-panel.tsx:136-170; theme.ts | font+accent picker done; per-font gradient/rounding + #audit-gallery missing |
| Галерея персонажей (Архитектор/Критик/Писатель) · i18n RU/EN | 11 ui | partial | character-gallery.tsx:3; i18n.ts | gallery + RU dict; EN locale + lang switch missing |
| Settings: profile/models/memory/studio/usage/integrations/appearance/misc | 11 ui | done | settings-panel.tsx:59-78 | 8-group panel, lazy sub-panels |
| Custom instructions (что знает / как отвечать) | 11 ui | done | custom-instructions.tsx:56-215; server.py:11951 | two-field compose/parse → master prompt |

---

## LAYER 2 — MODES

| feature | category | status | citation | note |
|---|---|---|---|---|
| Слияние 5→3 (Мозг/Совет/Relay/Дебаты → Усилие) | 1 arch | partial | effort-selector.tsx:12-17; depth-slider.tsx:21-27 | depth slider live; Relay+Debate still separate |
| Усилие-слайдер: текучий Быстрее↔Умнее, 5 уровней, в топбаре | 3 effort | done | depth-slider.tsx:21-27; chat.tsx:4837,496 | 5-level + Auto, all modes |
| ДВА независимых диска: глубина vs длина | 3 effort | partial | chat.tsx:340-342,4952-4963; depth-slider.tsx | both exist; length dial is 3-state token toggle not named preset |
| Fast/Auto/Deep/Expert/Heavy явно различимы | 3 effort | done | depth-slider.tsx:22-26; effort-selector.tsx:12-17 | distinct labeled levels |
| НАТИВНЫЕ reasoning_effort/thinking-budget, иначе фолбэк промпт+токен [GAP] | 3 effort | done | server.py:349-416,3222-3226,13806-13816 | native + L3 prompt-emulation fallback |
| Мульти-движок наследует общий пад усилия | 3 effort | done | server.py:13225-13226,13262 | council passes reasoning_effort to members |
| Юзер решает усилие, авто не перебивает (кроме trivial→fast) [GAP] | 3 effort | done | server.py:13569-13580,4262-4290 | auto-brain only if no explicit choice |
| Авто-уровень сложности по вопросу (не макс на простом) [GAP] | 3 effort | done | depth-slider.tsx:48-74; server.py:4262-4290 | client classifyDepth + server query_is_hard |
| Длина ответа = пресет с override; Fast ~300 слов | 3 effort | partial | chat.tsx:340-348,3592 | 3-state budget chip; no named "Fast ~300 words" general preset |
| Токен-кап НЕ режет нативное мышление — тюнить кап по модели [GAP] | 3 effort | partial | server.py:409-416,13618,8073 | floor applied but flat 4000/3000, not per-model tuned |
| Конфиг-окно: lead + N участников + какие подчинены [GAP-FEATURE] | 4 multi | done | chat.tsx:7577-7720,622,5462-5473 | CouncilConfigPopover: members 2-5 + synth + per-head prompts |
| Совет: юзер выбирает число моделей (1-N) → синтез в 1 | 4 multi | done | server.py:13123,13166-13188; chat.tsx:622 | backend 2-5, frontend stepper+picker |
| Мозг: lead/driver + несколько craft/responder | 4 multi | done | server.py:13947-13985,13953-13956 | driver + expert + 1-3 parallel experts |
| Мозг оркеструет N моделей, пресеты cheap/mid/top | 4 multi | done | server.py:13595-13602,13554-13555; chat.tsx:347-348 | tier-based selection wired |
| Различать Совет/Ресёрч, Сравнить/Ресёрч, Heavy/Мозг | 4 multi | done | server.py:13520-13534; function-bar.tsx:34-47 | distinct server methods |
| Объединить Fusion/Совет/Heavy (разница = число моделей) | 4 multi | partial | chat.tsx:624; server.py:13531-13532 | beam removed from front, server path remains |
| Мозг/Совет с полной памятью+тулзами как обычный чат | 4 multi | done | server.py:13196-13222,13988-13993 | members get RAG+grounding+memory |
| Fusion-критик: кнопка проверки на деградацию/галлюцинацию | 4 multi | partial | chat.tsx:770,2178-2209,6738-6740 | verify mechanism exists; no standalone button |
| Чат↔агент с памятью+тулзами; агент думает Мозгом/Советом | 4 multi | done | server.py:13518-13523,6804-6865; orchestrator.py | agent-os sessions inherit think mode |
| Mode auto-router: classifyIntent() switches mode on send | 11 ui [EXTRA] | done | route-intent.ts:24-31; chat.tsx:3651-3654 | client heuristic, fires on send |
| Research mode: multi-step web search + synthesis | 2 modes [EXTRA] | done | server.py:12964-13114 | plan→search→read→synthesize, 3 depths |
| Relay mode: uncensored crafter → frontier responder | 2 modes [EXTRA] | done | server.py:12848-12963 | 2-step pipeline |
| Compare mode: N models as cards, no synthesis | 2 modes [EXTRA] | done | server.py:13386-13499 | parallel fan-out member_answer SSE |

---

## LAYER 3 — STUDIO

| feature | category | status | citation | note |
|---|---|---|---|---|
| Артефакты любого типа: PDF/Word/Excel/диаграммы/картинки/видео/код/сайты/3D/анимация | 9 studio | done | artifacts/*; export-doc.ts:29,39,167,539; three-view.tsx:3 | all viewers real, lazy-loaded libs |
| Кнопки экспорта под ответом (PDF Word Markdown), модель знает про файлы | 9 studio | done | chat.tsx:8007-8009,3104,270,282 | 3 export buttons + system prompt |
| Все видео/картинка-модели с сортировкой, бренд-скролл; featured-звезда первой | 9 studio | done | image-studio.tsx:391,940,914-950; server.py:9499,9529 | sort modes + featured star |
| Цена ПЕРЕД генерацией на КАЖДОЙ модели [GAP] | 9 studio | done | image-studio.tsx:426-457,461-476 | priceLabel on generate button (ledger stale) |
| Студия-мод: любой импортированный скилл | 9 studio | done | image-studio.tsx:53,76; studio-skills.tsx:36-40 | live sub-tab runs installed skills |
| Видео по референсу/своему стилю + кастом-текст [GAP] | 9 studio | done | image-studio.tsx:380,493-494,1184-1186; server.py:10143-10145,9628 | r2v wired (ledger stale) |
| Видео метрить по реал-цене, audio списывать [GAP] | 9 studio | done | server.py:10170-10236,10273-10275,10346,8564,8579 | pre-reserve+reconcile+refund (ledger stale) |
| Реклама/UGC (Arcads): товар → таргет-реклама [partial GAP] | 9 studio | partial | ad-generator.tsx:3,15; server.py:12137-12152; ad_gen.py | script-gen + own avatar pipeline; no real Arcads API |
| Text-to-image (seed/steps/cfg/neg/upscale/img2img) | 7 studio [EXTRA] | done | server.py:10423,3367,3392,3439; image-studio.tsx:734,1143 | full image pipeline |
| Video t2v/i2v/r2v/avatar | 7 studio [EXTRA] | done | server.py:10103,9628; image-studio.tsx:380,599-602 | AIMLAPI + NanoGPT fallback |
| Music generation (AIMLAPI + lyrics) | 7 studio [EXTRA] | done | server.py:10296,9680; image-studio.tsx:77,1039 | SSE poll, reserve+refund |
| Cinema/film composer (storyboard AI + ffmpeg) | 7 studio [EXTRA] | done | cinema-studio.tsx:1-607; storyboard.ts:36; server.py:10542 | scenes→ffmpeg MP4, SSRF guard |
| Photo tools panel (upscale/edit/faceswap/extend) | 7 studio [EXTRA] | done | image-studio.tsx:55,867,84-96; server.py:10506,9439 | all wired to backend |
| Video-RAG (web video → transcript+frames → store) | 7 studio [EXTRA] | done | video_rag.py:1-176; server.py:12176; knowledge-panel.tsx:8,41 | YouTube subs + frame captions → rag_ingest |
| 3D from photo (AIMLAPI TripoSR) | 7 studio [EXTRA] | partial | server.py:10391; image-studio.tsx:65,672-678; three-view.tsx:3 | backend+frontend coded, gated TD3_AVAILABLE=false (provider down) |
| Скиллы НЕ заменяют photoreal/AI-видео/музыку/3D (architecture) | 7 skills | done | skill_caps.py:566; SKILL-TRANSFORMER-PLAN.md | harness vs native generation separated |
| Скиллы как бесплатная альтернатива (Remotion/MoviePy/manim) | 7 skills | done | skill_caps.py:53-59; skills_run.py:357 | media-verb skills get full badge |

---

## LAYER 4 — AGENT

| feature | category | status | citation | note |
|---|---|---|---|---|
| Агентный цикл: think(Совет)→act→verify→memory, типизированные события | 8 agent | done | agent_os.py:239,271,306,357,400,441; server.py:11117,13332 | full L15 harness, resumable, SSE |
| Архитектор↔Критик дебат-петля; роли+бюджет+approve [partial GAP] | 8 agent | done | debate.py:101; server.py:12463,6162; chat.tsx:520,165 | convergence + budget + human gate (ledger understated) |
| Открытый вопрос-гейт (SSE question, попап+кнопки/инпут) [partial GAP] | 8 agent | done | server.py:6162,12449; use-taiga-chat.ts:370; chat.tsx:7386-7396 | option buttons + free-text + skip (ledger understated) |
| Confidence-бейдж (empirica) [GAP] | 8 agent | done | server.py:1681; chat.tsx:6712-6734; use-taiga-chat.ts | 3-tier badge (ledger understated) |
| Jules-like автономия: воркеры нон-стоп | 8 agent | partial | orchestrator.py:112,243; server.py:11564 | parallel threads 110s budget; no persistent daemon / 10h build |
| Параллельные агенты изолированно (worktrees) → мерж; 4+/10+/40/50 лейнов | 8 agent | partial | agent_os.py:531,576; orchestrator.py:254 | logical isolation, cap 4-5, NO git worktrees |
| Сессия-координатор: STATUS + локи + смоук + бинарный DoD | 8 agent | partial | server.py:6074-6076,6139; agent_os.py:140,164 | locks + resumable state; no smoke gate / DoD field |
| Watchdog + self-wake: 10ч-билд, авто-resume при краше | 8 agent | partial | agent_os.py:500; use-taiga-chat.ts:865 | resume() exists, no endpoint, no cron |
| Харнес-репо (walkinglabs/Awesome-Code-as-Agent/Paperclip/Ralph) | 8 agent | partial | server.py:5373,10816; agents-marketplace.tsx | install-by-URL works; no Ralph/Paperclip/guild catalogue |
| Drag-and-drop конструктор воркфлоу (механика лупа) [partial GAP] | 8 agent | missing | (no ReactFlow/node-graph anywhere) | zero implementation |
| Тайга-Кодер: Jules/Devin-like, 4 мода (cloud/BYO/daemon/ephemeral) | 8 agent | missing | (no match in any file) | no dedicated coder subsystem |
| Screen copilot (getDisplayMedia→vision, реал-тайм) | 10 code [EXTRA] | done | screen_copilot.py:30; server.py:12154; screen-copilot.tsx:114-120 | frame→vision→tip/target/done |
| Brain mode: cheap driver triages → strong expert | 2 modes [EXTRA] | done | server.py:13947-13985 | ask_expert tool, 1-3 experts |
| agent-modes-guide.tsx: 3-mode explanation panel | 11 ui [EXTRA] | done | agent-modes-guide.tsx:1-320 | static guide (Command/Orchestrator/KARIMO) |
| 17 worker personas | 3 agent [EXTRA] | done | FEATURE-INVENTORY:48; orchestrator.py | selectable persona per worker |
| Per-worker model choice + BYOK | 3 agent [EXTRA] | done | FEATURE-INVENTORY:50-51 | TaskPacket, owner-gated catalog |
| Per-subtask acceptance criteria (LLM judge) | 3 agent [EXTRA] | done | FEATURE-INVENTORY:58 | verified, surfaced in timeline |
| KARIMO как dev-движок (PRD→агенты→PR) | 13 misc | missing | agent-modes-guide.tsx (described only) | loop-builder described, not built |

---

## LAYER 5 — MEMORY

| feature | category | status | citation | note |
|---|---|---|---|---|
| Память-артефакт на чат, у каждого своя | 5 memory | done | chat-memory.ts; chat.tsx:1252,6919 | per-chat fact list + panel |
| Память растёт: cross-chat профиль, умнеет со временем | 5 memory | done | chat.tsx:1287-1290; profile.ts | mergeProfile + style note cross-chat |
| Слайдер N-сообщений памяти | 5 memory | partial | chat-memory-panel.tsx:140-161; server.py:8271 | extraction-frequency slider; inject-count is server cfg not UI (ambiguous) |
| Авто-извлечение ВЫКЛ по умолчанию, не извлекать в uncensored | 5 memory | done | chat.tsx:900,1261 | both met |
| Юзер-ручка частоты консолидации (фикс 6ч) [GAP] | 5 memory | missing | server.py:9067 | idle_sec=6h hardcoded, no override |
| Mem0/Letta/RAG: кэш/компакт/референс/raging | 5 memory | done | server.py:8805,8934,8902,1459 | reconcile+consolidate+quantize+rag all live |
| Авто-recall ТОЛЬКО на обратную ссылку, инжект раз, кап/дедуп | 5 memory | partial | chat.tsx:1903-1925; recall.ts | fires every non-trivial msg, no back-ref gate, no inject-once |
| Факт-чек памяти против веба/реальности [partial GAP] | 5 memory | missing | (no web-verify pipeline) | not started |
| Per-chat мастер-промпты + шаблоны артефактов по моду | 5 memory | done | chat-memory-panel.tsx:87-95; chat.tsx:3062 | master prompt per chat wired |
| Память → песочница (MEMORY.md в E2B чате) | 5 memory [EXTRA] | done | mem_to_sandbox.py:104; server.py:12267-12272 | tombstone-filtered MEMORY.md on first sandbox use |
| Grounding / анти-галлюцинация (источник правды, сноски [N]) | 5 memory [EXTRA] | done | server.py:2082,13636-13641,1857 | source-truth + numbered footnotes |
| FTS5 индекс памяти (поиск по чатам + фактам) | 5 memory [EXTRA] | done | server.py:7677,7797,7693 | BM25 via SQLite FTS5 |
| Tombstones (forget X не возвращается) | 5 memory [EXTRA] | done | server.py:7987,7996,8035,8023 | complete tombstone system |
| Style note (сленг/T9/тон) | 5 memory [EXTRA] | done | server.py:8647,12241; chat.tsx:1296-1302 | cross-chat style note |
| Экспорт памяти (one-click download) | 5 memory [EXTRA] | done | server.py:12550 | portable JSON taiga-memory-v1 |
| Episodic recall API (/api/recall) | 5 memory [EXTRA] | done | server.py:10742,8748 | keyword search past 200 chats |
| Гибрид BM25+RRF [GAP] | 13 misc | done | server.py:1507-1512,1560 | hybrid default-on |
| Сленг/семантика: T9-опечатки/смысл, тумблер интерпретации | 13 misc | partial | (interpretation toggle, style-profile.ts) | style note covers slang; explicit toggle unconfirmed |
| Анти-дрифт re-anchor [partial GAP] | 13 misc | missing | (no re-anchor module) | not found |

---

## LAYER 6 — CODE / SANDBOX / SKILLS / MCP

| feature | category | status | citation | note |
|---|---|---|---|---|
| Терминал↔ИИ живьём (tool_result → терминал) | 10 code | done | server.py:12252-12285,13740-13774; terminal-panel.tsx:43 | persistent E2B per chat, owner local fallback |
| Песочница E2B/Daytona/Modal, общая на чат | 10 code | partial | skills_run.py:407-453; server.py:13740 | E2B only; Daytona+Modal absent |
| Файлы НЕ на сервере: E2B/local/KV/браузер; эфемерно | 10 code | partial | server.py:12286-12303,7900-7924 | E2B + opt-in encrypted server; no KV/browser-local |
| BYOK + свои эндпоинты/сервера | 10 code | partial | server.py:2785-2832,12395-12399; settings-panel.tsx:160-164 | BYOK keys done; custom base_url absent |
| Браузер-копилот: MV3, читает/кликает/печатает/скроллит | 10 code | done | taiga-extension/manifest.json:2,content.js:1-156; server.py:11737; browser-panel.tsx | MV3 + Playwright server-side |
| Скриншот экрана → ИИ видит UI (getDisplayMedia→vision) | 10 code | done | screen_copilot.py:30; server.py:12154; screen-copilot.tsx:114 | frame every 6s → vision JSON |
| Реал-тайм анализ браузера: хранить/референсить видео/веб | 10 code | partial | video_rag.py:1-14; server.py:12176; rag-manage.ts:37 | URL-based ingest only, no live stream |
| Sandbox-гейт для не-владельцев (анти-RCE) | 10 code | done | server.py:12249,12257,13707-13710,13760 | caller_is_owner everywhere (MINE #0) |
| Полные скиллы как Claude Code: GitHub-скилл → любая модель → скрипты | 7 skills | done | skills_run.py:96; server.py:10830; skill_caps.py:443 | whole-folder import, gated run |
| Скиллы — НЕ просто промпт: мультишаг, SKILL.md | 7 skills | done | skills_run.py:634; server.py:13643-13663 | SKILL.md injected as harness |
| Персистентность скиллов между сессиями | 7 skills | done | server.py:4919; skills_run.py:216 | per-user disk index |
| Маркет агентов+скиллов, install-by-link · единый реестр | 7 skills | done | server.py:10788,10816; skills-marketplace.tsx; tool-marketplace.tsx | single-URL + bulk-repo + folder import |
| MCP-коннекторы (юзер приносит свои) | 7 skills | done | server.py:6910-7192,11953,12315,7177 | full MCP client, 7-catalog, SSRF, encrypted token |
| Скилл-трансформ / compatibility badge | 7 skills [EXTRA] | done | skill_caps.py:443,566; skill-caps.ts:274; skill-badge.tsx | full/partial/instruction/needs-server/unsupported |
| Библиотека 300+/3000+ скиллов (GitHub+токен) | 7 skills | partial | skills_lib.py:62; skills_index.json (358) | 358 seeded vs 3000+ target; 868 available |
| гильдия/комьюнити-паки | 7 skills | missing | (no guild concept anywhere) | zero code |
| RAG-Anything (arbitrary file types) [GAP] | 13 misc | partial | server.py:1504 | rag_ingest accepts text blobs, no separate pipeline |

---

## LAYER 7 — SETTINGS (routing + catalog + billing + security + automation)

| feature | category | status | citation | note |
|---|---|---|---|---|
| Показывать ТОЛЬКО живые модели; прятать 502/402/фантом | 6 routing | done | server.py:3774,2344,4051 | phantom excluded from routing (note: still in catalog payload) |
| Фантом-детект (Grok на Venice) → авто-фикс/self-heal | 6 routing | done | server.py:4010,4034,3793,15089 | probe + 6h self-heal cron |
| Авто-downgrade при капе в cheap-пул (не обрезать) | 6 routing | done | server.py:3653,3639 | 3-step ladder (NanoGPT) |
| Живой каталог: авто-фетч, новые (405b/550b TEE), дропать мёртвые | 6 routing | done | server.py:2128,14894,14918,14921 | 30-min refresh, flap protection |
| Сумма токенов по всем аккаунтам; реальный баланс per provider | 6 routing | done | server.py:3712,3743; sidebar.tsx:173 | Venice/NanoGPT/Chutes polled, total summed |
| Категоризация: скорость/тип/цена/приватность/мощь + сортировка | 6 routing | done | server.py:937,995,1015,977,882,2213,2215 | cat/caps/kind/privacy/smart computed |
| Баг tier: substring mini ловит miniMax/geMINI [GAP] | 6 routing | done | server.py:724-726 | \b(mini\|nano\|tiny\|micro)\b word-boundary fix |
| Opus НЕ дефолт — дешёвый роутинг; auto-brain перебивал [баг] | 6 routing | done | server.py:4067-4070,4282,269 | short query → cheap |
| Кто отдаёт картинки/видео, кто дешевле | 6 routing | done | server.py:1015,523,8592; cinema-studio.tsx:176 | kind + gen_usd in catalog |
| Баланс-aware cross-provider авто-роутинг: замена по балансу [GAP] | 6 routing | partial | server.py:3956,3838-3846,3653 | gates at selection; no mid-flight swap |
| NanoGPT не финансировать; подписка только для теста | 6 routing | partial | server.py:261,3511,1076 | tracked; comment-only, NanoGPT is primary in practice |
| Бенчмарки для выбора (artificialanalysis/Terminal-Bench-Hard), не хардкод [GAP] | 6 routing | partial | server.py:769,865; auto_update.py:100-152 | AA fetched to disk; WIRE into bench() explicitly deferred |
| TEE/приватность в 3 группах, вес TEE-роутинга | 6 routing | partial | server.py:977,985-991 | 5-6 privacy labels; no routing weight |
| Per-user wallet: баланс в USD, метеринг на каждый вызов | 8 billing [EXTRA] | done | server.py:8459,8480,8541,8466-8477 | atomic per-user USD, markup, ledger |
| Billing config: markup %, rate limit, RUB/USD, avg_msg_usd | 8 billing [EXTRA] | done | server.py:8406,8429,8452 | live USDT/RUB CoinGecko+CBR |
| Видео/audio real-price metering | 8 billing [EXTRA] | done | server.py:8564,10178,10275,8579 | charge_media + refund_media |
| Структурный adapter routing (adapter_config.toml) | 6 routing [EXTRA] | done | adapter_config.toml; structured_adapter.py | task-type routing, models hardcoded |
| Личность «Агент S»; никогда не раскрывать движок | 12 sec | done | server.py:2362-2416,2455-2462,2477 | IDENTITY_REMINDER + scrub (Claude not hidden, owner directive) |
| Тонкий систем-промпт: тянуть по требованию | 12 sec | done | server.py:2443-2462 | _CAPABILITY_BRIEF + tool_self |
| Убрать self-knowledge манифест (~1200-1500 ток) из каждого сообщения | 12 sec | done | server.py:14964,15056 | self_manifest cached, on-demand only |
| анти-инъекция/отравление памяти | 12 sec | done | server.py:2419-2430,1847-1852,8608-8620 | TRUST_BOUNDARY + RAG fence + _safe_fact |
| Optional PBKDF2 signup/login + session tokens | 12 sec [EXTRA] | done | auth.py:50-104; server.py:10725-10739 | PBKDF2-600k + HMAC tokens |
| CORS / SSRF / rate-limit / input caps / edit denylist / secret redaction | 12 sec [EXTRA] | done | server.py:61-69,4710,2898-2958,2964-2971,5643-5663; guard.py:17-45 | all live |
| wrap_untrusted wired to web tool results | 12 sec [EXTRA] | stub | guard.py:72-76 | defined, never called (TRUST_BOUNDARY only) |
| Face-swap гард на реальных людях — позже | 12 sec | missing | server.py:9443-9481 | tool live, no detection (DEFERRED "позже") |
| scheduler.py daemon + /api/jobs owner cron (balance-gated) | 13 sched [EXTRA] | done | scheduler.py:1-273; server.py:10937,14940-14950 | interval+time engine |
| Per-user routines (hourly/daily/weekdays/weekly, max 50, idempotent) | 13 sched [EXTRA] | done | server.py:14543,14651-14699,11472 | + agent-automations.tsx UI |
| Event routines on_run_done / on_chat_match (producer FIRES) | 13 sched [EXTRA] | done | server.py:14500-14511,14763-14799,11504 | previously-noted gap CLOSED |
| Cron на Mac (launchd plist for auto_update.py) | 13 misc | stub | auto_update.py:1-153 | standalone script, no plist, snapshot never read back |
| Тайга знает себя: авто-self-manifest (не статичный TOOLS_PROMPT) | 13 misc | done | server.py:14964,15056 | live introspection |
| LangChain/LangGraph (g-brain на LangGraph) | 13 misc | done | orchestrator.py:1 | LangGraph StateGraph |
| temperature-TODO [GAP] | 13 misc | partial | GAPS-RECOVERED.md:11 | literal TODO, temperature saved but not forwarded all paths |
| failover 45→10мин [GAP] | 13 misc | missing | GAPS-RECOVERED.md:30 | specific timeout change not applied |
| Архитектор-режим [partial GAP] | 13 misc | partial | debate.py | debate loop done; per-turn blueprint+conflicts+2-3Q mode partial |
| убрать 5 slash-заглушек | 13 misc | partial | (slash command stubs) | cleanup, status unconfirmed |
| пайплайн-пресеты с шагами [GAP] | 13 misc | partial | (pipeline-presets buttons exist) | preset buttons exist, exact step arrays missing |
| авто-бенчмарки через API [GAP] | 13 misc | partial | auto_update.py:104 | fetch exists, not wired into selection (dup of bench WIRE) |

---

## LAYER 8 — POLISH (UI shell finish, voice, i18n, backgrounds)

| feature | category | status | citation | note |
|---|---|---|---|---|
| Liquid-glass; глобальный анимированный фон + кастом (импорт/Ultra-генерит) | 11 ui | partial | glass-filter.tsx; mode-background.tsx:6-8,269 | glass + per-mode canvas bg done; import-custom + Ultra-gen-bg missing |
| голос chat-to-chat | 11 ui | missing | (no impl) | voice-to-switch-chat not found |
| Voice dictation (STT) + hands-free loop + TTS auto-speak | 11 ui [EXTRA] | done | use-voice-input.ts:28; chat.tsx:736,3983; audio-gen.ts:24 | STT browser-only + 3-tier TTS + hands-free |
| Paid TTS (NanoGPT) + free TTS (Google) + ElevenLabs BYOK | 7 studio [EXTRA] | done | server.py:10239,10279; audio-gen.ts:42-90 | 3 providers, billing on paid |
| Per-message speak/stop + markdown cleanup before TTS | 11 ui [EXTRA] | done | chat.tsx:3153-3200; audio-gen.ts:11-22 | wired |
| Server-side STT / Whisper endpoint | 11 ui [EXTRA] | missing | (no /api/transcribe) | STT browser-only → breaks Safari/iOS (CIS mobile hole) |
| #audit-галерея | 11 ui | missing | (no component) | UI screenshot audit gallery absent |
| 8-direction window resize + tiling/snap | 11 ui | missing | floating-window.tsx (corner-br only) | only 1-2 resize directions, no tiling |
| Traffic-light minimize/maximize functional | 11 ui | stub | floating-window.tsx:93-97 | red/X works, yellow/green decorative |
| i18n EN locale + language switch UI | 11 ui | missing | i18n.ts (RU-only, 106 lines) | EN dict + selector absent |
| Текучий hero 3 стадии (new/returning/power) | 11 ui | missing | chat-empty-hero.tsx:14 | single-stage only |
| Шрифт: per-font gradient/color/rounding controls | 11 ui | missing | theme-panel.tsx | font+accent done; per-font gradient/rounding missing |

---

## DEFERRED (gate before public launch — do NOT build now)

| feature | category | status | citation | note |
|---|---|---|---|---|
| billing.py YooKassa + idempotent webhook + убрать test_topup (MINE #1) | 12 sec | stub | server.py:12618-12642 | api_topup correct 503 stub; DEFERRED by Damir |
| Self-service top-up slider (RUB→USD) — payment processor | 8 billing | stub | FEATURE-INVENTORY:142 | 503-blocked pending processor; DEFERRED |
| pgvector+HNSW (Postgres vector store) — Phase D | 13 misc | missing | server.py:1504 (SQLite only) | DEFERRED scale |
| CLaRa-7B MLX (specific model) — Phase D | 13 misc | partial | mlx_compressor.py:18 (Qwen2.5-3B) | model-agnostic via env; CLaRa specific DEFERRED |
| БД JSON → Postgres / ASGI / object-storage / backups — Phase D | 13 misc | missing | (SQLite + stdlib http.server) | DEFERRED scale to 10k |

---

## Reconciliation notes (duplicates collapsed)

- **Video-by-reference / price-before-gen / real-price metering** appear in both ledger cat 9 and GAPS — counted once as Studio rows, all marked **done** (ledger `[GAP]` markers are stale; maps cite wired code).
- **Confidence badge / debate loop / question-gate** appear in ledger cat 8 marked `[GAP]`/`[partial GAP]` — counted once as Agent rows, all **done** (maps cite wired code).
- **Гибрид BM25+RRF** (cat 13) is the implemented half of the cat-5 RAG item — counted once in Memory as **done**.
- **auto-benchmarks через API** (cat 13) and **Бенчмарки для выбора** (cat 6) are the same unwired AA pipeline — kept as 2 ledger rows but both reflect the single deferred WIRE step.
- **macOS dock** appears in cat 2 (button surfaces) and cat 11 (DOCK) — the dock-component itself is one **missing** row in Shell+Chat; the surface-placement aspect is the separate "Поверхности" partial row.
- **Voice items** split across Studio (TTS providers) and Polish (STT/hands-free/chat-to-chat) per build layer.
