# Тайга — мастер-карта покрытия порта (definition of done)

Гарантия: КАЖДАЯ реальная фича/окно/коннекшен из `taiga-web` (132 компонента · 72 эндпоинта · 95 фич-поверхностей) имеет дом в новом дизайне. Ничего не теряем. Статус: ✅ wired (есть, подключить как есть) · 🔧 rewire (логика есть, вынести/переподключить) · 🆕 build (собрать из кирпичей) · 🗑 dead (удалить).

Источник: forward-сверка (60 wired/12 rewire/1 halluc) + reverse-аудит (132 компонента, 52 at-risk, 70% уже кодом). 2026-06-17.

---

## ГЛОБАЛЬНЫЙ ШЕЛЛ (виден на всех столах)
- ✅ Левый рейл (Поиск⌘K · Память · Проекты · Маркет · Настройки) — `nav-rail`
- ✅ Топ мода-табы 6 столов (Чат·Дизайн·Студия·Агент·Код·Ultra) — `tier-nav` (+вернуть Ultra-таб, +Код-стол)
- ✅ macOS-окна (drag/8-resize/светофор/тайлинг) — `floating-window`+`resizable-frame`+`resize-handle`
- 🔧 Док + тайлинг + отцепить-зону-в-окно — `window-rearrange`+`rearrange-toggle`+`lib/ui-layout` (СОБРАН, Provider не вмонтирован — подключить)
- 🔧 3-зонный layout с mobile-стэком — `resizable-shell` (собран, смонтировать как основу)
- ✅ ⌘K универсальная палитра — `command-palette` (= «Поиск» рейла, НЕ потерять)
- 🆕 Глобальный анимированный фон (Звёзды/Аврора/Тубы/Ultra-3D) + кастом (импорт/сделать/Ultra-генерит-3D) — `starfield`+`aurora`+`tubes-cursor`+`mode-background`+`ultra-fx`
- ✅ Стекло + light/dark/accent — `glass-filter`+`theme-panel`
- 🆕 Кнопка-система (app-store of buttons): любая фича→кнопка→док/композер/сайдбар/внутрь окна, jiggle-delete, per-user — `custom-bar`+`custom-buttons`+`tool-marketplace`+`feature-visibility`
- ✅ Тосты + error-boundary (обернуть студии) — `toast`+`error-boundary`
- 🔧 Онбординг + тур + гайд режимов (фич БОЛЬШЕ → учить) — `onboarding`+`capability-tour`+`agent-modes-guide`
- 🆕 i18n RU/EN-переключатель · 🆕 живой персональный hero-заголовок

## СТОЛ ЧАТ
- ✅ Композер + лента + thinking + цитаты — `chat`(распил)+`thinking-steps`+`tool-card`+`markdown`+`followup-chips`+`decision-card`+`sources-panel`
- 🆕 Композер-«+» (все инструменты в одной кнопке) — слить `plus-menu`+`function-bar`+`model-picker`+`depth-slider`+`memory-window`
- ✅ Пикер модели Авто+11 лого — `model-picker` · ✅ усилие — `depth-slider`
- ✅ Совет — `/api/chat council` · ✅ Мозг (🔧вытащить из настроек) — brain · ✅ Дебаты — `debate-panel`/`/api/debate`
- ✅ Сравнить — compare · ✅ Relay — chat_relay · ✅ Без цензуры — `/api/uncensor` · ✅ Рерайт отказа — uncensor
- ✅ Веб-поиск — `/api/websearch` · ✅ Супер-поиск — `/api/supersearch` · ✅ Глубоко — reasoning · ✅ Ресёрч — `/api/chat research`+`depth-slider`
- ✅ Проверка реальности — `/api/verify` · ✅ Источники правды (grounded) — `source-truth-panel`/`/api/sources`
- ✅ Подсказки-продолжения — `followup-chips`/`/api/followups` · ✅ Персонажи — `character-gallery` · ✅ Улучшить промпт — `/api/improve`
- ✅ Каталог моделей по компаниям — `model-catalog` · ✅ индикатор памяти «помню N» — `chat-memory`

## СТОЛ ДИЗАЙН
- ✅ Прототип · Веб-артефакт — `design-canvas-workspace`+`artifacts/web` · ✅ Слайды — `slides-canvas`(🔧+.pptx-экспорт) · ✅ Лайв-правка — canvas
- ✅ График · Диаграмма(mermaid) · Таблица · 3D-сцена(three.js) — `artifacts/{chart,diagram,sheet,three-runtime}`
- ✅ Дизайн-система (токен-контракт) — `design-system-studio` · ✅ Лаунчер — `design-studio`+`design-templates` · ✅ Рисовалка — canvas

## СТОЛ СТУДИЯ (5 тип-табов)
- ✅ Картинки(деф) — `image-studio`/`/api/image` · ✅ Видео — `/api/video` · ✅ Музыка — `/api/music` · ✅ Озвучка — `/api/audio` · ✅ 3D — `/api/video_rag`/td3
- ✅ Кино(таймлайн) — `cinema-studio` · ✅ Реклама(UGC) — `ad-generator`/`/api/ad_gen` · ✅ Аватар · ✅ Режиссёр · ✅ Медиа-инструменты — `photo-tools`+`studio-skills`

