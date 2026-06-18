# ТАЙГА — ФИЧЕ-ПАРИТЕТ vs ЭТАЛОНЫ (из 78 скринов Damir, 2026-06-12)

Эталоны со скринов: ChatGPT gpt-5.5 · Claude Code/Desktop · Grok · LibreChat · Hermes/Nous ·
NanoGPT · Venice · MUAPI · Raycast · 21st.dev Magic · GitHub Copilot Agents · Chutes/RedPill billing.
✅ есть · 🟡 частично/не вынесено · 🔴 нет · ⛔ owner-gated/позже.

## A. КОМПОЗЕР И ИНСТРУМЕНТЫ
| Фича | Эталон | Тайга |
|---|---|---|
| «+» tools-меню: File Search / Web Search(+gear) / Skills / Run Code / Artifacts / Create image / Thinking / Deep research / Projects | ChatGPT | 🟡 куски есть чипами, НЕ в одном «+»-меню |
| Pin-инструмента в тулбар | ChatGPT | 🔴 |
| Бейдж модели в шапке чата + быстрый свитчер | ChatGPT | ✅ пикер |
| Web Search | ChatGPT/Grok | ✅ супер-поиск (8 движков) |
| File Search по докам | ChatGPT | 🟡 RAG есть, не тумблером |
| Run Code | ChatGPT | 🟡 coding-агент (owner) |
| Artifacts/canvas | ChatGPT | ✅ |
| Слайдер «память чата: последние N сообщений» (307) | RedPill/frontier | 🔴 (ты явно просил) |

## B. РЕЖИМЫ / МЫШЛЕНИЕ
| Fast / Auto / Expert / Heavy селектор | Grok | 🟡 есть авто/deep/brain, нет чистого селектора |
| Трейс «Думаю по шагам» сворачиваемый | Grok/Claude | ✅ |
| Research/DeepSearch режим | Perplexity/Grok | ✅ |
| Custom Instructions / Predictive outputs тумблеры | ChatGPT | 🟡 system-prompt есть |

## C. MCP / КОННЕКТОРЫ — 🔴 ГЛАВНАЯ ДЫРА
| MCP-маркетплейс: именованные коннекторы (mysql/Github/PayPal/Stripe/Vercel/HuggingFace/Gmail/DeepWiki/Gitmcp), edit/toggle/delete, фильтр, add | LibreChat | 🔴 только базовый /connect |
| MCP как раздел настроек первого класса | Hermes/Claude | 🟡 |

## D. АГЕНТЫ
| Agent marketplace/галерея (My/Featured/My Chats, автор, стартер-чипы) | ChatGPT/MUAPI/Hermes | 🟡 agent-gallery |
| Agent Builder (пара моделей) | LibreChat | ✅ |
| Оркестратор brain→workers→synthesis | — | ✅ (нет DAG) |
| Background-tasks панель (Running/Finished, токены/время/фазы) | Claude Code | 🔴 |
| Async coding-агент с PR/diff/Open in VS Code | GitHub Copilot | 🔴 |
| Расписание/routines (cron, триггеры «по будням 18:30») | Claude routines | 🟡 scheduler.py есть, UI нет |

## E. СКИЛЛЫ
| Библиотека Skills&Tools по КАТЕГОРИЯМ + тумблеры on/off + поиск | Hermes | 🟡 skill-builder, нет реестра-с-тумблерами |
| Делегат-кодинг скиллы (claude-code/codex/opencode) | Hermes | 🔴 |
| Toolsets вкладка | Hermes | 🔴 |
| OS-автоматизация (macos-use/notes/imessage) | Hermes | ⛔ (веб-апп, не наше) |

## F. ПАМЯТЬ / МОДЕЛЬ-РОУТИНГ
| Память: Persistent Memory / User Profile / Memory Budget / Context Compressor / Auto-Compression / Protected Recent | Hermes | 🟡 память+RAG есть, гранулярных контролей нет |
| **Auxiliary-модели на ЗАДАЧУ** (Vision/Web-extract/Compression/Skills/Approval/MCP/Title — дешёвая модель на под-задачу, дефолт «main») | Hermes | 🔴 (сильная идея — экономия) |
| Кросс-провайдер авто-роутер | Chutes | ✅ + circuit-breaker (мы) |
| Поиск по 732 моделям, сорт | — | ✅ |

