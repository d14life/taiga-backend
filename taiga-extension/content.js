// Тайга — content script.
// Две задачи: (1) СНИМОК страницы (видимый текст + компактный список интерактивных
// элементов со стабильными селекторами); (2) ВЫПОЛНЕНИЕ действий по команде из
// background.js: click / type / scroll / read / navigate(через background) и т.п.
// Ничего не решает само — только читает и делает то, что попросили.

(function () {
  if (window.__taigaCobrowseLoaded) return;
  window.__taigaCobrowseLoaded = true;

  // ---- утилиты ----
  function isVisible(el) {
    if (!el || !el.getClientRects || !el.getClientRects().length) return false;
    const s = window.getComputedStyle(el);
    if (s.visibility === "hidden" || s.display === "none" || s.opacity === "0") return false;
    const r = el.getBoundingClientRect();
    return r.width > 1 && r.height > 1;
  }

  function cssEscape(s) {
    if (window.CSS && CSS.escape) return CSS.escape(s);
    return String(s).replace(/[^a-zA-Z0-9_-]/g, "\\$&");
  }

  // Стабильный селектор: id → data-testid/name/aria-label → nth-of-type путь.
  function selectorFor(el) {
    if (el.id && document.querySelectorAll("#" + cssEscape(el.id)).length === 1) {
      return "#" + cssEscape(el.id);
    }
    const attrs = ["data-testid", "data-test", "name", "aria-label"];
    for (const a of attrs) {
      const v = el.getAttribute && el.getAttribute(a);
      if (v) {
        const sel = `${el.tagName.toLowerCase()}[${a}="${cssEscape(v)}"]`;
        try { if (document.querySelectorAll(sel).length === 1) return sel; } catch (e) {}
      }
    }
    // путь до body через nth-of-type
    const parts = [];
    let node = el;
    while (node && node.nodeType === 1 && node.tagName.toLowerCase() !== "html") {
      let part = node.tagName.toLowerCase();
      const parent = node.parentElement;
      if (parent) {
        const same = Array.from(parent.children).filter(
          (c) => c.tagName === node.tagName
        );
        if (same.length > 1) {
          part += `:nth-of-type(${same.indexOf(node) + 1})`;
        }
      }
      parts.unshift(part);
      if (node.id) { parts.unshift("#" + cssEscape(node.id)); break; }
      node = node.parentElement;
      if (parts.length > 6) break;
    }
    return parts.join(" > ");
  }

  function roleOf(el) {
    const r = el.getAttribute && el.getAttribute("role");
    if (r) return r;
    const t = el.tagName.toLowerCase();
    if (t === "a") return "link";
    if (t === "button") return "button";
    if (t === "input") return "input:" + (el.type || "text");
    if (t === "textarea") return "textarea";
    if (t === "select") return "select";
    return t;
  }

  function labelFor(el) {
    let txt = (el.innerText || el.value || "").trim();
    if (!txt) {
      txt =
        el.getAttribute("aria-label") ||
        el.getAttribute("placeholder") ||
        el.getAttribute("title") ||
        el.getAttribute("alt") ||
        "";
    }
    return txt.replace(/\s+/g, " ").trim().slice(0, 120);
  }

  // Снимок страницы: текст + до N интерактивных элементов.
  function snapshot() {
    const sel =
      "a[href], button, input:not([type=hidden]), textarea, select, " +
      "[role=button], [role=link], [onclick], [tabindex]";
    const seen = new Set();
    const elements = [];
    const nodes = document.querySelectorAll(sel);
    for (const el of nodes) {
      if (elements.length >= 80) break;
      if (!isVisible(el)) continue;
      let s;
      try { s = selectorFor(el); } catch (e) { continue; }
      if (!s || seen.has(s)) continue;
      seen.add(s);
      const r = el.getBoundingClientRect();
      elements.push({
        selector: s,
        tag: el.tagName.toLowerCase(),
        role: roleOf(el),
        text: labelFor(el),
        x: Math.round(r.left + r.width / 2),
        y: Math.round(r.top + r.height / 2),
      });
    }
    let text = "";
    try {
      text = (document.body && document.body.innerText || "").slice(0, 6000);
    } catch (e) {}
    return {
      url: location.href,
      title: document.title || "",
      text: text,
      elements: elements,
    };
  }

  function find(selector) {
    if (!selector) return null;
    try { return document.querySelector(selector); } catch (e) { return null; }
  }

  function doClick(selector) {
    const el = find(selector);
    if (!el) return { ok: false, error: "элемент не найден: " + selector };
    el.scrollIntoView({ block: "center", behavior: "instant" });
    try { el.focus(); } catch (e) {}
    el.click();
    return { ok: true, detail: "click " + selector };
  }

  function doType(selector, text) {
    const el = find(selector);
    if (!el) return { ok: false, error: "поле не найдено: " + selector };
    el.scrollIntoView({ block: "center", behavior: "instant" });
    try { el.focus(); } catch (e) {}
    const val = text == null ? "" : String(text);
    const proto =
      el.tagName === "TEXTAREA"
        ? window.HTMLTextAreaElement.prototype
        : window.HTMLInputElement.prototype;
    const setter = Object.getOwnPropertyDescriptor(proto, "value");
    if (setter && setter.set) setter.set.call(el, val);
    else el.value = val;
    el.dispatchEvent(new Event("input", { bubbles: true }));
    el.dispatchEvent(new Event("change", { bubbles: true }));
    return { ok: true, detail: "type в " + selector };
  }

  function doScroll(amount) {
    const dy = Number(amount) || 600;
    window.scrollBy({ top: dy, behavior: "smooth" });
    return { ok: true, detail: "scroll " + dy };
  }

  function doRead() {
    return { ok: true, snapshot: snapshot() };
  }

  // Слушаем команды от background.js
  chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (!msg || msg.target !== "taiga-content") return;
    try {
      if (msg.cmd === "snapshot") {
        sendResponse({ ok: true, snapshot: snapshot() });
      } else if (msg.cmd === "click") {
        sendResponse(doClick(msg.selector));
      } else if (msg.cmd === "type") {
        sendResponse(doType(msg.selector, msg.text));
      } else if (msg.cmd === "scroll") {
        sendResponse(doScroll(msg.amount));
      } else if (msg.cmd === "read") {
        sendResponse(doRead());
      } else if (msg.cmd === "ping") {
        sendResponse({ ok: true });
      } else {
        sendResponse({ ok: false, error: "неизвестная команда: " + msg.cmd });
      }
    } catch (e) {
      sendResponse({ ok: false, error: String(e && e.message || e) });
    }
    return true; // async-safe
  });
})();
