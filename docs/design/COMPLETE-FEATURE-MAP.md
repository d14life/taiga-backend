# COMPLETE FEATURE MAP — Taiga AI (NO-MISS CENSUS)

> **This document SUPERSEDES `AUDIT-95-CHECKLIST.md`** as the canonical no-miss feature census.
> It deduplicates **819 raw enumerated entries** across 5 sources by *meaning* (a UI window +
> its endpoint + its old-design screen = ONE feature), merges build-state (any-live → live;
> else partial > mock > absent), and tags which features need a master-prompt / config layer.
>
> Build-state merge rule: **live** beats everything; otherwise **partial** > **mock** > **absent**.
> "Config-section" = feature needs a per-feature master-prompt / settings layer (cfg:Y in any source).

## Totals

| Metric | Value |
|---|---|
| **Total unique features** | **186** |
| **Live** | 96 |
| **Partial** | 47 |
| **Mock** | 9 |
| **Absent** | 34 |
| **COUNT TO BUILD (partial+mock+absent)** | **90** |
| Features needing a config / master-prompt section | 38 |

### By desk
| Desk | Count |
|---|---|
| Чат / Разговор | 50 |
| Агент | 41 |
| Студия | 19 |
| Память | 22 |
| Код | 15 |
| Дизайн | 17 |
| Настройки | 28 |
| Ultra | 8 |
| global | 36 |

> (Reference-repo URLs and pure backend-arch notes are tracked separately at the end and not counted as product features.)

---

## DESK: Чат / Разговор

