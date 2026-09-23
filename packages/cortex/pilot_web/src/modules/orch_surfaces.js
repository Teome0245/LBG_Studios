/** Surfaces Orch absorbées — #/agents/map, #/providers, panneau LyraEngine sur #/lyra. */

function getBase() {
  const App = globalThis.PilotApp;
  if (App && typeof App.getBase === "function") {
    return App.getBase();
  }
  const el = document.getElementById("api-base");
  const fromInput = el && el.value ? String(el.value).trim().replace(/\/$/, "") : "";
  if (fromInput) return fromInput;
  try {
    return String(window.location.origin || "").replace(/\/$/, "") || "http://127.0.0.1:8000";
  } catch (_) {
    return "http://127.0.0.1:8000";
  }
}

function esc(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

async function orchGet(path) {
  const r = await fetch(getBase() + "/v1/pilot/orch" + path);
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error((j && (j.error || j.detail)) || "HTTP " + r.status);
  if (j && j.disabled === true) throw new Error(j.detail || "Proxies Orch désactivés (LBG_ORCH_UI_API_URL)");
  if (j && j.ok === false) throw new Error(j.error || j.detail || "orch ok:false");
  return j;
}

async function orchPost(path, body) {
  const r = await fetch(getBase() + "/v1/pilot/orch" + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error((j && (j.error || j.detail)) || "HTTP " + r.status);
  if (j && j.ok === false) throw new Error(j.error || j.detail || "orch ok:false");
  return j;
}

function setText(id, msg, isError) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = msg || "—";
  el.style.color = isError ? "#a30" : "";
}

function statusClass(st) {
  const s = String(st || "").toLowerCase();
  if (s === "ok" || s === "up" || s === "ready" || s === "online") return "orch-pill--ok";
  if (s === "error" || s === "down" || s === "offline" || s === "fail") return "orch-pill--err";
  return "orch-pill--muted";
}

/* ---------- Agents map ---------- */

function renderAgentsMap(data) {
  const meta = document.getElementById("orch-agents-meta");
  const list = document.getElementById("orch-agents-list");
  const raw = document.getElementById("orch-agents-raw");
  if (raw) raw.textContent = JSON.stringify(data, null, 2);

  const agents = Array.isArray(data && data.agents) ? data.agents : [];
  const routing = (data && data.devops_routing) || {};
  const cortex = (data && data.cortex_team) || {};
  if (meta) {
    meta.innerHTML =
      '<span class="orch-pill ' +
      statusClass(cortex.pilot_synced ? "ok" : "muted") +
      '">env ' +
      esc(data.env_scope || "?") +
      "</span>" +
      '<span class="muted">' +
      esc(routing.label || routing.mode || "") +
      "</span>" +
      '<span class="muted">' +
      agents.length +
      " agents · " +
      esc(String(cortex.orch_capability_count ?? "—")) +
      " caps orch</span>";
  }
  if (!list) return;
  if (!agents.length) {
    list.innerHTML = '<p class="muted">Aucun agent.</p>';
    return;
  }
  list.innerHTML = agents
    .map(function (a) {
      const id = a.id || a.name || "?";
      const label = a.label || id;
      const st = a.team_status || a.status || (a.registered ? "registered" : "—");
      const url = a.base_url || "";
      const src = a.source || a.kind || "";
      const caps = a.capability_count != null ? a.capability_count + " cap" : "";
      return (
        '<article class="orch-card">' +
        '<header><strong>' +
        esc(label) +
        '</strong> <span class="orch-pill ' +
        statusClass(st) +
        '">' +
        esc(st) +
        "</span></header>" +
        '<p class="muted orch-card-id"><code>' +
        esc(id) +
        "</code> · " +
        esc(src) +
        (caps ? " · " + esc(caps) : "") +
        "</p>" +
        (a.description
          ? '<p class="orch-card-desc">' + esc(String(a.description).slice(0, 180)) + "</p>"
          : "") +
        (url ? '<p class="muted"><code>' + esc(url) + "</code></p>" : "") +
        "</article>"
      );
    })
    .join("");
}

export async function orchAgentsMapBind() {
  setText("orch-agents-hint", "Chargement…", false);
  try {
    const j = await orchGet("/agents/map");
    renderAgentsMap(j);
    setText("orch-agents-hint", "OK · GET /v1/pilot/orch/agents/map", false);
  } catch (e) {
    setText("orch-agents-hint", String(e), true);
  }
}

/* ---------- Providers ---------- */

function renderProviders(data) {
  const meta = document.getElementById("orch-providers-meta");
  const list = document.getElementById("orch-providers-list");
  const auditEl = document.getElementById("orch-providers-audit");
  const raw = document.getElementById("orch-providers-raw");
  if (raw) raw.textContent = JSON.stringify(data, null, 2);

  const providers = Array.isArray(data && data.providers) ? data.providers : [];
  if (meta) {
    meta.innerHTML =
      '<span class="muted">env ' +
      esc(data.env_scope || "?") +
      " · " +
      providers.length +
      " providers · built " +
      esc(String(data.built_ms ?? "—")) +
      " ms</span>";
  }
  if (list) {
    list.innerHTML = providers.length
      ? providers
          .map(function (p) {
            const models = Array.isArray(p.models) ? p.models.slice(0, 6) : [];
            const more = Array.isArray(p.models) && p.models.length > 6 ? " +" + (p.models.length - 6) : "";
            return (
              '<article class="orch-card">' +
              "<header><strong>" +
              esc(p.label || p.id) +
              '</strong> <span class="orch-pill ' +
              statusClass(p.status) +
              '">' +
              esc(p.status || (p.configured ? "cfg" : "—")) +
              "</span></header>" +
              '<p class="muted orch-card-id"><code>' +
              esc(p.id) +
              "</code> · " +
              esc(p.kind || "") +
              (p.latency_ms != null ? " · " + Math.round(p.latency_ms) + " ms" : "") +
              "</p>" +
              (p.base_url ? '<p class="muted"><code>' + esc(p.base_url) + "</code></p>" : "") +
              (models.length
                ? '<p class="orch-models">' +
                  models.map(function (m) {
                    return "<code>" + esc(m) + "</code>";
                  }).join(" ") +
                  esc(more) +
                  "</p>"
                : "") +
              (p.error ? '<p class="orch-err">' + esc(p.error) + "</p>" : "") +
              "</article>"
            );
          })
          .join("")
      : '<p class="muted">Aucun provider.</p>';
  }

  const audit = data && data.ollama_audit;
  if (auditEl) {
    if (!audit || typeof audit !== "object") {
      auditEl.textContent = "—";
      return;
    }
    const gaps = Array.isArray(audit.gaps) ? audit.gaps : [];
    const missing = Array.isArray(audit.missing_models) ? audit.missing_models : [];
    auditEl.innerHTML =
      '<p><strong>Ollama audit</strong> · ' +
      (audit.ok === true ? '<span class="orch-pill orch-pill--ok">ok</span>' : '<span class="orch-pill orch-pill--err">ko</span>') +
      ' · models ' +
      esc(String(audit.model_count ?? "—")) +
      "</p>" +
      '<p class="muted">heavy <code>' +
      esc((audit.heavy && audit.heavy.base_url) || audit.base_url || "") +
      "</code> · light <code>" +
      esc((audit.light && audit.light.base_url) || audit.light_base_url || "") +
      "</code></p>" +
      (gaps.length ? "<p>Gaps : " + gaps.map(esc).join(", ") + "</p>" : "") +
      (missing.length ? "<p>Missing : " + missing.map(esc).join(", ") + "</p>" : "");
  }
}

export async function orchProvidersBind() {
  setText("orch-providers-hint", "Chargement…", false);
  try {
    const j = await orchGet("/providers/catalog");
    renderProviders(j);
    setText("orch-providers-hint", "OK · GET /v1/pilot/orch/providers/catalog", false);
  } catch (e) {
    setText("orch-providers-hint", String(e), true);
  }
}

/* ---------- LyraEngine panel on #/lyra ---------- */

function renderLyraEngine(data) {
  const gaugesEl = document.getElementById("orch-lyra-gauges");
  const metaEl = document.getElementById("orch-lyra-meta");
  const styleEl = document.getElementById("orch-lyra-style");
  const g = (data && data.gauges) || {};
  const keys = [
    ["chaleur", "Chaleur"],
    ["energie", "Énergie"],
    ["patience", "Patience"],
    ["confiance", "Confiance"],
  ];
  if (gaugesEl) {
    gaugesEl.innerHTML = keys
      .map(function (it) {
        const k = it[0];
        const label = it[1];
        const v = Math.max(0, Math.min(100, Number(g[k]) || 0));
        const pct = Math.round(v);
        return (
          '<div class="lyra-gauge">' +
          '<div class="lyra-gauge-head"><strong>' +
          esc(label) +
          '</strong><span class="muted">' +
          esc(k) +
          "</span></div>" +
          '<div class="lyra-bar"><div style="width:' +
          pct +
          '%;background:#4ade80"></div></div>' +
          '<div class="lyra-controls">' +
          '<button type="button" data-orch-lyra-delta="' +
          esc(k) +
          '" data-delta="5">+5</button>' +
          '<button type="button" data-orch-lyra-delta="' +
          esc(k) +
          '" data-delta="-5">−5</button>' +
          '<span class="muted">' +
          pct +
          "%</span></div></div>"
        );
      })
      .join("");
  }
  if (metaEl) {
    metaEl.textContent =
      "v" +
      (data.version || "?") +
      " · mode " +
      (data.mode || "—") +
      " · uptime " +
      (data.uptime_lyra || "—") +
      " · latency " +
      (data.latency != null ? data.latency + " ms" : "—");
  }
  if (styleEl) styleEl.textContent = data.style || "—";
}

let _lyraEngineBound = false;

function bindLyraEngineOnce() {
  if (_lyraEngineBound) return;
  const root = document.getElementById("orch-lyra-engine");
  if (!root) return;
  _lyraEngineBound = true;
  root.addEventListener("click", function (ev) {
    const btn = ev.target.closest("[data-orch-lyra-delta]");
    const refresh = ev.target.closest("#btn-orch-lyra-refresh");
    const reset = ev.target.closest("#btn-orch-lyra-reset");
    if (btn) {
      const gauge = btn.getAttribute("data-orch-lyra-delta");
      const delta = Number(btn.getAttribute("data-delta") || 0);
      orchLyraUpdate({ gauge: gauge, delta: delta }).catch(function (e) {
        setText("orch-lyra-hint", String(e), true);
      });
      return;
    }
    if (refresh) {
      orchLyraEngineBind();
      return;
    }
    if (reset) {
      orchLyraUpdate({ reset: true }).catch(function (e) {
        setText("orch-lyra-hint", String(e), true);
      });
    }
  });
}

async function orchLyraUpdate(body) {
  setText("orch-lyra-hint", "Update…", false);
  const j = await orchPost("/lyra/update", body);
  renderLyraEngine(j.gauges ? j : { ...j, gauges: j.gauges });
  // Re-fetch full state (style / mode) after update
  await orchLyraEngineBind();
}

export async function orchLyraEngineBind() {
  bindLyraEngineOnce();
  setText("orch-lyra-hint", "Chargement LyraEngine…", false);
  try {
    const j = await orchGet("/lyra/state");
    renderLyraEngine(j);
    setText("orch-lyra-hint", "OK · LyraEngine via /v1/pilot/orch/lyra/state", false);
  } catch (e) {
    setText("orch-lyra-hint", String(e), true);
  }
}

/* ---------- Router patch ---------- */

export function installOrchSurfaces() {
  const App = globalThis.PilotApp || (globalThis.PilotApp = {});
  App.orchAgentsMapBind = orchAgentsMapBind;
  App.orchProvidersBind = orchProvidersBind;
  App.orchLyraEngineBind = orchLyraEngineBind;

  const btnAgents = document.getElementById("btn-orch-agents-refresh");
  if (btnAgents) btnAgents.addEventListener("click", function () { orchAgentsMapBind(); });
  const btnProv = document.getElementById("btn-orch-providers-refresh");
  if (btnProv) btnProv.addEventListener("click", function () { orchProvidersBind(); });

  const origParse = App.pilotParseRoute;
  App.pilotParseRoute = function orchParseRoute() {
    const raw = (location.hash || "").replace(/^#/, "").replace(/^\//, "");
    const pathOnly = raw.split("?")[0];
    const parts = pathOnly.split("/").filter(Boolean);
    if (parts[0] === "agents" && parts[1] === "map") return "agents_map";
    if (parts[0] === "providers") return "providers";
    return typeof origParse === "function" ? origParse() : "home";
  };

  const origApply = App.pilotApplyRoute;
  App.pilotApplyRoute = function orchApplyRoute() {
    if (typeof origApply === "function") origApply();
    const r = App.pilotParseRoute();
    const agentsPage = document.getElementById("pilot-page-agents-map");
    const providersPage = document.getElementById("pilot-page-providers");
    if (agentsPage) agentsPage.hidden = r !== "agents_map";
    if (providersPage) providersPage.hidden = r !== "providers";

    document.querySelectorAll("#pilot-nav a[data-nav-route]").forEach(function (a) {
      const route = a.getAttribute("data-nav-route") || "";
      if (route === "agents_map" || route === "providers") {
        a.classList.toggle("pilot-nav-active", r === route);
      }
    });
    const campus = document.querySelector('#pilot-nav .pilot-nav-group[data-nav-group="campus"]');
    const projet = document.querySelector('#pilot-nav .pilot-nav-group[data-nav-group="projet"]');
    if (campus && r === "agents_map") campus.classList.add("pilot-nav-active");
    if (projet && r === "providers") projet.classList.add("pilot-nav-active");

    if (r === "agents_map") orchAgentsMapBind();
    if (r === "providers") orchProvidersBind();
    if (r === "lyra") orchLyraEngineBind();
  };
}
