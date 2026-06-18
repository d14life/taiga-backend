# Reference repos — откуда система берёт силу

Все внешние репо, на которых стоит Тайга-сборщик. Изучать ТОЛЬКО идеи/паттерны
(не копировать лицензированный код). Новая сессия может склонировать и разобрать любой.

## Память / знание (наш стек — поставлен, см. MEMORY-SETUP.md)
- **graphify** — https://github.com/safishamsi/graphify — граф кода (query вместо grep). Offline, без ключа.
- **gbrain** — https://github.com/garrytan/gbrain — память агента + синтез С ЦИТАТАМИ + пометки о пробелах (MCP). Garry Tan, YC.
- **rag-anything** — https://github.com/hkuds/rag-anything — мультимодальный RAG по PDF/докам/скринам (LightRAG).
- **Mem0** — https://github.com/mem0ai/mem0 — долгосрочная память: авто-факты + реконсиляция ADD/UPDATE/DELETE (не раздувается). За нашим RAG.

## Экономия токенов / качество кода
- **ponytail** — https://github.com/DietrichGebert/ponytail — плагин Claude Code: минимальный код
  (−22% токенов, −20% стоимости, −54% строк), НО не режет валидацию/безопасность/доступность.
  Установка: `/plugin marketplace add DietrichGebert/ponytail` → `/ponytail full`.
  Команды: `/ponytail-review` (диф на переусложнение), `/ponytail-audit` (весь репо), `/ponytail-debt`.

## Дизайн / фичи (откуда учились)
- **open-codesign (opendesign)** — https://github.com/OpenCoworkAI/open-codesign — система, у которой
  разбирали дизайн и фичи. Локальная копия для разбора: claude-sessions/2026-06-14/harness-analysis/open-design/.
- **awesome-design-md** — https://github.com/VoltAgent/awesome-design-md — каталог дизайн-паттернов в markdown.

## Наши репо
- backend + доки + дизайн: https://github.com/d14life/taiga-backend
- frontend: https://github.com/d14life/taiga-web

## Как использовать (для новой сессии)
1. Память: подними graphify (готов) + gbrain/rag (нужны NVIDIA-эмбеддинги, см. MEMORY-SETUP.md).
2. Токены: включи ponytail (`/ponytail full`) на всю сборку.
3. Идеи: при затыке — склонируй нужный reference-репо, разбери паттерн, перенеси ИДЕЮ (не код).