| Feature | Desk | Kind | Build | Config | Source |
|---|---|---|---|---|---|
| Чат (core stream chat: SSE, context, history) | Чат | window | live | | shell.html:1524 · api.js:37 · server.py:12006 /api/chat · AUDIT-95:12 · MFI:152 |
| SSE streaming core (Taiga.stream, delta/meta) | Чат | tool | live | | api.js:37 · MFI:153 |
| JSON POST helper (Taiga.post) | Чат | tool | live | | api.js:13 |
| Код (chat code-mode: highlight, diff) | Чат | window | partial | | shell.html:1525 · /chat /code · AUDIT-95:16 |
| Без цензуры (uncensored route) | Чат | window | live | | shell.html:1526 · modes.js:164 · /api/uncensor · AUDIT-95:20 |
| Рерайт отказа (refusal-detector → uncensored rewrite) | Чат | button | live | | shell.html:1530 · modes.js:164-210 · MFI:182 · AUDIT-95:48 |
| Ультра (auto-orchestrator entry) | Чат | window | partial | Y | shell.html:1527 · AUDIT-95:24 |
| Мозг (lead + craft experts → synthesis) | Чат | mode | live | Y | shell.html:1528 · modes.js:130-157 · FLEDGER:37 · AUDIT-95:28 |
| Совет (N models fan-out → synthesis) | Чат | mode | live | Y | shell.html:1486 · modes.js:92-115 · FLEDGER:36 · AUDIT-95:32 |
| Сравнить модели (side-by-side) | Чат | window | live | Y | shell.html:1487 · modes.js:218-281 · AUDIT-95:36 |
| Relay / конвейер моделей (request-fixer→responder) | Чат | mode | partial | | AUDIT-95:40 · flows2/f06-relay |
| Дебаты (architect vs critic rounds) | Чат | window | live | Y | shell.html:1529 · modes.js:322 · /api/debate · agent.js:172 |
| Веб-поиск (freshness, links, citations) | Чат | tool | live | | shell.html:1531 · tools.js:69 · /api/websearch · MFI:183 |
| Супер-поиск (multi-engine, dedup) | Чат | tool | live | | shell.html:1532 · modes.js:380 · /api/supersearch · MFI:184 |
| Глубоко (extended thinking / reasoning-effort) | Чат | window | partial | Y | shell.html:1533 · AUDIT-95:60 |
| Ресёрч (plan→search→read→report, bg task) | Чат | mode | live | | shell.html:1488 · MFI:186 · AUDIT-95:64 · flows2/f05-research |
| Проверка реальности (claim-extract + judge + verdicts) | Чат | window | live | | shell.html:1534 · memory.js:322 · /api/verify · AUDIT-95:68 |
| Источники правды (truth registry + RAG whitelist) | Чат | window | live | Y | shell.html:1518 · memory.js:261 · /api/sources · AUDIT-95:72 |
| Grounded mode / source-of-truth injection | Чат | mode | live | | flows2/f07-grounded · /api/sources |
| Подсказки-продолжения (follow-up chips, до 4) | Чат | button | live | | shell.html:1535 · chats.js:352 · /api/followups · MFI:123 |
| Модель / каталог (~800 model registry, thread-bound) | Чат | window | partial | Y | shell.html:902 · 21-model.png · AUDIT-95:80 |
| Авто-роутер модели (by last message) | Чат | tool | live | | MFI:194 |
| Баланс-aware cross-provider авто-роутинг | Чат | tool | partial | | FLEDGER:57 |
| Авто-уровень сложности по вопросу [GAP] | Чат | mode | absent | | FLEDGER:29 |
| Нативный reasoning_effort/thinking-budget + промпт-фолбэк | Чат | setting | partial | Y | FLEDGER:27 · modes.js:33-44 |
| Слияние 5→3 режимов (Мозг/Совет/Relay/Дебаты→Усилие) | Чат | mode | partial | | FLEDGER:11 |
| Конфиг-окно мульти-модельных режимов (lead+участники) | Чат | window | absent | Y | FLEDGER:35 |
| Два независимых диска: глубина мышления vs длина ответа | Чат | panel | partial | | FLEDGER:25 |
| Усилие-слайдер (Быстрее↔Умнее, 5 уровней) | Чат | panel | live | | FLEDGER:24 · MFI:111 · composer:1031 |
| Fusion-критик (проверка деградации/галлюцинации) | Чат | button | live | | FLEDGER:42 · /api/verify |
| Персонажи (system-prompt + avatar + settings store) | Чат | window | live | Y | shell.html:1496 · account.js:430 /api/identity · AUDIT-95:84 |
| Улучшить промпт (prompt-rewrite on fast model) | Чат | button | live | | shell.html:1536 · modes.js:422 · /api/improve · AUDIT-95:88 |
| Пресеты-роли (Юрист РФ / Сеньор-кодер / Копирайтер / Аналитик) | Чат | button | live | | shell.html:1024-1027 · MFI:162 |
| Пресет-система (мод+модели+промпт = кнопка) | Чат | setting | live | | FLEDGER:123 |
| Композер «+» (все тулзы в одном) | Чат | button | live | | shell.html:1029 · FLEDGER:120 |
| Композер — выбор модели (Авто pill) | Чат | button | live | | shell.html:1030 |
| Композер — усилие pill (Сбаланс.) | Чат | button | live | | shell.html:1031 |
| Композер — длина ответа pill (Средне) | Чат | button | live | | shell.html:1032 |
| Голос в композере (mic, STT) | Чат | button | mock | | shell.html:1033 · MFI:161 · 20-voice.png |
| Голос hands-free (STT + TTS auto-speak) | Чат | tool | live | Y | MFI:198 · 20-voice.png |
| Отправить / Enter-to-send (composer send) | Чат | button | live | | shell.html:1034 |
| Tools-panel «+» (9 групп: прикрепить/режим/поиск/доверие/приватность/усиление/бюджет/инструменты/действие) | Чат | panel | live | | shell.html:1152-1160 CHAT_TOOLS |
| Прикрепить — Файл/Картинку/Скриншот/RAG/MCP | Чат | button | live | | shell.html:1152 · tools.js:288 /api/extract |
| Скриншот-захват → screen copilot | Чат | button | live | | tools.js:311 · /api/screen_copilot |
| Приватность — Приватно / Призрак (ghost) | Чат | tool | partial | | shell.html:1156 |
| Хуки per-chat (триггер→инжект промпта) | Чат | tool | live | | MFI:197 · 18-hooks.png |
| Чат-хуки (trigger-matcher, sandbox runtime) | Чат | tool | partial | | AUDIT-95:259 |
| Sidebar chat search (local filter) | Чат | panel | live | | chats.js:227 · shell.html:725 |
| Map overlay chat search (/api/search_chats) | Чат | command | live | | chats.js:107 · server.py:12060 |
| Ghost-chat preview (/api/chat GET) | Чат | flow | live | | chats.js:128-190 |
| History compact (/api/compact) | Чат | command | live | | chats.js:396 · server.py:12244 |
| User config presets (/api/userconfig) | Чат | panel | live | Y | chats.js:482 · server.py:11939 |
| New chat reset / Новый чат | Чат | button | live | | shell.html:724 · chats.js:547 · dockHot:253 |
| Поиск по чатам (sidebar) | Чат | button | live | | shell.html:725 |
| Мульти-чат как LibreChat (проекты) | Чат | panel | live | | FLEDGER:122 |
| Hero morphing text (empty screen, 3 stages) | Чат | panel | mock | | MFI:202 |
| Slash-command mode activation (/council /brain etc.) | Чат | command | live | | modes.js:565 · MFI:196 |

---

## DESK: Дизайн

