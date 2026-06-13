// Тайга — side-панель. Чат-цель + живой лог шагов + подтверждения + Стоп.
const $ = (id) => document.getElementById(id);
const logEl = $("log");
const goalEl = $("goal");
const runBtn = $("runBtn");
const stopBtn = $("stopBtn");
const confirmBar = $("confirmBar");
const confirmText = $("confirmText");

let running = false;

function bg(payload) {
  return chrome.runtime.sendMessage(Object.assign({ target: "taiga-bg" }, payload));
}

function addEntry(cls, label, body, sub) {
  const div = document.createElement("div");
  div.className = "entry " + cls;
  const l = document.createElement("div");
  l.className = "label";
  l.textContent = label;
  div.appendChild(l);
  if (body != null) {
    const b = document.createElement("div");
    b.className = "body";
    b.textContent = body;
    div.appendChild(b);
  }
  if (sub) {
    const s = document.createElement("div");
    s.className = "sub";
    s.textContent = sub;
    div.appendChild(s);
  }
  logEl.appendChild(div);
  logEl.scrollTop = logEl.scrollHeight;
  return div;
}

function actionLabel(a) {
  return (
    {
      click: "Действие · клик",
      type: "Действие · ввод",
      scroll: "Действие · прокрутка",
      navigate: "Действие · переход",
    }[a] || "Действие"
  );
}

function actionBody(d) {
  if (d.action === "click") return "клик: " + (d.selector || "");
  if (d.action === "type") return "ввод «" + (d.text || "") + "» в " + (d.selector || "");
  if (d.action === "scroll") return "прокрутка страницы";
  if (d.action === "navigate") return "переход: " + (d.url || "");
  return d.action;
}

function setRunning(on) {
  running = on;
  runBtn.disabled = on;
  stopBtn.disabled = !on;
  goalEl.disabled = on;
}

// Сообщения от background.
chrome.runtime.onMessage.addListener((msg) => {
  if (!msg || msg.target !== "taiga-panel") return;
  switch (msg.type) {
    case "start":
      addEntry("e-goal", "Цель", msg.goal);
      setRunning(true);
      break;
    case "thinking":
      addEntry("e-thinking", "Думаю…", "шаг " + msg.step);
      break;
    case "action":
      addEntry("e-action", actionLabel(msg.action), actionBody(msg), msg.reason || "");
      break;
    case "result":
      addEntry(
        "e-result " + (msg.ok ? "ok" : "bad"),
        msg.ok ? "Результат ✓" : "Результат ✗",
        msg.detail || ""
      );
      break;
    case "confirm":
      showConfirm(msg.decision);
      break;
    case "done":
      addEntry("e-done", "Готово", msg.text || "");
      setRunning(false);
      hideConfirm();
      break;
    case "stopped":
      addEntry("e-stopped", "Остановлено", "по запросу пользователя");
      setRunning(false);
      hideConfirm();
      break;
    case "error":
      addEntry("e-error", "Ошибка", msg.message || "");
      setRunning(false);
      hideConfirm();
      break;
  }
});

function showConfirm(d) {
  let what = "Тайга хочет выполнить действие";
  if (d.action === "click") what = "Тайга хочет нажать «" + (textOf(d) || d.selector) + "»";
  else if (d.action === "type") what = "Тайга хочет ввести данные в поле";
  else if (d.action === "navigate") what = "Тайга хочет перейти на " + (d.url || "");
  confirmText.textContent = what + " — подтвердить?";
  confirmBar.classList.remove("hidden");
}
function textOf(d) {
  return (d.text || d.reason || "").slice(0, 40);
}
function hideConfirm() {
  confirmBar.classList.add("hidden");
}

$("approveBtn").addEventListener("click", () => {
  bg({ cmd: "confirm", approve: true });
  hideConfirm();
});
$("declineBtn").addEventListener("click", () => {
  bg({ cmd: "confirm", approve: false });
  hideConfirm();
});

runBtn.addEventListener("click", () => {
  const goal = goalEl.value.trim();
  if (!goal) return;
  bg({ cmd: "run", goal });
});
goalEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
    e.preventDefault();
    runBtn.click();
  }
});
stopBtn.addEventListener("click", () => {
  bg({ cmd: "stop" });
});

// Настройки.
$("settingsBtn").addEventListener("click", () => {
  $("settings").classList.toggle("hidden");
});
$("saveCfg").addEventListener("click", () => {
  bg({
    cmd: "savecfg",
    backend: $("backend").value.trim() || "http://127.0.0.1:8777",
    user: $("user").value.trim() || "default",
  });
  $("settings").classList.add("hidden");
  addEntry("e-result ok", "Настройки", "сохранены");
});

// Загрузить текущий конфиг в поля.
bg({ cmd: "getcfg" }).then((c) => {
  if (!c) return;
  $("backend").value = c.backend || "";
  $("user").value = c.user || "";
});

addEntry("e-thinking", "Тайга готова", "Откройте сайт, введите цель и нажмите «Запустить». Опасные шаги спрошу отдельно.");
