# BACKEND-API — контракты для CORE (kedr) · от ural (BACKEND)

Все эндпоинты ниже **готовы и протестированы** на backend (`server.py` @ 127.0.0.1:8777).
CORE: создай прокси-роут `src/app/api/<name>/route.ts` (форвард на BACKEND, как chat/catalog)
и подключи UI. Нет глобального прокси — каждый эндпоинт нужен пофайлово.

## RAG (документы → семантический поиск; уже инжектится в чат авто)
- `POST /api/rag_ingest` `{user, name, text}` (или `{raw_b64}` для файла) → `{ok, chunks, docs}`
- `POST /api/rag_query`  `{user, query, k}` → `{hits:[{doc,text,score}], docs}`
- `POST /api/rag_delete` `{user, name}` → `{ok, docs}` (удалить документ)
- **Уже работает в чате**: если у юзера есть доки, `chat()` сам подмешивает релевантное (rag_context). UI: загрузка дока → rag_ingest; показать список docs.

## Супер-поиск (ультра)
- `POST /api/supersearch` `{user, query, depth?:"normal"|"deep", engines?}` →
  `{answers:[{engine,answer}], sources:[{title,url,snippet,content?}], engines:[...]}`
- deep = 8 движков + Jina-чтение топ-3. Не-владелец платит ~$0.02, owner free.

## Медиа-поиск (для in-chat браузера/плееров)
- `POST /api/websearch` `{query, kinds?:["web","videos","images"]}` →
  `{web:[{title,url,snippet}], videos:[{videoId,title,thumb,embed}], images:[{image,thumb,title,source}]}`
- UI: YouTube-плеер (videos[].embed), сетка картинок (images[].thumb), карточки web.

## Агентный браузер (ИИ+юзер один экран)
- `POST /api/browser` `{user, action:"open"|"act"|"close", ...}`:
  - open: `{url, cookies?|saved?}` → `{screenshot(dataURL), title, url, text, links:[{t,href}]}`
  - act: `{act:"click"|"type"|"scroll"|"back"|"enter", x?,y?,text?,selector?}` → снимок
  - close: `{}` → `{ok}`
  - `saved` = имя сохранённого набора cookies (грузится расшифрованным).
  - Гейт: non-owner нужен баланс>0 + rate-limit. Секреты в text/links редактируются.
- UI: панель-браузер (рендер screenshot + клики юзера шлёт act + поле URL).

## Cookies (браузить под логином; шифр на диске)
- `POST /api/cookies` `{user, action:"save"|"list"|"delete", name?, cookies?}` → `{cookies:[...]}`
  - cookies = вставка из «Get cookies.txt LOCALLY» (Netscape txt ИЛИ JSON) — парсится сам.
  - Fernet-шифр, 0600, в контекст модели НЕ попадает.
- UI: поле «вставь cookies» + список сохранённых + переключатель «браузить под логином».

## Оркестратор агентов (LangGraph: мозг→воркеры→синтез) — «crazy agent thing»
- `POST /api/orchestrate` `{user, task, workers:[{skill, model?, key?, base?}], mode?:"parallel"|"sequential", stream?:bool}`
  - stream:true → **SSE live-таймлайн**: события `{kind:"step"|"agent", node|worker, status, ...}` + финальный `{kind:"done", final, plan, results}`
  - non-stream → `{plan, results:[{worker,skill,model,task,result}], final, steps}`
  - skills (17): general/researcher/coder/critic/writer/planner/architect/security/reviewer/debugger/optimizer/analyst/marketer/summarizer/translator/devops/qa
  - **BYOK**: worker.key/base = свой ключ юзера на воркера. researcher реально ищет (super_search).
- UI: панель как Copilot Agents — рендер `steps` живьём (plan→агенты running/done→synth), выбор skill+model на воркера, поле «свой ключ».

## Auth (мультиюзер — аддитивно, uid-режим всё ещё работает)
- `POST /api/auth` `{action:"signup"|"login"|"me", username, password, token}` →
  signup/login: `{ok, uid, token, username}` · me: `{uid}` (по токену). PBKDF2 + HMAC-токены.
- UI: экран логина/регистрации; храни token, шли в `me` для проверки сессии.

## Эпизодическая память / RAG-delete / cookies / websearch / supersearch (новые — нужны прокси-роуты!)
- `POST /api/recall` `{user, query, k}` → `{hits:[{chat_id,title,ts,role,snippet}]}` (поиск по прошлым чатам)
- `POST /api/rag_delete`, `/api/cookies`, `/api/websearch`, `/api/supersearch` — см. выше.
- **CORE TODO:** прокси-роуты для recall/rag_delete/cookies/websearch/catalog_refresh/auth (сейчас half-wire).

## Permission-ladder + Hooks (агент)
- В `/api/chat` поддержано поле `perm`: `"full"` (дефолт, всё) · `"auto"` (правки ок, shell/run_code блок) · `"plan"` (мутирующие только превью).
- Coding-агент дев-тулзы (owner): edit_file/write_file/revert_file (Aider-style).

## Каталог
- `POST /api/catalog_refresh` `{user}` (owner) → `{ok, models}`. Авто раз в 6ч (фон).

## ₽ (форматтер готов в CORE-лане)
- `src/lib/money.ts`: `setRate(billing.rub_per_usd)` на старте; `fmtRub`/`approxRub`/`fmtRubWhole`.
- `/api/init` → `balances[provider].low` (bool, <$2) — красное в UI.

— ural (BACKEND). Вопросы по контрактам — пиши в QUESTIONS, я отвечу в STATUS-ural.md.
