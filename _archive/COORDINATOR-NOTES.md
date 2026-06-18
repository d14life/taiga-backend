# ЗАМЕТКИ КООРДИНАТОРА (atlas) — для всех сессий + Damir

Снимок (ночь): **tsc=0 · backend HTTP 200 · server/orchestrator/browser/guard компилятся.** Всё зелёное.
Приоритеты — по `TAIGA-FOCUS.md` (12 Must-perfect, глубина не ширина). Делайте дифференциаторы.

## Что каждой лане делать дальше (по FOCUS)
**CORE (фронт):** доделать decision-card UI → **дерево сообщений** (lift LibreChat SiblingSwitch.tsx +
MultiMessage.tsx + parentMessageId) → **₽ везде** (import src/lib/money.ts, setRate(billing.rub_per_usd),
fmtRub/approxRub/fmtRubWhole) → **RAG-UI** (прокси /api/rag_ingest + /api/rag_query, инъекция [источник]) →
**супер-поиск UI** (/api/supersearch depth:"deep" в Ультре) → **браузер-панель** (/api/browser, скриншот+
клики, поле cookies) → **таймлайн оркестратора** (/api/agents + шаги). Browser-verify каждое.

**STUDIO (генерация):** cinema/photo-tools/agent-gallery — довести и **подключить к метеринг-эндпоинтам**;
**₽ на кнопках** (approxRub из money.ts); 191 NanoGPT-картинка уже в каталоге — показать; тулзы
(bg-remove/upscale/outpaint); **reels-генератор** (глитч-рейтинг шаблон, Revideo/ffmpeg + клипы + дубляж);
робастный поллинг видео (прогресс/отмена/watchdog). Метеринг НЕ выключать.

**BACKEND (server.py + модули):** orchestrator — **отдать стрим шагов (RUNS) для таймлайна**;
ECC-скиллы (262, MIT) в реестр; idle-очистка Chromium; шифрохранилище cookies; FTS5-память + /api/recall;
авто-рефреш каталога 6ч; payment — ТОЛЬКО скаффолд за флагом (test_topup ЗАКРЫТ).

## Координация (ОБЯЗАТЕЛЬНО)
- Впишите себя в `AGENTS-BOARD.md` (таблица КТО НА ЧЁМ) + ведите `STATUS-<id>.md`.
- Общие файлы (server.py, select.ts) — через замок `.agent-locks/` (см. AGENTS-BOARD.md), иначе затрёте.
- Вопросы → `QUESTIONS-<id>.md` (берите безопасный дефолт, НЕ стоп).
- Жёстко: без `git push`, без удаления данных, без реальной оплаты, без необратимого. tsc=0 всегда.

## 🔓 РАЗБЛОКИРОВКИ (atlas, проверено)
**@amur (STUDIO):** твой блокер УЖЕ решён — не жди ural.
- `nano_image_records()` уже влил **191 NanoGPT image-модель** в RICH-каталог (проверено: /api/catalog
  отдаёт 191 nano image-модель прямо сейчас).
- `nano_image(model, prompt, width, height)` уже есть в server.py — генерит через NanoGPT
  `/v1/images/generations`. Модель с id `ng:...` РОУТИТСЯ через /api/image автоматически.
- → bg-remove / outpaint / доп-провайдеры можно подключать СЕЙЧАС: бери nano edit/tool image-модели
  (id `ng:...`, ищи `*-edit-image` / *bg* / *outpaint* в каталоге) и зови /api/image с этим id.

**@ural (BACKEND):** запрос amur на nano-image ingestion закрыт (atlas сделал ранее). Не дублируй —
трать время на cookie-шифрохранилище + permission-tiers + охоту на half-wires.

## Решения, ждущие Damir (утро)
1. Процессор оплаты: CoinGate / OxaPay / BTCPay (СБП+крипта).
2. Воркеры оркестратора v1: наши модели (дёшево/крипта) ✅по умолчанию, или +Claude Agent SDK позже.
3. Музыка Suno — нужен крипто+ресейл провайдер (иначе park).
