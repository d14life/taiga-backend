# Taiga Agent-OS roadmap (research 2026-06-14: awesome-agent-harness + repos + frontier)

## Verdict
Taiga's Agent tab is ALREADY top-tier. Already shipped: orchestrator (live step trace + sub-agents, SSE), team-panel (plan→roles→budget→approve→go→monitor), loop-studio (drag-drop builder, fanout/debate, verify+retry Ralph, save/share/gallery), automations (REAL server scheduler), tasks (P0-P3), runs-panel (unified journal + real cost meter + pause/cancel), ralph-monitor, **chat branching (forkFrom/MsgTree/BranchSwitcher) ALREADY EXISTS**, **human-in-the-loop tool approval (pendingPermission/sendPermit/api/agent_permit) ALREADY EXISTS**, MCP/sandbox/browser/skills routes, memory/RAG.

Storage: chats in localStorage (taiga.chats, taiga.chat.<id>, taiga.tree.<id>). A chat and an agent run are BOTH "sessions" = messages[] + metadata. Run step-traces are NOT persisted (vanish on panel close) — THE key gap. RalphMonitor is fed no live data.

## Gap to world-class = the chat↔agent bridge + run traces (founder's exact ask)

## WAVE 1 (building now — highest ROI, ~80% reuses load()/forkFrom/TeamPanel(initialGoal)/agentEvents/api compact+orchestrate)
1. **Chat → Agent «Сделать агентом»** ⭐ — derive goal from convo + seed history → open TeamPanel/LoopStudio prefilled → run. (chat.tsx + team/loop seedContext + orchestrator seed + new derive-goal.ts; backend: /api/orchestrate accepts `seed`)
2. **Persist run traces + Agent → Chat «Открыть как чат»** ⭐ + feed Ralph monitor REAL data. (lib/agent-runs.ts trace, run-to-chat.ts, team/loop record steps, panels pass real runs, chat.tsx run→messages via load())
3. **Merge chats «Объединить»** — multi-select → concat + summarize (sidebar + chat.tsx + /api/compact).
4. **Unified Session model** (lib/session.ts) — keystone, makes 1-3 one-liners.
5. **Run replay / trace stepper** (depends on 2).
6. **Live agent dock** — global in-flight runs status (new agent-dock.tsx).

## WAVE 2 (depth, some backend)
7. Auto-approve classifier («auto mode» — safe tool calls auto, risky gated; we have the permit gate).
8. Event/trigger automations (heartbeats — «when run finishes / chat matches → spawn»; reuse chat-hooks.ts).
9. Task dependency graph (Beads — dependsOn[], next-unblocked).
10. Checkpoints/resume inside a run (extend branching to runs).
11. Goal-aligned audit «why» trace.

## WAVE 3 (frontier polish)
12. Sandbox/computer-use run surface (env panel; routes exist).
13. MCP/tool+skill marketplace picker in Agent tab.
14. Eval/regression harness for loops (Promptfoo-style).

## Licenses: awesome-agent-harness = NO LICENSE → ideas only. agentic-os = CC-BY-NC → ideas only. paperclip/ralph MIT, open-design/openskills Apache → reimplement concepts, our code. Never copy files.

## Shared run-trace shape (Wave-1 contract)
RunStep = { kind:"plan"|"worker"|"stage"|"tool"|"verify"|"synth"|"note"; label; content; model?; ok?; ts }
Run record extended with: trace?: RunStep[]; goal?: string.