| Feature | Desk | Kind | Build | Config | Source |
|---|---|---|---|---|---|
| Стол «Дизайн» — холст (dv-canvas, инструменты) | Дизайн | desk | live | | design.js:361-416 · MFI:209 · 32-designcanvas.png |
| Прототип (375/768/1440, версии, .html экспорт) | Дизайн | window | live | | shell.html:1489 · design.js:17-21 · AUDIT-95:109 · cap/design/3 |
| Слайды (генерация из брифа, .html) | Дизайн | window | live | | shell.html:1490 · design.js:17-21 · AUDIT-95:113 · cap/design/4 |
| Лайв-правка (postMessage DOM-мост + AST-патчи) | Дизайн | window | partial | | shell.html:1541 · AUDIT-95:117 |
| График (Vega-Lite/Chart.js iframe, SVG/PNG) | Дизайн | window | live | | shell.html:1542 · design.js:17-21 · AUDIT-95:121 |
| Таблица / Excel (HyperFormula + openpyxl/SheetJS) | Дизайн | window | live | | shell.html:1543 · AUDIT-95:125 |
| Диаграмма (mermaid, SVG→PNG) | Дизайн | window | live | | shell.html:1544 · design.js:17-21 · AUDIT-95:129 |
| 3D-сцена (three.js, орбита/свет) | Дизайн | window | live | | shell.html:1545 · MFI:216 · AUDIT-95:133 |
| Веб-артефакт (Превью/Код, .html, CSP) | Дизайн | window | live | | shell.html:1546 · design.js:88-127 · MFI:217 · AUDIT-95:137 |
| Дизайн-система (палитра/токены, W3C JSON) | Дизайн | window | live | Y | shell.html:1493 · design.js:155-185 · /api/design-system · AUDIT-95:141 |
| Дизайн-система из референс-картинки (vision-extract) | Дизайн | button | live | | design.js:196 · /api/design-system-from-ref |
| Рисовалка (PNG, слои, кисть, 1080×1080) | Дизайн | window | absent | | shell.html:1547 · MFI:219 · AUDIT-95:145 |
| Liquid-glass + глобальный анимированный фон (custom/Ultra-gen) | Дизайн | setting | partial | | FLEDGER:118 |
| Design artifact generator (/api/chat → HTML iframe) | Дизайн | flow | live | | design.js:88-127 |
| Design canvas generating state | Дизайн | section | live | | cap/design/2-design-generating |
| /canvas (command) | Дизайн | command | live | | shell.html:1108 |
| /image intent (image_intent endpoint) | Дизайн | endpoint | live | | server.py:12118 /api/image_intent · /api/image-tool |

---

## DESK: Студия

| Feature | Desk | Kind | Build | Config | Source |
|---|---|---|---|---|---|
| Картинки (text2image + img2img + апскейл ×4, Flux+ESRGAN) | Студия | window | live | Y | shell.html:1462 · studio.js:189 · /api/image · MFI:231 · AUDIT-95:75 |
| Видео (t2v/i2v/talking-head/r2v/avatar, async) | Студия | window | live | Y | shell.html:1481 · studio.js:221 · /api/video · MFI:232 · AUDIT-95:79 |
| Аватар (LoRA Flux / talking-head, instant-ID) | Студия | window | live | | shell.html:1485 · studio.js:523 · MFI:236 · AUDIT-95:83 |
| Кино (таймлайн/склейка MP4, ffmpeg) | Студия | window | live | | shell.html:1537 · /api/cinema-export · MFI:237 · AUDIT-95:87 |
| Реклама (UGC) (LLM-скрипт→talking-head+TTS+сабы, Arcads) | Студия | window | partial | | shell.html:1538 · /api/ad_gen · FLEDGER:101 · AUDIT-95:91 |
| Музыка (жанры, инструментал/вокал, waveform, стемы) | Студия | window | live | Y | shell.html:1482 · studio.js:257 · /api/music · MFI:233 · AUDIT-95:95 |
| Озвучка (TTS) (голоса, эмоции, XTTS/Kokoro, клон) | Студия | window | live | Y | shell.html:1483 · studio.js:295 · /api/audio · /api/free-tts · MFI:234 |
| 3D — .glb из фото (TripoSR/Hunyuan3D, three.js-вьювер) | Студия | window | partial | | shell.html:1484 · studio.js:323 · /api/td3 · MFI:235 · AUDIT-95:103 |
| Режиссёр / раскадровка (shot-list, grid 4) | Студия | window | absent | | shell.html:1539 · MFI:239 · AUDIT-95:107 |
| Медиа-инструменты (апскейл/face-swap/extend ×2/×4/×8) | Студия | window | live | | shell.html:1540 · /api/image-tool · MFI:240 · AUDIT-95:111 |
| Артефакты любого типа (PDF/Word/Excel/диаграммы/видео/3D) | Студия | tool | live | | FLEDGER:95 · 28-artifacts.png |
| Кнопки экспорта под ответом (PDF/Word/Markdown) | Студия | button | live | | FLEDGER:96 |
| Видео по референсу/стилю + кастом-текст [GAP] | Студия | tool | absent | | FLEDGER:97 |
| Цена ПЕРЕД генерацией на каждой модели | Студия | panel | live | | FLEDGER:99 · studio.js:70-95 (price-confirm) |
| Video model catalog (/api/video-models) | Студия | tool | live | | studio.js:49 · server.py:11994 |
| Music model catalog (/api/music-models) | Студия | tool | live | | studio.js:50 · server.py:11997 |
| 3D model catalog (/api/td3-models) | Студия | tool | live | | studio.js:51 · server.py:11999 |
| Студия (настройка) — пресеты/конфиг | Студия | window | partial | Y | shell.html:1573 · AUDIT-95:311 |
| Studio price-confirm UI (double-click guard) | Студия | flow | live | | studio.js:70-95 |

---

## DESK: Агенты

