# Session C — ТАЙГА Agent-OS harness (L15 / session-agent / L13)

Branches: `session-c` (backend) · `session-c-fe` (frontend). All milestones GREEN (proven).

## L15 core — DONE
- NEW module `agent_os.py` (no import of server.py → merge-safe; deps via `HarnessDeps` DI).
  - SCOPE → THINK (propose→critique-repair→adversarial→fuse) → ACT (existing tools as
    code-as-action) → VERIFY (accept criteria, bounded repair retries) → STATE
    (working/semantic/experiential/long-term, resumable JSON in user_dir/agent_os/).
  - `TaskPacket` delegation envelope (claw-code). Reuses council/best_n_for_task/tools/aux_model.
  - Public: `run()`, `resume()`, `fan_out()`.
- server.py: thin only — `_agent_os_deps()` DI builder + 2 SSE routes.
- Endpoint: `POST /api/agent_os` (SSE timeline: start/phase/scope/subgoal/think_step/act/verify_done/repair/final/done).
- FE: `lib/agent-os.ts` (runAgentOs) + `components/agent-os-panel.tsx` (live timeline) + chat.tsx plus-menu item "Тайга Агент-ОС".
- Verified: ast.parse OK, import OK, end-to-end fake-deps smoke (all phases fire), tsc 0.
- Commits: BE 41876f5 · FE d9c376d

## Session-level agent mode (Damir) — DONE
- BE: `chat()` checkpoint → if `settings.agent_mode_default` OR `req.agent_os` (and no other special
  mode) → `chat_agent_os()` runs the harness, bridges timeline into chat-SSE (agent_phase/tool/delta/done).
- FE: `🤖 Агент` toggle pill (persists localStorage + pushes settings.agent_mode_default), sends
  `agentOs:true`; new `agent_phase` SSE handler renders harness phases as message steps.
- Verified: ast.parse OK, import OK, tsc 0.
- Commits: BE 11495b3 · FE 7e4a606

## L13 parallel agents (Chad-style) — DONE
- BE: `agent_os.fan_out()` — N logically-isolated sub-agents (in-process async ThreadPool) →
  disjoint-subtask split → each runs the harness → clean merge. Endpoint `POST /api/agent_fanout`.
- FE: "Команда агентов" mode in agent-os-panel (per-agent live status → merged result).
- Verified: fake-deps smoke (2 agents → merge), tsc 0.
- Commits: BE 41876f5 · FE d9c376d

## Merge surface (server.py additions, all localized)
- `import agent_os` is LAZY (inside handlers) — top of server.py untouched.
- Added: `_agent_os_deps`, `api_agent_os`, `api_agent_fanout`, `chat_agent_os` methods;
  2 route lines in `_do_POST_inner`; 1 checkpoint block in `chat()`. No existing logic changed.

## L12 — FULL SKILLS — DONE (import / run / auto-trigger / model-agnostic)
- NEW module `skills_run.py` (deps via params from server.py → merge-safe):
  - WHOLE-FOLDER import (SKILL.md + scripts/ + resources/) server-side per account,
    2MB cap, anti-traversal, idempotent reinstall; registers in personal index.
  - on/off toggle + list; run_skill_script GATED — owner→server subprocess,
    user→browser-wasm marker (code returned), bash/heavy→cloud-sandbox TODO stub.
  - AUTO-TRIGGER: keyword/overlap match of user msg vs enabled skills →
    inject SKILL.md into system prompt (model-agnostic) + run_skill_script tool factory.
- server.py thin: `/api/skill_folder` route (import/list/toggle/run), `_parse_skill_text`
  dep wrapper, chat-path auto-trigger hook (inject + tool + fired_skills in SSE meta).
- FE: `lib/skills/full-skills.ts` (API wrapper + Pyodide browser-WASM runner),
  `full-skills-panel.tsx` (folder import + toggles + per-script run), chat.tsx entry
  button/plus-item + "сработал навык: <name>" indicator; use-taiga-chat threads meta.skills.
- Verified: BE match/inject/toggle-off/owner-vs-user-run + anti-traversal (fake-deps), import OK;
  FE tsc 0. Commits: BE 342415e · FE f0db63b.

## L3 — reasoning dial for stubborn models — DONE
- `ignores_effort()`/`depth_preface()` near `_REJECTS_EFFORT`: detect models that accept but
  ignore reasoning_effort (grok-nano/mini, deepseek-chat/v3, gemma/llama/mistral/qwen/gpt-oss);
  real reasoners (deepseek-reasoner/R1, gemini-3-pro, opus) untouched.
- Chat path: on medium/high depth for those, inject "think step-by-step" preface + token-floor
  bump instead of the ignored param. Verified detection table, import OK. Commit: BE 1c03ab8.

## Merge surface (this session, additions only)
- NEW files: `skills_run.py`. server.py: 1 route line + `api_skill_folder` method + `_parse_skill_text`
  helper + `ignores_effort`/`depth_preface`/`_EFFORT_IGNORERS`/`_DEPTH_PREFACE` + 2 small chat-path
  hook blocks (auto-trigger inject, L3 depth) + 1 SSE-meta line. No existing logic changed.
