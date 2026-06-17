# Тайга ИИ — восстановленные ДИЗАЙН-ЗАПРОСЫ Damir

Источник: транскрипт сессии `2ab72971-a978-46a3-9f64-0e2570cfa1b6.jsonl` (79 708 строк, ~2357 user-сообщений).
Извлечено: 2026-06-17. Только чтение транскрипта.

**Контекст, который запустил эту задачу** — последнее сообщение Damir (line 79703):
> "bro analyze teh chat and creae urself new up to date memory analyse last 50 prompts of my requetys how i see the system... just make the mock be real thing from a to z... **tho chnage svg and other design choices i made when u were building the wrong one those request should be noted and apllied!Q!!!!!**"

То есть: Claude долго строил «неправильную» React-версию (approximation), пока Damir давал дизайн-правки. Эти правки могли потеряться. Их надо собрать и применить к `public/shell.html` (macOS-perfect HTML — тот, который Damir хвалил).

ВАЖНО про два артефакта:
- **HTML-макет** `~/Downloads/claude-sessions/2026-06-10/taiga-redesign/index.html` (порт :8901) — «macOS-perfect», Damir его любит («exactly how i wanted»). Сейчас цель — сделать ЕГО живым (`public/shell.html`).
- **React-апп** `taiga-web/` — реальный код, в который ушли многие правки (токены/иконки/морфинг). При этом Damir несколько раз сказал, что React-версия — «trash / old design / approximation», а нужен именно тот HTML.

---

## 1. ДИЗАЙН-ПРАВКИ К ПРИМЕНЕНИЮ (для public/shell.html)

### A. Окно / шелл в стиле macOS («liquid glass»)

- **macOS-стиль окон со «светофором»** — главный визуальный язык.
  > L76724: "make this actually wokr and nothing feel resiible and dragagble option full screen or not fully screem **like on macos this the design i want to feel like liqui glass** to and add the logog for all ai models"
  > L76868: "like this for the windwos **macbook style bar** like this"
  > L74921: "**mac os.ios style fully costumasible clena premium and iphone in jn the world of ai 100m dollars liqui glass colors svg premium icons**"
  - ЧТО: каждое окно/панель = карточка с верхней macOS-полосой (3 кружка-светофора слева), стекло (`backdrop-filter: blur`), мягкая тень, скруглённые углы.
  - ГДЕ: контейнеры всех панелей/окон в shell.html.

- **Liquid glass на ВСЕХ UI-элементах** (кнопки, пилюли, чипы), не только на окнах.
  > L (summary) "make everytghi nliquid glass liek ui elements buttons"
  > L77289 (про новый дизайн): "the first our old design feel a bit more liquid glasss than our 2nd design now" — Т.Е. СТАРЫЙ был стекляннее; новый просел → вернуть больше стекла.
  - ЧТО: усилить стеклянность (полупрозрачный фон + blur + тонкая светлая граница `1px rgba(255,255,255,.1)` + внутренняя specular-подсветка) на кнопках/пилюлях/композере.

- **Композер (поле ввода) — стеклянный**, кнопка отправки с inset-тенью.
  > (summary) composer: `backdropFilter:"blur(14px) url(#liquid-glass)"`, send button glass inset shadow; SVG-фильтр `#liquid-glass` = feTurbulence(baseFrequency 0.008)+feDisplacementMap(scale 20).
  - ГДЕ: композер чата.

### B. Иконки — icons8 «Liquid Glass Color», объёмные, 3D

- **Только настоящие icons8 «Liquid Glass Color»** (Damir купил подписку, $18/мес, ~100 икон/мес, MCP подключён). Рисованные Claude иконки ОТВЕРГНУТЫ.
  > L75185: "**NOW I BTOUGH A SUBCRPTION USER THEIR ICOSN URS LOOK SHIT**"
  > L75214→ "**JUST USE WEBSITE LINKS I GAVE U**"
  > Ссылки, которые он дал многократно:
  > - https://icons8.com/icons/set/popular--style-liquid-glass-color
  > - https://icons8.com/icons/all--style-liquid-glass-color  (L75102: "those actually the4 look even better")
  > - https://icons8.com/icons/all--os-ios--corners-round--multi  (L75091: "use those icons exactly for the whole system")
  > - https://www.flaticon.com/free-icons/ios , https://developer.apple.com/design/human-interface-guidelines/icons (L77120)
  - ЧТО: заменить ВСЕ глифы/эмодзи на icons8 liquid-glass-color SVG. Если иконки нет в библиотеке — нарисовать кастом-SVG В ТОМ ЖЕ стиле (iOS · round corners · multicolor), Damir это разрешил:
  > L75116: "yes just take there and **draw the identical one**"
  > L77369: "use this [svg-icon-generator skill] and cretar your wons icons if not found in library"