| Feature | Desk | Kind | Build | Config | Source |
|---|---|---|---|---|---|
| Стол «Агент» — канбан-доска (Очередь/В работе/Готово) | Агент | desk | live | Y | shell.html:917 · agent.js:62-121 · /api/agent_os · MFI:254 · 27-agentpanel.png |
| Агент-ОС (ядро, шина задач, supervise/pause/kill) | Агент | window | live | | shell.html:1549 · /api/agent_os · AUDIT-95:157 · sub-overview |
| Сделать агента (конструктор: имя/режим/промпт/MCP) | Агент | flow | partial | Y | shell.html:1494 · MFI:258 · AUDIT-95:141 |
| Мои агенты + маркет (published_agents, scopes consent) | Агент | window | live | | shell.html:1548 · /api/install_agent · AUDIT-95:145 |
| Команда (Исследователь/Кодер/Критик, бюджет-резерв) | Агент | window | live | Y | shell.html:1463 · agent.js:123-170 · /api/orchestrate · MFI:255 · 23-team.png |
| Бюджет-слайдер + апрув-режим (Спрашивать/Авто) | Агент | panel | live | | MFI:257 |
| Оркестратор (план→воркеры→синтез, LangGraph DAG) | Агент | window | live | Y | shell.html:1491 · /api/orchestrate · MFI:260 · 26-orchestrate.png |
| Конвейер (пайплайн модель→модель, пресеты) | Агент | window | partial | | shell.html:1550 · MFI:262 · AUDIT-95:161 |
| Ralph (авто-цикл implement→verify, монитор) | Агент | window | partial | | shell.html:1551 · MFI:263 · AUDIT-95:165 · sub-ralph |
| Студия лупов (редактор шаблонов циклов) | Агент | window | absent | | shell.html:1552 · MFI:264 · AUDIT-95:169 · 24-loops.png |
| Галерея лупов (готовые шаблоны, клон) | Агент | window | absent | | shell.html:1553 · MFI:265 · AUDIT-95:173 |
| Луп-оценки (Promptfoo-стиль сюиты/скоры) | Агент | window | absent | | shell.html:1554 · MFI:266 · AUDIT-95:177 |
| Рутины (промпт по расписанию) | Агент | window | live | Y | shell.html:1492 · agent.js:222 · /api/routines · automations.js:160 · MFI:268 |
| Расписание (cron / Jobs, TZ, misfire) | Агент | window | live | | shell.html:1555 · automations.js:75 · /api/jobs · MFI:269 · 11-jobs.png |
| Доска задач (kanban, realtime-ws) | Агент | window | live | | shell.html:1556 · automations.js:131 · /api/jobs · AUDIT-95:189 · sub-tasks |
| Прогоны (история запусков, трейс, replay) | Агент | window | live | | shell.html:1557 · automations.js:184 · MFI:271 · sub-runs |
| Оценки (скоринг прогонов, A/B, промоут) | Агент | window | live | | shell.html:1558 · MFI:272 · AUDIT-95:197 · sub-evals |
| Песочница агента (E2B контейнер, аудит, promote→prod) | Агент | window | partial | | shell.html:1559 · AUDIT-95:201 · sub-sandbox |
| Гайд: 3 режима (рекомендатель режима, deeplink) | Агент | window | partial | | shell.html:1560 · AUDIT-95:205 · sub-modes |
| Дебаты двух моделей (роли+бюджет+approve) | Агент | mode | live | Y | shell.html:1529 · agent.js:172 · /api/debate · MFI:275 |
| Архитектор↔Критик дебат-петля [partial GAP] | Агент | mode | partial | | FLEDGER:89 |
| 17 worker personas | Агент | setting | live | | MFI:280 |
| Агентный цикл: think→act→verify→memory | Агент | flow | live | | FLEDGER:82 · flows2/f12-agent · /api/agent_fanout |
| Открытый вопрос-гейт (SSE question, попап) | Агент | panel | live | | FLEDGER:90 · /api/agent_answer · /api/agent_permit |
| Confidence-бейдж | Агент | button | live | | FLEDGER:92 |
| Параллельные агенты в worktrees (4-50 лейнов) | Агент | tool | partial | | FLEDGER:85 |
| Сессия-координатор (STATUS + локи + смоук + DoD) | Агент | tool | partial | | FLEDGER:86 |
| Watchdog + self-wake (10ч-билд, авто-resume) | Агент | tool | partial | | FLEDGER:87 |
| Drag-and-drop конструктор воркфлоу [partial GAP] | Агент | panel | absent | | FLEDGER:88 |
| KARIMO как dev-движок (PRD→агенты→PR) | Агент | tool | absent | | FLEDGER:142 |
| Agent Auto sub-tab (autonomous auto-run) | Агент | panel | live | | cap/agentdesign/sub-auto |
| Agent Tools sub-tab (tool registry) | Агент | panel | live | | cap/agentdesign/sub-tools |
| Скиллы (GitHub-import, SKILL.md, мультишаг) | Агент | window | live | Y | shell.html:1480 · code.js:232 · /api/skills · FLEDGER:72 · 04-skills.png |
| Маркет скиллов (модерация, подпись авторов, скан) | Агент | window | live | | shell.html:1561 · store.js:68 · /api/install_skill · AUDIT-95:215 · 03-skillmkt.png |
| Все скиллы (GitHub, read-only клон, AST-разбор) | Агент | window | live | | shell.html:1562 · code.js:302 · /api/import_skill_repo · AUDIT-95:219 |
| Библиотека 300+/3000+ скиллов (GitHub+токен) | Агент | panel | partial | | FLEDGER:74 · 02-fullskills.png |
| Маркет агентов+скиллов (install-by-link, гильдия) | Агент | panel | live | | FLEDGER:78 · store.js:150 |
| MCP-коннекторы (юзер приносит свои) | Агент | tool | live | | FLEDGER:79 · code.js:432 · /api/mcp · 01-mcp.png |
| Skill import & run flow (GitHub URL→import→run→output) | Агент | flow | live | | flows2/skill-import-run · /api/skill_folder |
| Agent multi-tool flow (multi-step tools→result) | Агент | flow | live | | feature-flows/agent-multitool · /api/agent_fanout |

