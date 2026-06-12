# ДОСКА АГЕНТОВ — координация Claude-сессий Тайги (НЕ затирать друг друга)

Несколько Claude Code сессий работают над ОДНИМ репо одновременно. Эта доска + папка
`.agent-locks/` — общий механизм, чтобы две сессии не правили один файл.

## ЛАНЫ (зоны) — каждая сессия берёт ОДНУ свободную
| Лана | Файлы (твои) | НЕ трогать |
|---|---|---|
| **CORE** (фронт/чат/состояние) | src/components/{chat,sidebar,model-picker,settings-panel,master-prompt-panel,canvas-panel}.tsx · src/lib/use-taiga-chat.ts · src/lib/* (кроме gen-image/video-gen/audio-gen) · src/app/api/* прокси · команды | image-studio.tsx, *-gen.ts, server.py, orchestrator.py, browser_hub.py, guard.py |
| **STUDIO** (генерация) | image-studio.tsx · video-gen.ts · audio-gen.ts · gen-image.ts · src/app/api/{video,audio,image,video-models} · ТОЛЬКО ген-функции server.py (api_video/api_audio/api_image/charge_media/nano_image) | chat.tsx, use-taiga-chat.ts, orchestrator.py, остальной server.py |
| **BACKEND** (server.py ядро + модули) | server.py (каталог/биллинг/поиск/браузер/rag/агент) · orchestrator.py · browser_hub.py · guard.py | любые src/components/*.tsx, студийные либы |

**Общие файлы** (`server.py`, `src/lib/models/select.ts`): только через ПОФАЙЛОВЫЙ замок ниже.

## ПРОТОКОЛ ЗАМКА (атомарный, переживает падение сессии)
Перед правкой любого файла ВНЕ своей ланы ИЛИ общего файла — запусти:
```bash
claim() {  # $1 = путь к файлу, $2 = твой session_id
  cd <repo>; L=".agent-locks/$(echo "$1" | tr '/.' '__').lock"
  if mkdir "$L" 2>/dev/null; then echo "$2 $(date +%s)" > "$L/owner"; echo "CLAIMED"; return 0; fi
  read o t < "$L/owner" 2>/dev/null
  if [ $(( $(date +%s) - ${t:-0} )) -gt 900 ]; then rm -rf "$L"; mkdir "$L"; echo "$2 $(date +%s)" > "$L/owner"; echo "CLAIMED(stale)"; return 0; fi
  echo "BUSY:$o"; return 1   # занято другой сессией → возьми другую задачу
}
release() { rm -rf ".agent-locks/$(echo "$1" | tr '/.' '__').lock"; }
```
- `mkdir` атомарен → гонок нет. `CLAIMED` = можно править. `BUSY:<id>` = пропусти, делай другое.
- Замок старше 15 мин = сессия умерла → можно перехватить (stale).
- После правки файла — `release`. Свою лану клеймить пофайлово НЕ нужно (она только твоя).

## HEARTBEAT + СТАТУС
Раз в ~10 мин обновляй свою строку в таблице ниже (id, лана, что делаешь, время).
Чтобы не драться за саму доску — каждая сессия пишет в СВОЙ файл `STATUS-<id>.md`, а сюда
вписывает строку ОДИН раз при старте.

## КТО НА ЧЁМ (заполняют сессии при старте)
| session_id | лана | старт | статус-файл |
|---|---|---|---|
| atlas | COORDINATOR (доки/анализ/мониторинг — НЕ правит код) | ночь | STATUS-atlas.md |
| kedr | CORE | 06:30 | STATUS-kedr.md |
| ural | BACKEND | 06:35 | STATUS-ural.md |
| amur | STUDIO | 06:33 | STATUS-amur.md |
| sosna | CORE-B (libraries: skills-реестр/темы/Voice/Prompts/Bookmarks/Memories) | 18:20 | STATUS-sosna.md |