- **Сделать иконки «более 3D, больше liquid glass»** — прямой запрос на визуальный апгрейд.
  > L78108: "**can u make icodn a bit more 3d and more liquid glass like use the desing tastse skill**"
  - ЧТО: двойной бевел + specular highlight + цветное свечение под иконкой по её доминирующему цвету (в React уже сделан `LiquidTile`: «3D glass: double-bezel + specular + colored glow per icon's dominant hue» — портировать этот вид в shell.html).
  - Реакция Damir на объёмные плитки: L78340 "**very nice what u d8d well done !!!**" (про «Объёмные стеклянные плитки» в tier-nav) — значит направление верное, тиражировать на остальные поверхности.

- **Иконки/логотипы для КАЖДОЙ AI-модели и компании-провайдера** (бренд по логотипу, не дефолтный).
  > L76724: "add the logog for all ai models"
  > L77624: "tab of the company and theri model liek **atrnopic logo opne ai logog** and other main ocmoaneis like we had before and **each models in the won drop down wiht lgogos too**"
  > Историческая боль: Hermes показывал иконку Llama/Meta, MiniMax — Cpu. Должны быть СВОИ логотипы (lobehub: HermesAgent/NousResearch/Minimax/Venice).
  - ЧТО: в каталоге моделей и дропдауне — реальный бренд-логотип на каждую модель; вкладка-скролл по брендам.

- **Иконки везде, где есть фича/модель** (не пустые места).
  > L77235: "**chekc image no icond there and other places too porbably fix it**"
  > L77289: "this need icons too / make them all icons / nothing opens i feel like bor manny feautre really done have ui"
  > L78340 (council): "add icont every hwere bro for each model"

### C. Док (Dock) в стиле macOS/iOS

- **Док центрировать ВОКРУГ чата**, не на всю ширину.
  > L77809: "**move docket to be centred aroujnd chat wtf bro**"
  > (история фиксов) `positionDock()` считает центр из `m.left + (innerWidth - wsW)`.
  - ГДЕ: контейнер дока.

- **Можно перетаскивать «приложения»-фичи в док** для быстрого доступа (как иконки приложений на iPhone). Пользователь сам решает, что закрепить.
  > L77062: "make so in the docket like **mac bheaviour u can aslo drop an appes for quikc acces** from docket so users kind decides thinkgs that stay there permantly and open tabs like in the picutre"
  > L77624: "make so i can grab the butti nand add the to the docker like **little apps on iponhe** and same with delelt **u hold and it shakes and u can press delet** or left lcik like rnomals only the ones that are not hardcoded such tabs and main ones and can go bakc in the library... like appstore"
  - ЧТО: drag-чтобы-добавить-в-док; долгое нажатие → иконки трясутся (iOS jiggle) → крестик удаления; удалённые возвращаются в библиотеку/каталог. Хардкодные главные табы — неудаляемые.

- Добавлять в док можно из каталога фич.
  > L77289: "add so u can add those to the dokcer too and make icond ebtter with [icons8 liquid-glass]"

### D. iOS-флюидность: перетаскивание окон и контента

- **Плавное iOS-перетаскивание окон/секций** — при движении окна контейнер вокруг сереет (grey container), плавные «резиновые» движения.
  > L77326: "we need this typoe **fludidity to move chat app around like in ios** and every aorund smoothe mooths and **section beein moves grey the container around** and other ios fluid moves such as **dragin images in the chat** and any where same with files... in terminla **drag in drop**... in oane studio for picture and images only... add this iphone of ios type of thing"
  - ЧТО: при drag окна — подсветка drop-зоны серым; плавная пружинная анимация (spring). Drag-and-drop картинок/файлов в чат, в Студию (картинки), в Терминал.

### E. Ресайз окон — ХРОНИЧЕСКАЯ боль (просил десятки раз)

- **ВСЕ окна ресайзятся, не только боковые панели.** Хэндлы ВОКРУГ всего окна (8 сторон), а не только слева/справа. Ресайзится и поле ввода, и окно ответа ИИ.
  > L69683: "windows for the chat are still not resible **i have asked this so many timea**"
  > L76263: "it should fully resible and not only the chat iwndows for typeing **bit the answer windows to**... fully resizble costume made / and in the pitcure the where i need press to **far from the actual boundries**" (хэндлы далеко от края — ПЛОХО, должны быть НА краю)
  > L76334: "bruh make them **fully around the chat not just left and right**"
  > L76588: "make **most windows that are not left and right panels** to be resizible i have been asking this for so long now"
  - ЧТО: 8-хэндловый ресайз (все стороны + углы) НА самой границе окна; на главном чате — и композер, и контейнер ответа; на центральных модалках — хотя бы угловой ресайз.

- **Кнопка-замок + перетаскивание-перекладка** окон (rearrange) — пользователь может двигать окна, замок фиксирует.
  > L76506: "i still ned this all rezible windows re arrange for all componnent **create a lock button** tehre if user wnat to mve things arround"
  - ЧТО: режим перекладки + кнопка-замок (lock), позиции/размеры сохраняются (localStorage).

- **Полноэкран / не-полноэкран** как на macOS (зелёный кружок).
  > L76724: "full screen or not fully screem like on macos"

- **Размер окна = по контенту** (не на весь экран, но подогнано).
  > (summary) "make windows be the same size as the content this just lok ridiculous not ful scren but adjusted" → `fitWin`/`fitWin` content-sized.

### F. Морфинг-вордмарк и шрифты

- **Морфинг-текст** в hero, циклит: ТАЙГА ИИ → ВСЕ МОДЕЛИ → ПРИВАТНОСТЬ → БЕЗ ЦЕНЗУРЫ → МОЖЕТ ВСЁ.
- **Градиент морфинга — янтарный, НЕ радуга.** Переход цвета ПЛАВНЫЙ, слева-направо по тексту, а не «вся надпись мигает разом».
  > L202: "make the fotn change colors like this, bro make it like **change more left side is like orange oither is red**... when text fully render **make less shapr more rounded** bro sharp looks bad **SMOOTH GRADIENT CHAGING FROM COLORS**"
  > (summary) "rather thwn whoe lthing chaign colkors it should **smooth going from one to another from left side of the wiritng to the rifhgt side**"
  > Финальное решение в React (Wave A): радугу-гу убрали → `INK="linear-gradient(180deg,#FFB088,#FF9E64)"`, goo-фильтр убран, crossfade+translateY.
  - ЧТО для shell.html: янтарный градиент (#FFB088→#FF9E64), мягкие (не острые) края глифов, плавная волна по тексту.

- **Единый янтарный акцент по всему UI** (#FF9E64 / `oklch(0.78 0.13 55)`). Раньше была радуга из 7 цветов — убрать.
  > L76441 (бриф): "единый янтарный акцент (#FF9E64), тёмная тема"
  - ЧТО: один акцентный цвет; сохранить семантику positive/caution/critical (зелёный/жёлтый/красный), всё «декоративно-цветное» (cyan/blue/violet) → янтарь.

- **3 разных шрифта по режимам** (у кода — свой моноширинный, как в старом дизайне по ссылке).
  > L454: "I LIKE THIS IN THE OLD ONE... FOR CODING FORNT WE HAVDE DIFFREENT FOR EACH MODE... so for now we have 3 different forn and like 5 background design"
  - ЧТО: для режима «Код» — VS-Code-подобный вид/шрифт; чат и студия — свои.

### G. Фоны — живые, по режимам, генерируемые

- **Анимированный фон на ВСЕХ экранах** (двигающиеся звёзды/северное сияние). Разный фон под каждый режим.
  > (summary) "also add so there are always on all screen a **moving star background**... user can either **import or make their own backgrounds** too"
  > "backgroudn it soo cool bro wiht moving start very nice i ver like it" — ОДОБРИЛ starfield.
  > "и брат задник должен быть больше **как северное сияние** понял !!!!! цвета переливаються как до этого" — aurora, переливы.
  > Режимы: chat=Aurora+Starfield(950 звёзд), code=synthwave-сетка, image=вертикальные капли-бары, ultra=3D WebGPU.
- **Цветные «turbo»-курсоры** разные по режимам.
  > "all of those DESIGN MODES need diffrent color **TURBU CURSORS** like before"
- **Фон можно сгенерировать через Студию** и поставить; Ultra-чат может генерить движущийся 3D-фон и менять систему.
  > L74894: "(b) «сгенерировать фон» через Студию yes liek **with ultra chat generate make moving 3d** and use in the system as this how ultra chat behaviuoisi change system how needed"

### H. Персональный hero-заголовок

- Сообщение на главном экране меняется по имени/памяти пользователя — кастомный заголовок.
  > (summary) "another cool idea i want bro the message on the front of the chat would **change depending on the name memory... custom made title for the user**"

### I. Без эмодзи

- **Никаких эмодзи** в UI — только линейные/SVG-иконки.
  > L76868: "**no emojis allowed by they way**"

---

## 2. КАК DAMIR ВИДИТ СИСТЕМУ (ментальная модель и предпочтения)

- **Нужен ИМЕННО тот macOS-perfect HTML, а не React-приближение.** Это самое важное и повторялось в конце:
  > L79365: "i just look at ut webstie locallhost 3000 bro **u used the old desing this whole time**"
  > L79433: "i sped so muhc token for u to achive nothign **we made new dewsing and wanted to make it real deal**"
  > L79542: "trash **i liked exactly hwo it owas in the new design**"
  > L79571: "why can u mkae html just alive **i realy like before how it was maxos poerfect style exactly how i wanted**"
  > L79631: "HTML (ровно тот macOS-perfect вид) и делаем ЕГО живым. that is the in tila plan make all feature and everythgin like before fully work"
  Вывод: брать `taiga-redesign/index.html` (macOS-стекло) как источник истины вида и оживлять его (`public/shell.html`), НЕ перетаскивать его в старый React-вид.

- **Цикл build → test → fix, до идеала, с пруфами.** Не «готово» без доказательств.
  > L79703: "make the mock be real thing... full build test comparsin fix build **this endless lookp of user cases screneshto**... and analysis of screenshot and fixes until perfect"
  > L78607: "run some user worflows test doo screnshot and find bugs... **analyze screeshots and chekc against how it should look and how behave** use reasl input real generation use my moeny"
  Скриншот каждой фичи → сверить «как должно выглядеть и вести себя» → починить → пересоснять. Не пере-тестировать уже подтверждённое.

- **Ни одна фича не теряется.** 182 (+~36 найденных) фич в 12 областях. Минималистичный редизайн НЕ должен выкидывать рабочие фичи.
  > L74695: "we need **all feature** we have created in new one design, either removed that did not exist before and jsut halucination or **wired in the same way**"
  > L79659: "Полный список — **182 фичи в 12 областях** we have mde like other 42 **why are degrading bro**"
  Чисто, но мультифункционально, без перегруза:
  > L76868: "i watn them all to wokr but at the same time **not to over stimulate the user it has to bclean but multifcuntion** think use ur desing skills"

- **Каждая фича доступна и КЛИКАБЕЛЬНА; у каждой — своя рабочая экранка.** «Ничего не открывается» — частая жалоба.
  > L76548: "make it **fully ckiclabale so i can truly ckilc all buttons** there"
  > L77289: "**nothing opens** i feel like bor manny feautre really done have ui"
  > L77763: "**check all scren we have tabs and widnwos** to see if w ehave all feature and actullay press and see that iut odes show a desing for this feature"
  > L77459: "**no inquie desing ofr each tab**" (НЕ один и тот же экран на каждый таб — у каждого свой дизайн)

- **App Store кнопок/фич.** Пользователь сам строит/перекладывает систему: кнопки = «приложения», добавляются в док/чат/Ultra/сайдбар; удаляются и возвращаются в библиотеку.
  > L74877: "**we should have appstore of button** and can be added to the doker to the chat to ultra chat... i need the system to be **redwsignble by demand of the user**"
  > L79484: "remmerber about **app store for features** features that is not anywhere else in the system"

- **4–5 главных табов + Ultra.** Чат/Код/Студия/Дизайн/Агент + Ultra. У каждого режима — своя экранка, но «один мозг» (любой чат может всё).
  > L77459: "for code have like **visual studio code type**... normal chat and code... studio to mkae content and design"
  > Ultra: "чат рулит всем" — инлайн-карточки что настроено (модель/RAG/память) + кнопка «прыгнуть в настройку» + эксклюзивная власть пересобирать систему.
  > L77424: "where other tabs we should have **4**"

- **Управление моделью — 3 способа в КАЖДОМ режиме** + общий Авто:
  1) Усилие (effort: all/high/fast — как у ChatGPT),
  2) Авто-по-тиру (cheap/normal/expensive/top — берёт лучшую модель в ценовой категории),
  3) Ручной выбор модели.
  > L78340: "we control system i n3 ways effore... second way is by having auto mode... cheap, norma, epensive and tiop... third way it by just picking models u want / but for eahc mode eahc of those ways should eist"
  (В React уже собрано как ModelControl Auto|Усилие|Тир|Выбор — портировать вид.)

