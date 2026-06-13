// Тайга — background service worker (MV3).
// Владеет связью с бэкендом Тайги и крутит act-loop:
//   снимок страницы → спросить бэкенд про следующее действие → выполнить через
//   content.js → записать результат → повторить (до done / Stop / лимита шагов).
// Опасные/отправляющие действия и ввод данных в формы — только после подтверждения
// пользователя в side-панели.

const DEFAULTS = {
  backend: "http://127.0.0.1:8777",
  user: "default",
  maxSteps: 15,
};

let RUN = null; // активный прогон: {tabId, goal, history, stop, step}

// Включаем открытие side-панели по клику на иконку.
chrome.runtime.onInstalled.addListener(() => {
  if (chrome.sidePanel && chrome.sidePanel.setPanelBehavior) {
    chrome.sidePanel
      .setPanelBehavior({ openPanelOnActionClick: true })
      .catch(() => {});
  }
});

async function getCfg() {
  const s = await chrome.storage.local.get(["backend", "user"]);
  return {
    backend: (s.backend || DEFAULTS.backend).replace(/\/+$/, ""),
    user: s.user || DEFAULTS.user,
    maxSteps: DEFAULTS.maxSteps,
  };
}

async function activeTab() {
  const [tab] = await chrome.tabs.query({ active: true, lastFocusedWindow: true });
  return tab;
}

// Шлём команду content-скрипту; при отсутствии — инжектим и повторяем.
async function sendToContent(tabId, payload) {
  payload = Object.assign({ target: "taiga-content" }, payload);
  try {
    return await chrome.tabs.sendMessage(tabId, payload);
  } catch (e) {
    try {
      await chrome.scripting.executeScript({
        target: { tabId },
        files: ["content.js"],
      });
      return await chrome.tabs.sendMessage(tabId, payload);
    } catch (e2) {
      return { ok: false, error: "content-скрипт недоступен: " + (e2.message || e2) };
    }
  }
}

function panel(type, data) {
  // Лог в side-панель (она слушает runtime-сообщения).
  chrome.runtime
    .sendMessage(Object.assign({ target: "taiga-panel", type }, data || {}))
    .catch(() => {});
}

async function askBackend(cfg, goal, snapshot, history) {
  const res = await fetch(cfg.backend + "/api/browser_act", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user: cfg.user, goal, page: snapshot, history }),
  });
  if (!res.ok) {
    let msg = "HTTP " + res.status;
    try {
      const j = await res.json();
      if (j && j.error) msg = j.error;
    } catch (e) {}
    throw new Error(msg);
  }
  return res.json();
}

// Действия, которые требуют явного подтверждения пользователя.
const DESTRUCTIVE = /(отправ|купить|оплат|удал|подтверд|публик|submit|buy|pay|delete|send|post|sign|войти|оформ)/i;

function needsConfirm(decision) {
  if (decision.confirm) return true;
  if (decision.action === "type") return true; // ввод данных в форму
  const blob = [decision.selector, decision.text, decision.reason]
    .filter(Boolean)
    .join(" ");
  if (decision.action === "click" && DESTRUCTIVE.test(blob)) return true;
  return false;
}

