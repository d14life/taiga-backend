# Тайга ИИ — внешний аудит архитектуры (2 промпта)

**Как пользоваться (2 шага):**
1. **ПРОМПТ 1** (ниже) — отдаёшь внешней ИИ. Она выдаёт «идеальную», полностью исследованную архитектуру нашей агентной ОС. **Сохрани её ответ — это эталон.**
2. Строим дальше по плану.
3. **ПРОМПТ 2** (в конце файла) — отдаёшь ТОЙ ЖЕ ИИ: вставляешь (а) её ответ-эталон из шага 1 и (б) наш свежий `TAIGA-REQUIREMENTS.md` (что реально построено). Она делает **сравнительный анализ**: где совпали с эталоном, где разошлись (и оправдано ли), что пропущено, что сделали лучше/хуже, и приоритетный список «что доделать».

> Тот же приём в одной сессии: дай ПРОМПТ 1 → дождись ответа → дай ПРОМПТ 2 — она сама сверит свой эталон с тем, что у нас построено.

---

# ПРОМПТ 1 — как ПРАВИЛЬНО построить агентную ОС (исследование)

> Скопируй всё, что ниже, и вставь в ChatGPT / Gemini / Claude / Grok. Самодостаточно — файлы не нужны.

You are a **principal AI-product architect and staff engineer** with deep, current expertise in building agentic AI applications (the architecture behind Claude Code, ChatGPT, LibreChat, Hermes/Nous, Cursor, Perplexity). I am a solo founder. I need a **fully-researched, opinionated, detailed architecture and implementation plan** for my product. Do not give generic advice — challenge my assumptions, cite concrete patterns, name specific technologies, and tell me the *right* way to build this so it actually works as an agentic OS, not a chatbot wrapper.