- **Стиль общения:** русский «ты/брат», без жаргона, бинарные статус-строки, решать технические вопросы самому при «go/c/just do it», НЕ говорить отдыхать, НЕ заваливать выбором. Action-oriented, бесит когда Claude «стопает».
  > L78946: "go why u kee\ stoping **keep going until done al**"
  > L78567: "**JUST BUILD TTHE APP ALREADY**... just land dynami wokrflows an many paralel agnet and build !!!"

---

## 3. СКРИНШОТЫ / РЕФЕРЕНСЫ (что хвалил / ругал)

ХВАЛИЛ:
- **macOS-perfect HTML-макет** (`taiga-redesign/index.html`, :8901) — «exactly how i wanted», «i liked exactly how it was in the new design». ЭТАЛОН.
- **Starfield-фон** — "soo cool bro wiht moving start very nice i ver like it".
- **Северное сияние (Aurora)** — "задник должен быть больше как северное сияние, цвета переливаються".
- **Объёмные стеклянные плитки в tier-nav** (icons8 3D glass) — L78340 "very nice what u d8d well done !!!".
- **icons8 «Liquid Glass Color» / «iOS round corners multi»** наборы — его выбранный стиль иконок.
- Старый дизайн «feel a bit more liquid glass» — старая версия была стекляннее, это плюс.