// CAPTCHA / антибот — стоп.
const CAPTCHA = /(captcha|recaptcha|hcaptcha|я не робот|i'?m not a robot|подтвердите, что вы человек|cf-challenge|cloudflare)/i;

function looksLikeCaptcha(snapshot) {
  const t = (snapshot.text || "") + " " + (snapshot.title || "");
  return CAPTCHA.test(t);
}

let pendingConfirm = null; // {resolve}

function waitConfirm(decision) {
  return new Promise((resolve) => {
    pendingConfirm = { resolve };
    panel("confirm", { decision });
  });
}

async function execDecision(tabId, decision) {
  const a = decision.action;
  if (a === "click") {
    return sendToContent(tabId, { cmd: "click", selector: decision.selector });
  }
  if (a === "type") {
    return sendToContent(tabId, {
      cmd: "type",
      selector: decision.selector,
      text: decision.text,
    });
  }
  if (a === "scroll") {
    return sendToContent(tabId, { cmd: "scroll", amount: decision.amount });
  }
  if (a === "navigate") {
    let url = String(decision.url || "");
    if (url && !/^https?:\/\//.test(url)) url = "https://" + url;
    await chrome.tabs.update(tabId, { url });
    await new Promise((r) => setTimeout(r, 1500));
    return { ok: true, detail: "navigate " + url };
  }
  return { ok: false, error: "неизвестное действие: " + a };
}

async function runLoop(goal) {
  const cfg = await getCfg();
  const tab = await activeTab();
  if (!tab || !tab.id) {
    panel("error", { message: "нет активной вкладки" });
    return;
  }
  if (/^chrome:\/\/|^chrome-extension:\/\/|^edge:\/\//.test(tab.url || "")) {
    panel("error", { message: "на служебных страницах браузера агент не работает — откройте обычный сайт" });
    return;
  }
  RUN = { tabId: tab.id, goal, history: [], stop: false, step: 0 };
  panel("start", { goal });

  for (let i = 0; i < cfg.maxSteps; i++) {
    if (RUN.stop) {
      panel("stopped", {});
      break;
    }
    RUN.step = i + 1;

    // 1) снимок
    const snapRes = await sendToContent(RUN.tabId, { cmd: "snapshot" });
    if (!snapRes || !snapRes.ok) {
      panel("error", { message: (snapRes && snapRes.error) || "не удалось прочитать страницу" });
      break;
    }
    const snapshot = snapRes.snapshot;

    // безопасность: CAPTCHA → стоп
    if (looksLikeCaptcha(snapshot)) {
      panel("done", {
        text: "Похоже на проверку CAPTCHA / антибот. Я не решаю такие проверки — пройдите её сами, потом дайте новую цель.",
      });
      break;
    }

    panel("thinking", { step: RUN.step });

    // 2) спросить бэкенд
    let decision;
    try {
      decision = await askBackend(cfg, goal, snapshot, RUN.history);
    } catch (e) {
      panel("error", { message: "бэкенд: " + (e.message || e) });
      break;
    }

    if (decision.action === "done") {
      panel("done", { text: decision.text || decision.reason || "Готово." });
      break;
    }

    panel("action", {
      step: RUN.step,
      action: decision.action,
      selector: decision.selector,
      text: decision.text,
      url: decision.url,
      reason: decision.reason,
    });

    // 3) подтверждение для опасных шагов
    if (needsConfirm(decision)) {
      const ok = await waitConfirm(decision);
      if (!ok) {
        RUN.history.push({
          action: decision.action,
          detail: decision.selector || decision.url || "",
          result: "пользователь отклонил",
        });
        panel("result", { ok: false, detail: "пользователь отклонил шаг" });
        continue;
      }
    }

    // 4) выполнить
    if (RUN.stop) { panel("stopped", {}); break; }
    const exec = await execDecision(RUN.tabId, decision);
    const resultStr = exec && exec.ok ? (exec.detail || "ok") : "ошибка: " + ((exec && exec.error) || "?");
    RUN.history.push({
      action: decision.action,
      detail: decision.selector || decision.url || decision.text || "",
      result: resultStr,
    });
    panel("result", { ok: !!(exec && exec.ok), detail: resultStr });

    await new Promise((r) => setTimeout(r, 700)); // дать странице обновиться

    if (i === cfg.maxSteps - 1) {
      panel("done", { text: "Достигнут лимит шагов (" + cfg.maxSteps + "). Остановился." });
    }
  }
  RUN = null;
}

// Сообщения из side-панели.
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (!msg || msg.target !== "taiga-bg") return;
  if (msg.cmd === "run") {
    runLoop(String(msg.goal || "").trim());
    sendResponse({ ok: true });
  } else if (msg.cmd === "stop") {
    if (RUN) RUN.stop = true;
    if (pendingConfirm) { pendingConfirm.resolve(false); pendingConfirm = null; }
    sendResponse({ ok: true });
  } else if (msg.cmd === "confirm") {
    if (pendingConfirm) {
      pendingConfirm.resolve(!!msg.approve);
      pendingConfirm = null;
    }
    sendResponse({ ok: true });
  } else if (msg.cmd === "savecfg") {
    chrome.storage.local
      .set({ backend: msg.backend, user: msg.user })
      .then(() => sendResponse({ ok: true }));
    return true;
  } else if (msg.cmd === "getcfg") {
    getCfg().then((c) => sendResponse(c));
    return true;
  }
  return true;
});
