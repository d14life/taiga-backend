# AGENTIC-OS HARNESS — UNBLOCKED (correction). 2026-06-13.

## The miss
LANES.md L13 was tagged "BLOCKED — needs Damir's agentic-harness repo link." That was WRONG —
Damir already provided the links. L15 + L13 = the agentic-OS harness = "the main agentic feature."
Do NOT skip it. It is now being BUILT.

## The repos Damir sent (the design source — these unblock L15/L13)
- walkinglabs/learn-harness-engineering — "model smart, harness reliable." 5 subsystems:
  Instructions · State · Verification · Scope · Session-lifecycle.
- YennNing/Awesome-Code-as-Agent-Harness — code = executable stateful substrate;
  multi-agent = collaborative-synthesis / critique-repair / adversarial / debate.
- ECC `agentic-os` SKILL.md — router → specialists → file-state core loop (the blueprint).
- claw-code `TaskPacket` — per-sub-task {model/provider + acceptance/verification} delegation envelope.

## Where it's being built
Isolated worktree `mostik-ai-C` (branches session-c / session-c-fe). NEW-MODULE-FIRST: core in a new
`agent_os.py`, minimal server.py edits, so it merges cleanly alongside session-b (product lanes) + main.

## What it delivers
- L15 Тайга Agent: SCOPE (one sub-goal) · THINK (multi-model deliberation, reuse council/Brain) ·
  ACT (existing typed tools as code-as-action) · VERIFY (run→only-passing=done) · STATE (memory layering + resumable).
  New endpoint POST /api/agent_os.
- Session-level agent mode: setting "new chats start as agent" → whole session orchestrates from msg 1.
- L13 Parallel agents in the product (Chad-style): fan out N sub-agents on disjoint sub-tasks → merge.

## Merge order note (for whoever merges)
main ← session-c (agent_os.py is new, conflicts minimal) ← session-b (product lanes).
Bring agent_os.py in first; resolve the few server.py route-registration lines by hand.
