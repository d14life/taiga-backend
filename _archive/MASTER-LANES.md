# MASTER LANES — Damir «do all / many lanes» (2026-06-12)

Coordinator merges; agents edit disjoint files, DON'T commit. Verify: backend=ast+curl, frontend=tsc.

## WAVE 1 (parallel, disjoint files)
- **L1 BACKEND (server.py):** (a) баланс — total_usd по всем 5 аккаунтам + live-refresh (фикс «+$20 не обновилось»); (b) каталог моделей live-refresh (новые 405b появляются без рестарта) + /api/catalog/refresh; (c) скилл по GitHub-URL: blob→raw, кап 256КБ→1МБ для скиллов, опц. user GitHub-token.
- **L2 SKILLS-UI (skills-marketplace.tsx, lib/skills/user-skills.ts, app/api/skills, app/api/install_skill):** показать 358 ECC-скиллов (поиск /api/skills) = сотни пресетов; GitHub-URL вставка (token-поле, дружелюбная ошибка).
- **L3 BALANCE+MODELS-UI (sidebar.tsx, model-picker.tsx, model-strip.tsx):** показать ИТОГО по всем кошелькам + кнопка обновить (live); пикер моделей перечитывает каталог (новые модели видны).
- **L4 AGENTS→ORCH (orchestrator-panel.tsx, lib/orchestrator.ts, lib/agents/user-agents.ts):** сохранённые агенты гонят оркестратор (panel шлёт workers).
- **L5 SLASH (lib/commands/builtins.ts, lib/commands/*, chat.tsx):** 5 заглушек /projects /vision /video /agents /checkpoint — развести/убрать; дедуп /pipeline /agents.

## WAVE 2 (after merge)
- MCP: OAuth (GitHub/Notion), resources/prompts, видимость в обычном чате.
- Унификация фрагментации: 3 формата скиллов / 3 списка агентов → один реестр.
- Ещё пресеты скиллов из репо (alirezarezvani/claude-skills, vercel-labs/skills).
- Темы/Voice-STT/Bookmarks дольёт в chat.tsx; мобайл-проход.

## Contract: skill GitHub install
Frontend POST /api/install_skill {user, url, token?}; backend конвертит github.com/blob → raw.githubusercontent, token→Bearer (только для raw host), кап до 1МБ.
