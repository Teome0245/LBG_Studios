/** Fleet Team — #/team/fleet (supervision anti-sprawl + dry-run ops health). */

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

function setText(id, msg, isError) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = msg || "—";
  el.style.color = isError ? "#a30" : "";
}

function statusClass(st) {
  const s = String(st || "").toLowerCase();
  if (s === "busy" || s === "running" || s === "ok") return "orch-pill--ok";
  if (s === "failed" || s === "error" || s === "down") return "orch-pill--err";
  if (s === "review" || s === "waiting_approval") return "orch-pill--muted";
  return "orch-pill--muted";
}

function fmtCounts(obj) {
  if (!obj || typeof obj !== "object") return "—";
  return Object.keys(obj)
    .sort()
    .map(function (k) {
      return k + "=" + obj[k];
    })
    .join(" · ");
}

async function fleetFetch() {
  const r = await fetch(getBase() + "/v1/pilot/team/fleet");
  const j = await r.json().catch(function () {
    return {};
  });
  if (!r.ok) throw new Error((j && (j.error || j.detail)) || "HTTP " + r.status);
  if (j && j.ok === false) throw new Error(j.error || j.detail || "fleet ok:false");
  return j;
}

function renderFleet(data) {
  const m = (data && data.metrics) || {};
  const flags = (data && data.flags) || {};
  const chat = flags.chat_agentic || {};
  const meta = document.getElementById("fleet-meta");
  if (meta) {
    meta.innerHTML =
      '<span class="orch-pill ' +
      statusClass(m.agents_busy ? "busy" : "ok") +
      '">busy ' +
      esc(String(m.agents_busy ?? 0)) +
      "</span>" +
      '<span class="orch-pill ' +
      statusClass(m.team_l2_pending ? "review" : "ok") +
      '">L2 ' +
      esc(String(m.team_l2_pending ?? 0)) +
      "</span>" +
      '<span class="orch-pill ' +
      statusClass(m.jobs_waiting_approval ? "waiting_approval" : "ok") +
      '">jobs ⏳ ' +
      esc(String(m.jobs_waiting_approval ?? 0)) +
      "</span>" +
      '<span class="muted">agents ' +
      esc(String(data.agents_count ?? 0)) +
      " · chat_agentic=" +
      esc(String(!!chat.LBG_CHAT_AGENTIC)) +
      " · jobs_runner=" +
      esc(String(!!flags.jobs_runner)) +
      "</span>";
  }

  const metricsEl = document.getElementById("fleet-metrics");
  if (metricsEl) {
    metricsEl.textContent =
      "agents_by_status: " +
      fmtCounts(data.agents_by_status) +
      "\nteam_by_status: " +
      fmtCounts(m.team_by_status) +
      "\njobs_by_status: " +
      fmtCounts(m.jobs_by_status) +
      "\njobs_total: " +
      (m.jobs_total ?? "—") +
      " · team_l2_pending: " +
      (m.team_l2_pending ?? "—");
  }

  const list = document.getElementById("fleet-agents-list");
  const agents = Array.isArray(data.agents) ? data.agents : [];
  if (list) {
    if (!agents.length) {
      list.innerHTML = '<p class="muted">Aucun agent.</p>';
    } else {
      list.innerHTML = agents
        .map(function (a) {
          const st = a.status || "idle";
          const tid = a.task_id ? String(a.task_id) : "";
          const orphan = a.orphan ? ' <span class="orch-pill orch-pill--err">orphan</span>' : "";
          return (
            '<article class="orch-card">' +
            "<header><strong>" +
            esc(a.display_name || a.agent_id) +
            '</strong> <span class="orch-pill ' +
            statusClass(st) +
            '">' +
            esc(st) +
            "</span>" +
            orphan +
            "</header>" +
            '<p class="muted orch-card-id"><code>' +
            esc(a.agent_id) +
            "</code> · " +
            esc(a.role || "—") +
            (a.location ? " · " + esc(a.location) : "") +
            "</p>" +
            '<p class="orch-card-desc">' +
            esc(a.current_action || "—") +
            "</p>" +
            (tid
              ? '<p class="muted"><a href="#/team?task=' +
                encodeURIComponent(tid) +
                '">#' +
                esc(tid.slice(0, 8)) +
                "</a></p>"
              : "") +
            "</article>"
          );
        })
        .join("");
    }
  }

  const l2 = document.getElementById("fleet-l2-list");
  const pending = (((data.team || {}).l2_pending) || []).slice(0, 20);
  if (l2) {
    if (!pending.length) {
      l2.innerHTML = '<p class="muted">Aucune validation L2 en attente.</p>';
    } else {
      l2.innerHTML = pending
        .map(function (t) {
          const tid = String(t.id || "");
          return (
            '<div class="office-validation-item" data-fleet-l2="' +
            esc(tid) +
            '">' +
            "<div>" +
            '<div class="vi-title">' +
            esc(t.role || "?") +
            " · " +
            esc(t.status) +
            "</div>" +
            '<div class="vi-meta">' +
            esc((t.objective || "").slice(0, 100)) +
            ' · <a href="#/team?task=' +
            encodeURIComponent(tid) +
            '">#' +
            esc(tid.slice(0, 8)) +
            "</a></div></div>" +
            '<div class="vi-actions" style="display:flex;flex-wrap:wrap;gap:0.35rem;margin-top:0.35rem;">' +
            '<input type="password" data-fleet-token-for="' +
            esc(tid) +
            '" placeholder="token L2" style="max-width:9rem;" />' +
            '<button type="button" data-fleet-approve="' +
            esc(tid) +
            '">Approuver</button>' +
            '<button type="button" data-fleet-run="' +
            esc(tid) +
            '">Exécuter</button>' +
            "</div></div>"
          );
        })
        .join("");
      l2.querySelectorAll("[data-fleet-approve]").forEach(function (btn) {
        btn.addEventListener("click", function () {
          const tid = btn.getAttribute("data-fleet-approve") || "";
          const tokEl = l2.querySelector('input[data-fleet-token-for="' + cssEsc(tid) + '"]');
          const token = tokEl && tokEl.value ? String(tokEl.value).trim() : "";
          fleetApproveTask(tid, token).catch(function () {});
        });
      });
      l2.querySelectorAll("[data-fleet-run]").forEach(function (btn) {
        btn.addEventListener("click", function () {
          const tid = btn.getAttribute("data-fleet-run") || "";
          const tokEl = l2.querySelector('input[data-fleet-token-for="' + cssEsc(tid) + '"]');
          const token = tokEl && tokEl.value ? String(tokEl.value).trim() : "";
          fleetRunTask(tid, token).catch(function () {});
        });
      });
    }
  }

  const lastEl = document.getElementById("fleet-last-pilot");
  const last = ((data.ops_health_pilot || {}).last_run) || {};
  if (lastEl) {
    if (!last.ts && !last.decision) {
      lastEl.textContent = "Aucun run persisté.";
    } else {
      lastEl.textContent =
        "decision=" +
        (last.decision || "—") +
        " · dry_run=" +
        String(!!last.dry_run) +
        " · task=" +
        (last.remediation_task_id || "—") +
        " · " +
        (last.elapsed_ms != null ? last.elapsed_ms + "ms" : "") +
        "\n" +
        String(last.summary || "").slice(0, 280);
    }
  }

  const flagsEl = document.getElementById("fleet-flags");
  if (flagsEl) {
    const chat = (data.flags || {}).chat_agentic || {};
    flagsEl.textContent =
      "LBG_CHAT_AGENTIC=" +
      String(!!chat.LBG_CHAT_AGENTIC) +
      "\nintents=" +
      ((chat.LBG_CHAT_AGENTIC_INTENTS || []).join(",") || "(tous si agentic on)") +
      "\njobs_runner=" +
      String(!!(data.flags || {}).jobs_runner) +
      "\n" +
      (chat.note || "");
  }

  const jobsWait = document.getElementById("fleet-jobs-waiting");
  const waiting = (((data.jobs || {}).waiting_approval) || []).slice(0, 12);
  if (jobsWait) {
    if (!waiting.length) {
      jobsWait.innerHTML = '<p class="muted">Aucun job en waiting_approval.</p>';
    } else {
      jobsWait.innerHTML = waiting
        .map(function (j) {
          return (
            "<div><code>" +
            esc(String(j.id).slice(0, 8)) +
            "</code> · " +
            esc((j.objective || "").slice(0, 90)) +
            ' · <a href="#/jobs">Jobs</a></div>'
          );
        })
        .join("");
    }
  }

  const raw = document.getElementById("fleet-raw");
  if (raw) raw.textContent = JSON.stringify(data, null, 2);

  // Enrich metrics page if present
  const jobsMetrics = document.getElementById("metrics-jobs");
  if (jobsMetrics) {
    jobsMetrics.textContent =
      "runner: " +
      String(!!((data.jobs || {}).runner_enabled)) +
      "\ntotal: " +
      String(m.jobs_total ?? "—") +
      "\nwaiting_approval: " +
      String(m.jobs_waiting_approval ?? "—") +
      "\nby_status: " +
      fmtCounts(m.jobs_by_status) +
      "\nteam_l2_pending: " +
      String(m.team_l2_pending ?? "—") +
      "\nops_health: " +
      String(m.ops_health_last_decision ?? "—");
  }
}

