# MEMORY-PLAYBOOK — самый дешёвый способ знать код (ponytail)

Цель: знать систему, НЕ читая server.py (900 KB) и chat.tsx (8157 строк) целиком. Правило: **сначала индекс (graphify, бесплатно) → точечный Read; доки — один запрос gbrain с цитатами.**

## Разделение труда (главное)
| Вопрос | Инструмент | Цена |
|--------|-----------|------|
| «Где/как X в КОДЕ?» | **graphify** (offline AST) | 0 токенов |
| «Что эта функция делает?» | **Read** диапазона, что дал graphify (≤250 строк) | дёшево |
| «Почему/что РЕШИЛИ про X?» (замысел/спека/решение) | **gbrain** (1 запрос) | сеть+NVIDIA, раз |
| «Какие скиллы под задачу?» | **pick-skills** → process→impl→verify | дёшево |

Никогда: слепой grep по большому файлу, чтение целого server.py/chat.tsx, цикл из gbrain-запросов, чтение всех доков после gbrain (его вывод уже сжат: счёт+чанк+цитата).

## graphify (бесплатно, 0 токенов, offline) — ИНДЕКС, всегда первым
- `graphify query "X"` → список узлов file:line+community → Read только этот узкий диапазон.
- `graphify path "A" "B"` → как два символа связаны.
- `graphify explain "X"` → окрестность символа.
- `graphify update .` после правок кода (бесплатно, AST, без LLM) — держать свежим (граф был на коммите a294f97; обновлять при изменении кода).
- Готовые артефакты вместо повторных запросов: `graphify-out/GRAPH_REPORT.md` (God Nodes + Community Hubs + Surprising Connections), `manifest.json` (символ→локация).

### God Nodes = ядро системы (знать наизусть, чтобы не искать заново)
Бэк: `Handler` (HTTP-класс server.py, через него ВСЁ) · `is_owner()` (гейт безопасности) · `venice_complete()` (вызов LLM) · `user_balance()` (кошелёк) · `strip_model_prefix()` (роутинг моделей).
Фронт (всё про macOS-окна): `cn()` (classname-утиль, 315 рёбер) · `useRestoreWinSize()` · `useEscClose()` · `ResizeHandle()` · `fetchT()` (fetch+timeout).

## gbrain (сеть, дорого по латентности — экономно) — ДОК-ОРАКУЛ
- Запуск: `export OPENAI_BASE_URL=https://integrate.api.nvidia.com/v1; export OPENAI_API_KEY=$(grep ^NVIDIA_API_KEY= ~/.reel-intelligence.env|cut -d= -f2-); ~/.bun/bin/gbrain search "<вопрос>"`.
- ОДИН богатый запрос → топ-K чанков с цитатами → ответ или Read одного среза. Не зацикливать.
- Для «почему/замысел/решение/спека», НЕ для «где код» (это graphify).

## Прочие скиллы (ponytail-роутинг)
- `pick-skills` в начале задачи → process (`brainstorming` новое / `systematic-debugging` баг) → impl (UI: `refero-design`/`impeccable`/`high-end-visual-design`; `superpowers:*`) → `verification-before-completion`.
- Стандинг-критик на фичу = отдельный адверсариальный агент (code-review/критик-роль).
- ponytail на КАЖДЫЙ вывод: 6-ступеней (YAGNI→stdlib→native→dep→1строка→минимум), минимум кода/токенов, НЕ резать валидацию/безопасность.

## В агентах-воркерах (вшито в RECIPE)
≤2 вызова памяти на агента: 1× graphify (бесплатно) обязательно, gbrain — только если нужен замысел. Read только диапазоны от graphify. Это убирает токен-раздувание и зависания (большие чтения = причина прошлого зависа).
