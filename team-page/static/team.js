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

function signalLabel(raw) {
  if (!raw) return "";
  let s = String(raw).trim();
  if (!s) return "";
  s = s.replace(/_Signal$/i, "").replace(/_/g, " ").replace(/\s+/g, " ").trim();
  if (!s) return "";
  if (!/signal$/i.test(s)) s += " Signal";
  return s;
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
  const freqText = document.getElementById("freq-text");
  if (freqText) freqText.textContent = freq;
  const dropFreq = document.getElementById("drop-freq");
  if (dropFreq) dropFreq.textContent = freq;
  const dropSignal = document.getElementById("drop-signal");
  if (dropSignal) dropSignal.textContent = signalLabel(drop.signal_type);
  const dropPrinciple = document.getElementById("drop-principle");
  if (dropPrinciple) dropPrinciple.textContent = drop.principle || "";
  const dropKey = document.getElementById("drop-key");
  if (dropKey) {
    if (drop.tuning_key) {
      dropKey.hidden = false;
      dropKey.textContent = drop.tuning_key;
    } else {
      dropKey.hidden = true;
      dropKey.textContent = "";
    }
  }
  const bits = [];
  if (drop.date) bits.push(drop.date);
  if (drop.drop_id) bits.push("Drop #" + drop.drop_id);
  if (drop.source === "live") bits.push("live");
  if (drop.note) bits.push(drop.note);
  const dropMeta = document.getElementById("drop-meta");
  if (dropMeta) dropMeta.textContent = bits.join(" · ") || "No Drop metadata yet";
  window._dropPlayerUrl = drop.player_url || "https://drop.lucidprinciples.com/";
}