**Respond in Russian** (I'm a Russian speaker), but keep all technical terms/library names in English.

## The product — "Тайга ИИ" (Taiga AI)

A **privacy-first, uncensored, multi-model AI chat that is meant to feel like an agentic OS**, for the Russian/CIS market. The pitch: *"one interface to all the intelligence on the planet"* — 732 models from many providers under one brand, private (no-logs / TEE), uncensored, with agentic capabilities. Business model: aggregator — user pays us, we pay providers, ~50% markup; payment via Russian rails (СБП) / crypto.

**The moat is NOT the models** (we resell others' APIs). The moat is: unified access + privacy (TEE/no-logs) + uncensored + Russian-market UX + payment + an agentic layer that turns chat into a workspace.

## Current tech stack

- **Frontend:** Next.js 16 (App Router, Turbopack), React 19, TypeScript, Tailwind v4, Framer Motion. Heavy custom UI (per-mode animated backgrounds, glass, command palette).
- **Backend:** Python (stdlib `http.server`, ~3000 lines), OpenAI-compatible (`/v1/models`, `/v1/chat/completions`). Streams typed SSE events (meta/delta/tool/research_step/council). Routes to providers: **Venice** (uncensored core, E2EE/no-logs), **NanoGPT, Chutes, Redpill/Phala** (some TEE/confidential-compute). Has a real agent tool-loop (web_search, calc, code-run, shell, file-read, webhook, MCP), per-user balance/metering/markup, abuse filter, API-key issuance.
- **Storage:** flat JSON files per user (no real DB yet). Per-chat memory + global "master prompt" stored client-side in localStorage (privacy-first).
- **Catalog metadata per model:** id, provider, smart-score, ctx, vision, reasoning, code, tools, uncensored%, **privacy (tee/e2ee/no-logs/gateway/varies)**, price.

## The product structure I want (3 tiers)

1. **Обычный (Normal):** chat + code + uncensored merged into one everyday tier, with the FULL agentic toolset — write & run code, run terminal (sandboxed), read/write files, produce diagrams, connect to MCP servers, control a browser, web search — plus a "g-brain" relay (a cheap uncensored model triages/cleans the prompt, a smart model answers) and a security guardrail layer. Uncensored but with hard safety floors (block clearly-illegal only).
2. **Студия (Studio):** image / video / voice generation.
3. **Ультра (Ultra):** premium expensive tier — the best single model + uncensored front + security + inline image/video generation + a "g-brain" *workflow of agents* (orchestrated subagents), the most capable agentic class.

I want **TEE/private model routing** preferred in Normal, Ultra, and Image where possible.

## What's already built (✅) vs missing (🔴)

✅ 5 chat modes with per-mode system prompts/backgrounds; smart auto model-selection per task with brand-diverse fallback; "relay" (cheap→smart) and "brain" (triage→expert) two-model pipelines; council (parallel models→synthesis); deep/research with visible steps; a command palette (~50 slash commands) + user-defined commands & pipelines; skill builder (named instruction toggles) + agent builder; per-chat memory artifact (auto-extract + user-editable, anti-poisoning filter) + a global "master prompt / core memory"; **Canvas/Artifacts** (live-render generated HTML/React/SVG in a sandboxed iframe); file upload (PDF/DOCX/CSV → text into context) + vision; voice input (Web Speech); image studio (top models surfaced); a Settings panel (history-privacy modes local/E2EE/server, editable system prompt & relay instruction, max-tokens, dev-mode, API keys); **privacy: 3-group model categorization (TEE/E2EE · no-logs · gateway) + a TEE-preference router + per-model privacy badges + filter**; message actions (copy/edit/regenerate); budget control (eco/norm/max); ghost (no-store) chat.

🔴 **Messages stored as a flat list, not a tree** (so no real fork/branch); no full-text search across chats; no cross-chat user profile that compounds over time; no context compaction at scale; semantic **RAG** (chunk/embed/retrieve) for large doc corpora; a **visible agent step-timeline + permission ladder** (plan→auto-edit→full, allow-once/always) like Claude Code; **subagents** (isolated context + parallel) / background agents / scheduled (cron) agents; a **skills marketplace** (thousands of SKILL.md with progressive disclosure + search); **MCP client** (streamable-HTTP, per-user creds); **real payment** (СБП/crypto — currently stubbed, a security hole); a real database; video/voice generation; presets.

## What I want from you — the deliverable

A **detailed, fully-researched architecture + build plan**. Be specific and opinionated. Address ALL of the following:

1. **The agent loop done right.** The exact cancellable plan→tool→observe→repeat loop; stop conditions & step limits; the typed event contract (what events the backend should emit so the UI renders visible steps, tool cards, diffs, subagents, permission prompts); how to keep it model-agnostic across many providers.
2. **Tool registry + permissions.** How to declare/discover/execute tools (built-in, OpenAPI-actions, MCP); the permission ladder & modes; sandboxing dangerous tools (shell/write/browser) — what isolation tech (Docker / microVM / E2B / gVisor) fits a multi-user web SaaS.
3. **Data model.** Should I move messages to a tree now? Schema for conversation/message/preset/agent/endpoint. What real database (Postgres + pgvector? SQLite + FTS5? something else) for a privacy-first product, and how to reconcile "local-first / no-logs" with server features (search, cross-device, cross-chat memory). How to do E2EE history honestly.
4. **Memory.** Frozen-snapshot core blocks vs episodic FTS5 recall vs semantic RAG — when to use which; anti-poisoning / threat-scanning; a cross-chat user profile that gets smarter without bloating or poisoning context.
5. **Skills at scale.** SKILL.md + progressive disclosure (metadata→body→scripts); how a marketplace of thousands stays cheap on tokens (search_skills vs preload); security model for user-installed skills.
6. **Subagents / background / scheduled.** Orchestration model; context isolation; when to use a job queue (Celery/Arq/Temporal); how the "Ultra workflow of agents" should actually work.
7. **Multi-provider routing & the 3-tier structure.** Is collapsing 5 modes into my 3 tiers (Normal/Studio/Ultra) the right UX? How should routing, the g-brain relay, and TEE-preference compose per tier? How to expose 732 models without overwhelming users (the casual-vs-pro UX).
8. **Privacy/TEE as a real feature.** How to make "the provider can't see your prompt" true and verifiable (TEE attestation, Venice E2EE), and how to message it honestly without over-claiming on gateway models.
9. **Payments & unit economics** for the RU market (СБП via aggregators, crypto via NOWPayments/CoinGate/OxaPay), per-user metering, prepaid token packets, fraud/abuse, and the legal line on reselling provider APIs (which providers allow it vs BYOK-only).
10. **Build sequence.** Given a solo founder who must ship: the exact order to build the missing 🔴 items, what's foundational (unlocks the most), what to defer, and what to cut (YAGNI). Flag anything in my current plan that's a trap or wasted effort.
11. **Anti-patterns & risks.** Where this kind of product usually goes wrong; the 3 decisions most likely to bite me later; what I'm probably underestimating.

**Format:** structured sections, concrete and prioritized, with short rationale for each recommendation and named technologies/libraries. Where you're uncertain, say so and give the trade-off. Assume MIT-licensed reference code (LibreChat, Hermes/NousResearch hermes-agent, RAG-Anything) is fair to borrow patterns from. End with a one-page **"if you do only 5 things, do these"** summary and a 90-day build roadmap.

---

# ПРОМПТ 2 — сравнительный анализ: эталон vs. что мы построили

> Дай ЭТО той же ИИ ПОСЛЕ того, как получил её ответ на ПРОМПТ 1. В двух блоках ниже вставь:
> **[A]** — её собственный ответ на ПРОМПТ 1 (рекомендованная «идеальная» архитектура).
> **[B]** — наш текущий `TAIGA-REQUIREMENTS.md` (живой статус: что ✅ построено / 🔴 нет).

You previously gave me a recommended "ideal" architecture for my agentic-OS product **Тайга ИИ** (the full product context is in that earlier answer — reuse it). Now I need a **rigorous gap analysis** between that ideal and what I have actually built so far.

**Respond in Russian**, technical terms in English. Be a strict, honest auditor — no flattery. Where I diverged from your recommendation, judge whether the divergence is *justified* (a reasonable trade-off for a solo founder / privacy-first RU product) or a *mistake to fix*.

**[A] YOUR RECOMMENDED ARCHITECTURE (paste your full answer to the previous prompt here):**
<<< вставь сюда ответ ИИ на ПРОМПТ 1 >>>

**[B] WHAT I ACTUALLY BUILT (paste the current TAIGA-REQUIREMENTS.md here — ✅ = done, 🆕 = recent, 🟡 = regression, 🔴 = missing):**
<<< вставь сюда текущий TAIGA-REQUIREMENTS.md >>>

Produce:

1. **Scorecard table.** One row per major architectural area from [A] (agent loop, tool registry & permissions, data model / message tree, memory, skills, subagents/background/scheduled, multi-provider routing & tiers, privacy/TEE, payments, context management, sandboxing, DB). For each: **Ideal (1 line)** · **What we built (1 line, cite [B])** · **Match: 🟢 close / 🟡 partial / 🔴 far / ➖ not started** · **Gap (what's missing or wrong)**.

2. **Justified divergences vs. real mistakes.** Two lists. (a) Places where what we built differs from your ideal but the choice is *defensible* — say why it's fine. (b) Places where it's an actual mistake / tech-debt trap — say the concrete risk and the fix.

3. **What we got RIGHT** that you'd keep (so I don't waste time "fixing" things that are already good).

4. **Critical missing foundations** — the 🔴 items from [B] that BLOCK other work (e.g. message-tree, real DB, payment, agent step-timeline + permission ladder). Rank by "how much else it unlocks."

5. **Re-prioritized build order** — given the *actual* current state in [B] (not a greenfield), the exact next 8–10 things to build, in order, with a one-line reason each. Note anything in [B] marked 🔴/⏳ that's actually a *trap* (low value, skip it).

6. **Honest verdict** — on a 0–100 scale, how close is the current build to a real, sellable agentic OS (not a chatbot)? What are the 3 highest-leverage moves to raise that score fastest?

Be specific, cite line items from [B], and don't hedge — I need the real picture, not encouragement.
