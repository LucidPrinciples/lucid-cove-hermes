const DROP_PLAYER_URL = "https://drop.lucidprinciples.com";

const badge = document.getElementById("freq-badge");
const freqText = document.getElementById("freq-text");
const overlay = document.getElementById("drop-overlay");
const dropFrame = document.getElementById("drop-frame");
const dropTitle = document.getElementById("drop-title");
const pcFrame = document.getElementById("pc-frame");
const pcEmbed = document.getElementById("pc-embed");
const pcEmpty = document.getElementById("pc-empty");
const btnClose = document.getElementById("drop-close");

const houseShell = document.getElementById("house-shell");
const actionPane = document.getElementById("action-pane");
const switchLinks = document.querySelectorAll(".board-switch a");

let attentionLoaded = false;

function hideAttentionEmbed(hidden) {
  if (pcEmbed) pcEmbed.hidden = hidden;
  else if (pcFrame) pcFrame.hidden = hidden;
}

async function loadAttention() {
  if (!pcFrame || attentionLoaded) return;
  try {
    const res = await fetch("/api/attention", { credentials: "same-origin" });
    const data = await res.json().catch(() => ({}));
    const source = data && data.source;
    const url = (data && data.url) || "";
    if (pcEmbed) pcEmbed.classList.toggle("pc-embed--hermes", source === "hermes");
    if (source === "none" || !url) {
      pcFrame.removeAttribute("src");
      pcFrame.hidden = true;
      if (pcEmpty) pcEmpty.hidden = false;
      pcFrame.title = "Attention";
      return;
    }
    if (pcEmpty) pcEmpty.hidden = true;
    pcFrame.hidden = false;
    pcFrame.title = (data && data.title) || "Attention";
    pcFrame.src = url;
    attentionLoaded = true;
  } catch (_) {
    if (pcEmbed) pcEmbed.classList.remove("pc-embed--hermes");
    pcFrame.removeAttribute("src");
    pcFrame.hidden = true;
    if (pcEmpty) pcEmpty.hidden = false;
  }
}

function isActionPath(pathname) {
  const path = pathname || location.pathname;
  return path === "/tools" || path.startsWith("/tools/");
}

function showBoard(action, push) {
  const actionOn = !!action;
  hideAttentionEmbed(actionOn);
  if (actionPane) actionPane.hidden = !actionOn;
  switchLinks.forEach((a) => {
    const href = a.getAttribute("href") || "";
    const isActionLink = href.startsWith("/tools");
    a.classList.toggle("on", actionOn ? isActionLink : !isActionLink);
  });
  document.title = actionOn
    ? "Action Board — Lucid Cove on Hermes"
    : "Lucid Principles — Attention";
  if (push) {
    const url = actionOn ? "/tools?tab=actions" : "/work";
    history.pushState({ action: actionOn }, "", url);
  }
  if (actionOn && typeof showTab === "function") {
    const tab = new URLSearchParams(location.search).get("tab");
    if (tab) showTab(tab);
  }
  if (!actionOn) loadAttention();
}

if (!houseShell) {
  switchLinks.forEach((a) => {
    a.addEventListener("click", (e) => {
      const href = a.getAttribute("href") || "";
      if (!href.startsWith("/work") && !href.startsWith("/tools")) return;
      e.preventDefault();
      showBoard(href.startsWith("/tools"), true);
    });
  });

  window.addEventListener("popstate", () => {
    showBoard(isActionPath(), false);
  });

  showBoard(isActionPath(), false);
}

function applyFreq(drop) {
  const freq = drop.frequency || "Peace";
  const colors = drop.colors || {};
  document.documentElement.dataset.frequency = freq;
  freqText.textContent = freq;
  dropTitle.textContent = freq + (drop.date ? " · " + drop.date : "");
  if (colors.primary) {
    document.documentElement.style.setProperty("--freq-primary", colors.primary);
    document.documentElement.style.setProperty("--freq-secondary", colors.secondary || colors.primary);
    document.documentElement.style.setProperty("--freq-glow", colors.glow || "transparent");
  }
}

async function refreshDrop() {
  try {
    const res = await fetch("/api/team");
    const data = await res.json();
    applyFreq(data.drop || {});
  } catch (e) {
    console.warn("drop refresh failed", e);
  }
}

function openDrop() {
  if (!dropFrame.src || dropFrame.src === "about:blank") {
    dropFrame.src = DROP_PLAYER_URL;
  }
  overlay.hidden = false;
  badge.setAttribute("aria-expanded", "true");
}

function closeDrop() {
  overlay.hidden = true;
  badge.setAttribute("aria-expanded", "false");
}

if (!houseShell) {
  if (badge) badge.addEventListener("click", openDrop);
  if (btnClose) btnClose.addEventListener("click", closeDrop);
  if (overlay) {
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) closeDrop();
    });
  }
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && overlay && !overlay.hidden) closeDrop();
  });
  refreshDrop();
  setInterval(refreshDrop, 60000);
}