## G. ГОЛОС / ВНЕШНИЙ ВИД / НАСТРОЙКИ
| Voice TTS+STT с выбором провайдера (OpenAI/Edge/ElevenLabs/xAI) | Hermes | 🟡 NanoGPT-TTS + mic |
| Темы/палитры (Nous/Midnight/Ember/Cyberpunk/Slate) + Light/Dark/System | Hermes | 🔴 |
| Полный IA настроек (Model/Chat/Appearance/Workspace/Safety/Memory/Voice/Advanced/Providers/Gateway/Tools&Keys/MCP/About) | Hermes | 🟡 settings-panel проще |

## H. МЕДИА / СТУДИЯ
| Рейл модальностей Image/Video/Audio/Avatar/3D/Tools | MUAPI/Venice | 🟡 студия с табами (+ P0-баг сброса) |
| AI-Tools сетка: face-swap/watermark-remover/upscale/skin-enhancer/image-extension — цена за вызов inline | MUAPI | 🟡 часть фото/видео-тулз |
| **Playground на модель**: Input/Result, Form/JSON, system-prompt, живая цена на кнопке, API Reference/Embed Code | MUAPI | 🔴 |
| Workflows (Templates/My/Published, коллекции по индустрии) | MUAPI | 🔴 |
| Image studio (модель/негатив/референс/формат/batch/seed) | MUAPI | ✅ (склонировано) |
| Video i2v маркетплейс с ценой, aspect/duration, режимы видео/картинка/оживить/аватар | NanoGPT/AIMLAPI | ✅ (студия) |
| Музыка / 3D | MUAPI/AIMLAPI | 🟡 ждут (AIMLAPI оплачен → можно) |
| Embed на сайт / Developer API | MUAPI | 🟡 OpenAI-совместимый эндпоинт есть |

## I. БИЛЛИНГ / ЭКОСИСТЕМА
| Top-up модалка мульти-рейл: Card/Crypto(BTC)/PayPal/Invoice, пресеты, авто-топап, redeem promo, история | NanoGPT/AIMLAPI | ⛔ (оплата отложена Damir) |
| Usage-аналитика: Spend/Tokens/Requests, период, по-модельные бары | NanoGPT | 🔴 |
| Метры подписки (недельные токены, дневные картинки, сброс) | NanoGPT | 🟡 знаем статус |
| «Что нового»/чейнджлог-фид | NanoGPT | 🔴 |
| In-app браузер (co-browse) | Claude | ✅ |
| TEE/приватный verifiable-инференс тир | NanoGPT | ✅ TEE-роутинг |

---

## 🐞 БАГИ С ТВОИХ СКРИНОВ (агенты нашли)
1. 🔴 **«Основная модель недоступна — беру запасную» на КАЖДОМ сообщении** (даже на «привет») — постоянный фолбэк primary→gpt-5.1/grok. ЭТО мой circuit-breaker/роутер уже чинил — надо подтвердить что эти скрины ДО фикса и сейчас чисто.
2. 🔴 **Радужный неон-фон протекает по всему UI** (кино/студия) — контраст-глитч, контролы нечитаемы.
3. 🔴 **Студия «не вышло»** (видео-сцена упала) — нужен retry/обработка ошибки сцены.
4. 🔴 **Оркестратор «долго не отвечает»** — таймаут.
5. 🔴 **Галлюцинированные имена моделей** в подсказках: «grok-4.1-fast / grok-4-20 / grok-4.20» — баг нейминга/роутинга.
6. ⚠️ **ПРАВОВОЙ РИСК:** на одном скрине — face-swap БЕЗ СОГЛАСИЯ против загруженного фото реального человека (дипфейк). Uncensored — ок для контента, но дипфейк реального лица = юридически опасно даже для нас. Нужен гард: блок face-swap на фото реальных людей / требование согласия (как abuse_check для минор+секс). НЕ цензура — защита от посадки.

## ИТОГ
Движок и базовые фишки — **паритет/лучше** фронтира. До «как на скринах» не хватает (по приоритету):
🔴 MCP-маркетплейс · 🔴 «+»-tools-меню · 🟡 Grok-режимы · 🔴 слайдер памяти · 🔴 auxiliary-модели ·
🟡 skills-библиотека · 🔴 темы · 🔴 MUAPI playground/AI-tools · 🟡 музыка/3D · 🔴 voice-STT.
Owner-gated/позже: биллинг-модалка, аналитика, соц-публикация, async-coding-PR.
