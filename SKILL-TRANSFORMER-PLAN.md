# Skill Transformer / Compatibility Layer — план (аудит достоверности 2026-06-14)

## Честный вердикт
Скиллы Тайги — РЕАЛЬНО исполняемые (не промпт), но нативно-эквивалентны ТОЛЬКО для: чистых stdlib-Python-скриптов + 4 медиа-глаголов (image/audio/video/music). Прозу-скиллы — близко, но зависят от модели. СЛОМАНЫ для скиллов, которым нужны: pip-пакеты, argv/CLI, соседние resource-файлы, Node, или (без E2B-ключа) shell/сеть.

Два структурных блокера:
1. Браузерный Pyodide НЕ грузит пакеты → `import numpy/requests/...` падает у юзеров.
2. Запуск у owner = `python -I -c <code>` в пустой временной папке → нет argv, нет cwd, нет соседних resources, нет stdin (`server.py:run_code_lang:4684`, `skills_run.py:run_skill_script:355`).

## Лейны сборки (владение файлами; Lane C ждёт, пока волна Мозг/фичи освободит общие файлы)
- **Lane A (бэкенд, НОВЫЕ файлы — в любой момент):** `skill_caps.py` (анализатор возможностей) + `skill_pyodide_packages.json` (список Pyodide-колёс). Схема ниже.
- **Lane B (фронт, НОВЫЕ файлы — после волны, чтобы не пачкать tsc/git):** `taiga-web/src/lib/skills/skill-caps.ts` (типы + `runInBrowserWithDeps`: `loadPackagesFromImports`+`micropip` + монтаж bundle-файлов в Pyodide FS) + `taiga-web/src/components/skill-badge.tsx` (чип-бейдж) + врезка бейджа в `full-skills-panel.tsx`.
- **Lane C (правит ОБЩИЕ файлы — после волны):** `skills_run.py` (анализатор в импорт + выбор рантайма по caps + argv/cwd/stdin/resource-шимы), `server.py` (`run_code_lang` argv/cwd/stdin; модель-пин в инъекции скилла), `skill-run.ts` (model override для claude-authored), `full-skills.ts` (Pyodide-пакеты+FS), `studio-skills.tsx` + `chat.tsx` (показ бейджа).

## Общая схема (бэкенд skill_caps.py и фронт skill-caps.ts ОБЯЗАНЫ совпадать)
caps = { language, imports[], third_party_packages[], pyodide_ok[], pyodide_no[], needs_argv, needs_resources, needs_shell, needs_network, needs_node, media_verbs[], claude_authored, recommended_model|null }
badge ∈ { full, partial, instruction-only, needs-server, unsupported }
Правило бейджа (первое совпадение): проза-или-все-тулзы-маппятся ИЛИ чистый stdlib/только-pyodide_ok + без argv/resources → **full**; argv/resources (восстановимо у owner) или pyodide_ok-пакеты или claude-проза-без-пина → **partial**; скрипты-не-запускаются-но-SKILL.md-самодостаточен → **instruction-only**; needs_shell/network/node/pyodide_no → **needs-server** (ready если есть ~/.e2b_key, иначе config); иначе → **unsupported**.

## 3 быстрых победы (максимум достоверности на усилие)
1. Pyodide `loadPackagesFromImports` + `micropip(pyodide_ok)` + монтаж bundle-файлов в Pyodide FS → сломано→full для большинства юзер-Python-скиллов (0 стоимости сервера).
2. Запуск у owner из папки скилла: `python <skilldir>/<script> <argv>`, cwd=skilldir, input=stdin → нативные CLI-скиллы (argparse + references/) реально работают.
3. Модель-пин claude-authored скиллов на `ng:claude-opus-4-8`, когда юзер не выбрал модель → дизайн/бренд/письмо-скиллы Anthropic выходят на нативное качество.
Бонус: показать E2B «needs-server» путь (`run_in_cloud_sandbox` уже готов) с понятным CTA, когда задан ~/.e2b_key.

## Порядок исполнения
Lane A — сейчас (безопасно). Lane B + Lane C — следующая волна сразу после завершения текущего workflow (фикс Мозг/Совет + фичи), чтобы не повредить его проверку и коммит.
