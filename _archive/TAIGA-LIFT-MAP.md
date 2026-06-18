# Тайга — КАРТА «откуда взять код» (verified 2026-06-12)

Проверено по живому GitHub + локальным клонам (`~/LibreChat`, `~/.hermes/hermes-agent`).
Лицензии — из реальных LICENSE-файлов. Вердикт: **CODE** = можно копировать легально ·
**PATTERN** = только идея, код закрыт.

## Вердикт по продуктам Damir-списка
| Продукт | Статус | Что берём |
|---|---|---|
| **LibreChat** | MIT ✅ CODE (локально `~/LibreChat`) | message-tree, presets, artifacts UI, MCP-дизайн |
| **rag_api** (danny-avila/rag_api) | MIT ✅ CODE | весь RAG-сервис (FastAPI+pgvector) как sidecar |
| **Claude Agent SDK** (anthropics/claude-agent-sdk-python/ts) | MIT ✅ CODE | agent-loop, subagents, hooks, permissions |
| **Aider** | Apache-2.0 ✅ CODE | diff/apply движок (Python) |
| **OpenHands SDK** | MIT ✅ CODE | confirmation/permission gate (Python) |
| **Cline** | Apache-2.0 ✅ CODE | shadow-git чекпоинты/undo (паттерн) |
| **Continue** | Apache-2.0 ✅ CODE | streamDiff, tool-policies (TS) |
| **CodeRabbit** | закрытый, НО предок MIT ✅ | `openai-pr-reviewer` форки (review-loop) |
| **Claude Code CLI** | проприетарный ⚠️ PATTERN | permission-ladder, decision-flow (через SDK) |
| **Pika** | закрытый ⚠️ PATTERN | UX; код → ComfyUI |
| **ComfyUI + Wan2.x/Mochi-1** | GPL / Apache ✅ CODE | видео-движок + «эффект = воркфлоу» |
| **Hermes** (NousResearch) | MIT, но НЕ чат-UI | только skill-creation/memory-loop |
| Cursor / Perplexity / v0 | закрытые ⚠️ PATTERN | чекпоинты · цитаты-до-генерации · живой канвас |

## Точные файлы (lift-source)

### Message-tree / форк / правка (→ наш §13 #1, §14)  — LibreChat MIT
- Схема: `packages/data-schemas/src/schema/message.ts` — поля `messageId` / `parentMessageId` /
  `conversationId`, корень = sentinel `00000000-0000-0000-0000-000000000000`.
- Форк: route `POST /fork` в `api/server/routes/convos.js`; логика `forkConversation` в
  `api/server/utils/import/fork.js` (обход дерева — портировать алгоритм в Python).
- UI свитчер «‹ 2/3 ›»: `client/src/components/Chat/Messages/SiblingSwitch.tsx` (копи-пейст почти
  как есть) + `MultiMessage.tsx` (логика выбора сиблинга) + `EditMessage.tsx` (правка→regenerate).
- **Портируемость: EASY.**

### RAG (→ §4) — danny-avila/rag_api MIT, FastAPI Python
- Запускать **как sidecar** (ближайшее к нашему стеку). Эндпоинты `app/routes/document_routes.py`:
  `POST /embed`, `POST /query` (k=4, scope by file_id), `GET /documents/{id}/context`.
- LibreChat зовёт по HTTP: `api/app/clients/prompts/createContextHandlers.js` (env `RAG_API_URL`,
  JWT, инъекция чанков в system-промпт). **Портируемость: MEDIUM (копируем сервис целиком).**

### Presets (→ §13) — LibreChat MIT, EASY
- Схема `packages/data-schemas/src/schema/preset.ts` (`presetId`, `model`, `promptPrefix`=системник,
  `temperature`...). UI `client/src/components/Chat/Menus/Presets/`.

### Решает-сам / права / риск-оценка (→ наша фича «Решает сам») — OpenHands SDK MIT, Python
- `openhands-sdk/openhands/sdk/security/confirmation_policy.py` — `should_confirm(risk)` +
  `AlwaysConfirm` / `NeverConfirm` / `ConfirmRisky(threshold)`. Риск: `security/risk.py` +
  `security/llm_analyzer.py`. **Самый чистый, готовый, на Python — копировать прямо.**

### Diff / применение правок (→ режим Код) — Aider Apache-2.0, Python
- `aider/coders/editblock_coder.py` — `find_original_update_blocks`, `replace_most_similar_chunk`
  (точное→пробелы→`...`→fuzzy), `do_replace`. + `search_replace.py`, `udiff_coder.py`.
  **Лучший OSS diff-движок, Python, drop-in.**

### Agent-loop / subagents / hooks (→ g-brain, §8) — Claude Agent SDK MIT
- `anthropics/claude-agent-sdk-python` — тот же движок, что под Claude Code CLI: цикл, исполнение
  тулзов, субагенты (изолированный контекст, параллель), hooks (PreToolUse/PostToolUse/Stop/
  UserPromptSubmit), permission-режимы. Тулзы = in-process MCP-сервера (ложится на наш Python).
- Альтернатива/дополнение для g-brain: LangGraph (провайдер-агностик, лучше под мульти-провайдер).
- Чекпоинты/undo: Cline shadow-git (паттерн). Streaming-diff UI: Continue `core/diff/streamDiff.ts`.

### Видео-студия (→ §6/§16) — ComfyUI GPL + Wan2.1/Mochi-1 Apache (коммерч-безопасно)
- ComfyUI = node-граф воркфлоу → **«именованный эффект = сохранённый воркфлоу»** (= идея
  reference-шаблонов вирусных видео). T2V/I2V/V2V/lip-sync. UX-паттерны Pika: режим-табы,
  regenerate→сетка вариантов, «modify region» (видео-inpaint).

### Code-review (если делаем) — openai-pr-reviewer форки MIT (FluxNinja/Tao He)
- `review.ts` (цикл), `bot.ts` (LLM), `commenter.ts` (комменты), `tokenizer.ts` (бюджет токенов),
  инкрементальный ревью только дельты между коммитами. Канонический CodeRabbit-репо = 404, брать форк.

## Топ-6 «взять первым» (закрывает Тир-1 без переписывания)
1. **rag_api** целиком (sidecar) → §4 RAG готов.
2. **SiblingSwitch.tsx + MultiMessage.tsx + message-tree схема + fork-алгоритм** → §13 дерево.
3. **OpenHands `confirmation_policy.py` + `risk.py`** → фича «Решает сам» (готовый риск-гейт).
4. **Aider `editblock_coder.py`** → применение правок в режиме Код.
5. **Claude Agent SDK** → не переписывать agent-loop; обернуть (subagents+hooks+права бесплатно).
6. **LibreChat presets + artifacts UI** → §13 пресеты + боковая панель артефактов.

## Честные флаги
- LibreChat Code-Interpreter **песочница = платная проприетарная** (открыт только UI) → свою.
- LibreChat agent-loop + MCP = TS/LangGraph (`danny-avila/agents`, `packages/api/src/mcp/`) —
  для Python только ПАТТЕРН; брать официальный Python MCP SDK.
- «Hermes» НЕ даёт чат-UI код. Источник чат-кода = LibreChat.
- Все «CODE»-репо: сохранять attribution (MIT/Apache NOTICE).