---

## DESK: Навыки и код

| Feature | Desk | Kind | Build | Config | Source |
|---|---|---|---|---|---|
| Стол «Код» — IDE (дерево+табы+код+терминал+чат) | Код | desk | live | | code.js:597-681 · MFI:299 · 15-terminal.png |
| Терминал (E2B shell, эфемерный контейнер, вывод) | Код | window | live | | shell.html:1464 · code.js:79 · /api/terminal · MFI:300 |
| Двойной терминал (2 сессии, мультиплексор) | Код | window | live | | shell.html:1565 · MFI:301 · AUDIT-95:235 |
| Запуск кода (Python/JS/bash, gVisor/firejail) | Код | window | live | | shell.html:1566 · code.js:177 · /api/run · MFI:302 · AUDIT-95:239 |
| Песочница моделей (API-playground ~769 моделей) | Код | window | partial | Y | shell.html:921 · tools.js:237 · /api/sandbox · 16-playground.png · AUDIT-95:243 |
| Конструктор команд (слэш-шаблоны, типизир. аргументы) | Код | window | live | | shell.html:1563 · code.js:392 · /api/build_function · AUDIT-95:223 |
| Конструктор функций (JSON-Schema, sandbox seccomp) | Код | window | live | | shell.html:1564 · code.js:346 · /api/build_function · AUDIT-95:227 |
| Браузер (агентный headless / MV3 копилот) | Код | window | live | | shell.html:1567 · code.js:481 · /api/browser · MFI:311 · 13-browser.png |
| Браузер-копилот MV3 (читает/кликает/печатает) | Код | tool | live | | FLEDGER:109 · /api/browser_act |
| Со-пилот экрана (getDisplayMedia→vision, kill-switch) | Код | window | live | | shell.html:1568 · code.js:527 · /api/screen_copilot · FLEDGER:110 · 19-copilot.png |
| Хуки (событийная шина, sandbox-исполнение) | Код | window | live | | shell.html:1569 · 18-hooks.png · AUDIT-95:255 |
| MCP-серверы (7 встроенных + свои) | Код | window | live | | shell.html:1571 · code.js:432 · /api/mcp · MFI:310 |
| File Search — семантический поиск по файлам | Код | tool | partial | | MFI:317 · 09-filesearch.png |
| Терминал↔ИИ живьём (tool_result→терминал) | Код | tool | live | | FLEDGER:105 |
| Песочница E2B/Daytona/Modal (общая на чат) | Код | tool | partial | | FLEDGER:106 · /api/sandbox |
| Тайга-Кодер (Jules/Devin-like, 4 мода) | Код | mode | absent | | FLEDGER:84 |
| Server-side STT / Whisper endpoint | Код | tool | absent | | MFI:325 |

---

## DESK: Память и данные

| Feature | Desk | Kind | Build | Config | Source |
|---|---|---|---|---|---|
| Память (per-account vector store, факты edit/add/forget) | Память | window | live | Y | shell.html:1472 · memory.js:57 · /api/remember · /api/forget · MFI:344 · 05-memory.png |
| Память-артефакт на чат (у каждого своя) | Память | tool | live | | FLEDGER:46 |
| Память растёт cross-chat (профиль) | Память | tool | live | | FLEDGER:47 |
| Авто-извлечение памяти ВЫКЛ по умолчанию (не uncensored) | Память | setting | live | | FLEDGER:49 · /api/mem_extract |
| Memory consolidate (/api/memory_consolidate) | Память | tool | live | | server.py:12228 |
| Слайдер N-сообщений памяти | Память | panel | partial | | FLEDGER:48 |
| Юзер-ручка частоты консолидации [GAP] | Память | setting | absent | | FLEDGER:50 |
| Экспорт памяти (скачать JSON/MD, подпись, реимпорт) | Память | window | live | | shell.html:1572 · memory.js:110 · /api/export_memory · MFI:348 |
| База знаний (RAG) (ingest→chunk→embed, BM25+вектор, rerank) | Память | window | live | Y | shell.html:1515 · memory.js:163 · /api/rag_ingest · /api/rag_query · MFI:349 · 07-knowledge.png |
| RAG delete (/api/rag_delete) | Память | button | live | | memory.js:155 · server.py:12196 |
| Видео-RAG (URL/файл, ASR+vision-эмбеддинги, таймкоды) | Память | window | live | | shell.html:1516 · memory.js:207 · /api/video_rag · MFI:350 · 06-smartrag.png |
| Проекты (папки чатов, общий RAG+память, ACL) | Память | window | live | | shell.html:1495 · MFI:351 · 25-projects.png · AUDIT-95:283 |
| Эпизодический поиск (recall по прошлым чатам) | Память | window | live | | shell.html:1517 · memory.js:225 · /api/recall · MFI:352 |
| Источники правды (реестр доменов/документов) | Память | window | live | Y | shell.html:1518 · memory.js:261 · /api/sources |
| Живой документ (версии, re-ingest, diff, анти-дрифт) | Память | window | absent | | shell.html:1519 · MFI:355 · AUDIT-95:291 |
| Файлы на сервере (per-account envelope-keys, каскад-удаление) | Память | window | live | | shell.html:1520 · tools.js:192 · /api/userfiles · /api/files · AUDIT-95:295 |
| Рабочая память (scratchpad, TTL, авто-суммаризация) | Память | window | absent | | shell.html:1521 · MFI:357 · AUDIT-95:299 |
| Mem0/Letta/RAG (кэш/компакт/референс/raging) | Память | tool | live | | FLEDGER:51 |
| Факт-чек памяти против веба [partial GAP] | Память | tool | absent | | FLEDGER:53 |
| Per-chat мастер-промпты + шаблоны артефактов по моду | Память | setting | live | Y | FLEDGER:54 |
| RAG-Anything / CLaRa-7B MLX / BM25+RRF / pgvector+HNSW [GAP] | Память | tool | partial | | FLEDGER:139 |
| Memory recall flow (memorize→new chat→recall) | Память | flow | live | | feature-flows/memory-recall |

