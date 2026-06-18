# Тайга ИИ — MANIFEST (анти-путаница система)

**Назначение:** жёсткие рельсы, чтобы сессия НЕ путалась и НЕ забывала (как было раньше).
Читается ПЕРВЫМ. Порядок ниже — не пропускать шаги.

---

## ШАГ 0 — ПОСТРОИТЬ ГРАФ ЗНАНИЙ (graphify) — делать ДО всего

Вместо грепанья и забывания — **запрашивай граф знаний всего проекта.**

```bash
uv tool install graphifyy
graphify install            # зарегистрировать скилл в Claude Code
/graphify .                 # построить граф по ВСЕМУ репо: код + доки + PDF + скрины
```
Даёт `graph.html` (визуал), `GRAPH_REPORT.md` (концепции+связи+вопросы), `graph.json` (queryable).
Дальше вместо «где это / что это» — спрашивай граф:
- `/graphify query "как связаны чат-режимы и оркестратор?"`
- `/graphify query "какие фичи студии и где их код?"`
- `/graphify path "PaymentProvider" "scheduler"`

Граф ингестит 36 языков (tree-sitter) + Markdown + PDF + картинки. То есть ВСЕ 115 доков,
дизайны, 2 PDF-каталога и скрины попадают в один запрашиваемый граф. Код/видео — локально,
доки/PDF/картинки — через твой LLM-ключ. Репо: https://github.com/safishamsi/graphify

**Это и есть «система чтобы не путаться»: один граф истины, а не память агента.**

---

## ШАГ 1 — СТРОГИЙ ПОРЯДОК ЧТЕНИЯ (не пропускать)
1. `docs/MANIFEST.md` (этот файл) — рельсы + гардрейлы
2. `docs/NEW-SESSION-START.md` — точка входа + готовый промпт
3. `docs/PROJECT-BIBLE.md` — блюпринт: 182 фичи, решения, история
4. `docs/LOVABLE-HANDOFF.md` — build-spec: API + SSE + токены + 8 фаз
5. `REBUILD-BRIEF.md` — план + 2 мины
6. `FEATURE-INVENTORY.md` — чек-лист фич (поведение байт-в-байт)
7. `ARCHITECTURE-MAP.md` + `BACKEND-API.md` — что где + эндпоинты
8. `docs/design/README.md` — какой дизайн канон, какие доноры

## ШАГ 2 — ГАРДРЕЙЛЫ «НЕ ПУТАТЬСЯ» (локнутые истины — НИКОГДА не нарушать)
- **Дизайн-канон = `design-v3-current-shell-jun17.html`.** НЕ пересобирать с v0/v1/v2 — они ДОНОРЫ.
  Из доноров тянуть ТОЛЬКО когда Damir прямо укажет. usertest-jun15/ = старый вид, тоже донор.
- **ДОК:** в v3 добавить macOS-док снизу (иконки-приложения), как было раньше. Это первая задача сборки.
- **Не ломать shell.html** (macOS-окна + convo-dock) — он зафиксирован.
- **Стек:** фронт `taiga-web` (Next.js 16/React 19/Tailwind 4/@ai-sdk), бэк `server.py` (stdlib http.server, БЕЗ фреймворка).
- **Данные:** `~/.mostik-ai/` (db/taiga.db SQLite). Бэк :8777, фронт :3000, маршрут `/app`.
- **Security мины (перед публичным выкатом — обязательны):**
  - #0 `resolve_caller()` — НЕ доверять полю `user` из тела (подделка owner → RCE).
  - #1 RU-платёж не подключён → PaymentProvider (YooKassa/CloudPayments) + вебхук + идемпотентность.
- **Импорт скилла НЕ исполняет код**; запуск гейтится owner + песочница + денилист.
- **Планка:** без emoji (line/SVG иконки), без заглушек (`full-output-enforcement`), пруфы перед «готово».
- **Скиллы:** каждую задачу через `pick-skills` → process→implementation→verify. Не строить с нуля если скилл есть.
- **Не путать продукт:** это Тайга (AI-чат), НЕ Mostik (VPN-роутер). Разные проекты.

## ШАГ 3 — КАРТА РЕСУРСОВ ПО ОБЛАСТЯМ (фича → где доки/скрины/флоу/код)
| Область | Доки | Визуал |
|---------|------|--------|
| Ядро чата + режимы (Мозг/Совет/Сравнение/Ресёрч/Дебаты) | PROJECT-BIBLE, FEATURE-INVENTORY | screenshots/10-14, flows brain/council/debate |
| Студия (картинки/видео/музыка/озвучка/3D) | LOVABLE-HANDOFF (API), BACKEND-API | screenshots/13, flows image-gen/video-gen/music-gen/tts-gen |
| Агенты / Agent-OS | ROADMAP-AGENT-OS, AGENTIC-OS-UNBLOCK | screenshots/30-39, flows agent-multitool/orchestrate/team-run |
| Навыки + код + MCP + skill-transform | SKILL-TRANSFORMER-PLAN, DEV-TOOLING | screenshots/45,50-52, flows mcp-connect-use/skill-import-run |
| Память / RAG / grounding | PROJECT-BIBLE (память) | screenshots/46, usertest panels 05-memory/06-smartrag/07-knowledge |
| Голос / непрерывный разговор | LOVABLE-HANDOFF (audio API) | usertest panels 20-voice, flows tts-gen |
| Песочница / sandbox | REBUILD-BRIEF (security), PHASE-A-C-HARDENING | usertest panels 14-workspace/15-terminal |
| Биллинг / кошелёк | REBUILD-BRIEF (мина #1) | usertest panels 11-jobs, screenshots billing |
| Аккаунты / безопасность | REBUILD-BRIEF (мина #0) | settings screenshots |
| Автоматизация / крон | scheduler в ARCHITECTURE-MAP | usertest panels 24-loops |
| Настройки / кастомизация | GRAND-PLAN-CUSTOMIZABILITY | screenshots/44, usertest 17-settings/18-hooks |

Дизайн: `docs/design/` (v0-v3 + usertest-jun15 + 32 панели + 16 feature-flows + 2 PDF + 48 скринов + галереи).
Юзер-кейсы для теста: `USER-CASES.md` + `docs/qa/`.

## ШАГ 4 — ПОТОК СБОРКИ (детерминированный, см. промпт в NEW-SESSION-START)
ПОНИМАНИЕ → ВОПРОСЫ → ПЛАН → ДОК(задача 1) → СБОРКА(pipeline фаз) → ФИКС-ПЕТЛЯ(loop-until-perfect) → ТЕСТ.
Каждая фаза: tsc=0, /app=200, смоук, скрин, сверка с v3+screenshots. Дальше ТОЛЬКО на зелёном.
Масштаб: ultracode, dynamic workflows, до 20 параллельных агентов, бесконечная петля до идеала.

---
**Если сессия в чём-то не уверена — НЕ гадать: спросить граф (`/graphify query`) или спросить Damir.**
