# ТАЙГА — MASTER PLAN (единый источник правды, 2026-06-12)

Приватный, UNCENSORED, мульти-модель AI-чат + медиа-генерация для RU/СНГ, крипто-оплата, ресейл.
Этот файл = индекс + консолидированный Definition of Done. Детали — в связанных доках.

## ДОКИ-СПУТНИКИ
- `FINISH-PLAN.md` — задачи по ланам + DoD + беклог (рабочий план сессий)
- `PARITY-MATRIX.md` — фичи эталонов (ChatGPT/Grok/LibreChat/Hermes/MUAPI…) vs у нас (со 78 скринов)
- `LIFT-MAP-2.md` — что лифтить из 11 реп Damir (все MIT)
- `LIFT-MAP-3.md` — репы, что Damir НЕ находил (Mem0/Letta/big-AGI/ACE-Step/sqlite-vec… + лиценз-ловушки)
- `ADDON-FINAL.md` · `DISPATCH.md` — что сессии берут
- `TAIGA-GAP-ANALYSIS.md` — аудит ~80% готовности

## ПРОДУКТ: 3 ЯРУСА (🅜)
- **Обычный** — чат/код + все тулзы + g-мозг + uncensored под охраной (TEE) + терминал/файлы/диаграммы.
- **Студия** — картинки/видео/музыка/3D (платные модели + БЕСПЛАТНЫЙ код-рендер тир).
- **Ультра** — премиум-супер-агент: топ-модель, генерит видео/картинки ВНУТРИ чата, полный no-refusal, супер-поиск+оркестратор по умолчанию.
Fast/Auto/Expert/Heavy = ось УСИЛИЯ внутри яруса.

## DEFINITION OF DONE (🅜 must · 🅝 nice · ⏳ после-v1 · ⛔ отложено-Damir)
**Чат/ядро:** мульти-модель+роутинг+circuit-breaker+кросс-провайдер ✅ · 🅜 tools-меню (ChatGPT) ·
🅜 режимы Fast/Auto/Expert/Heavy ✅ · 🅜 слайдер памяти ✅ · 🅜 3-яруса · 🅜 /pipeline-конструктор цепочек ·
🅜 /uncensor команда · 🅝 тоггл-лимит трат · 🅜 **Decision/Question попапы** (Claude-Code-стиль, НОВОЕ).
**Память:** на-чат ✅ + профиль ✅ + 🅜 Memories-панель · 🅜 **Mem0** (долгосрочная, авто-факты) · 🅜 **Letta-паттерн** (модель сама правит память + умнеет со временем) · T9/семантика.
**Агенты/скиллы:** agent-builder ✅ · оркестратор ✅ · 🅜 skills-библиотека ✅ · 🅜 MCP-маркетплейс · 🅜 MCP-коннектор-при-создании · 🅜 **скилл-автоустановщик по ссылке** (НОВОЕ) · auxiliary-модели · self-knowledge · 🅝 big-AGI Beam (веер→слияние).
**Студия:** img✅/video✅/music✅/3D · 🅜 P0-сброс fix · 🅜 **FREE код-рендер** (картинки+видео: manim/MoviePy+ACE-Step+Kokoro+FLUX-schnell+ComfyUI-сервис) · видео-по-референсу · 🅝 медиа-плеер+ИИ-со-просмотр (НОВОЕ).
**Инфра:** 🅜 SQLite-миграция (sqlite-vec+sqlite-utils+Litestream) · 🅝 LLM-Guard-сайдкар (безопасность, без цензуры) · 🅝 rate-limit.
**Вид:** 🅝 темы/палитры · 🅝 Voice (Kokoro-TTS+faster-whisper STT) · 🅝 шрифты/фоны-по-режиму (НОВОЕ).
**Качество:** только рабочие модели ✅ · понятные ошибки ✅ · баг-свип (P0-reset/оркестр-таймаут/студия-retry) · мобайл · smoke 0 fail.
**🅝 само-тест:** /sprint (Тайга тестит себя, НОВОЕ).

## ЛАНЫ (сессии авто-тянут из FINISH-PLAN/LIFT-MAP)
- **S1 CORE (kedr):** chat.tsx — P0-fix, tools-меню, режимы, слайдер, 3-яруса, /pipeline, /uncensor-фронт, спенд-лимит, Decision-попапы, assistant-ui примитивы, Beam-UI.
- **S2 STUDIO (amur):** медиа — FREE код-рендер (ComfyUI/FLUX-schnell/ACE-Step/manim), видео-референс, медиа-плеер.
- **S3 BACKEND (ural):** server.py — SQLite-миграция, Mem0+Letta-память, rewrite_uncensored, генерация-роутер, MCP-маркетплейс, auxiliary, self_manifest, LLM-Guard, big-AGI Beam-движок, скилл-автоустановщик-бэк.
- **S4 CORE-B (sosna):** skills-реестр, темы/шрифты/фоны, Voice(Kokoro/whisper), Prompts/Bookmarks/Memories, AnythingLLM workspace-изоляция.
- **S5 COORDINATOR (я):** smoke+DoD+замки каждые 30 мин, гейт финиша.

## ЛИЦЕНЗИИ (жёстко)
✅ Копировать: MIT/Apache (free-claude-code, Mem0, Letta, big-AGI, assistant-ui, ACE-Step, Kokoro, faster-whisper, sqlite-vec, ECC, RAG-Anything, open-generative-ai).
⚠️ Только сервис/паттерн: ComfyUI(GPL), Open-WebUI(BSD пост-0.6.6), Agno(MPL).
🚫 НЕ копировать/НЕ смотреть: tanbiralam/claude-code (СЛИТО, DMCA — для скелета бери free-claude-code), anthropics/claude-code (закрыт), Lobe/Cherry/Jan (проприет/AGPL).
🚫 Лиценз-ЛОВУШКИ в медиа: MusicGen=CC-BY-NC · FLUX-dev=non-comm · Remotion=платно 4+ · Piper=GPL · Coqui=CPML → бери коммерч-замены (ACE-Step/FLUX-schnell/manim/Kokoro).

## ⏳ ПОСЛЕ v1 · ⛔ ОТЛОЖЕНО Damir
⏳: нативное десктоп-приложение · Cursor/Codex-фишки · Zep-граф-память (при противоречиях) · LlamaFirewall.
⛔: реальная оплата (BTCPayServer готов когда расцензуришь) · гард-дипфейк · соц-публикация · usage-аналитика · 3D пока triposr-провайдер лежит.
⚠️ muapi.ai — перепроверить крипто+ресейл (раньше OUT); если нет крипты — мимо правила.

## КООРДИНАЦИЯ (как это работает без ручного промпта)
Сессии само-обслуживаются из этих план-файлов (DISPATCH приказал «закончил блок → бери из беклога»).
Координатор кладёт новую работу в план → сессии подбирают сами. Damir пастит руками ТОЛЬКО для
перезапуска мёртвой сессии. Финиш = все 🅜must зелёные → координатор даёт СТОП «v1 done».
