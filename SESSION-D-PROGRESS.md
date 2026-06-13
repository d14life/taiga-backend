# Session D — Тайга cobrowse browser-agent (Chrome MV3 extension)

Branch: `session-d`. New isolated folder: `taiga-extension/`. One thin backend endpoint added to `server.py`.

## Status (binary)
- manifest + load: DONE — valid MV3 manifest, loads as unpacked extension.
- content-script read+act: DONE — `content.js` snapshots page (text + interactable elements with stable selectors) and performs click/type/scroll/read.
- side-panel chat: DONE — `sidepanel.html/css/js`, dark/violet Тайга style, goal input + live step log + Stop + settings.
- act-loop: DONE — `background.js` runs bounded (max 15) think→act→verify loop.
- backend `/api/browser_act`: DONE — one handler `api_browser_act()` + one route line; reuses `best_for_task` + `resolve_key` + `venice_complete`. Also added CORS (`_cors_headers`) + `do_OPTIONS` so the extension can call cross-origin.
- safety-confirm: DONE — destructive/submitting/payment/type actions pause for user confirm in the panel; CAPTCHA/antibot detection stops the run; never auto-fills passwords/cards (model + UI both instructed); server forces confirm on `type`.

## Architecture
1. User types a goal in the side panel → `background.js` `runLoop`.
2. `background.js` asks `content.js` for a page snapshot (url + title + text + up to 80 interactable elements, each with a stable CSS selector, role, text, center x/y).
3. `background.js` POSTs `{user, goal, page, history}` to `POST /api/browser_act`.
4. Backend builds a tight RU system prompt, calls the best model via `venice_complete` (temperature 0), parses ONE next-action JSON `{action, selector?, text?, url?, reason, confirm}` with `_extract_json_object`.
5. `background.js` executes the action via `content.js` (or `chrome.tabs.update` for navigate), records the result in history, loops until `action=done`, Stop, or step limit.

## Safety layers (defense in depth)
- System prompt: never solve CAPTCHA; set `confirm=true` for irreversible/submitting actions; never enter passwords/cards/credentials.
- Server: forces `confirm=true` on any `type` action (data entry into forms).
- Background: `needsConfirm()` also catches destructive keywords in click targets, and forces confirm on `type`. CAPTCHA/antibot text on the page halts the loop with a message.
- Panel: explicit "Тайга хочет нажать «…» — подтвердить?" with Подтвердить / Отклонить before the action runs.
- Refuses to run on chrome:// / extension pages.

## Files
- `taiga-extension/manifest.json` — MV3, permissions activeTab/scripting/tabs/storage/sidePanel, host `<all_urls>`.
- `taiga-extension/background.js` — service worker, connection + act-loop + safety gating.
- `taiga-extension/content.js` — page snapshot + action executor.
- `taiga-extension/sidepanel.html` / `.css` / `.js` — chat panel (dark/violet).
- `taiga-extension/icons/icon{16,48,128}.png` — brand-violet placeholder icons.
- `server.py` — added `api_browser_act()`, route `/api/browser_act`, `_cors_headers()`, `do_OPTIONS()`.

## LOAD-INSTRUCTIONS (load unpacked in Chrome)
1. Make sure the Тайга backend is running on `http://127.0.0.1:8777` (it already runs).
2. Open `chrome://extensions` in Chrome.
3. Toggle **Developer mode** (top-right) ON.
4. Click **Load unpacked**.
5. Select the folder: `/Users/damir12/Downloads/claude-sessions/2026-06-10/mostik-ai-D/taiga-extension/`.
6. Pin "Тайга — браузер-агент" and click its icon → the side panel opens.
   (If the panel doesn't open on click, right-click the icon → "Open side panel".)

## What to test live
1. Open a normal site (e.g. a Wikipedia article or a shop page).
2. In the panel, set Settings → backend `http://127.0.0.1:8777`, user `default` (or owner uid) → Save.
3. Goal: "прокрути вниз и найди раздел X" → watch: Думаю → Действие · прокрутка → Результат ✓ → Готово.
4. Goal that needs a destructive click (e.g. "нажми кнопку Отправить") → confirm bar must appear before the click runs; Отклонить skips it.
5. Open a page with a captcha → run any goal → it should stop with the CAPTCHA message.
6. Verify the backend: `curl -s -XPOST http://127.0.0.1:8777/api/browser_act -H 'Content-Type: application/json' -d '{"user":"default","goal":"кликни ссылку Войти","page":{"url":"https://x.test","title":"T","text":"hello","elements":[{"selector":"a#login","tag":"a","role":"link","text":"Войти"}]},"history":[]}'` → returns a JSON action.

## Notes / limits
- The model picks selectors from the provided element list; very dynamic SPAs may need a re-snapshot (the loop already re-snapshots every step).
- Icons are flat violet placeholders — swap with real Тайга art later.
- Backend endpoint respects existing key resolution (BYOK / pool) via `resolve_key`; non-owner users without a usable key get a clear error.
