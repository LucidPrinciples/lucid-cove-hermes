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

function formatVaultMarkdown(src) {
  const raw = String(src ?? "").replace(/\r\n/g, "\n");
  const inline = (s) => {
    let t = esc(s);
    t = t.replace(/`([^`]+)`/g, "<code>$1</code>");
    t = t.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    t = t.replace(
      /\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g,
      '<a href="$2" target="_blank" rel="noopener">$1</a>',
    );
    return t;
  };
  const lines = raw.split("\n");
  const out = [];
  let i = 0;
  const flushPara = (buf) => {
    const text = buf.join(" ").trim();
    if (text) out.push("<p>" + inline(text) + "</p>");
    buf.length = 0;
  };
  while (i < lines.length) {
    const line = lines[i];
    if (!line.trim()) {
      i += 1;
      continue;
    }
    if (/^```/.test(line)) {
      const buf = [];
      i += 1;
      while (i < lines.length && !/^```/.test(lines[i])) {
        buf.push(esc(lines[i]));
        i += 1;
      }
      if (i < lines.length) i += 1;
      out.push("<pre><code>" + buf.join("\n") + "</code></pre>");
      continue;
    }
    if (/^---+$/.test(line.trim())) {
      out.push("<hr>");
      i += 1;
      continue;
    }
    const heading = /^(#{1,3})\s+(.*)$/.exec(line);
    if (heading) {
      const n = heading[1].length;
      out.push("<h" + n + ">" + inline(heading[2]) + "</h" + n + ">");
      i += 1;
      continue;
    }
    if (line.startsWith("> ")) {
      const buf = [];
      while (i < lines.length && lines[i].startsWith("> ")) {
        buf.push(lines[i].slice(2));
        i += 1;
      }
      out.push("<blockquote>" + inline(buf.join(" ")) + "</blockquote>");
      continue;
    }
    if (line.startsWith("|")) {
      const rows = [];
      while (i < lines.length && lines[i].startsWith("|")) {
        rows.push(lines[i]);
        i += 1;
      }
      const cells = (row) =>
        row
          .replace(/^\|/, "")
          .replace(/\|$/, "")
          .split("|")
          .map((c) => c.trim());
      const isSep = (row) => /^\s*\|?\s*:?-{3,}/.test(row);
      let html = "<table>";
      rows.forEach((row, idx) => {
        if (isSep(row)) return;
        const tag = idx === 0 ? "th" : "td";
        html +=
          "<tr>" +
          cells(row)
            .map((c) => "<" + tag + ">" + inline(c) + "</" + tag + ">")
            .join("") +
          "</tr>";
      });
      html += "</table>";
      out.push(html);
      continue;
    }
    if (/^[-*]\s+/.test(line)) {
      out.push("<ul>");
      while (i < lines.length && /^[-*]\s+/.test(lines[i])) {
        out.push("<li>" + inline(lines[i].replace(/^[-*]\s+/, "")) + "</li>");
        i += 1;
      }
      out.push("</ul>");
      continue;
    }
    if (/^\d+\.\s+/.test(line)) {
      out.push("<ol>");
      while (i < lines.length && /^\d+\.\s+/.test(lines[i])) {
        out.push("<li>" + inline(lines[i].replace(/^\d+\.\s+/, "")) + "</li>");
        i += 1;
      }
      out.push("</ol>");
      continue;
    }
    const para = [];
    while (
      i < lines.length &&
      lines[i].trim() &&
      !/^#{1,3}\s/.test(lines[i]) &&
      !/^[-*]\s+/.test(lines[i]) &&
      !/^\d+\.\s+/.test(lines[i]) &&
      !lines[i].startsWith("|") &&
      !lines[i].startsWith("> ") &&
      !/^```/.test(lines[i]) &&
      !/^---+$/.test(lines[i].trim())
    ) {
      para.push(lines[i]);
      i += 1;
    }
    flushPara(para);
  }
  return out.join("");
}

function ensureBriefDrawer() {
  if (document.getElementById("ab-brief-overlay")) return;
  const overlay = document.createElement("div");
  overlay.id = "ab-brief-overlay";
  overlay.className = "ab-brief-overlay";
  overlay.hidden = true;
  overlay.innerHTML = `
    <div class="ab-brief-panel" role="dialog" aria-modal="true" aria-labelledby="ab-brief-title">
      <header class="ab-brief-head">
        <div>
          <h3 id="ab-brief-title"></h3>
          <p class="ab-brief-path" id="ab-brief-path"></p>
        </div>
        <button type="button" class="ab-brief-close" id="ab-brief-close" aria-label="Close">× Close</button>
      </header>
      <article class="ab-brief-body md-prose" id="ab-brief-body"></article>
    </div>`;
  document.body.appendChild(overlay);
  const close = () => {
    overlay.hidden = true;
  };
  overlay.querySelector("#ab-brief-close").addEventListener("click", close);
  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) close();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !overlay.hidden) close();
  });
}

