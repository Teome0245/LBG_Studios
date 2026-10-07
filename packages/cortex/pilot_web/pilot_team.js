    function teamTaskHref(taskId) {
      const id = String(taskId || "").trim();
      if (!id) return "#/team";
      return "#/team?task=" + encodeURIComponent(id);
    }

    function teamSetHashTask(taskId) {
      const next = teamTaskHref(taskId).replace(/^#/, "");
      const cur = (location.hash || "").replace(/^#/, "");
      if (cur !== next) location.hash = next;
    }

    let __teamSelectedId = null;
    let __teamBound = false;
    let __teamLastForgePatch = null;
    let __teamObjectiveCustom = false;
    let __teamMetaRoles = null;
    let __teamReunificationBrief = false;
    let __teamGodotSupervisor = false;
    let __teamGodotTrack = false;
    let __teamInfographiste = false;
    let __teamPygmalionMesh = false;
    let __teamGodotTrackKey = "";
    let __teamCore3Build = false;
    let __teamCore3BuildExecute = false;
    let __teamGodotValidation = false;
    let __teamParallelPrime = false;
    let __teamM9TrackKey = "";
    let __teamGodotDevPersona = "";
    let __teamGodotDevTrack = "";
    let __teamIrisForge = false;

    let __teamAutoconsult = false;
    let __teamEvolutionSprint = false;

    /* ===================== Bureau Team (presence) ===================== */
    let __officeWs = null;
    let __officePoll = null;
    let __officeAgents = new Map();
    let __officeZones = [
      ["zone_core", "Open Space Core (140)"],
      ["zone_front", "Front web (.100)"],
      ["zone_llm", "Forge LLM (.110 / .111)"],
      ["zone_mmo_lab", "Lab SWG (245)"],
      ["zone_prime", "Monde Prime (246)"],
      ["zone_games", "Salle de jeux"],
      ["zone_coffee", "Pause café"],
    ];
    /** @type {Map<string, object>} meta zones (host_status, host_badge…) depuis le snapshot */
    let __officeZoneState = new Map();
    let __officeZonePoll = null;
    let __officePing = null;
    let __officeAnim = {};
    let __officeView = "map";
    let __officeMapReady = false;
    let __officeSelectedId = null;
    let __officeSelectedTaskId = null;
    let __officePlayerIa = null;
    let __officePlayerIaPoll = null;

    function officeParseView() {
      const raw = (location.hash || "").replace(/^#/, "");
      const qIdx = raw.indexOf("?");
      if (qIdx < 0) return "map";
      const params = new URLSearchParams(raw.slice(qIdx + 1));
      const v = (params.get("view") || "map").toLowerCase();
      return v === "classic" ? "classic" : "map";
    }

    function officeSetHashView(view) {
      const base = "#/team/office";
      const next = view === "classic" ? base + "?view=classic" : base + "?view=map";
      if (location.hash !== next && location.hash.replace(/^#/, "") !== next.replace(/^#/, "")) {
        location.hash = next.replace(/^#/, "");
      }
    }

    function officeApplyView(view) {
      __officeView = view === "classic" ? "classic" : "map";
      const mapWrap = document.getElementById("office-map-wrap");
      const classicWrap = document.getElementById("office-classic-wrap");
      const btnMap = document.getElementById("office-btn-map");
      const btnClassic = document.getElementById("office-btn-classic");
      if (mapWrap) mapWrap.hidden = __officeView !== "map";
      if (classicWrap) classicWrap.hidden = __officeView !== "classic";
      const piaBar = document.getElementById("office-player-ia-bar");
      // Barre globale en vue carte ; en classic les chips sont dans la tuile Monde Prime.
      if (piaBar) piaBar.hidden = __officeView !== "map";
      if (btnMap) btnMap.classList.toggle("is-active", __officeView === "map");
      if (btnClassic) btnClassic.classList.toggle("is-active", __officeView === "classic");
      if (__officeView === "classic") {
        try { if (window.LbgOfficeMap) LbgOfficeMap.stop(); } catch (_) {}
        __officeMapReady = false;
        officeRender();
      } else {
        officeEnsureMap();
        officeRenderPlayerIaBar();
      }
    }

    function officeEnsureMap() {
      if (!window.LbgOfficeMap) {
        officeSetConn("Phaser module manquant");
        return;
      }
      if (LbgOfficeMap.isRunning()) {
        officeSyncMap(false);
        return;
      }
      LbgOfficeMap.start({
        host: document.getElementById("office-map-host"),
        onSelect: officeSelectAgent,
      }).then(function () {
        __officeMapReady = true;
        officeSyncMap(false);
      }).catch(function (err) {
        officeSetConn("Carte KO — " + (err && err.message ? err.message : "erreur"));
        officeApplyView("classic");
      });
    }

    function officeSyncMap(animate) {
      if (__officeView !== "map" || !window.LbgOfficeMap || !LbgOfficeMap.isRunning()) return;
      LbgOfficeMap.sync(Array.from(__officeAgents.values()), { animate: !!animate });
    }

    function officeSelectAgent(agent) {
      if (!agent) return;
      __officeSelectedId = agent.agent_id;
      __officeSelectedTaskId = agent.task_id ? String(agent.task_id) : null;
      const empty = document.getElementById("office-side-empty");
      const body = document.getElementById("office-side-body");
      const title = document.getElementById("office-side-title");
      const status = document.getElementById("office-side-status");
      const action = document.getElementById("office-side-action");
      const meta = document.getElementById("office-side-meta");
      if (empty) empty.hidden = true;
      if (body) body.hidden = false;
      if (title) title.textContent = agent.display_name || agent.agent_id;
      if (status) {
        status.textContent = agent.status || "idle";
        status.className = "side-status " + (agent.status || "idle");
      }
      if (action) action.textContent = agent.current_action || "—";
      if (meta) {
        const tid = agent.task_id ? String(agent.task_id) : "";
        meta.innerHTML =
          officeEsc(agent.location || "?") +
          (agent.host_hint ? " · " + officeEsc(agent.host_hint) : "") +
          (tid
            ? ' · <a href="' + officeEsc(teamTaskHref(tid)) + '" title="Ouvrir la tâche">' +
              "#" + officeEsc(tid.slice(0, 8)) + "</a>"
            : "");
      }
      officeRefreshApprovalPanel(__officeSelectedTaskId, agent).catch(function () {});
    }

    function officeTaskNeedsHumanValidation(task) {
      if (!task || typeof task !== "object") return false;
      const status = String(task.status || "").toLowerCase();
      if (status === "review") return true;
      const approvalRequired = task.approval_required === true;
      return approvalRequired && (status === "queued" || status === "waiting_approval");
    }

    function officeAgentNeedsValidation(agent) {
      if (!agent || typeof agent !== "object") return false;
      if (!agent.task_id) return false;
      // Idle sans flag L2 actif = pas au bureau (évite fantômes approval_required).
      if (agent.awaiting_human_approval === true || agent.awaiting_run === true) return true;
      const st = String(agent.status || "").toLowerCase();
      if (st === "review") return true;
      if (st === "idle") return false;
      return agent.approval_required === true && (st === "queued" || st === "waiting_approval");
    }

    function officeAgentAwaitingHumanApproval(agent) {
      if (!agent || typeof agent !== "object") return false;
      if (agent.awaiting_human_approval === true) return true;
      if (agent.awaiting_run === true) return false;
      return officeAgentNeedsValidation(agent);
    }

    function officeAgentAwaitingRun(agent) {
      if (!agent || typeof agent !== "object") return false;
      return agent.awaiting_run === true || officeAgentNeedsValidation(agent);
    }

    function officeCollectPendingValidations() {
      const seen = new Set();
      const rows = [];
      __officeAgents.forEach(function (a) {
        if (!officeAgentNeedsValidation(a)) return;
        const tid = String(a.task_id || "");
        if (!tid || seen.has(tid)) return;
        seen.add(tid);
        rows.push({
          task_id: tid,
          label: a.display_name || a.role || "agent",
          role: a.role || "",
          action: a.current_action || "Validation L2",
          location: a.location || "",
          awaiting_run: a.awaiting_run === true,
          awaiting_human_approval: officeAgentAwaitingHumanApproval(a),
        });
      });
      return rows;
    }

    function officeRenderValidationDesk() {
      const listEl = document.getElementById("office-validation-list");
      const emptyEl = document.getElementById("office-validation-empty");
      const countEl = document.getElementById("office-validation-count");
      const desk = document.getElementById("office-validation-desk");
      if (!listEl || !emptyEl || !desk) return;
      const rows = officeCollectPendingValidations();
      if (countEl) countEl.textContent = rows.length ? "(" + rows.length + ")" : "";
      if (!rows.length) {
        emptyEl.hidden = false;
        listEl.hidden = true;
        listEl.innerHTML = "";
        return;
      }
      emptyEl.hidden = true;
      listEl.hidden = false;
      listEl.innerHTML = rows.map(function (r) {
        const tid = r.task_id;
        const short = tid.slice(0, 8);
        const tag = r.awaiting_run ? "Prêt — Exécuter" : "Token L2 requis";
        return (
          '<div class="office-validation-item" data-office-desk-task="' + officeEsc(tid) + '">' +
            "<div>" +
              '<div class="vi-title">' + officeEsc(r.label) + " — " + officeEsc(r.action) + "</div>" +
              '<div class="vi-meta">' +
                officeEsc(tag) + " · " + officeEsc(r.role || "") +
                (r.location ? " · " + officeEsc(r.location) : "") +
                ' · <a href="' + officeEsc(teamTaskHref(tid)) + '">#' + officeEsc(short) + "</a>" +
              "</div>" +
            "</div>" +
            '<div class="vi-actions">' +
              (r.awaiting_human_approval
                ? '<input type="text" data-office-token-for="' + officeEsc(tid) + '" placeholder="token L2" />' +
                  '<button type="button" data-office-approve-task="' + officeEsc(tid) + '">Approuver</button>'
                : "") +
              '<button type="button" data-office-run-task="' + officeEsc(tid) + '">Exécuter</button>' +
            "</div>" +
          "</div>"
        );
      }).join("");
      listEl.querySelectorAll("[data-office-approve-task]").forEach(function (btn) {
        btn.addEventListener("click", function (ev) {
          ev.preventDefault();
          ev.stopPropagation();
          const taskId = btn.getAttribute("data-office-approve-task") || "";
          const tokenEl = listEl.querySelector('input[data-office-token-for="' + cssEscape(taskId) + '"]');
          const token = tokenEl && tokenEl.value ? String(tokenEl.value).trim() : "";
          officeApproveTaskById(taskId, token).catch(function () {});
        });
      });
      listEl.querySelectorAll("[data-office-run-task]").forEach(function (btn) {
        btn.addEventListener("click", function (ev) {
          ev.preventDefault();
          ev.stopPropagation();
          const taskId = btn.getAttribute("data-office-run-task") || "";
          const tokenEl = listEl.querySelector('input[data-office-token-for="' + cssEscape(taskId) + '"]');
          const token = tokenEl && tokenEl.value ? String(tokenEl.value).trim() : "";
          officeRunTaskById(taskId, token).catch(function () {});
        });
      });
    }

    async function officeRefreshApprovalPanel(taskId, agent) {
      const panel = document.getElementById("office-side-approval");
      const text = document.getElementById("office-side-approval-text");
      if (!panel || !text) return;
      if (!taskId) {
        panel.hidden = true;
        return;
      }
      if (agent && officeAgentNeedsValidation(agent)) {
        panel.hidden = false;
        const ready = agent.awaiting_run === true;
        text.textContent = ready
          ? "Approuvée — clique Exécuter (" + (agent.display_name || agent.role || "agent") + ")"
          : "Validation humaine requise — " +
            (agent.display_name || agent.role || "agent") +
            " · statut review";
        const tokenEl = document.getElementById("office-side-approval-token");
        const btnApprove = document.getElementById("office-side-btn-approve");
        if (tokenEl) tokenEl.hidden = ready;
        if (btnApprove) btnApprove.hidden = ready;
        return;
      }
      const out = await jobsGet(getBase() + "/v1/pilot/team/tasks/" + encodeURIComponent(taskId));
      const task = out.json || {};
      if (!task.id || !officeTaskNeedsHumanValidation(task)) {
        panel.hidden = true;
        return;
      }
      panel.hidden = false;
      text.textContent =
        "Validation humaine requise — " +
        (task.role_label || task.role || "agent") +
        " · statut " +
        (task.status || "?");
    }

    async function officeApproveTaskById(taskId, token) {
      if (!taskId) return;
      if (!token) {
        officeSetConn("Token d'approbation requis.");
        return;
      }
      officeSetConn("Approbation en cours…");
      const out = await postJson(
        getBase() + "/v1/pilot/team/tasks/" + encodeURIComponent(taskId) + "/approve",
        { token: token },
        30000
      );
      if (!teamResponseOk(out)) {
        officeSetConn("Approbation KO: " + teamApiError(out));
        return;
      }
      officeSetConn("Tâche approuvée. Tu peux exécuter.");
      try { await officeFetchSnapshot(); } catch (_) {}
      await officeRefreshApprovalPanel(taskId);
    }

    async function officeRunTaskById(taskId, token) {
      if (!taskId) return;
      const body = token ? { approval_token: token } : {};
      officeSetConn("Exécution en cours…");
      const out = await postJson(
        getBase() + "/v1/pilot/team/tasks/" + encodeURIComponent(taskId) + "/run",
        body,
        300000
      );
      if (!teamResponseOk(out)) {
        officeSetConn("Exécution KO: " + teamApiError(out));
        return;
      }
      const st = String((out.json || {}).status || "?");
      const res = (out.json || {}).result || {};
      const summary = String(res.human_summary || "").trim();
      if (st === "done" && summary) {
        officeSetConn("Déjà faite / OK — " + summary.slice(0, 160));
      } else {
        officeSetConn("Tâche: " + st);
      }
      try { await officeFetchSnapshot(); } catch (_) {}
      await officeRefreshApprovalPanel(taskId);
    }

    async function officeApproveSelectedTask() {
      const taskId = __officeSelectedTaskId;
      if (!taskId) return;
      const tokenEl = document.getElementById("office-side-approval-token");
      const token = tokenEl && tokenEl.value ? String(tokenEl.value).trim() : "";
      await officeApproveTaskById(taskId, token);
    }

    async function officeRunSelectedTask() {
      const taskId = __officeSelectedTaskId;
      if (!taskId) return;
      const tokenEl = document.getElementById("office-side-approval-token");
      const token = tokenEl && tokenEl.value ? String(tokenEl.value).trim() : "";
      await officeRunTaskById(taskId, token);
    }

    const OFFICE_ZONE_META = {
      zone_core: { ico: "⌂", ip: "192.168.0.140", short: "Core" },
      zone_front: { ico: "▣", ip: "192.168.0.100", short: "Front" },
      zone_llm: { ico: "⚡", ip: ".110 / .111", short: "LLM" },
      zone_mmo_lab: { ico: "⚒", ip: "192.168.0.245", short: "Lab" },
      zone_prime: { ico: "◉", ip: "192.168.0.246", short: "Prime" },
      zone_games: { ico: "▶", ip: "personas out-game", short: "Jeux" },
      zone_coffee: { ico: "☕", ip: "pause", short: "Café" },
    };

    function officeEsc(s) {
      return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
        return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c];
      });
    }

    function cssEscape(s) {
      return String(s == null ? "" : s).replace(/["\\]/g, "\\$&");
    }

    function officeInitials(name) {
      const parts = String(name || "?").trim().split(/\s+/).filter(Boolean);
      if (!parts.length) return "?";
      if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }

    function officeSetConn(htmlOrText, asHtml) {
      const el = document.getElementById("office-conn-text");
      if (!el) return;
      if (asHtml) el.innerHTML = htmlOrText;
      else el.textContent = htmlOrText;
    }

    function officePlayerIaChipHtml(bot) {
      const online = !!(bot && bot.online);
      const inWorld = !!(bot && bot.in_world);
      const name = (bot && (bot.display_name || bot.id)) || "?";
      const zone = bot && (bot.zone_display || bot.zone) ? String(bot.zone_display || bot.zone) : "";
      const age = bot && bot.age_s != null ? Number(bot.age_s) : null;
      const state = !online ? "offline" : (inWorld ? "online" : "stale");
      const label = !online ? "hors jeu" : (zone || (inWorld ? "en jeu" : "snapshot vieux"));
      const ageTxt = age != null && !Number.isNaN(age) ? (" · " + (age < 10 ? age.toFixed(1) : Math.round(age)) + "s") : "";
      const title = name + " — " + label + ageTxt + " (prime-hub · lecture seule)";
      return (
        '<span class="office-pia-chip office-pia-chip--' + state + '" title="' + officeEsc(title) + '">' +
          '<span class="office-pia-dot" aria-hidden="true"></span>' +
          '<span class="office-pia-name">' + officeEsc(name) + "</span>" +
          '<span class="office-pia-meta">' + officeEsc(label) + "</span>" +
        "</span>"
      );
    }

    function officePlayerIaStripHtml(compact) {
      const rt = __officePlayerIa;
      if (!rt) {
        return '<div class="office-pia-strip' + (compact ? " office-pia-strip--compact" : "") + '">' +
          '<span class="office-pia-label">Joueurs IA · Lost Heaven</span>' +
          '<span class="muted" style="font-size:0.72rem;">chargement…</span></div>';
      }
      const bots = Array.isArray(rt.bots) ? rt.bots : [];
      const online = rt.online_count != null ? rt.online_count : bots.filter(function (b) { return b && b.online; }).length;
      const hubOk = rt.sidecar_ok !== false;
      const head = hubOk
        ? (online + "/" + bots.length + " en hub")
        : "prime-hub KO";
      const chips = bots.length
        ? bots.map(officePlayerIaChipHtml).join("")
        : '<span class="muted" style="font-size:0.72rem;">aucun bot</span>';
      return (
        '<div class="office-pia-strip' + (compact ? " office-pia-strip--compact" : "") + '" title="Runtime prime-hub :8787 — flotte IG (Chœur supervise)">' +
          '<span class="office-pia-label">Joueurs IA · Lost Heaven</span>' +
          '<span class="office-pia-count' + (hubOk ? "" : " office-pia-count--ko") + '">' + officeEsc(head) + "</span>" +
          '<div class="office-pia-chips">' + chips + "</div>" +
        "</div>"
      );
    }

    function officeRenderPlayerIaBar() {
      const bar = document.getElementById("office-player-ia-bar");
      if (!bar) return;
      bar.innerHTML = officePlayerIaStripHtml(false);
    }

    async function officeFetchPlayerIaRuntime() {
      const base = (typeof getBase === "function" ? getBase() : "").replace(/\/$/, "");
      const r = await fetch(base + "/v1/pilot/player-ia/runtime");
      const data = await r.json().catch(function () { return null; });
      if (!data || data.ok === false) {
        __officePlayerIa = {
          ok: false,
          sidecar_ok: false,
          bots: [],
          online_count: 0,
          error: (data && (data.error || data.detail)) || ("HTTP " + r.status),
        };
      } else {
        __officePlayerIa = data;
      }
      officeRenderPlayerIaBar();
      if (__officeView === "classic") officeRender();
    }

    function officeRender() {
      const floor = document.getElementById("office-floor");
      if (!floor) return;
      const byZone = {};
      __officeZones.forEach(function (z) { byZone[z[0]] = []; });
      __officeAgents.forEach(function (a) {
        const loc = (a.location && byZone[a.location]) ? a.location : "zone_core";
        byZone[loc].push(a);
      });
      floor.innerHTML = __officeZones.map(function (pair) {
        const id = pair[0];
        const label = pair[1];
        const meta = OFFICE_ZONE_META[id] || { ico: "·", ip: "", short: id };
        const zState = __officeZoneState.get(id) || {};
        const hostOff = String(zState.host_status || "") === "offline";
        const hostBadge = hostOff
          ? String(zState.host_badge || "Éteinte")
          : "";
        const list = byZone[id] || [];
        const flags = [];
        list.forEach(function (a) {
          if (a.status === "busy") flags.push("has-busy");
          if (a.status === "failed") flags.push("has-failed");
          if (a.status === "review") flags.push("has-review");
        });
        if (hostOff) flags.push("is-host-off");
        const zoneClass = ("office-zone " + flags.join(" ")).trim();
        const cards = list.length
          ? list.map(function (a) {
              const st = a.status || "idle";
              const anim = __officeAnim[a.agent_id] || "";
              const tidFull = a.task_id ? String(a.task_id) : "";
              const href = tidFull ? teamTaskHref(tidFull) : "#/team/office";
              const tid = tidFull ? tidFull.slice(0, 8) : "";
              const needVal = officeAgentNeedsValidation(a);
              const needApprove = officeAgentAwaitingHumanApproval(a);
              const needRun = officeAgentAwaitingRun(a);
              const approvalHtml = needVal
                ? (
                    '<div class="office-card-approval">' +
                      '<span class="office-l2-tag">' +
                        (a.awaiting_run ? "PRÊT — EXÉCUTER" : "TOKEN L2 REQUIS") +
                      "</span>" +
                      (needApprove
                        ? '<input type="text" data-office-token-for="' + officeEsc(tidFull) + '" placeholder="token approbation" />'
                        : "") +
                      (needApprove
                        ? '<button type="button" data-office-approve-task="' + officeEsc(tidFull) + '">Approuver</button>'
                        : "") +
                      (needRun
                        ? '<button type="button" data-office-run-task="' + officeEsc(tidFull) + '">Exécuter</button>'
                        : "") +
                    "</div>"
                  )
                : "";
              return (
                '<article class="office-card ' + officeEsc(st) + (anim ? " " + anim : "") +
                  '" data-agent-id="' + officeEsc(a.agent_id) + '">' +
                  '<div class="office-avatar" aria-hidden="true">' +
                    officeEsc(officeInitials(a.display_name || a.agent_id)) +
                    '<span class="busy-ring"></span>' +
                  "</div>" +
                  '<div class="office-card-main">' +
                    '<div class="name">' + officeEsc(a.display_name || a.agent_id) + "</div>" +
                    '<div class="role-tag">' + officeEsc(a.role || a.agent_id) + "</div>" +
                    '<div class="action">' + officeEsc(a.current_action || "—") + "</div>" +
                    '<div class="host">' + officeEsc(a.host_hint || "") +
                    (tid
                      ? (' · <a href="' + officeEsc(href) + '" title="Ouvrir la tâche #' + officeEsc(tid) + '">#' +
                        officeEsc(tid) + "</a>")
                      : "") +
                    "</div>" +
                    approvalHtml +
                  "</div>" +
                  '<span class="office-status">' + officeEsc(st) + "</span>" +
                "</article>"
              );
            }).join("")
          : '<div class="office-empty"><span class="ghost" aria-hidden="true">∅</span>salle vide</div>';
        const piaStrip = id === "zone_prime" ? officePlayerIaStripHtml(true) : "";
        const ipLine = hostBadge
          ? (officeEsc(meta.ip) + ' · <span class="office-zone-host-badge">' + officeEsc(hostBadge) + "</span>")
          : officeEsc(meta.ip);
        const badgeChip = hostBadge
          ? ('<span class="office-zone-chip office-zone-chip--off" title="Hôte ' +
              officeEsc(zState.host || meta.ip) + ' injoignable">' + officeEsc(hostBadge) + "</span>")
          : "";
        return (
          '<section class="' + zoneClass + '" data-zone="' + officeEsc(id) + '">' +
            '<div class="office-zone-head">' +
              '<div class="office-zone-ico" title="' + officeEsc(meta.short) + '">' + meta.ico + "</div>" +
              '<div class="office-zone-titles">' +
                "<h2>" + officeEsc(label) + "</h2>" +
                '<span class="ip">' + ipLine + "</span>" +
              "</div>" +
              badgeChip +
              '<span class="count" title="agents">' + list.length + "</span>" +
            "</div>" +
            piaStrip +
            '<div class="office-agents">' + cards + "</div>" +
          "</section>"
        );
      }).join("");
      floor.querySelectorAll("[data-agent-id]").forEach(function (card) {
        card.addEventListener("click", function (ev) {
          const target = ev.target;
          if (target && target.closest && target.closest("[data-office-approve-task],[data-office-run-task],input[data-office-token-for]")) {
            return;
          }
          const agentId = card.getAttribute("data-agent-id");
          if (!agentId) return;
          const agent = __officeAgents.get(agentId);
          if (agent) officeSelectAgent(agent);
        });
      });
      floor.querySelectorAll("[data-office-approve-task]").forEach(function (btn) {
        btn.addEventListener("click", function (ev) {
          ev.preventDefault();
          ev.stopPropagation();
          const taskId = btn.getAttribute("data-office-approve-task") || "";
          const tokenEl = floor.querySelector('input[data-office-token-for="' + cssEscape(taskId) + '"]');
          const token = tokenEl && tokenEl.value ? String(tokenEl.value).trim() : "";
          officeApproveTaskById(taskId, token).catch(function () {});
        });
      });
      floor.querySelectorAll("[data-office-run-task]").forEach(function (btn) {
        btn.addEventListener("click", function (ev) {
          ev.preventDefault();
          ev.stopPropagation();
          const taskId = btn.getAttribute("data-office-run-task") || "";
          const tokenEl = floor.querySelector('input[data-office-token-for="' + cssEscape(taskId) + '"]');
          const token = tokenEl && tokenEl.value ? String(tokenEl.value).trim() : "";
          officeRunTaskById(taskId, token).catch(function () {});
        });
      });
      Object.keys(__officeAnim).forEach(function (k) { delete __officeAnim[k]; });
      officeRenderValidationDesk();
    }

    function officeUpsert(p, opts) {
      opts = opts || {};
      if (!p || !p.agent_id) return;
      const prev = __officeAgents.get(p.agent_id) || null;
      if (prev && !opts.silent) {
        if (prev.location && p.location && prev.location !== p.location) {
          __officeAnim[p.agent_id] = "office-card--walk";
        } else if (prev.status && p.status && prev.status !== p.status) {
          __officeAnim[p.agent_id] = "office-card--pulse";
        }
      }
      __officeAgents.set(p.agent_id, Object.assign({}, prev || {}, p));
      if (!opts.batch) {
        if (__officeView === "classic") officeRender();
        else officeSyncMap(true);
        if (__officeSelectedId === p.agent_id) officeSelectAgent(__officeAgents.get(p.agent_id));
      }
    }

    function officeApplySnapshot(snap) {
      if (!snap || !Array.isArray(snap.agents)) return;
      if (Array.isArray(snap.zones) && snap.zones.length) {
        __officeZoneState = new Map();
        __officeZones = snap.zones
          .slice()
          .sort(function (a, b) { return (a.sort_order || 0) - (b.sort_order || 0); })
          .map(function (z) {
            if (z && z.id) __officeZoneState.set(z.id, z);
            return [z.id, z.label || z.id];
          });
        try {
          if (window.LbgOfficeMap && typeof LbgOfficeMap.setZoneHostStates === "function") {
            LbgOfficeMap.setZoneHostStates(Array.from(__officeZoneState.values()));
          }
        } catch (_) {}
      }
      __officeAgents.clear();
      snap.agents.forEach(function (a) { officeUpsert(a, { silent: true, batch: true }); });
      if (__officeView === "classic") officeRender();
      else officeSyncMap(false);
      officeSetConn("mode " + (snap.mode || "live") + " · " + __officeAgents.size + " agents");
      const banner = document.getElementById("office-banner");
      if (banner && snap.mode === "mock") {
        banner.hidden = false;
        banner.textContent = "Mode mock — brancher Cortex pour le live.";
      } else if (banner) {
        banner.hidden = true;
      }
    }

    function officeStop() {
      try { if (window.LbgOfficeMap) LbgOfficeMap.stop(); } catch (_) {}
      __officeMapReady = false;
      if (__officeWs) {
        try { __officeWs.close(); } catch (_) {}
        __officeWs = null;
      }
      if (__officePoll) {
        window.clearInterval(__officePoll);
        __officePoll = null;
      }
      if (__officePing) {
        window.clearInterval(__officePing);
        __officePing = null;
      }
      if (__officeZonePoll) {
        window.clearInterval(__officeZonePoll);
        __officeZonePoll = null;
      }
      if (typeof __officeLyraPoll !== "undefined" && __officeLyraPoll) {
        window.clearInterval(__officeLyraPoll);
        __officeLyraPoll = null;
      }
      if (__officePlayerIaPoll) {
        window.clearInterval(__officePlayerIaPoll);
        __officePlayerIaPoll = null;
      }
    }

    async function officeFetchSnapshot() {
      const base = (typeof getBase === "function" ? getBase() : "").replace(/\/$/, "");
      const r = await fetch(base + "/v1/pilot/team/presence/snapshot");
      const data = await r.json();
      if (data && data.agents) officeApplySnapshot(data);
      else if (data && data.ok === false) {
        officeSetConn("snapshot KO — " + (data.error || r.status));
      }
    }

    function officeConnectWs() {
      const proto = location.protocol === "https:" ? "wss" : "ws";
      const url = proto + "://" + location.host + "/v1/pilot/team/presence/ws";
      try {
        const ws = new WebSocket(url);
        __officeWs = ws;
        ws.onopen = function () {
          officeSetConn('WS <strong style="color:#3ecf8e">live</strong>', true);
        };
        ws.onclose = function () {
          officeSetConn("WS coupé — polling 5s");
          if (!__officePoll) {
            __officePoll = window.setInterval(function () {
              officeFetchSnapshot().catch(function () {});
            }, 5000);
          }
        };
        ws.onerror = function () {
          officeSetConn("WS erreur — fallback poll");
        };
        ws.onmessage = function (ev) {
          try {
            const msg = JSON.parse(ev.data);
            if (msg.type === "snapshot") officeApplySnapshot(msg.payload || {});
            else if (msg.type === "presence") officeUpsert(msg.payload);
          } catch (_) {}
        };
        __officePing = window.setInterval(function () {
          if (ws.readyState === 1) ws.send("ping");
        }, 20000);
      } catch (e) {
        officeSetConn("WS indisponible — poll");
        if (!__officePoll) {
          __officePoll = window.setInterval(function () {
            officeFetchSnapshot().catch(function () {});
          }, 5000);
        }
      }
    }

    function officeBindPage() {
      officeStop();
      __officeView = officeParseView();
      const btnMap = document.getElementById("office-btn-map");
      const btnClassic = document.getElementById("office-btn-classic");
      if (btnMap && !btnMap._officeBound) {
        btnMap._officeBound = true;
        btnMap.addEventListener("click", function () {
          officeSetHashView("map");
          officeApplyView("map");
        });
      }
      if (btnClassic && !btnClassic._officeBound) {
        btnClassic._officeBound = true;
        btnClassic.addEventListener("click", function () {
          officeSetHashView("classic");
          officeApplyView("classic");
        });
      }
      const btnAct = document.getElementById("office-btn-act");
      const btnMission = document.getElementById("office-btn-mission");
      if (btnAct && !btnAct._officeBound) {
        btnAct._officeBound = true;
        btnAct.addEventListener("click", function () {
          officeLyraAct().catch(function () {});
        });
      }
      if (btnMission && !btnMission._officeBound) {
        btnMission._officeBound = true;
        btnMission.addEventListener("click", function () {
          officeLyraMission().catch(function () {});
        });
      }
      const btnClose = document.getElementById("office-btn-mission-close");
      if (btnClose && !btnClose._officeBound) {
        btnClose._officeBound = true;
        btnClose.addEventListener("click", function () {
          officeLyraCloseMission(false).catch(function () {});
        });
        btnClose.addEventListener("dblclick", function (ev) {
          ev.preventDefault();
          officeLyraCloseMission(true).catch(function () {});
        });
      }
      const btnApprove = document.getElementById("office-side-btn-approve");
      const btnRun = document.getElementById("office-side-btn-run");
      if (btnApprove && !btnApprove._officeBound) {
        btnApprove._officeBound = true;
        btnApprove.addEventListener("click", function () {
          officeApproveSelectedTask().catch(function () {});
        });
      }
      if (btnRun && !btnRun._officeBound) {
        btnRun._officeBound = true;
        btnRun.addEventListener("click", function () {
          officeRunSelectedTask().catch(function () {});
        });
      }
      officeApplyView(__officeView);
      officeFetchSnapshot()
        .catch(function () { officeSetConn("snapshot KO"); })
        .finally(function () { officeConnectWs(); });
      officeFetchPlayerIaRuntime().catch(function () {});
      if (__officePlayerIaPoll) window.clearInterval(__officePlayerIaPoll);
      __officePlayerIaPoll = window.setInterval(function () {
        officeFetchPlayerIaRuntime().catch(function () {});
      }, 8000);
      // Refresh zones (badge Éteinte Lab 245) même si le WS agents est live.
      if (__officeZonePoll) window.clearInterval(__officeZonePoll);
      __officeZonePoll = window.setInterval(function () {
        officeFetchSnapshot().catch(function () {});
      }, 45000);
      officeLyraRefresh().catch(function () {});
      if (__officeLyraPoll) window.clearInterval(__officeLyraPoll);
      __officeLyraPoll = window.setInterval(function () {
        officeLyraRefresh().catch(function () {});
      }, 20000);
    }

    let __officeLyraPoll = null;

    function officeLyraSetReport(text) {
      const el = document.getElementById("office-lyra-report");
      if (el) el.textContent = text || "—";
    }

    function officeLyraSetMode(mode, reason) {
      const el = document.getElementById("office-lyra-mode");
      if (!el) return;
      el.textContent = mode ? ("mode " + mode) : "mode —";
      el.title = reason || "";
    }

    async function officeLyraRefresh() {
      const out = await jobsGet(getBase() + "/v1/pilot/team/campus/status");
      const d = out.json || {};
      if (!d.ok && d.error) {
        officeLyraSetReport("status KO: " + d.error);
        return;
      }
      const dec = d.decision || {};
      officeLyraSetMode(dec.mode, dec.reason);
      const miss = d.mission || {};
      const lr = d.last_report || {};
      const lines = [
        (dec.reason || "—"),
        "busy=" + (d.busy_agent_count != null ? d.busy_agent_count : "?") +
          " queued=" + (d.queued_count != null ? d.queued_count : "?") +
          " café=" + ((d.coffee_fill || {}).coffee_idle != null ? d.coffee_fill.coffee_idle : "?"),
      ];
      if (miss.id) {
        lines.push("mission: " + (miss.status || "?") + " — " + String(miss.objective || "").slice(0, 60));
        const cl = d.mission_closure || {};
        if (cl.closable) {
          lines.push("clôturable → " + (cl.outcome || "?") + " (" + (cl.reason || "") + ")");
        } else if (cl.reason && cl.reason !== "no_open_mission") {
          lines.push("clôture: " + cl.reason);
        }
      }
      if (lr.outcome) lines.push("dernier: " + lr.outcome + (lr.acted_as ? " (" + lr.acted_as + ")" : ""));
      officeLyraSetReport(lines.join("\n"));
    }

    async function officeLyraCloseMission(force) {
      officeLyraSetReport(force ? "Clôture forcée…" : "Clôture mission…");
      const out = await postJson(
        getBase() + "/v1/pilot/team/campus/mission/close",
        { force: !!force, reason: force ? "pilot_force" : "pilot_ui" },
        30000
      );
      const d = out.json || {};
      if (d.error && d.ok === false) {
        officeLyraSetReport("Clôture KO: " + d.error + (d.evaluation ? " — " + JSON.stringify(d.evaluation.reason || d.evaluation) : ""));
        return;
      }
      const m = d.mission || {};
      officeLyraSetReport(
        "mission " + (m.status || "?") +
          " · " + String(m.close_reason || m.objective || "").slice(0, 80)
      );
      try { await officeFetchSnapshot(); } catch (_) {}
      try { await officeLyraRefresh(); } catch (_) {}
    }

    async function officeLyraAct() {
      officeLyraSetReport("Conduite en cours…");
      const out = await postJson(getBase() + "/v1/pilot/team/campus/act", { dry_run: false }, 60000);
      const d = out.json || {};
      if (d.error && !d.ok) {
        officeLyraSetReport("Erreur: " + d.error);
        return;
      }
      const dec = d.decision || {};
      officeLyraSetMode(dec.mode || d.acted_as, dec.reason);
      officeLyraSetReport(
        "outcome=" + (d.outcome || "?") +
          " mode=" + (d.acted_as || dec.mode || "?") +
          " started=" + ((d.started || []).length) +
          "\n" + (dec.reason || "")
      );
      try { await officeFetchSnapshot(); } catch (_) {}
    }

    async function officeLyraMission() {
      const input = document.getElementById("office-mission");
      const objective = ((input && input.value) || "").trim();
      if (!objective) {
        officeLyraSetReport("Saisis une mission NL d’abord.");
        return;
      }
      officeLyraSetReport("Mission — planification…");
      const out = await postJson(
        getBase() + "/v1/pilot/team/campus/mission",
        { objective: objective, dry_run: false, auto_act: true, max_tasks: 6 },
        90000
      );
      const d = out.json || {};
      if (d.error && d.ok === false) {
        officeLyraSetReport("Erreur: " + d.error);
        return;
      }
      const m = d.mission || {};
      const act = d.act || {};
      officeLyraSetMode((act.decision || d.decision || {}).mode, (act.decision || {}).reason);
      officeLyraSetReport(
        "mission " + (m.status || "?") + " · créées=" + ((d.created || []).length) +
          " · act=" + (act.outcome || "—") +
          "\n" + String(m.objective || objective).slice(0, 80)
      );
      try { await officeFetchSnapshot(); } catch (_) {}
    }

    const TEAM_ROLE_DEFAULTS = {
      qa: "Smoke LAN read-only (healthz + systemd via script si configuré)",
      ops: "Sonde santé orchestrateur et backend (read-only)",
      pm: "Brief jalons et prochaines tâches projet",
      pm_reunif: "Brief réunification sous-projets — jalons, statuts et prochaines actions (Thémis)",
      autoconsult: "Round autoconsultation Fable — Thémis + sondes Iris/Hermès/Pygmalion/Argus/Héphaïstos",
      evolution_sprint: "Sprint évolution 7j — audit full infra/Team/LLM/jeu + plan + L1 auto",
      godot_supervise: "Supervise client Godot — sidecar 246, miroir M1, readiness lbg-ws/2",
      godot_lbg_ws2: "Audit lbg-ws/2 gateway Godot Prime — gaps et proposition forge",
      infographiste_ia: "Audit pipeline assets Infographiste IA — manifest GLB Godot et prochain export Blender",
      mesh_3d: "Pygmalion — ComfyUI concept 2D + mesh TRELLIS.2 (worker GPU, L2 si activé)",
      soe_m3: "Audit SOE M3 — login + zone UDP Godot Prime (soe_handshake)",
      soe_m5: "Audit SOE M5 — play ZQSD prime_controller sur Prime",
      zb0_audit: "Audit ZB-0 LbgZoneBridge C++ — header et hook ZoneServer",
      zb1_audit: "Audit ZB-1 export JSON 20 Hz — gateway lbg-ws/2 live",
      parallel_prime: "Parallèle Vulcan plan build Core3 + audit ZB-1 gateway",
      m9_planete: "Audit M9a Scrapaltai — texture planète + POI sync + pipeline export Godot",
      m9_minimap: "Audit M9b minimap HUD — SubViewport coin écran style SWG",
      m9_carte_m: "Audit M9c carte planétaire M — waypoints + locations tree",
      m9_full: "Audit M9 complet — Scrapaltai 2D + minimap + carte M Prime Client",
      iris_m9: "Iris — audit M9 complet Scrapaltai (dev_godot)",
      iris_m9c: "Iris — audit M9c carte planétaire Ctrl+M + waypoints",
      iris_forge_m9: "Iris — forge GDScript M9 : sondes + patches staging depuis gaps",
      hermes_soe: "Hermès — audit SOE M3/M5 + ZB + gateway client live",
      client_live: "Audit client Godot live — M3 SOE + M5 play + ZB-0 + lbg-ws/2",
      validate_godot: "Valider client Godot — smokes LAN + checklist lancement Godot",
      core3_build_plan: "Plan build Core3 ZB-0 Antigravity (dry-run, Vulcan)",
      core3_build_compile: "Compiler Core3 ZB-0 sur Prime 246 — rsync + cmake (L2)",
      dev_game: "Analyser bug gameplay / correctif proposé (hors sandbox mmmorpg gelé)",
      dev_godot: "Iris/Hermès — audit Godot Prime Client (M9, SOE, gateway)",
      player_ia_probe: "Sonde joueurs IA Core3 Prime (246) — sidecar + snapshots Lia/Nix",
      player_ia_think: "Think/tick joueur IA Lia",
    };

    const TEAM_PRESETS = {
      smoke_lan: { role: "qa", objectiveKey: "qa", autoRun: true },
      probe_ia: { role: "player_ia", player_ia_mode: "probe", objectiveKey: "player_ia_probe", autoRun: true },
      brief_reunif: { role: "pm", objectiveKey: "pm_reunif", reunification: true, autoRun: true },
      autoconsult: { role: "pm", objectiveKey: "autoconsult", autoconsult: true, autoRun: true },
      evolution_sprint: { role: "pm", objectiveKey: "evolution_sprint", evolutionSprint: true, autoRun: true },
      godot_supervise: { role: "qa", objectiveKey: "godot_supervise", godotSupervisor: true, autoRun: true },
      godot_lbg_ws2: { role: "dev_game", objectiveKey: "godot_lbg_ws2", godotTrack: true, autoRun: true },
      infographiste_ia: { role: "dev_game", objectiveKey: "infographiste_ia", infographiste: true, autoRun: true },
      mesh_3d: { role: "dev_game", objectiveKey: "mesh_3d", infographiste: true, pygmalionMesh: true, autoRun: true },
      soe_m3: { role: "dev_game", objectiveKey: "soe_m3", godotTrackKey: "soe_m3", autoRun: true },
      soe_m5: { role: "dev_game", objectiveKey: "soe_m5", godotTrackKey: "soe_m5", autoRun: true },
      zb0_audit: { role: "dev_game", objectiveKey: "zb0_audit", godotTrackKey: "zb0", autoRun: true },
      zb1_audit: { role: "dev_game", objectiveKey: "zb1_audit", godotTrackKey: "zb1", autoRun: true },
      parallel_prime: { role: "dev_game", objectiveKey: "parallel_prime", parallelPrime: true, autoRun: true },
      m9_planete: { role: "dev_game", objectiveKey: "m9_planete", m9TrackKey: "m9a", autoRun: true },
      m9_minimap: { role: "dev_game", objectiveKey: "m9_minimap", m9TrackKey: "m9b", autoRun: true },
      m9_carte_m: { role: "dev_game", objectiveKey: "m9_carte_m", m9TrackKey: "m9c", autoRun: true },
      m9_full: { role: "dev_game", objectiveKey: "m9_full", m9TrackKey: "m9_full", autoRun: true },
      iris_m9: { role: "dev_godot", objectiveKey: "iris_m9", godotDevPersona: "iris", godotDevTrack: "m9_full", autoRun: true },
      iris_m9c: { role: "dev_godot", objectiveKey: "iris_m9c", godotDevPersona: "iris", godotDevTrack: "m9c", autoRun: true },
      iris_forge_m9: { role: "dev_godot", objectiveKey: "iris_forge_m9", godotDevPersona: "iris", godotDevTrack: "m9_full", irisForge: true, autoRun: true },
      hermes_soe: { role: "dev_godot", objectiveKey: "hermes_soe", godotDevPersona: "hermes", godotDevTrack: "client_live", autoRun: true },
      client_live: { role: "dev_game", objectiveKey: "client_live", godotTrackKey: "client_live", autoRun: true },
      validate_godot: { role: "qa", objectiveKey: "validate_godot", godotValidation: true, autoRun: true },
      core3_build_plan: { role: "dev_game", objectiveKey: "core3_build_plan", core3Build: true, autoRun: true },
      core3_build_compile: { role: "dev_game", objectiveKey: "core3_build_compile", core3BuildExecute: true, approvalRequired: true, autoRun: false },
      think_lia: { role: "player_ia", player_ia_mode: "think_tick", player_id: "lia", objectiveKey: "player_ia_think", autoRun: false },
    };

    function teamGetActor() {
      const el = document.getElementById("team-actor");
      return (el && el.value ? el.value.trim() : "") || "pilot:team";
    }

    function teamHint(msg, isError) {
      pilotInlineHint("team-create-hint", msg || "—", !!isError);
    }

    function teamApiError(out) {
      const j = out && out.json ? out.json : {};
      if (out && out.status === 0) return j.error || "réseau indisponible";
      if (j.detail) return typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail);
      if (j.error) return String(j.error);
      if (j.body) return String(j.body).slice(0, 240);
      return "HTTP " + (out && out.status ? out.status : "?");
    }

    function teamResponseOk(out) {
      return !!(out && out.status === 200 && out.json && out.json.ok !== false);
    }

    function teamDefaultObjective(role, mode) {
      if (__teamMetaRoles && __teamMetaRoles[role]) return __teamMetaRoles[role];
      if (role === "player_ia") {
        return mode === "think_tick" ? TEAM_ROLE_DEFAULTS.player_ia_think : TEAM_ROLE_DEFAULTS.player_ia_probe;
      }
      return TEAM_ROLE_DEFAULTS[role] || "";
    }

    function teamThinkObjective(playerId) {
      const p = (playerId || "lia").trim() || "lia";
      const cap = p.charAt(0).toUpperCase() + p.slice(1);
      return "Think/tick joueur IA " + cap;
    }

    function teamSyncFormUi() {
      const roleEl = document.getElementById("team-role");
      const role = roleEl ? roleEl.value : "qa";
      const wrap = document.getElementById("team-player-ia-wrap");
      const modeEl = document.getElementById("team-player-ia-mode");
      const mode = modeEl && modeEl.value ? String(modeEl.value) : "probe";
      const playerWrap = document.getElementById("team-player-id-wrap");
      if (wrap) wrap.hidden = role !== "player_ia";
      if (playerWrap) playerWrap.hidden = role !== "player_ia" || mode !== "think_tick";
      if (!__teamObjectiveCustom) {
        const objEl = document.getElementById("team-objective");
        if (objEl) {
          if (role === "player_ia" && mode === "think_tick") {
            const pidEl = document.getElementById("team-player-id");
            objEl.value = teamThinkObjective(pidEl ? pidEl.value : "lia");
          } else {
            objEl.value = teamDefaultObjective(role, mode);
          }
        }
      }
    }

    function teamApplyPreset(key, launch) {
      if (key === "plan_llm_demo") {
        const planEl = document.getElementById("team-plan-objective");
        const llmCk = document.getElementById("team-plan-use-llm");
        const demo =
          "l'équipe doit vérifier que tout fonctionne avant la démo de demain";
        if (planEl) planEl.value = demo;
        if (llmCk) llmCk.checked = true;
        const adv = document.getElementById("team-advanced");
        if (adv) adv.open = true;
        document.querySelectorAll("[data-team-preset]").forEach(function (btn) {
          btn.classList.toggle("preset--active", btn.getAttribute("data-team-preset") === key);
        });
        teamHint("Plan LLM démo — objectif NL sans mots-clés. Cliquez Proposer (ou double-clic preset).", false);
        if (launch) {
          teamPlan().catch(function () {});
        }
        return;
      }
      const preset = TEAM_PRESETS[key];
      if (!preset) return;
      __teamObjectiveCustom = false;
      __teamReunificationBrief = !!preset.reunification;
      __teamAutoconsult = !!preset.autoconsult;
      __teamEvolutionSprint = !!preset.evolutionSprint;
      __teamGodotSupervisor = !!preset.godotSupervisor;
      __teamGodotTrack = !!preset.godotTrack;
      __teamInfographiste = !!preset.infographiste;
      __teamPygmalionMesh = !!preset.pygmalionMesh;
      __teamGodotTrackKey = preset.godotTrackKey ? String(preset.godotTrackKey) : "";
      __teamCore3Build = !!preset.core3Build;
      __teamCore3BuildExecute = !!preset.core3BuildExecute;
      __teamGodotValidation = !!preset.godotValidation;
      __teamParallelPrime = !!preset.parallelPrime;
      __teamM9TrackKey = preset.m9TrackKey ? String(preset.m9TrackKey) : "";
      __teamGodotDevPersona = preset.godotDevPersona ? String(preset.godotDevPersona) : "";
      __teamGodotDevTrack = preset.godotDevTrack ? String(preset.godotDevTrack) : "";
      __teamIrisForge = !!preset.irisForge;
      const apprEl = document.getElementById("team-approval-required");
      if (apprEl) {
        apprEl.checked = !!preset.approvalRequired || preset.player_ia_mode === "think_tick";
      }
      const roleEl = document.getElementById("team-role");
      if (roleEl) roleEl.value = preset.role;
      const modeEl = document.getElementById("team-player-ia-mode");
      if (modeEl && preset.player_ia_mode) modeEl.value = preset.player_ia_mode;
      const pidEl = document.getElementById("team-player-id");
      if (pidEl && preset.player_id) pidEl.value = preset.player_id;
      teamSyncFormUi();
      if (preset.objectiveKey) {
        const def = TEAM_ROLE_DEFAULTS[preset.objectiveKey];
        const objEl = document.getElementById("team-objective");
        if (def && objEl) objEl.value = def;
      }
      document.querySelectorAll("[data-team-preset]").forEach(function (btn) {
        btn.classList.toggle("preset--active", btn.getAttribute("data-team-preset") === key);
      });
      if (launch) {
        if (__teamParallelPrime) {
          (async function () {
            __teamCore3Build = true;
            __teamCore3BuildExecute = false;
            __teamGodotTrackKey = "";
            const objEl = document.getElementById("team-objective");
            if (objEl) objEl.value = TEAM_ROLE_DEFAULTS.core3_build_plan || objEl.value;
            await teamCreate({ autoRun: true });
            __teamCore3Build = false;
            __teamGodotTrackKey = "zb1";
            if (objEl) objEl.value = TEAM_ROLE_DEFAULTS.zb1_audit || objEl.value;
            await teamCreate({ autoRun: true });
            __teamParallelPrime = false;
          })().catch(function () {});
        } else {
          teamCreate({ autoRun: true }).catch(function () {});
        }
      }
    }

    function teamBuildPayload() {
      const roleEl = document.getElementById("team-role");
      const objEl = document.getElementById("team-objective");
      const role = roleEl ? roleEl.value : "qa";
      const objective = objEl && objEl.value ? objEl.value.trim() : "";
      const ctx = {};
      if (role === "player_ia") {
        const modeEl = document.getElementById("team-player-ia-mode");
        const mode = modeEl && modeEl.value ? String(modeEl.value) : "probe";
        ctx.player_ia_mode = mode;
        if (mode === "think_tick") {
          const pidEl = document.getElementById("team-player-id");
          const pid = pidEl && pidEl.value ? String(pidEl.value).trim() : "";
          if (pid) ctx.player_id = pid;
          else {
            const m = objective.toLowerCase();
            ["lia", "nix", "mira", "kael"].forEach(function (p) {
              if (m.indexOf(p) >= 0) ctx.player_id = p;
            });
          }
        }
      }
      if (__teamReunificationBrief || /réunification|reunification/i.test(objective)) {
        ctx.reunification_brief = true;
        ctx.pm_include_plan = true;
        ctx.pm_include_structure = true;
      }
      if (__teamAutoconsult || /autoconsult/i.test(objective)) {
        ctx.autoconsult_round = true;
        ctx.reunification_brief = true;
        ctx.pm_include_plan = true;
      }
      if (__teamEvolutionSprint || /sprint.?évolution|sprint.?evolution|evolution_sprint|amélioration continue/i.test(objective)) {
        ctx.evolution_sprint = true;
        ctx.reunification_brief = true;
        ctx.pm_include_plan = true;
      }
      if (__teamGodotSupervisor || /supervise.*godot|godot.*supervise/i.test(objective)) {
        ctx.godot_supervisor = true;
        ctx.godot_mode = "full";
      }
      if (__teamGodotTrack || role === "dev_game" && /lbg-ws|lbg_ws|godot|gateway|zone.bridge/i.test(objective)) {
        ctx.godot_track = "lbg_ws2";
      }
      if (__teamGodotValidation || /valider.*godot|validation.*client/i.test(objective)) {
        ctx.godot_validation = true;
      }
      if (__teamCore3Build || __teamCore3BuildExecute || /build.*core3|plan build.*zb/i.test(objective)) {
        ctx.core3_build = true;
        ctx.subproject = "core3_build";
        ctx.dev_game_focus = true;
        if (__teamCore3BuildExecute || /compiler core3|build réel/i.test(objective)) {
          ctx.core3_build_execute = true;
        }
        if (/parallel|poll.*log/i.test(objective)) {
          ctx.parallel_prime = true;
          ctx.poll_build_log = true;
        }
      }
      if (__teamGodotTrackKey) {
        ctx.godot_track = __teamGodotTrackKey;
        ctx.subproject = "client_godot";
        ctx.dev_game_focus = true;
      }
      if (__teamM9TrackKey) {
        ctx.m9_track = __teamM9TrackKey;
        ctx.subproject = "prime_client_2d";
        ctx.dev_game_focus = true;
      }
      if (__teamGodotDevPersona) {
        ctx.godot_dev_persona = __teamGodotDevPersona;
        ctx.godot_dev_track = __teamGodotDevTrack || "iris_full";
        ctx.subproject = __teamGodotDevPersona === "hermes" ? "godot_hermes" : "godot_iris";
        ctx.dev_godot_focus = true;
      }
      if (__teamIrisForge || /iris forge|forge gdscript|forge m9/i.test(objective)) {
        ctx.iris_forge = true;
      }
      if (__teamInfographiste || /infographiste|infograph|pipeline.?assets|\.glb|blender|assets? 3d/i.test(objective)) {
        ctx.infographiste_ia = true;
        ctx.subproject = "infographiste_ia";
        ctx.dev_game_focus = true;
      }
      if (__teamPygmalionMesh || /trellis|mesh.?3d|image.?to.?3d/i.test(objective)) {
        ctx.pygmalion_mesh = true;
        ctx.mesh_3d = true;
        ctx.pygmalion_generate = true;
        ctx.infographiste_ia = true;
        ctx.subproject = "infographiste_ia";
      }
      const payload = {
        role: role,
        objective: objective,
        actor_id: teamGetActor(),
        context: ctx,
      };
      const apprEl = document.getElementById("team-approval-required");
      if (apprEl && apprEl.checked) payload.approval_required = true;
      const tokEl = document.getElementById("team-create-token");
      const tok = tokEl && tokEl.value ? tokEl.value.trim() : "";
      if (tok) payload.approval_token = tok;
      return payload;
    }

    function teamLikelyNeedsApproval(payload) {
      if (payload.approval_required === true) return true;
      if (payload.role === "player_ia" && payload.context && payload.context.player_ia_mode === "think_tick") return true;
      return false;
    }

    function teamCanAutoRun(payload) {
      if (!teamLikelyNeedsApproval(payload)) return true;
      return !!payload.approval_token;
    }

    async function teamLoadMeta() {
      const out = await jobsGet(getBase() + "/v1/pilot/team/meta");
      if (!teamResponseOk(out)) return;
      const roles = (out.json && out.json.roles) || [];
      const map = {};
      roles.forEach(function (r) {
        if (r.role && r.default_objective) map[r.role] = String(r.default_objective);
      });
      __teamMetaRoles = map;
      try {
        const feats = (out.json && out.json.features) || {};
        const traces = feats.traces || {};
        const el = document.getElementById("team-meta-metrics");
        if (el) {
          const nLessons = traces.lessons_count != null ? traces.lessons_count : "—";
          const nGolden = traces.golden_cases != null ? traces.golden_cases : "—";
          const last = traces.last_judge || {};
          const score =
            last && last.score != null ? Number(last.score).toFixed(2) : "—";
          const passed = last && last.pass != null ? (last.pass ? "pass" : "fail") : "—";
          const lastM = traces.last_mutation || {};
          const mut =
            lastM && lastM.candidate_ready
              ? " · mutation candidat"
              : lastM && lastM.run_id
                ? " · mutation ok"
                : "";
          const lastP = traces.last_proposal || {};
          const prop = lastP && lastP.slug ? " · proposal " + lastP.slug : "";
          el.textContent =
            "Miroir / leçons : " +
            nLessons +
            " leçon(s) · golden " +
            nGolden +
            " · dernier juge score=" +
            score +
            " (" +
            passed +
            ")" +
            mut +
            prop;
        }
      } catch (_) {}
      teamSyncFormUi();
    }

    async function teamListRefresh() {
      const list = document.getElementById("team-list");
      if (!list) return;
      const role = (document.getElementById("team-filter-role") || {}).value || "";
      const status = (document.getElementById("team-filter-status") || {}).value || "";
      const actor = (document.getElementById("team-filter-actor") || {}).value || "";
      let url = getBase() + "/v1/pilot/team/tasks?limit=50";
      if (role) url += "&role=" + encodeURIComponent(role);
      if (status) url += "&status=" + encodeURIComponent(status);
      if (actor.trim()) url += "&actor_id=" + encodeURIComponent(actor.trim());
      const out = await jobsGet(url);
      const data = out.json || {};
      if (!data.ok && data.tasks === undefined) {
        list.textContent = data.error || "erreur chargement";
        return;
      }
      const tasks = data.tasks || [];
      if (!tasks.length) { list.textContent = "Aucune tâche."; return; }
      list.innerHTML = tasks.map(function (t) {
        const active = t.id === __teamSelectedId ? " jobs-card--active" : "";
        const appr = t.approval_required ? " · L2" : "";
        return '<button type="button" class="jobs-card' + active + '" data-team-id="' + escapeHtmlPm(t.id) + '">' +
          '<strong>' + escapeHtmlPm(t.role_label || t.role_alias || t.role) + '</strong> · ' + escapeHtmlPm(t.status) + appr +
          '<br><span class="muted" style="font-size:0.82rem;">' + escapeHtmlPm((t.actor_id || "") + " — " + (t.objective || "")).slice(0, 96) + '</span></button>';
      }).join("");
      list.querySelectorAll("[data-team-id]").forEach(function (btn) {
        btn.addEventListener("click", function () {
          teamSelect(btn.getAttribute("data-team-id"));
        });
      });
    }

    async function teamLoadMessages(task) {
      const pre = document.getElementById("team-detail-messages");
      if (!pre || !task || !task.id) return;
      pre.textContent = "…";
      const ids = [task.id];
      const parent = task.context && task.context.parent_task_id ? String(task.context.parent_task_id) : "";
      if (parent && parent !== task.id) ids.push(parent);
      const all = [];
      for (let i = 0; i < ids.length; i++) {
        const tid = ids[i];
        try {
          const out = await jobsGet(
            getBase() + "/v1/pilot/team/messages?task_id=" + encodeURIComponent(tid) + "&limit=40"
          );
          const msgs = (out.json && out.json.messages) || [];
          msgs.forEach(function (m) {
            all.push(Object.assign({ _scope: tid === task.id ? "task" : "parent" }, m));
          });
        } catch (_) {}
      }
      all.sort(function (a, b) {
        return (b.created_ts || 0) - (a.created_ts || 0);
      });
      if (!all.length) {
        pre.textContent = "(aucun message bus pour cette tâche)";
        return;
      }
      pre.textContent = all.slice(0, 40).map(function (m) {
        const scope = m._scope === "parent" ? "↑parent " : "";
        const pay = m.payload && typeof m.payload === "object"
          ? JSON.stringify(m.payload).slice(0, 140)
          : "";
        return scope + (m.kind || "?") + " " + (m.from_agent || "?") + "→" + (m.to_agent || "?") +
          (pay ? " " + pay : "");
      }).join("\n");
    }

    async function teamSelect(id, opts) {
      if (!id) return;
      __teamSelectedId = id;
      const syncHash = !(opts && opts.skipHash);
      if (syncHash) {
        try { teamSetHashTask(id); } catch (_) {}
      }
      const out = await jobsGet(getBase() + "/v1/pilot/team/tasks/" + encodeURIComponent(id));
      const t = out.json || {};
      const empty = document.getElementById("team-detail-empty");
      const detail = document.getElementById("team-detail");
      if (!t.id) {
        if (empty) { empty.hidden = false; empty.textContent = t.error || "introuvable"; }
        if (detail) detail.hidden = true;
        return;
      }
      if (empty) empty.hidden = true;
      if (detail) detail.hidden = false;
      const obj = document.getElementById("team-detail-objective");
      const meta = document.getElementById("team-detail-meta");
      const res = document.getElementById("team-detail-result");
      const sum = document.getElementById("team-detail-summary");
      if (obj) obj.textContent = t.objective || "";
      if (meta) {
        let m = (t.role_label || t.role) + " · id=" + t.id + " · status=" + t.status + " · actor=" + (t.actor_id || "");
        if (t.approval_required) m += " · approbation L2 requise";
        if (t.context && t.context._qa_followup_task_ids) {
          m += " · suivi: " + t.context._qa_followup_task_ids.join(", ");
        }
        meta.textContent = m;
      }
      if (sum) {
        const hs = t.result && t.result.human_summary ? String(t.result.human_summary) : "";
        sum.textContent = hs || "—";
        sum.hidden = !hs;
      }
      await teamLoadMessages(t);
      if (res) res.textContent = JSON.stringify(t.result || {}, null, 2);
      __teamLastForgePatch = null;
      const forgeBtn = document.getElementById("btn-team-forge-assistant");
      const forgeHint = document.getElementById("team-forge-hint");
      const prop =
        t.result && t.result.action_proposal && typeof t.result.action_proposal === "object"
          ? t.result.action_proposal
          : null;
      if (prop && prop.context_patch && typeof prop.context_patch === "object") {
        __teamLastForgePatch = prop.context_patch;
        if (forgeBtn) forgeBtn.hidden = false;
        if (forgeHint) {
          forgeHint.hidden = false;
          forgeHint.textContent =
            "Forge : " +
            String(prop.summary || prop.capability || "prototype_game") +
            " (dry-run — voir action_proposal dans le JSON).";
        }
      } else {
        if (forgeBtn) forgeBtn.hidden = true;
        if (forgeHint) {
          if (t.result && t.result.forge_note) {
            forgeHint.hidden = false;
            forgeHint.textContent = String(t.result.forge_note);
          } else {
            forgeHint.hidden = true;
            forgeHint.textContent = "";
          }
        }
      }
      await teamListRefresh();
    }

    function teamForgeToAssistant() {
      if (!__teamLastForgePatch || typeof __teamLastForgePatch !== "object") {
        teamHint("Aucune proposition forge dans la tâche sélectionnée.", true);
        return;
      }
      let ctx = {};
      try {
        ctx = assistantParseJsonTextarea("assistant-context", {});
        if (!ctx || typeof ctx !== "object" || Array.isArray(ctx)) ctx = {};
      } catch (_) {
        ctx = {};
      }
      Object.assign(ctx, __teamLastForgePatch);
      const ctxEl = document.getElementById("assistant-context");
      if (ctxEl) ctxEl.value = JSON.stringify(ctx, null, 2);
      teamHint("context_patch forge copié — ouvrez #/assistant pour dry-run.", false);
      location.hash = "#/assistant";
    }

    async function teamCreate(opts) {
      const options = opts || {};
      const payload = teamBuildPayload();
      if (!payload.objective) { teamHint("Objectif vide.", true); return null; }
      const needsApproval = teamLikelyNeedsApproval(payload);
      const autoRun = options.autoRun === true && teamCanAutoRun(payload);
      teamHint(autoRun ? "Création et exécution…" : "Création…");
      const out = await postJson(getBase() + "/v1/pilot/team/tasks", payload, 60000);
      if (!teamResponseOk(out) || !out.json.id) {
        teamHint("Échec création : " + teamApiError(out), true);
        return null;
      }
      const task = out.json;
      __teamSelectedId = task.id || null;
      if (autoRun) {
        teamHint("Exécution…");
        const runOut = await postJson(
          getBase() + "/v1/pilot/team/tasks/" + encodeURIComponent(task.id) + "/run",
          payload.approval_token ? { approval_token: payload.approval_token } : {},
          300000
        );
        if (!teamResponseOk(runOut)) {
          teamHint("Créée mais exécution échouée : " + teamApiError(runOut), true);
          await teamListRefresh();
          await teamSelect(task.id);
          return task;
        }
        const ran = runOut.json || {};
        const st = ran.status || "";
        if (st === "review" || ran.approval_required) {
          teamHint("Tâche créée — approbation L2 requise (détail → Approuver → Exécuter).", false);
        } else {
          teamHint(st === "done" ? "Terminé (" + task.id + ")" : "Statut : " + (st || "?"), st === "failed");
        }
        await teamSelect(task.id);
        return ran;
      }
      if (needsApproval) {
        teamHint("Tâche créée (" + task.id + ") — approbation L2 : détail → token → Approuver → Exécuter.", false);
      } else {
        teamHint("Tâche créée (" + task.id + "). Cliquez Lancer ou Exécuter dans le détail.", false);
      }
      await teamListRefresh();
      await teamSelect(task.id);
      return task;
    }

    async function teamPlan() {
      const el = document.getElementById("team-plan-objective");
      const objective = el && el.value ? el.value.trim() : "";
      if (!objective) { teamHint("Objectif NL vide.", true); return; }
      const llmCk = document.getElementById("team-plan-use-llm");
      const forceLlm = !!(llmCk && llmCk.checked);
      const body = {
        objective: objective,
        actor_id: teamGetActor(),
      };
      if (forceLlm) body.use_llm = true;
      teamHint(forceLlm ? "Planification LLM…" : "Planification…");
      const badge = document.getElementById("team-plan-source-badge");
      if (badge) badge.textContent = "source: …";
      const out = await postJson(getBase() + "/v1/pilot/team/plan", body, 120000);
      const pre = document.getElementById("team-plan-out");
      if (!teamResponseOk(out)) {
        if (pre) pre.textContent = teamApiError(out);
        if (badge) badge.textContent = "source: erreur";
        teamHint("Échec plan : " + teamApiError(out), true);
        return;
      }
      const data = out.json || {};
      const source = data.source || "heuristic";
      const proposals = data.proposals || [];
      if (badge) {
        badge.textContent = "source: " + source + " · " + proposals.length + " prop.";
      }
      const lines = proposals.map(function (p, i) {
        const role = p.role_label || p.alias || p.role || "?";
        const rat = p.rationale ? " — " + String(p.rationale).slice(0, 120) : "";
        const src = p.plan_source ? " [" + p.plan_source + "]" : "";
        return (i + 1) + ". " + role + src + ": " + (p.objective || "") + rat;
      });
      if (pre) {
        pre.textContent =
          (lines.length ? lines.join("\n") : "(aucune)") +
          "\n\n— meta —\n" +
          JSON.stringify(data.meta || {}, null, 2);
      }
      teamHint(proposals.length + " proposition(s) · source " + source + ".", false);
    }

    async function teamRun() {
      if (!__teamSelectedId) return;
      const tok = (document.getElementById("team-approve-token") || {}).value || "";
      const createTok = (document.getElementById("team-create-token") || {}).value || "";
      const token = tok.trim() || createTok.trim();
      const body = token ? { approval_token: token } : {};
      teamHint("Exécution…");
      const out = await postJson(
        getBase() + "/v1/pilot/team/tasks/" + encodeURIComponent(__teamSelectedId) + "/run",
        body,
        300000
      );
      if (!teamResponseOk(out)) {
        teamHint("Échec exécution : " + teamApiError(out), true);
        return;
      }
      const data = out.json || {};
      await teamSelect(__teamSelectedId);
      const st = data.status || "";
      if (st === "review") teamHint("En attente d'approbation L2.", false);
      else teamHint(st === "done" ? "Terminé" : ("Statut : " + (st || "—")), st === "failed");
    }

    async function teamApprove() {
      if (!__teamSelectedId) return;
      const tok = (document.getElementById("team-approve-token") || {}).value || "";
      const createTok = (document.getElementById("team-create-token") || {}).value || "";
      const token = tok.trim() || createTok.trim();
      if (!token) { teamHint("Token requis (détail ou options avancées).", true); return; }
      teamHint("Approbation…");
      const out = await postJson(
        getBase() + "/v1/pilot/team/tasks/" + encodeURIComponent(__teamSelectedId) + "/approve",
        { token: token },
        30000
      );
      if (!teamResponseOk(out)) {
        teamHint("Échec approbation : " + teamApiError(out), true);
        return;
      }
      teamHint("Approuvée — vous pouvez Exécuter.", false);
      await teamSelect(__teamSelectedId);
    }

    async function teamCancel() {
      if (!__teamSelectedId) return;
      teamHint("Annulation…");
      const out = await postJson(
        getBase() + "/v1/pilot/team/tasks/" + encodeURIComponent(__teamSelectedId) + "/cancel",
        {},
        30000
      );
      if (!teamResponseOk(out)) {
        teamHint("Échec annulation : " + teamApiError(out), true);
        return;
      }
      teamHint("Annulée.", false);
      await teamSelect(__teamSelectedId);
    }

    function teamBindPage() {
      if (__teamBound) return;
      __teamBound = true;
      const bLaunch = document.getElementById("btn-team-launch");
      const bCreate = document.getElementById("btn-team-create");
      const bPlan = document.getElementById("btn-team-plan");
      const bRefresh = document.getElementById("btn-team-refresh");
      const bRun = document.getElementById("btn-team-run");
      const bApprove = document.getElementById("btn-team-approve");
      const bCancel = document.getElementById("btn-team-cancel");
      const roleEl = document.getElementById("team-role");
      const modeEl = document.getElementById("team-player-ia-mode");
      const pidEl = document.getElementById("team-player-id");
      const objEl = document.getElementById("team-objective");
      if (bLaunch) bLaunch.addEventListener("click", function () {
        const payload = teamBuildPayload();
        teamCreate({ autoRun: teamCanAutoRun(payload) }).catch(function () {});
      });
      if (bCreate) bCreate.addEventListener("click", function () { teamCreate({ autoRun: false }).catch(function () {}); });
      if (bPlan) bPlan.addEventListener("click", function () { teamPlan().catch(function () {}); });
      if (bRefresh) bRefresh.addEventListener("click", function () { teamListRefresh(); });
      document.querySelectorAll("[data-team-preset]").forEach(function (btn) {
        btn.addEventListener("click", function () {
          teamApplyPreset(btn.getAttribute("data-team-preset"), false);
        });
        btn.addEventListener("dblclick", function () {
          teamApplyPreset(btn.getAttribute("data-team-preset"), true);
        });
      });
      if (roleEl) roleEl.addEventListener("change", function () {
        __teamObjectiveCustom = false;
        __teamReunificationBrief = false;
        __teamAutoconsult = false;
        __teamEvolutionSprint = false;
        __teamGodotSupervisor = false;
        __teamGodotTrack = false;
        __teamInfographiste = false;
        __teamPygmalionMesh = false;
        __teamGodotTrackKey = "";
        __teamCore3Build = false;
        __teamCore3BuildExecute = false;
        __teamGodotValidation = false;
        __teamParallelPrime = false;
        teamSyncFormUi();
      });
      if (modeEl) modeEl.addEventListener("change", function () { __teamObjectiveCustom = false; teamSyncFormUi(); });
      if (pidEl) pidEl.addEventListener("change", function () { __teamObjectiveCustom = false; teamSyncFormUi(); });
      if (objEl) objEl.addEventListener("input", function () { __teamObjectiveCustom = true; });
      ["team-filter-role", "team-filter-status", "team-filter-actor"].forEach(function (id) {
        const el = document.getElementById(id);
        if (el) el.addEventListener("change", function () { teamListRefresh(); });
        if (el && el.tagName === "INPUT") el.addEventListener("keyup", function (ev) {
          if (ev.key === "Enter") teamListRefresh();
        });
      });
      if (bRun) bRun.addEventListener("click", function () { teamRun().catch(function () {}); });
      if (bApprove) bApprove.addEventListener("click", function () { teamApprove().catch(function () {}); });
      if (bCancel) bCancel.addEventListener("click", function () { teamCancel().catch(function () {}); });
      const bForge = document.getElementById("btn-team-forge-assistant");
      if (bForge) bForge.addEventListener("click", function () { teamForgeToAssistant(); });
      teamSyncFormUi();
      teamLoadMeta().catch(function () {});
    }

    /* ===================== Métriques Team (#/team/metrics) ===================== */
    let __teamMetricsBound = false;

    function teamMetricsFmt(obj) {
      try {
        return JSON.stringify(obj == null ? {} : obj, null, 2);
      } catch (_) {
        return String(obj);
      }
    }

    async function teamMetricsRefresh() {
      const out = await jobsGet(getBase() + "/v1/pilot/team/meta");
      const feats = (out.json && out.json.features) || {};
      const traces = feats.traces || {};
      const judgeEl = document.getElementById("metrics-judge");
      const lessonsEl = document.getElementById("metrics-lessons");
      const mutEl = document.getElementById("metrics-mutation");
      const propEl = document.getElementById("metrics-proposal");
      const rawEl = document.getElementById("metrics-raw");
      if (judgeEl) {
        const j = traces.last_judge || (feats.outcome_judge && feats.outcome_judge.last_judge) || {};
        judgeEl.textContent =
          "golden_cases: " +
          (traces.golden_cases != null ? traces.golden_cases : "—") +
          "\nlast_judge.score: " +
          (j.score != null ? j.score : "—") +
          "\npass: " +
          (j.pass != null ? j.pass : "—") +
          "\nmode: " +
          (j.mode || "—") +
          "\ntask: " +
          (j.task_id || "—");
      }
      if (lessonsEl) {
        const L = feats.lessons_learned || {};
        lessonsEl.textContent =
          "count: " +
          (traces.lessons_count != null ? traces.lessons_count : L.count != null ? L.count : "—") +
          "\nenabled: " +
          (L.enabled != null ? L.enabled : "—") +
          "\npath: " +
          (L.path || "—");
      }
      if (mutEl) {
        const m = traces.last_mutation || {};
        mutEl.textContent =
          "run_id: " +
          (m.run_id || "—") +
          "\ncandidate: " +
          (m.candidate_ready != null ? m.candidate_ready : "—") +
          "\nwinner: " +
          ((m.winner && m.winner.id) || "—") +
          "\nΔscore: " +
          ((m.winner && m.winner.score_delta) || "—") +
          "\nsmoke_task: " +
          (m.smoke_task_id || "—") +
          "\nl2: " +
          (m.l2_task_id || "—");
      }
      if (propEl) {
        const p = traces.last_proposal || {};
        propEl.textContent =
          "slug: " +
          (p.slug || "—") +
          "\ntitle: " +
          (p.title || "—") +
          "\nbible_ok: " +
          (p.bible_ok != null ? p.bible_ok : "—") +
          "\nsmoke_task: " +
          (p.smoke_task_id || "—") +
          "\nl2: " +
          (p.l2_task_id || "—") +
          "\nbranch: " +
          ((p.branch && p.branch.branch) || "—");
      }
      if (rawEl) {
        rawEl.textContent = teamMetricsFmt({
          traces: traces,
          outcome_judge: feats.outcome_judge,
          lessons_learned: feats.lessons_learned,
          agent_mutator: feats.agent_mutator,
          feature_proposer: feats.feature_proposer,
        });
      }
    }

    function teamMetricsBindPage() {
      if (!__teamMetricsBound) {
        __teamMetricsBound = true;
        const btn = document.getElementById("btn-metrics-refresh");
        if (btn) btn.addEventListener("click", function () { teamMetricsRefresh().catch(function () {}); });
      }
      teamMetricsRefresh().catch(function () {});
    }

    /* ===================== Jobs autonomes ("type Cowork") ===================== */
    let __jobsPoll = null;
    let __jobsSelectedId = null;
    let __jobsSelectedJob = null;
    let __jobsEventSource = null;
    let __jobsBound = false;
    let __jobsCatalogJsonCopy = null;
    let __jobsDevicesJsonCopy = null;

