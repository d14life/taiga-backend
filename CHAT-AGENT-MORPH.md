# CHAT ↔ AGENT MORPH — core product principle (Damir, 2026-06-13)

THE differentiator. Others split "Chat" and "Agent" into separate products/modes/wizards.
Тайга = ONE thread that fluidly morphs both ways, seam invisible, always conversational.

## The principle
- OPEN CHAT → CLOSED AGENT: when a message is a task/goal, the SAME thread silently enters the
  agent-loop (agent_os: scope→think→act→verify), shows steps inline, and returns the result IN
  the same thread. User never switched a "mode" or left the conversation.
- CLOSED AGENT → OPEN CHAT: when the agent finishes (or the user interjects mid-task), the thread
  relaxes back to normal conversation. No rigid wizard that traps the user.
- Both directions are AUTOMATIC (Auto/power-slider routes simple→chat, complex→agent) with an
  optional manual nudge. The morph is the default behavior, not a setting buried in a menu.

## Output style (critical)
- Agent mode still TALKS LIKE CHAT. Paste a prompt → it does the work → replies conversationally,
  with the step-trace available but collapsible. NOT a dry step-log dump. (Like Claude-in-Chrome.)

## Where this lives
1. Web app (taiga-web chat): the thread morphs. Foundation exists — agent_os harness + Auto routing.
   Needs the seamless wrapper: one stream that shows "думаю → действия → ответ" but reads as one
   continuous conversational reply, and lets the user keep typing to drop back to chat.
2. Browser extension (taiga-extension, session-d): side panel is CHAT-FIRST. Paste prompt → acts in
   the tab → answers conversationally. Keep chatting = morph back. Same brain (/api/browser_act).

## Unify: two "hands", one brain
- Server-side browser (/api/browser) and the extension (user's real Chrome) are two executors of the
  SAME agent decision loop. Chat input → server browser; extension → user's browser. One toggle picks
  the hand. A task can start in chat and hand off browser steps to the extension via the relay queue
  (/api/ext_pull + /api/ext_result).

## Build order
- D finishes the extension MVP first → then step 2: (a) chat↔extension relay queue, (b) conversational
  morph output in the panel. Web-app morph wrapper = a follow-up lane after.
