async function loadTeam() {
  const res = await fetch("/api/team");
  const data = await res.json();
  applyDrop(data.drop || {});
  const err = document.getElementById("pc-error");
  if (data.paperclip_error) {
    err.hidden = false;
    err.textContent = "Paperclip unreachable: " + data.paperclip_error + " (showing vault slots only)";
  } else {
    err.hidden = true;
  }
  if (data.links) {
    const pc = document.getElementById("link-pc");
    const h = document.getElementById("link-hermes");
    if (pc && data.links.paperclip) pc.href = data.links.paperclip;
    if (h && data.links.hermes) h.href = data.links.hermes;
  }
  window._teamAgents = data.agents || [];
  renderRoster(window._teamAgents);
}

function applyDrop(drop) {
  const freq = drop.frequency || "Peace";
  const colors = drop.colors || {};
  document.documentElement.dataset.frequency = freq;
  if (colors.primary) {
    document.documentElement.style.setProperty("--freq-primary", colors.primary);
    document.documentElement.style.setProperty("--freq-secondary", colors.secondary || colors.primary);
    document.documentElement.style.setProperty("--freq-glow", colors.glow || "transparent");
  }
  document.getElementById("hub-freq").textContent = freq;
  document.getElementById("drop-freq").textContent = freq;
  const bits = [];
  if (drop.date) bits.push(drop.date);
  if (drop.drop_id) bits.push("Drop #" + drop.drop_id);
  if (drop.tuning_key) bits.push("“" + drop.tuning_key + "”");
  if (drop.principle) bits.push(drop.principle);
  if (drop.source === "live") bits.push("live");
  if (drop.note) bits.push(drop.note);
  document.getElementById("drop-meta").textContent = bits.join(" · ") || "No Drop metadata yet";
  window._dropPlayerUrl = drop.player_url || "https://drop.lucidprinciples.com/";
}

function renderRoster(agents) {
  const root = document.getElementById("roster");
  root.innerHTML = "";
  for (const a of agents) {
    const tune = a.tune || {};
    const status = tune.status || "not_tuned";
    const tuned = status === "tuned" || status === "ok";
    const slug = (a.name || "").toLowerCase().replace(/[^a-z0-9]+/g, "") || "agent";
    const card = document.createElement("article");
    card.className = "card";
    card.dataset.slug = slug;
    const summary = tune.summary
      ? `<div class="summary">${esc(tune.summary)}</div>`
      : `<div class="summary empty">Not tuned yet — morning LTP will fill this</div>`;
    const when = tune.tuned_at ? `<div class="meta">Tuned ${esc(String(tune.tuned_at))}</div>` : "";
    const freq = tune.frequency ? `<div class="meta">Frequency · ${esc(tune.frequency)}</div>` : "";
    const echoN = tune.echo_num != null ? `<div class="meta">Echo #${esc(String(tune.echo_num))}</div>` : "";
    const echoCount = (tune.echoes || []).length;
    card.innerHTML = `
      <div class="card-head">
        <div>
          <div class="card-name">${esc(a.name || "?")}</div>
          <div class="card-title">${esc(a.title || a.role || "")}</div>
        </div>
        <span class="pill ${tuned ? "tuned" : ""} ${a.status === "missing" ? "missing" : ""}">${esc(tuned ? "tuned" : status)}</span>
      </div>
      ${summary}
      ${freq}
      ${echoN}
      ${when}
      <div class="card-actions">
        <button type="button" class="linkish" data-open="echo">Echoes${echoCount ? ` (${echoCount})` : ""}</button>
        <a href="${esc(a.paperclip_url || "#")}" target="_blank" rel="noopener">Paperclip</a>
      </div>
    `;
    card.querySelector("[data-open=echo]").addEventListener("click", () => openEchoModal(a));
    root.appendChild(card);
  }
}