---

## DESK: Настройки

| Feature | Desk | Kind | Build | Config | Source |
|---|---|---|---|---|---|
| Настройки (8 групп: profile/models/memory/studio/usage/integrations/appearance/misc) | Настройки | window | live | Y | shell.html:1473 · account.js · MFI:377 · 17-settings.png |
| Профиль (имя/язык/стиль/uncensored, OTP, аватар S3) | Настройки | window | live | Y | shell.html:1497 · account.js:210 · /api/settings · AUDIT-95:303 |
| Модели (реестр цена/лимиты, per-user default/favourites) | Настройки | window | live | Y | shell.html:927 · account.js · /api/catalog · AUDIT-95:307 |
| Живой каталог моделей (авто-фетч, дроп мёртвых) | Настройки | panel | live | | FLEDGER:61 · /api/catalog/refresh |
| Показывать ТОЛЬКО живые модели (скрыть 502/402/фантом) | Настройки | setting | live | | FLEDGER:58 |
| Фантом-детект (Grok на Venice) → авто-фикс/self-heal | Настройки | tool | live | | FLEDGER:59 · /api/selftest |
| Биллинг / кошелёк (баланс, Карта/СБП/Крипта, ledger) | Настройки | window | partial | | shell.html:927 · account.js:130 · /api/billing · /api/topup · MFI:380 |
| Биллинг YooKassa + идемпотентность (отложено) | Настройки | setting | mock | | FLEDGER:128 · AUDIT-95:315 |
| Пополнение баланса (topup в топбаре/sidebar) | Настройки | button | partial | | shell.html:728 · MFI:112 |
| Balance display (/api/init billing) | Настройки | panel | live | | account.js:56 · /api/balance · /api/balances |
| Интеграции (vault секреты, OAuth refresh, MCP revoke) | Настройки | window | live | | shell.html:1574 · account.js:338 · AUDIT-95:319 |
| Интеграции: BYOK keys (/api/userkeys) | Настройки | section | live | | account.js:338 · server.py:12395 |
| Интеграции: API keys (/api/apikeys create/revoke) | Настройки | section | live | | account.js:368 · server.py:12400 |
| Интеграции: cookies store (/api/cookies save/delete/list) | Настройки | section | live | | account.js:373 · server.py:12236 |
| BYOK + свои эндпоинты/серверы | Настройки | setting | live | | FLEDGER:108 |
| Тема / палитра (тема/шрифт/плотность/акцент, CSS-токены) | Настройки | window | live | Y | shell.html:1508 · account.js:261 · /api/settings · MFI:389 |
| Язык интерфейса (ru/en, ICU i18n, fallback RU) | Настройки | setting | partial | | shell.html:1575 · account.js:315 · MFI:391 |
| i18n RU/EN (полный перевод) | Настройки | setting | absent | | FLEDGER:124 |
| Размер шрифта / Размер иконок (sm/md/lg) | Настройки | setting | live | | shell.html:1038 SIZE_STEPS · iconscale |
| Каталог фич (реестр метаданных, feature-flags, телеметрия) | Настройки | window | partial | | shell.html:1576 · store.js:302 · /api/catalog · AUDIT-95:331 |
| Аналитика расхода (timeseries токены×цена, CSV, алерты) | Настройки | window | absent | | shell.html:1577 · MFI:393 · AUDIT-95:335 |
| Диагностика / здоровье (health-чеки апстримов, статус) | Настройки | window | absent | | shell.html:1582 · MFI:394 · AUDIT-95:339 |
| Счётчики подписки (квоты, сброс окна, апсейл) | Настройки | window | absent | | shell.html:1583 · MFI:395 · AUDIT-95:343 |
| Библиотека промптов (CRUD, теги, переменные-плейсхолдеры) | Настройки | window | absent | | shell.html:1584 · MFI:396 · AUDIT-95:347 |
| Закладки-менеджер (папки/теги, fulltext, переход) | Настройки | window | absent | | shell.html:1585 · MFI:397 · AUDIT-95:351 |
| Что нового / changelog (лента релиз-нот, бейдж) | Настройки | window | live | | shell.html:1586 · store.js:379 · AUDIT-95:355 |
| Гид по режимам (sandbox-демо, deeplink, телеметрия) | Настройки | window | absent | | shell.html:1587 · MFI:399 · AUDIT-95:359 |
| Dev-режим per-user с гардрейлами | Настройки | setting | live | | FLEDGER:21 |
| Личность «Агент S» / не раскрывать движок | Настройки | setting | live | | FLEDGER:131 |
| Тонкий систем-промпт (убрать манифест из каждого сообщения) | Настройки | setting | live | | FLEDGER:132 |
| БД JSON → Postgres / failover 45→10мин [GAP] | Настройки | setting | absent | | FLEDGER:140 |