function openBrief(id) {
  ensureBriefDrawer();
  const overlay = document.getElementById("ab-brief-overlay");
  const title = document.getElementById("ab-brief-title");
  const pathEl = document.getElementById("ab-brief-path");
  const body = document.getElementById("ab-brief-body");
  title.textContent = "Loading…";
  pathEl.textContent = "";
  body.textContent = "";
  overlay.hidden = false;
  fetch("/api/links/" + encodeURIComponent(id))
    .then((r) => r.json())
    .then((d) => {
      title.textContent = d.title || id;
      pathEl.textContent = d.exists
        ? "vault/" + (d.relpath || "")
        : "Missing on house vault — vault/" + (d.relpath || "");
      if (d.exists) {
        body.innerHTML = formatVaultMarkdown(d.markdown || "");
      } else {
        body.innerHTML =
          "<p>This watch card is wired. The markdown is not on the house vault yet, so there is nothing to compare.</p>";
      }
    })
    .catch(() => {
      title.textContent = "Could not load";
      body.innerHTML = "<p>Links watch request failed.</p>";
    });
}

function loadLinks() {
  fetch("/api/links")
    .then((r) => r.json())
    .then((d) => renderLinks(d.links || []))
    .catch(() => renderLinks([]));
}

function renderLinks(links) {
  const container = document.getElementById("ab-links-list");
  if (!container) return;
  if (!links || !links.length) {
    container.innerHTML = '<div class="ab-empty">No links yet — create them from Actions.</div>';
    return;
  }
  container.innerHTML = links
    .map((link) => {
      if (link.href) {
        const title = link.id === "open-lucid-tuner" ? (link.title || "Open Lucid Tuner") : (link.title || "");
        const extTarget = window === window.top ? "_blank" : "_self";
        return `
      <a class="ab-tool-card" href="${esc(link.href)}" target="${extTarget}" rel="noopener noreferrer"
           style="--tool-agent-color: var(--freq-primary)">
        <div class="ab-tool-header">
          <h3>${esc(title)}</h3>
          <span class="ab-tool-agent">${esc(link.agent || "")}</span>
        </div>
        <p class="ab-tool-desc">${esc(link.description || "")}</p>
        <div class="ab-tool-meta"><span class="ab-tool-status-active">Open</span></div>
      </a>`;
      }
      const status = link.exists
        ? '<span class="ab-tool-status-active">On vault</span>'
        : '<span class="ab-tool-status-missing">Missing on vault</span>';
      return `
      <div class="ab-tool-card" role="button" tabindex="0" data-link-id="${esc(link.id)}"
           style="--tool-agent-color: var(--freq-primary)">
        <div class="ab-tool-header">
          <h3>${esc(link.title)}</h3>
          <span class="ab-tool-agent">${esc(link.agent)}</span>
        </div>
        <p class="ab-tool-desc">${esc(link.description)}</p>
        <p class="ab-link-path">vault/${esc(link.relpath)}</p>
        <div class="ab-tool-meta">${status}</div>
      </div>`;
    })
    .join("");
  container.querySelectorAll(".ab-tool-card").forEach((card) => {
    if (card.tagName === "A") return;
    const go = () => {
      openBrief(card.getAttribute("data-link-id"));
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

function actionCard(action) {
  const href = "https://app.lucidtuner.com";
  if (action.id === "connect-lucid-tuner") {
    return `
    <article class="ab-tool-card" id="ab-action-connect" data-action="connect-tuner">
      <div class="ab-tool-header">
        <h3>Connect Lucid Tuner</h3>
      </div>
      <p class="ab-tool-desc">Create a Lucid Tuner account (or sign in), then paste the connect key in Gear. This overlay does not create the account.</p>
      <ol class="ab-action-steps">
        <li>Open <a href="${href}" target="_blank" rel="noopener">app.lucidtuner.com</a></li>
        <li>Settings → <strong>Get my connect key</strong> (shown once)</li>
        <li>Paste it in <strong>Gear</strong> on this house</li>
      </ol>
      <p class="ab-tool-meta"><a href="${href}" target="_blank" rel="noopener">Create account or sign in</a></p>
    </article>`;
  }
  if (action.id === "create-goals-brief") {
    return `
    <article class="ab-tool-card" id="ab-action-goals-brief" data-action="create-goals-brief">
      <div class="ab-tool-header">
        <h3>Create Goals Brief</h3>
      </div>
      <p class="ab-tool-desc">Write the standing goals for this house. Once the brief exists, it leaves Action and lives on Links.</p>
      <p class="ab-tool-meta"><button type="button" class="ab-action-create" data-create-brief>Create brief</button></p>
    </article>`;
  }
  return `
    <article class="ab-tool-card" data-action="${esc(action.id)}">
      <div class="ab-tool-header">
        <h3>${esc(action.title || action.id)}</h3>
      </div>
      <p class="ab-tool-desc">${esc(action.description || "")}</p>
    </article>`;
}

function paintActionLists(root, data) {
  const standing = data.standing || [];
  const daily = data.daily || [];
  const standingBody = standing.length
    ? standing.map(actionCard).join("")
    : '<div class="ab-empty">No standing actions.</div>';
  const dailyBody = daily.length
    ? daily.map(actionCard).join("")
    : '<div class="ab-empty">No daily actions yet.</div>';
  root.innerHTML = `
    <section class="ab-action-kind" data-kind="standing">
      <h3 class="ab-action-kind-title">Standing</h3>
      ${standingBody}
    </section>
    <section class="ab-action-kind" data-kind="daily">
      <h3 class="ab-action-kind-title">Daily</h3>
      ${dailyBody}
    </section>`;
  root.querySelectorAll("[data-create-brief]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      fetch("/api/actions/goals-brief", { method: "POST", credentials: "same-origin" })
        .then(() => {
          paintActions();
          loadLinks();
        })
        .catch(() => {});
    });
  });
}

function paintActions() {
  const root = document.getElementById("ab-actions-list");
  if (!root) return;
  fetch("/api/actions")
    .then((r) => r.json())
    .then((d) => paintActionLists(root, d || {}))
    .catch(() => paintActionLists(root, { standing: [], daily: [] }));
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

const AB_TABS = ["actions", "links", "flows", "tools"];

function tabFromUrl() {
  try {
    const q = new URLSearchParams(location.search).get("tab");
    if (q && AB_TABS.includes(q)) return q;
  } catch (_) {}
  const h = (location.hash || "").replace(/^#/, "");
  if (h && AB_TABS.includes(h)) return h;
  return null;
}

let stored = "tools";
try {
  stored = localStorage.getItem("lch-ab-tab") || "tools";
} catch (_) {}
if (!AB_TABS.includes(stored)) stored = "tools";
const start = tabFromUrl() || stored;
showTab(start);
paintActions();
renderTools();
ensureBriefDrawer();
loadLinks();

fetch("/api/tools")
  .then((r) => r.json())
  .then((d) => {
    if (d.frequency) {
      const freqText = document.getElementById("freq-text");
      if (freqText) freqText.textContent = d.frequency;
      document.documentElement.dataset.frequency = d.frequency;
    }
  })
  .catch(() => {});

if (!document.getElementById("pc-frame")) {
  let dropPlayerUrl = "https://drop.lucidprinciples.com/";
  fetch("/api/team")
    .then((r) => r.json())
    .then((d) => {
      if (d.drop && d.drop.player_url) dropPlayerUrl = d.drop.player_url;
    })
    .catch(() => {});

  function openDropPlayer() {
    const overlay = document.getElementById("drop-overlay");
    const frame = document.getElementById("drop-frame");
    if (!overlay || !frame) return;
    if (!frame.src || frame.src === "about:blank") frame.src = dropPlayerUrl;
    overlay.hidden = false;
  }

  function closeDropPlayer() {
    const overlay = document.getElementById("drop-overlay");
    if (overlay) overlay.hidden = true;
  }

  const freqBadge = document.getElementById("freq-badge");
  if (freqBadge) freqBadge.addEventListener("click", openDropPlayer);
  const dropClose = document.getElementById("drop-close");
  if (dropClose) dropClose.addEventListener("click", closeDropPlayer);
  const dropOverlay = document.getElementById("drop-overlay");
  if (dropOverlay) {
    dropOverlay.addEventListener("click", (e) => {
      if (e.target.id === "drop-overlay") closeDropPlayer();
    });
  }
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeDropPlayer();
  });
}