function renderRoster(agents) {
  const root = document.getElementById("roster");
  root.innerHTML = "";
  for (const a of agents) {
    const tune = a.tune || {};
    const status = tune.status || "not_tuned";
    const tuned = status === "tuned" || status === "ok";
    const slug = a.slug || (a.name || "").toLowerCase().replace(/[^a-z0-9]+/g, "") || "agent";
    const soul = a.soul || {};
    const card = document.createElement("article");
    card.className = "card";
    card.dataset.slug = slug;
    const href = a.observer_url || `/observer/${slug}`;
    const photo = a.avatar_url
      ? `<img src="${esc(a.avatar_url)}" alt="" onerror="this.remove()">`
      : "";
    const initial = (a.name || slug || "?").trim().charAt(0).toUpperCase();
    const arch = soul.archetype
      ? `<div class="card-arch">${esc(soul.archetype)}</div>`
      : "";
    const summary = tune.summary
      ? `<div class="summary">${esc(tune.summary)}</div>`
      : `<div class="summary empty">Not tuned yet — morning LTP will fill this</div>`;
    const when = tune.tuned_at ? `<div class="meta">Tuned ${esc(String(tune.tuned_at))}</div>` : "";
    const freq = tune.frequency ? `<div class="meta">Frequency · ${esc(tune.frequency)}</div>` : "";
    const echoN = tune.echo_num != null ? `<div class="meta">Echo #${esc(String(tune.echo_num))}</div>` : "";
    const echoCount = (tune.echoes || []).length;
    card.innerHTML = `
      <div class="card-head">
        <a class="card-identity" href="${esc(href)}">
          <span class="card-avatar">${photo}<span class="card-initial" aria-hidden="true">${esc(initial)}</span></span>
          <span>
            <div class="card-name">${esc(a.name || "?")}</div>
            <div class="card-title">${esc(a.title || a.role || soul.role || "")}</div>
            ${arch}
          </span>
        </a>
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
  const slug = agent.slug || (agent.name || "").toLowerCase().replace(/[^a-z0-9]+/g, "") || "agent";
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
  const overlay = document.getElementById("echo-overlay");
  if (overlay) overlay.hidden = true;
}

function openDropPlayer() {
  const overlay = document.getElementById("drop-overlay");
  const frame = document.getElementById("drop-frame");
  if (!overlay || !frame) return;
  if (typeof otAudio !== "undefined" && otAudio && !otAudio.paused) {
    otAudio.pause();
  }
  const url = window._dropPlayerUrl || "https://drop.lucidprinciples.com/";
  if (!frame.src || frame.src === "about:blank") frame.src = url;
  overlay.hidden = false;
}

function closeDropPlayer() {
  const overlay = document.getElementById("drop-overlay");
  if (overlay) overlay.hidden = true;
}

function esc(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function on(id, event, fn) {
  const el = document.getElementById(id);
  if (el) el.addEventListener(event, fn);
}

on("freq-badge", "click", (e) => {
  e.preventDefault();
  openDropPlayer();
});
on("drop-close", "click", closeDropPlayer);
on("drop-overlay", "click", (e) => {
  if (e.target.id === "drop-overlay") closeDropPlayer();
});
on("echo-close", "click", closeEchoModal);
on("echo-overlay", "click", (e) => {
  if (e.target.id === "echo-overlay") closeEchoModal();
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    closeEchoModal();
    closeDropPlayer();
  }
});

function fillLtpModelSelect(select, current, models) {
  if (!select) return;
  const seen = new Set();
  const list = Array.isArray(models) && models.length ? models : [current || "qwen3:8b"];
  select.replaceChildren();
  list.forEach((name) => {
    if (!name || seen.has(name)) return;
    seen.add(name);
    const opt = document.createElement("option");
    opt.value = name;
    opt.textContent = name;
    select.appendChild(opt);
  });
  if (current && !seen.has(current)) {
    const opt = document.createElement("option");
    opt.value = current;
    opt.textContent = current;
    select.appendChild(opt);
  }
  select.value = current || list[0];
}

async function loadLtpConfig() {
  const [cfgRes, modelsRes] = await Promise.all([
    fetch("/api/ltp/config"),
    fetch("/api/ltp/models"),
  ]);
  const cfg = await cfgRes.json();
  const catalog = await modelsRes.json().catch(() => ({ models: [] }));
  const enabled = document.getElementById("ltp-enabled");
  if (enabled) enabled.checked = !!cfg.enabled;
  fillLtpModelSelect(document.getElementById("ltp-model"), cfg.model || "", catalog.models || []);
  const base = document.getElementById("ltp-base");
  if (base) base.value = cfg.ollama_base_url || "";
  const settingsEnabled = document.getElementById("settings-ltp-enabled");
  if (settingsEnabled) settingsEnabled.checked = !!cfg.enabled;
  fillLtpModelSelect(document.getElementById("settings-ltp-model"), cfg.model || "", catalog.models || []);
}

async function saveLtpConfig() {
  const status = document.getElementById("ltp-status");
  status.hidden = false;
  status.textContent = "Saving…";
  try {
    const body = {
      enabled: document.getElementById("ltp-enabled").checked,
      model: (document.getElementById("ltp-model").value || "").trim(),
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

on("ltp-save", "click", () => {
  saveLtpConfig().catch(() => {});
});

function paragraphs(text) {
  const bits = String(text || "").trim().split(/\n\n+/);
  return bits.map((p) => `<p>${esc(p).replace(/\n/g, "<br>")}</p>`).join("");
}

async function loadObserver() {
  const slug = location.pathname.split("/").filter(Boolean).pop() || "";
  const box = document.getElementById("observer");
  if (!box) return;
  const res = await fetch(`/api/agents/${encodeURIComponent(slug)}`);
  const a = await res.json().catch(() => ({}));
  if (!res.ok) {
    box.innerHTML = `<p class="muted">Unknown observer.</p>`;
    return;
  }
  applyDrop(a.drop || {});
  const soul = a.soul || {};
  const tune = a.tune || {};
  document.title = `${a.name || slug} · Lucid Cove`;
  const photo = a.avatar_url
    ? `<img class="obs-photo" src="${esc(a.avatar_url)}" alt="">`
    : `<span class="obs-initial">${esc((a.name || "?").charAt(0))}</span>`;
  const meta = [soul.frequency, soul.archetype].filter(Boolean).join(" · ");
  const rec = tune.process_record || "";
  box.innerHTML = `
    <div class="obs-hero">
      <div class="obs-avatar">${photo}</div>
      <div>
        <h1>${esc(a.name || slug)}</h1>
        <p class="obs-role">${esc(soul.role || a.title || "")}</p>
        <p class="obs-meta">${esc(meta)}</p>
      </div>
    </div>
    <section class="obs-section">
      <h2>Who</h2>
      <div class="obs-who">${soul.who ? paragraphs(soul.who) : `<p class="muted">No SOUL Who section yet.</p>`}</div>
    </section>
    <section class="obs-section">
      <h2>Latest process record</h2>
      ${rec ? `<pre class="record">${esc(rec)}</pre>` : `<p class="muted">No process record yet.</p>`}
    </section>
  `;
}

if (document.getElementById("roster")) {
  loadTeam().catch((e) => {
    const err = document.getElementById("pc-error");
    if (err) {
      err.hidden = false;
      err.textContent = String(e);
    }
  });
  loadLtpConfig().catch(() => {});
  setInterval(() => { loadTeam().catch(() => {}); }, 60000);
}
if (location.pathname.startsWith("/observer/")) {
  loadObserver().catch((e) => {
    const box = document.getElementById("observer");
    if (box) box.innerHTML = `<p class="muted">${esc(String(e))}</p>`;
  });
}