function cssEsc(s) {
  return String(s == null ? "" : s).replace(/["\\]/g, "\\$&");
}

async function fleetApproveTask(taskId, token) {
  if (!taskId) return;
  if (!token) {
    setText("fleet-hint", "Token L2 requis pour Approuver.", true);
    return;
  }
  setText("fleet-hint", "Approbation " + taskId.slice(0, 8) + "…", false);
  const r = await fetch(getBase() + "/v1/pilot/team/tasks/" + encodeURIComponent(taskId) + "/approve", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token: token }),
  });
  const j = await r.json().catch(function () {
    return {};
  });
  if (!r.ok || j.ok === false) {
    setText("fleet-hint", (j && (j.error || j.detail)) || "approve KO", true);
    return;
  }
  setText("fleet-hint", "Approuvée — tu peux Exécuter.", false);
  await fleetBind();
}

async function fleetRunTask(taskId, token) {
  if (!taskId) return;
  setText("fleet-hint", "Exécution " + taskId.slice(0, 8) + "…", false);
  const body = token ? { approval_token: token } : {};
  const r = await fetch(getBase() + "/v1/pilot/team/tasks/" + encodeURIComponent(taskId) + "/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const j = await r.json().catch(function () {
    return {};
  });
  if (!r.ok || j.ok === false) {
    setText("fleet-hint", (j && (j.error || j.detail)) || "run KO", true);
    return;
  }
  setText("fleet-hint", "Statut tâche: " + (j.status || "?"), false);
  await fleetBind();
}