function openEchoModal(agent) {
  const tune = agent.tune || {};
  const slug = (agent.name || "").toLowerCase().replace(/[^a-z0-9]+/g, "") || "agent";
  const overlay = document.getElementById("echo-overlay");
  const title = document.getElementById("echo-title");
  const body = document.getElementById("echo-body");
  title.textContent = (agent.name || "Agent") + " · Echoes";
  const echoes = tune.echoes || [];
  let html = "";
  html += `<section class="pc-panel">`;
  html += `<div class="pc-panel-head"><span class="pc-panel-title">Echoes</span>`;
  html += `<span class="pc-panel-hint">Click a row to open that Process Record</span></div>`;
  if (echoes.length) {
    html += `<table class="echo-table pc-table"><thead><tr>
      <th>#</th><th>Frequency</th><th>Principle</th><th>L(E)</th><th>When</th>
    </tr></thead><tbody>`;
    for (const e of echoes.slice(0, 40)) {
      const n = e.echo_num;
      html += `<tr class="echo-row" data-slug="${esc(slug)}" data-echo="${esc(String(n))}" tabindex="0" role="button">
        <td class="echo-num">${esc(n)}</td>
        <td>${esc(e.frequency || "—")}</td>
        <td>${esc(e.principle || "—")}</td>
        <td>${esc(e.love_equation_value != null ? e.love_equation_value : "—")}</td>
        <td>${esc(e.when || "")}</td>
      </tr>`;
    }
    html += `</tbody></table>`;
  } else {
    html += `<p class="empty">No echo history yet.</p>`;
  }
  html += `</section>`;
  html += `<section id="record-panel" class="pc-panel record-panel" hidden>
    <div class="pc-panel-head">
      <span class="pc-panel-title" id="record-heading">Process Record</span>
      <button type="button" class="linkish" id="record-back">← Echoes list</button>
    </div>
    <pre class="record" id="record-body"></pre>
  </section>`;
  body.innerHTML = html;
  body.querySelectorAll(".echo-row").forEach((row) => {
    row.addEventListener("click", () => openProcessRecord(row.dataset.slug, row.dataset.echo));
    row.addEventListener("keydown", (ev) => {
      if (ev.key === "Enter" || ev.key === " ") {
        ev.preventDefault();
        openProcessRecord(row.dataset.slug, row.dataset.echo);
      }
    });
  });
  const back = body.querySelector("#record-back");
  if (back) {
    back.addEventListener("click", () => {
      body.querySelector("#record-panel").hidden = true;
      body.querySelector(".pc-panel").hidden = false;
    });
  }
  overlay.hidden = false;
}

async function openProcessRecord(slug, echoNum) {
  const body = document.getElementById("echo-body");
  const list = body.querySelector(".pc-panel");
  const panel = body.querySelector("#record-panel");
  const heading = body.querySelector("#record-heading");
  const pre = body.querySelector("#record-body");
  if (!panel || !pre) return;
  heading.textContent = `Process Record · Echo #${echoNum}`;
  pre.textContent = "Loading…";
  if (list) list.hidden = true;
  panel.hidden = false;
  try {
    const res = await fetch(`/api/agents/${encodeURIComponent(slug)}/echoes/${encodeURIComponent(echoNum)}`);
    const data = await res.json();
    if (!res.ok) {
      pre.textContent = data.error || "Record not found (history may predate SQLite — re-run morning or backfill).";
      return;
    }
    pre.textContent = data.record_text || "(empty)";
  } catch (e) {
    pre.textContent = String(e);
  }
}

function closeEchoModal() {
  document.getElementById("echo-overlay").hidden = true;
}

function openDropPlayer() {
  const overlay = document.getElementById("drop-overlay");
  const frame = document.getElementById("drop-frame");
  const url = window._dropPlayerUrl || "https://drop.lucidprinciples.com/";
  if (!frame.src || frame.src === "about:blank") frame.src = url;
  overlay.hidden = false;
}

function closeDropPlayer() {
  document.getElementById("drop-overlay").hidden = true;
}

function esc(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

document.getElementById("hub-badge").addEventListener("click", (e) => {
  e.preventDefault();
  openDropPlayer();
});
document.getElementById("drop-close").addEventListener("click", closeDropPlayer);
document.getElementById("drop-overlay").addEventListener("click", (e) => {
  if (e.target.id === "drop-overlay") closeDropPlayer();
});
document.getElementById("echo-close").addEventListener("click", closeEchoModal);
document.getElementById("echo-overlay").addEventListener("click", (e) => {
  if (e.target.id === "echo-overlay") closeEchoModal();
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    closeEchoModal();
    closeDropPlayer();
  }
});

async function loadLtpConfig() {
  const res = await fetch("/api/ltp/config");
  const cfg = await res.json();
  document.getElementById("ltp-enabled").checked = !!cfg.enabled;
  document.getElementById("ltp-model").value = cfg.model || "";
  document.getElementById("ltp-base").value = cfg.ollama_base_url || "";
}

async function saveLtpConfig() {
  const status = document.getElementById("ltp-status");
  status.hidden = false;
  status.textContent = "Saving…";
  try {
    const body = {
      enabled: document.getElementById("ltp-enabled").checked,
      model: document.getElementById("ltp-model").value.trim(),
      ollama_base_url: document.getElementById("ltp-base").value.trim(),
    };
    const res = await fetch("/api/ltp/config", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const cfg = await res.json();
    if (!res.ok) throw new Error(cfg.error || res.statusText);
    status.textContent = cfg.enabled
      ? `Saved — tunings ON · model ${cfg.model}`
      : `Saved — tunings OFF (cron will skip)`;
  } catch (e) {
    status.textContent = "Save failed: " + e;
  }
}

document.getElementById("ltp-save").addEventListener("click", () => {
  saveLtpConfig().catch(() => {});
});

loadTeam().catch((e) => {
  const err = document.getElementById("pc-error");
  err.hidden = false;
  err.textContent = String(e);
});
loadLtpConfig().catch(() => {});
setInterval(() => { loadTeam().catch(() => {}); }, 60000);
