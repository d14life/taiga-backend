# ОСТАЛОСЬ ДО «v1 done» (координатор, проверено кодом 2026-06-12 ~19:35)

Смоук весь зелёный (tsc=0, server.py parse OK, /api/init 200, чат-стрим работает: __auto__→venice, «Понг», биллинг считает, локов нет).
3 из 4 лан фактически закрыты. ОСТАЛИСЬ 3 backend-🅜must — НЕ сделаны (проверено grep server.py = 0 совпадений):

## 🔴 BACKEND / ural — забрать из беклога (LIFT-MAP-3 raskidka)
1. **Mem0** (`mem0ai/mem0`, Apache) — долгосрочная память: авто-извлечение фактов + реконсиляция ADD/UPDATE/DELETE (не раздувается). За нашим RAG.  → `server.py` 0 совпадений `mem0`.
2. **Letta-паттерн** (`letta-ai/letta`, Apache) — модель САМА правит свою память (core_memory_append/replace) + sleep-time консолидация. Это «Тайга умнеет со временем».  → 0 совпадений.
3. **SQLite-миграция** (sqlite-vec + sqlite-utils) — JSON-файлы → один .db с вектор-поиском. Сейчас всё ещё JSON.  → 0 совпадений `sqlite`.

## ЗЕЛЁНОЕ (подтверждено кодом — НЕ трогать)
- S1 CORE (kedr): P0-fix, /pipeline, /uncensor, 3-яруса, Fast/Auto/Expert/Heavy, слайдер-памяти, tools-меню, спенд-лимит, **decision-card.tsx**, хук тем+Voice(onInsert/initTheme).
- S2 STUDIO (amur): картинки/видео/музыка, FREE код-рендер, видео-по-референсу(r2v), free-TTS. 3D ⏸ = провайдер AIMLAPI лежит (не наша вина).
- S3 BACKEND (ural) ЧАСТИЧНО: rewrite_uncensored, gen-роутер, auxiliary, self_manifest, **T9/семантика/сленг (6 совпадений)**, MCP-маркетплейс, skill-install — ✅. Память/БД (выше) — ❌.
- S4 CORE-B (sosna): skills-библиотека, prompts, memories-панель, bookmarks, бэкап. Темы+Voice — хук от kedr ОТДАН (initTheme+onInsert), осталась финальная привязка.

## ВЕРДИКТ: НЕ «v1 done». Осталось 3 backend-must (умная память + БД). Приложение работает и БЕЗ них — это апгрейды качества/масштаба, безопасно вынести в следующую пачку.