РУГАЛ:
- **React-вид на localhost:3000** — «old design this whole time», «trash», «achieved nothing».
- **Рисованные Claude SVG-иконки** — "URS LOOK SHIT" (после покупки icons8).
- **Радужный морфинг-вордмарк** (7 цветов, мигает разом, острые края) — заменён на янтарь, плавную волну, мягкие края.
- **Хэндлы ресайза далеко от края окна** — должны быть НА границе.
- **Одинаковый экран на разных табах / «ничего не открывается»** — каждая фича должна иметь свою кликабельную экранку.
- **Док на всю ширину / перекрывает чат** — центрировать вокруг чата.

Референс-ссылки, которые Damir давал под дизайн (применить):
- icons8 liquid-glass-color / os-ios-round-corners-multi (см. раздел 1.B).
- flaticon ios, Apple HIG icons.
- svg-icon-generator skill (рисовать недостающие в том же стиле):
  `npx -y skills add jeremylongshore/claude-code-plugins-plus-skills --skill svg-icon-generator`
- design-taste-frontend skill — для апгрейда вида/иконок («use the desing tastse skill»).
- Под анимации/вид компонентов: 21st-dev agent-elements, Ruixen AI (shining-text/liquid-text), particle-text-effect, hero-futuristic (WebGPU «BUILD YOUR DREAMS» для Ultra), spotlight-card (подсветка вокруг контейнеров моделей), agent-plan (выпадающие шаги мышления).

