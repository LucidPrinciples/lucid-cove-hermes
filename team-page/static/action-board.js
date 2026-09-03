/* Action Board — Lucid Cove on Hermes (Cove-shaped tabs + tool cards) */

const TOOLS = [
  {
    id: "jules",
    name: "Jules",
    agent: "Jules",
    agent_color: "var(--freq-primary)",
    description:
      "Voice capture — talk, then save to stewart Nextcloud Inbox. Backlog may become tickets; Hold waits for discussion.",
    status: "active",
    href: "/jules",
  },
];

function esc(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderTools() {
  const container = document.getElementById("ab-tools-list");
  if (!container) return;
  container.innerHTML = TOOLS.map((tool) => {
    const statusClass = tool.status === "active" ? "tool-active" : "tool-placeholder";
    const status =
      tool.status === "active"
        ? '<span class="ab-tool-status-active">Active</span>'
        : '<span class="ab-tool-status-soon">Coming soon</span>';
    return `
      <div class="ab-tool-card ${statusClass}" role="button" tabindex="0"
           data-href="${esc(tool.href || "#")}"
           style="--tool-agent-color: ${tool.agent_color || "var(--freq-primary)"}">
        <div class="ab-tool-header">
          <h3>${esc(tool.name)}</h3>
          <span class="ab-tool-agent">${esc(tool.agent)}</span>
        </div>
        <p class="ab-tool-desc">${esc(tool.description)}</p>
        <div class="ab-tool-meta">${status}</div>
      </div>`;
  }).join("");

  container.querySelectorAll(".ab-tool-card").forEach((card) => {
    const go = () => {
      const href = card.getAttribute("data-href");
      if (href && href !== "#") window.location.href = href;
    };
    card.addEventListener("click", go);
    card.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        go();
      }
    });
  });
}

function showTab(id) {
  document.querySelectorAll(".ab-act-tab").forEach((t) => {
    t.classList.toggle("active", t.dataset.tab === id);
  });
  ["actions", "links", "flows", "tools"].forEach((name) => {
    const panel = document.getElementById("panel-" + name);
    if (panel) panel.hidden = name !== id;
  });
  try {
    localStorage.setItem("lch-ab-tab", id);
  } catch (_) {}
}

document.querySelectorAll(".ab-act-tab").forEach((btn) => {
  btn.addEventListener("click", () => showTab(btn.dataset.tab));
});

let start = "tools";
try {
  start = localStorage.getItem("lch-ab-tab") || "tools";
} catch (_) {}
showTab(start);
renderTools();

fetch("/api/tools")
  .then((r) => r.json())
  .then((d) => {
    if (d.frequency) {
      document.getElementById("hub-freq").textContent = d.frequency;
      document.documentElement.dataset.frequency = d.frequency;
    }
  })
  .catch(() => {});