---

## DESK: Ultra

| Feature | Desk | Kind | Build | Config | Source |
|---|---|---|---|---|---|
| Ultra-режим (суб-столы Обзор/Дизайн/Студия/Агент/Код) | Ultra | desk | live | | shell.html:1760 ULT_DESKS · ultra.js:86 · MFI:331 |
| Ultra desk chat (/api/chat SSE, full history) | Ultra | desk | live | | ultra.js:86-145 |
| Ultra — Пульт чата (side panel, ULT_CFG) | Ultra | panel | live | Y | shell.html:1793 · ULT_CFG[0..6] (Модель/Усилие/Память/RAG/Мастер-промпт/Режим/Инструменты) |
| Ultra — эксклюзив пересборки интерфейса (3D-фон/тема/раскладка) | Ultra | mode | absent | | shell.html:1527 · MFI:337 · FLEDGER:9 |
| Ultra Enter-to-send wiring | Ultra | button | live | | ultra.js:149-155 |
| Ultra history re-render on setUltSub/setMode | Ultra | flow | live | | ultra.js:159-172 |
| Ультра (авто-оркестратор) | Ultra | mode | partial | | shell.html:941 · AUDIT-95:24 |
| 3-яруса (Обычный / Студия / Ultra) | Ultra | mode | partial | | FLEDGER:7 |

---

## DESK: global (shell / nav / desktop / store / infra)

| Feature | Desk | Kind | Build | Config | Source |
|---|---|---|---|---|---|
| Переключатель режимов (Чат/Дизайн/Студия/Агент/Код/Ultra) | global | button | live | | shell.html:936-941 MODES · MFI:109 |
| 6 столов: Чат Дизайн Студия Агент Код Ultra | global | desk | live | | FLEDGER:10 |
| Группы-флайауты (7 групп, openFly) + drag-to-dock | global | panel | partial | | shell.html:897-926 GROUPS · MFI:123 |
| Левый рейл (Поиск/Память/Проекты/Маркет/Аудит/Настройки/Тема) | global | panel | live | | shell.html:951-960 RAIL · MFI:117 |
| Поиск по всему ⌘K / Feature Map оверлей | global | command | live | | shell.html:766 #overlay openMap() · MFI:118 |
| Feature Map — поиск по фичам | global | command | live | | shell.html:769 #mapSearch |
| Feature Map — слэш-команды (27 команд) | global | command | live | | shell.html:1108 COMMANDS[0..26] · MFI:120 |
| Feature Map — конструктор кнопки (создать+закрепить) | global | panel | live | | shell.html:774 .creator · MFI:121 |
| ВСЁ = кнопка-объект {id иконка ярлык группа действие} | global | setting | live | | FLEDGER:14 |
| Магазин кнопок (app-store) по 7 группам | global | panel | live | | FLEDGER:15 · store.js |
| Drag, jiggle-delete, правый-клик, drag-reorder (кнопки) | global | button | partial | | FLEDGER:17 |
| macOS Dock — пины + drag-to-pin + jiggle-delete | global | panel | absent | | shell.html:1373 DOCK_DEFAULTS · MFI:127 |
| Desktop dock pin persist (/api/settings desktop.pins) | global | setting | live | | desktop.js:41-56 |
| Window layout persist (/api/settings desktop.wins) | global | setting | live | | desktop.js:60-76 |
| Desktop restore from server (/api/init settings.desktop) | global | flow | live | | desktop.js:160-187 |
| macOS-окна: drag/8-resize/светофор/тайлинг | global | window | partial | | FLEDGER:117 · MFI:117 |
| Тайлинг-меню окна (8 вариантов + во весь экран) | global | window | absent | | MFI:126 |
| Меню «Открыть как…» (wsMenu) | global | window | absent | | shell.html:740 · MFI:114 |
| Ресайз рабочей панели (drag левого края) | global | panel | absent | | MFI:115 |
| Рабочая панель + 7 WS-вкладок (Превью/Картинки/Файлы/Артефакты/План/Терминал/Задачи) | global | panel | partial | | shell.html:1649-1655 WS_TABS · MFI:113 |
| Выбор модели в топбаре (modelpick, каталог ~800) | global | button | mock | | shell.html:739 · MFI:116 |
| Топ-пилюля «Усилие» (5 уровней) | global | button | live | | shell.html:739 #topEffort · MFI:111 |
| Кнопка «Сайдбар» (toggleSide) | global | button | live | | MFI:110 |
| Маркет скиллов и агентов (store, install-by-link) | global | panel | live | | store.js:68-218 · MFI:140 · /api/skills |
| Feature catalog (/api/catalog + /api/init) | global | window | live | | store.js:302 |
| What's new snapshot (/api/init live stats) | global | window | live | | store.js:379 |
| App Store map header live counters | global | panel | live | | store.js:409 |
| Аудит готовности / #audit-галерея (все фичи+потоки) | global | panel | absent | | shell.html:534 #auditOv openAudit() · MFI:138 |
| Auth / Аккаунты (регистрация/вход, PBKDF2) | global | flow | live | | /api/auth · MFI:143 |
| iOS-бейджи уведомлений (setBadge/bumpBadge) | global | panel | absent | | MFI:132 |
| Тост-уведомления (toast) | global | panel | live | | MFI:133 |
| Клавиатурные шорткаты (Escape, ⌘K) | global | command | live | | MFI:135 |
| Мобильный сайдбар slide-in + scrim | global | panel | partial | | MFI:136 |
| Экспорт чата (/export command, PDF/Word/MD) | global | command | live | | shell.html:1108 COMMANDS[19] |
| OpenAI-совместимый endpoint (/v1/chat/completions, /v1/models) | global | endpoint | live | | server.py:11979 · 12402 |