---

## 4. ОТЛОЖЕНО НА ПОТОМ («запомнить / сделать после»)

Damir прямо просил не забыть это после завершения текущего билда (L79703: "there were thing that were planned after this... dont forget about them"):

- **Hard, post-testing список** (явно припаркован, L78457): CLaRa / RAG (rag-anything), g-brain, **визуализация графа памяти/мозга**, голосовой режим (voice mode, MediaRecorder+STT), sandbox-доступ к файлам, Obsidian-интеграция.
  > L78457: "we still have things like clara RAG rag, gbrain and obsidian maybe **visualize the brain memory graphics** to and voice mode and sandbo acces to files... keep this in the bakc of the brain"

- **Английский язык интерфейса** (EN-рынок) — «Язык интерфейса» был помечен как галлюцинация, но Damir сказал строить: L74783 "english too yes", L74695-ветка "english too".

- **Платёжный код / юрлицо** — рано: L74761 "not now for this too early" (ЮKassa/CloudPayments, ИП/ООО, KYC). СБП-биллинг — позже.

- **Миграция данных при публичном флипе** — «ничего не должно быть в системе, только пресеты/готовые коннекшены»: L74761.

- **Burner/ghost-чат** (ничего не хранит) — заявлен, могла остаться недоделка.

- **Бюджет/кредит-тоггл для крупных операций** (Эконом/Норма/Макс, как effort в Claude Code, с кэпом+стопом) — при кэпе авто-даунгрейд на дешёвую модель (не обрезка).

