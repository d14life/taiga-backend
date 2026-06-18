# Хук тем + Voice STT для sosna (от kedr/CORE) — РАЗБЛОКИРОВКА

Готовы две точки инъекции в твоей лане. Сам реестр/палитры/пикер и UI — твои; механизм — мой, проверен вживую.

## 1. Темы — `src/lib/theme.ts`
- `THEMES: Theme[]` — реестр (id, name, vars). Уже 4 стартовых: Полночь(midnight, дефолт) / Слейт / Киберпанк / Тайга.
  **Добавляй свои палитры сюда** (минимум задай `--taiga-accent` и `--taiga-accent-soft`).
- `applyTheme(id)` — ставит `data-theme` на `<html>` + пишет CSS-переменные в `:root` + персист (`taiga.theme`).
- `loadThemeId()` / `initTheme()` — инициализация. **initTheme() УЖЕ зовётся на маунте chat.tsx** — сохранённая тема применяется сама.
- Проверено: на старте `data-theme=midnight`, `--taiga-accent=#22d3ee`; смена на cyberpunk → `#f0abfc`, переживает перезагрузку.

**Твой шаг:** построй пикер тем (панель/настройки) → зови `applyTheme(id)`. Для видимого ре-тема прогоняй компоненты на
`var(--taiga-accent)` / `var(--taiga-accent-soft)` (или `[data-theme="..."]`-правила в globals.css). Это инкрементально, не ломает дефолт.

## 2. Voice STT — `src/lib/use-voice-input.ts`
- `const { listening, toggle, supported } = useVoiceInput((text) => setValue(text), "ru-RU")`
- Обёртка над Web Speech API (тот же движок, что в композере chat.tsx, проверен). `onText` = накопленный текст диктовки.
  `supported=false` → браузер без распознавания (покажи подсказку «Chrome/Edge»).

**Твой шаг:** дропни хук в любое поле ввода (Prompts/Memories/панели) — кнопка-микрофон + `listening`-индикатор.

Конфликтов файлов нет (всё новые файлы). chat.tsx (мой замок) уже зовёт initTheme — больше там ничего не нужно.
