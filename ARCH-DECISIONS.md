# Тайга — architecture decisions (Damir-approved). Feeds L12 (full skills) + L15 (agent envs).

## EXEC HOSTING — where user code/skill-scripts/agent run (Damir: HYBRID, 2026-06-13)
TODAY: tool_run_code = subprocess on OUR server, OWNER-ONLY, tempdir+timeout (NOT real isolation).
  → Must NEVER expose to users as-is = RCE. Keep owner-only until the sandbox below exists.

DECIDED — HYBRID:
  • BROWSER-WASM (Pyodide for Python, WebContainers for Node) = FREE DEFAULT. Runs on the USER's
    device in the browser sandbox. Zero server cost, safe, instant. Covers light skills + data/code.
  • CLOUD SANDBOX-PER-USER (E2B / Daytona / Modal / Firecracker microVM) = HEAVY/FULL path. Disposable
    isolated container per session: real terminal, binaries, full Claude-Code-style agent env. Cost ~$/run
    → PASSED to the user's credits (not us). Gated behind credits.
  • BROWSER-AGENT env = server-side headless browser (Playwright in a sandbox) OR user's real browser via
    extension. (Тайга already has /api/browser server-side.)
  • RULE: never run user code on the bare backend. Route: light→WASM (free), heavy→cloud sandbox (paid).

## FULL SKILLS (L12 expanded) — "paste a GitHub Claude-Code skill, ANY model uses it"
  HAVE: install_skill_from_url imports SKILL.md across a repo (GitHub trees API, Claude format);
        search_skills/load_skill (progressive disclosure, 358+); never executes downloaded code.
  BUILD:
   1. Import the WHOLE skill folder (SKILL.md + scripts/ + resources/), not just the .md.
   2. RUN bundled scripts in the sandbox above (WASM light / cloud heavy), owner/credit-gated.
   3. AUTO-TRIGGER the right skill in normal chat (not only agent mode).
   4. MODEL-AGNOSTIC: harness injects SKILL.md instructions + runs scripts via tools → GPT/Gemini/DeepSeek
      use Claude-format skills just like Claude Code. ← the differentiator.

## AGENT ENVIRONMENTS (L15) — high-level, across real working envs (Damir)
  BROWSER (research/act) · TERMINAL/CODING (sandbox above) · STUDIO (image/video/music/3D).
  Foundations exist (/api/browser · run_code/shell/DEV_TOOLS · studio APIs); L15 = orchestrate them with
  multi-model deliberation → tool action → verify loops → memory layering → session-level agent mode.

## MCP CONNECTORS = ✅ ALREADY BUILT (full client + catalog + mcp-panel UI + agent integration). Not a gap.