- **Merge/compact чатов** — `/api/compact` не дёргался, объединение пустое — «добей мерж».

- **Окно-попап с вопросами + кнопки-выбор в конце промпта** (open-question-gate / agent-question-card) — Damir несколько раз переподтверждал, легко теряется: L75185 "окно с вопросами + кнопки-выбор в конце промпта".

- **IA-рефактор (часть осталась):** слить multiModel в один enum (council/compare/brain/debate; Relay/Beam уже удалены); Debate как вариант Совета; единый Depth-slider вместо Effort+Deep; 6-стол nav без дублей входов; правильная раскладка фич (Pipeline из Чата/Кода, Memory-export → Настройки, Видео-пилюля → Студия>Видео). Проверка «новый юзер понимает за 3 сек».
  > L79066: "agnet mode setting for example would have in it option for realy and brain but this is the same thing and this agent feautre shoudl in agent tab"

- **Per-chat vs per-account различение состояния:** что хранится на чат (память, мастер-промпт, режим), что на аккаунт.
  > L76996: "what staty for per chat session in sutdio chat desing agent... what are for whole account like we have per chat memroy and per chat master prompts"

- **Вкладка-артефакты справа** (как в Claude Code) — для каждого чата.
  > L76993: "u missed the tab on the right that we had before... claudew code... we need this for each chat"

---

## КОРОТКИЙ ЧЕК-ЛИСТ ДИЗАЙН-ПРАВОК ДЛЯ public/shell.html (применить)

1. Все окна = macOS-карточки: верхняя полоса + 3 светофора, стекло (blur), тень, скругление.
2. Liquid glass усилить на кнопках/пилюлях/чипах/композере (вернуть «стекляннее старого»).
3. Иконки — только icons8 liquid-glass-color (по ссылкам); недостающие рисовать в том же iOS-round-multicolor стиле; сделать «более 3D» (double-bevel + specular + цветное свечение по доминирующему цвету).
4. Логотип на КАЖДУЮ модель и компанию (бренд, не дефолт); вкладка-скролл по брендам; логотипы в дропдауне моделей.
5. Иконки везде, где фича/модель — никаких пустых мест, никаких эмодзи.
6. Док: центрировать вокруг чата; drag-чтобы-добавить-фичу; iOS-jiggle + удаление по долгому нажатию; возврат в библиотеку; хардкодные табы неудаляемы.
7. iOS-флюидность: spring-перетаскивание окон, серая подсветка drop-зоны; drag-drop картинок/файлов в чат, Студию, Терминал.
8. Ресайз: 8 хэндлов НА границе всех окон (включая композер и окно ответа и центральные модалки); кнопка-замок + перекладка с сохранением.
9. Полноэкран/не-полноэкран (зелёный кружок); окна по размеру контента.
10. Морфинг-вордмарк: янтарный градиент #FFB088→#FF9E64, плавная волна слева-направо, мягкие края (НЕ радуга, НЕ мигание целиком).
11. Единый янтарный акцент (#FF9E64); цветную радугу → янтарь; сохранить green/yellow/red семантику.
12. 3 шрифта по режимам (код = VS-Code-вид); 5 живых фонов по режимам (chat=Aurora+Starfield, code=synthwave, image=капли, ultra=3D); цветные turbo-курсоры; импорт/генерация фона через Студию.
13. Персональный hero-заголовок по имени/памяти.
14. У КАЖДОЙ фичи своя кликабельная экранка (не один экран на все табы); 182+ фич не терять; чисто, но мультифункционально, без перегруза.
15. 4–5 главных табов + Ultra; «один мозг»; ModelControl (Авто|Усилие|Тир|Выбор) в каждом режиме.
16. App Store кнопок: добавлять/удалять/возвращать; система перекраивается пользователем.