async function fleetBind() {
  setText("fleet-hint", "Chargement…", false);
  try {
    const data = await fleetFetch();
    renderFleet(data);
    setText("fleet-hint", "OK · GET /v1/pilot/team/fleet", false);
  } catch (e) {
    setText("fleet-hint", String(e && e.message ? e.message : e), true);
  }
}

async function fleetRunOpsPilot(dryRun) {
  setText("fleet-pilot-hint", dryRun ? "Dry-run ops health…" : "Run live ops health…", false);
  try {
    const r = await fetch(getBase() + "/v1/pilot/team/ops_health_pilot", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        dry_run: !!dryRun,
        // live → notify auto (null) ; dry-run → pas de spam
        notify: dryRun ? false : null,
        spawn_l2_remediation: true,
        include_smoke: false,
      }),
    });
    const j = await r.json().catch(function () {
      return {};
    });
    if (!r.ok || j.ok === false) {
      throw new Error((j && (j.error || j.detail || j.body)) || "HTTP " + r.status);
    }
    const out = document.getElementById("fleet-pilot-out");
    if (out) out.textContent = JSON.stringify(j, null, 2);
    setText(
      "fleet-pilot-hint",
      "decision=" +
        (j.decision || "?") +
        " · dry_run=" +
        String(!!j.dry_run) +
        " · task=" +
        (j.remediation_task_id || "—") +
        " · " +
        (j.elapsed_ms || "?") +
        "ms",
      false
    );
    await fleetBind();
  } catch (e) {
    setText("fleet-pilot-hint", String(e && e.message ? e.message : e), true);
  }
}

export function installTeamFleet() {
  const App = globalThis.PilotApp || (globalThis.PilotApp = {});
  App.fleetBind = fleetBind;
  App.fleetRunOpsPilot = fleetRunOpsPilot;

  const btn = document.getElementById("btn-fleet-refresh");
  if (btn) btn.addEventListener("click", function () {
    fleetBind();
  });
  const btnDry = document.getElementById("btn-fleet-ops-dry");
  if (btnDry) {
    btnDry.addEventListener("click", function () {
      fleetRunOpsPilot(true);
    });
  }
  const btnLive = document.getElementById("btn-fleet-ops-live");
  if (btnLive) {
    btnLive.addEventListener("click", function () {
      if (!window.confirm("Lancer ops_health_pilot en live (peut créer une tâche L2 si KO) ?")) return;
      fleetRunOpsPilot(false);
    });
  }

  const origParse = App.pilotParseRoute;
  App.pilotParseRoute = function fleetParseRoute() {
    const raw = (location.hash || "").replace(/^#/, "").replace(/^\//, "");
    const pathOnly = raw.split("?")[0];
    const parts = pathOnly.split("/").filter(Boolean);
    if (parts[0] === "team" && parts[1] === "fleet") return "team_fleet";
    return typeof origParse === "function" ? origParse() : "home";
  };

  const origApply = App.pilotApplyRoute;
  App.pilotApplyRoute = function fleetApplyRoute() {
    if (typeof origApply === "function") origApply();
    const r = App.pilotParseRoute();
    const page = document.getElementById("pilot-page-team-fleet");
    if (page) page.hidden = r !== "team_fleet";

    document.querySelectorAll("#pilot-nav a[data-nav-route]").forEach(function (a) {
      const route = a.getAttribute("data-nav-route") || "";
      if (route === "team_fleet") {
        a.classList.toggle("pilot-nav-active", r === "team_fleet");
      }
    });
    const campus = document.querySelector('#pilot-nav .pilot-nav-group[data-nav-group="campus"]');
    if (campus && r === "team_fleet") campus.classList.add("pilot-nav-active");

    if (r === "team_fleet") fleetBind();
    if (r === "team_metrics") {
      fleetFetch()
        .then(renderFleet)
        .catch(function () {});
    }
  };
}
