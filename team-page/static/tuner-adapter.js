/* Thin adapter so lucid-cove Tuner JS runs on this overlay.
   Do not add a new wizard or player here. */
(function () {
  if (typeof window.ESC !== "function") {
    window.ESC = function (s) {
      if (s == null) return "";
      return String(s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    };
  }
  window.esc = window.esc || window.ESC;
  window.formatDateOnly = window.formatDateOnly || function (iso) {
    if (!iso) return "";
    return String(iso).slice(0, 10);
  };
  window._buildVersion = window._buildVersion || "overlay";
  window.activeTab = window.activeTab || "tune";
  window.MC = window.MC || {
    isTuner: true,
    tier: { level: 10 },
    features: {},
    instance: { name: "Lucid Tuner" },
    tabs: [{ id: "home" }, { id: "tune" }, { id: "playlists" }, { id: "go-deeper" }],
  };
  window.showUpgradeModal = window.showUpgradeModal || function () {};
})();