## СТОЛ АГЕНТ
- ✅ Сделать агента — `agent-builder` · ✅ Мои агенты+маркет — `agents-panel`+`agents-marketplace` · ✅ Команда — `team-panel`
- ✅ Оркестратор — `orchestrator-panel` · ✅ Агент-ОС (verify-харнес) — `agent-os-panel` · ✅ Конвейер — `pipeline-builder`+`pipeline-presets` · ✅ Ralph — `agent-ralph-monitor`
- ✅ Студия/Галерея лупов — `loop-studio`+`loop-gallery` · ✅ Луп-оценки — `loop-evals` · ✅ Рутины — `agent-automations`/`/api/routines`
- 🔧 Расписание(cron) — `/api/jobs` (нужен билдер UI) · ✅ Доска задач — `agent-tasks` · ✅ Прогоны — `agent-runs-panel` · ✅ Реплей — `run-replay`
- ⚠️ **AT-RISK НА ВИДУ:** Спенд-кап/бюджет — `spend-cap`+`agent-runs-panel` (тормоз денег) · Глобальный док прогонов — `agent-dock` · Права/вопрос mid-run — `permission-modal`+`agent-question-card`
- ✅ Песочница агента — `run-sandbox` · ✅ Дашборд/чарты — `agent-os-overview`+`agent-os-charts` (depriority) · ✅ Гайд 3 режима — `agent-modes-guide`

## СТОЛ КОД
- ✅ Терминал — `terminal-panel`/`/api/terminal` · ✅ Двойной терминал — `dual-terminal` · ✅ Запуск кода — `run-sandbox`/`/api/run` · ✅ Песочница моделей — `playground`
- ✅ **Браузер в чате (как Mac/Chrome)** — `browser-panel`+`browser-copilot-bar`/`/api/browser`+`/api/browser_act`+`lib/cobrowse-ext` ← ТВОЁ
- ✅ **Со-пилот по экрану** — `screen-copilot`/`/api/screen_copilot` · ✅ **Cookies/коннекшены** — `cookies-panel`/`/api/cookies`
- ✅ Скиллы — `full-skills-panel`/`/api/skills` · ✅ Маркет скиллов — `skills-marketplace` · ✅ Все скиллы(GitHub) — `/api/import_skill_repo`
- ✅ Конструктор команд — `command-builder` · ✅ Конструктор функций — `function-builder`+`func-config-popover`
- ✅ Хуки · Чат-хуки(🔧слить) — `hooks-panel`/`lib/chat-hooks` · ✅ **MCP-серверы/коннекторы** — `mcp-panel`/`/api/mcp` (+дубль в Настройки→Интеграции) ← ТВОЁ
- ✅ Dev-режим (киллсвитч shell/файлы) — `dev-mode-panel`

## ПАМЯТЬ / ДАННЫЕ (рейл + панели)
- ✅ Память(профиль+факты) — `memories-panel`+`chat-memory-panel`/`/api/remember,recall,forget` · ✅ Экспорт памяти — `memory-export-button`/`/api/export_memory`
- ✅ База знаний(RAG) — `knowledge-panel`/`/api/rag_*` · ✅ Видео-RAG — `/api/video_rag`
- 🔧 Проекты(папки чатов) · 🔧 Эпизодический поиск(`/api/search_chats`) · 🔧 Живой документ(`lib/living-doc`+anti-drift) · 🔧 Рабочая память(`chat-memory`)
- ✅ **Файлы на сервере (юзер-файлы, sandbox)** — `/api/userfiles`+`/api/files`+`run-sandbox` ← ТВОЁ · ✅ Источники правды — `sources-panel`

## НАСТРОЙКИ (хаб `settings-panel` — дёшево спасает кучу at-risk)
- ✅ Профиль · Модели(`model-settings`) · Память · Студия-дефолты · Биллинг/кошелёк(`/api/billing,topup,balance`) · Интеграции(MCP/секреты vault)
- ✅ Тема/палитра — `theme-panel` · 🆕 Язык RU/EN · ✅ Каталог фич — `feature-catalog`+`feature-visibility`
- ⚠️ usage-analytics НЕ дропать (несёт recordUsage-проводку для spend-cap) · ✅ Диагностика — `diagnostics` · ✅ Счётчики — `sub-meters`
- ✅ Библиотека промптов — `prompts-panel` · ✅ Мастер-промпт — `master-prompt-panel`+`custom-instructions` · ✅ Закладки — `bookmarks-panel` · ✅ Что нового — `whats-new`

## УДАЛИТЬ (мёртвое, проверено)
- 🗑 `agent-runs-viewer` ✅ удалён · 🗑 `sidebar-resizer` ✅ удалён · 🗑 UI-обёртки `mode-pills`/`effort-selector` (типы ModeId/MODES/EffortId ОСТАВИТЬ) · 🗑 `design-canvas` (старый ручной, после подтверждения)
- УДАЛИТЬ из дизайна: ничего (язык-свитчер → 🆕 строим EN+RU)

---
**Итог покрытия:** 6 столов + рейл + настройки + глобальный шелл = 100% реальных фич/окон/коннекшенов размещены. Браузер-в-чате, sandbox, файлы юзера, MCP, со-пилот экрана, cookies — все ✅ в столе Код/Память. При сборке каждой Фазы отмечаем строки этой карты — пока все не ✅, порт не «done».
