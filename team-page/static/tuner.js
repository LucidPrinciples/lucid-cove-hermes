(function () {
  function whichFromPath(pathname) {
    const path = (pathname || "/tune").replace(/\/$/, "") || "/tune";
    if (path === "/playlists") return "playlists";
    if (path === "/deeper") return "deeper";
    return "tune";
  }

  function showPanel(which, { load } = { load: true }) {
    document.querySelectorAll(".top-nav [data-nav]").forEach((a) => {
      a.classList.toggle("on", a.getAttribute("data-nav") === which);
    });
    document.querySelectorAll(".tuner-panel").forEach((el) => {
      el.hidden = el.id !== "panel-" + which;
    });
    window.activeTab = which;
    if (!load) return;
    if (which === "tune" && typeof loadTuneFlow === "function") {
      loadTuneFlow();
    } else if (which === "playlists" && typeof loadPlaylistsTab === "function") {
      loadPlaylistsTab();
    }
  }

  window.switchToTab = function (id) {
    const map = { tune: "/tune", playlists: "/playlists", "go-deeper": "/deeper" };
    const path = map[id];
    if (!path) return;
    const which = whichFromPath(path);
    if (location.pathname !== path) {
      history.pushState({ tuner: which }, "", path);
    }
    showPanel(which, { load: true });
  };

  document.querySelectorAll(".top-nav [data-nav]").forEach((a) => {
    a.addEventListener("click", function (e) {
      e.preventDefault();
      const id = a.getAttribute("data-nav");
      window.switchToTab(id === "deeper" ? "go-deeper" : id);
    });
  });

  window.addEventListener("popstate", function () {
    showPanel(whichFromPath(location.pathname), { load: true });
  });

  const badge = document.getElementById("freq-badge");
  const freqText = document.getElementById("freq-text");
  const overlay = document.getElementById("drop-overlay");
  const dropFrame = document.getElementById("drop-frame");
  const dropTitle = document.getElementById("drop-title");
  let dropPlayerUrl = "https://drop.lucidprinciples.com/";

  function openDrop() {
    if (dropFrame && (!dropFrame.src || dropFrame.src === "about:blank")) {
      dropFrame.src = dropPlayerUrl;
    }
    if (overlay) overlay.hidden = false;
    if (badge) badge.setAttribute("aria-expanded", "true");
  }
  function closeDrop() {
    if (overlay) overlay.hidden = true;
    if (badge) badge.setAttribute("aria-expanded", "false");
  }
  if (badge) badge.addEventListener("click", openDrop);
  const btnClose = document.getElementById("drop-close");
  if (btnClose) btnClose.addEventListener("click", closeDrop);
  if (overlay) {
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) closeDrop();
    });
  }
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && overlay && !overlay.hidden) closeDrop();
  });

  fetch("/api/team")
    .then((r) => r.json())
    .then((d) => {
      const freq = (d.drop && d.drop.frequency) || "Peace";
      if (freqText) freqText.textContent = freq;
      if (dropTitle) {
        dropTitle.textContent = "Tuning Hub · " + freq + (d.drop && d.drop.date ? " · " + d.drop.date : "");
      }
      if (d.drop && d.drop.player_url) dropPlayerUrl = d.drop.player_url;
      document.documentElement.setAttribute("data-frequency", freq);
      const colors = (d.drop && d.drop.colors) || {};
      if (colors.primary) {
        document.documentElement.style.setProperty("--freq-primary", colors.primary);
        document.documentElement.style.setProperty("--freq-secondary", colors.secondary || colors.primary);
        document.documentElement.style.setProperty("--freq-glow", colors.glow || "transparent");
        document.documentElement.style.setProperty("--daily-freq", colors.primary);
      }
    })
    .catch(() => {});

  showPanel(whichFromPath(location.pathname), { load: true });
})();
