const DROP_PLAYER_URL = "https://drop.lucidprinciples.com";
const PAPERCLIP_URL = (window.LCH_PAPERCLIP_URL || "http://127.0.0.1:3100");

const badge = document.getElementById("freq-badge");
const freqText = document.getElementById("freq-text");
const overlay = document.getElementById("drop-overlay");
const dropFrame = document.getElementById("drop-frame");
const dropTitle = document.getElementById("drop-title");
const pcFrame = document.getElementById("pc-frame");
const btnClose = document.getElementById("drop-close");

pcFrame.src = PAPERCLIP_URL;

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

badge.addEventListener("click", openDrop);
btnClose.addEventListener("click", closeDrop);
overlay.addEventListener("click", (e) => {
  if (e.target === overlay) closeDrop();
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && !overlay.hidden) closeDrop();
});

refreshDrop();
setInterval(refreshDrop, 60000);