---

## OLD-DESIGN-ONLY — present in old design / usertest captures, NOT yet in new (localhost:3000) shell — MUST still exist

These appeared in `usertest-jun15` captures or the old EVIDENCE/FINAL galleries and are flagged
`[old-only?]`. They still belong in the product and must be carried forward:

| Feature | Desk | Build | Note |
|---|---|---|---|
| Cookies / Session Cookies Panel | Настройки | live | 12-cookies.png — lives as backend `/api/cookies` + Integrations section; needs own UI panel in new shell |
| Beam Chat Mode | Чат | absent | EVIDENCE-GALLERY — old multi-branch beam mode, dropped from new mode list |
| Super / Super-agent Panel | Агент | partial | 30-super.png — folded into Agent-OS / orchestrator in new shell |
| Ralph Monitor sub-tab | Агент | partial | sub-ralph.png — Ralph exists as window; monitor sub-tab not in new ULT/agent desk |
| Truth / Source-of-Truth sub-tab (agent desk) | Агент | live | sub-truth.png — exists as «Источники правды» window, but not as agent sub-tab |
| Studio — Avatar Generation tab | Студия | live | cap/studio/5-аватар — exists as «Аватар» window |
| Studio — Kino tab | Студия | live | cap/studio/5-кино — exists as «Кино» window |
| Studio — Reklama / UGC tab | Студия | partial | cap/studio/5-реклама — exists as «Реклама (UGC)» window |
| Code Chat Mode | Код | partial | p24-mode-code — exists as «Код» chat-mode |
| Uncensored Chat Mode | Чат | live | p25-mode-uncensored — exists as «Без цензуры» |
| Ultra Chat Mode | Ultra | live | p26-mode-ultra — exists as Ultra desk |
| Billing Console / Cost Tracker | Настройки | partial | p13-billing — partial billing window in new shell |
| Persona / System-prompt config panel | Настройки | live | p15-persona — exists as «Персонажи» / identity |
| 3D Model Generation artifact (.glb) | Студия | partial | gen/model-proof.glb — exists as «3D — .glb из фото» |

> Net new-product gaps from old design: **Beam Chat Mode** (truly dropped) and standalone
> **Cookies panel UI** + **agent-desk Truth/Ralph sub-tabs** (backend exists, UI sub-tab missing).
> Everything else is a rename/relocation, not a loss.

---

## Reference repos & backend-arch notes (tracked, NOT counted as product features)

- Backend repo `taiga-backend` (github.com/d14life/taiga-backend), frontend `taiga-web`.
- `server.py` monolith ~15125 lines (ThreadingHTTPServer); `chat.tsx` ~8157 lines god-component.
- Donor repos: graphify, gbrain, gstack, rag-anything, mem0, letta, graphiti, ml-clara, sqlite-vec,
  ponytail, ralph, openharness, agentic-os, personal-os, librechat, lobe-chat, open-webui, big-agi,
  cherry-studio, anything-llm, langchain, langgraph, crewai, pydantic-ai, claude-squad, shadcn-ui,
  comfyui, flux, audiocraft, faster-whisper, chatterbox, vercel skills, llm-guard, bolt.diy, next.js,
  litestream, btcpayserver. (See `REFERENCE-REPOS.md`.)
- All `/api/*` endpoints (server.py:11908–12426) are mapped onto their product features in the tables above.

---

*Generated as the no-miss census. Supersedes AUDIT-95-CHECKLIST.md.*
