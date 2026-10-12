    /* ===================== Bureau Team (presence) ===================== */
    let __officeWs = null;
    let __officePoll = null;
    let __officeAgents = new Map();
    /** L2 pending depuis GET /v1/pilot/team/fleet (complète la présence bureau). */
    let __officeFleetL2 = [];
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

    function officeIsBridgeAgent(agent) {
      if (!agent) return false;
      const role = String(agent.role || "");
      const aid = String(agent.agent_id || "");
      return role === "player_bridge" || aid.indexOf("player_bridge_") === 0;
    }

    function officeHubBotForBridge(agent) {
      const rt = __officePlayerIa;
      const bots = rt && Array.isArray(rt.bots) ? rt.bots : [];
      if (!bots.length || !agent) return null;
      const aid = String(agent.agent_id || "");
      const login = String(agent.account_login || agent.persona || "");
      const ig = String(agent.mmo_player || "").toLowerCase();
      for (let i = 0; i < bots.length; i++) {
        const b = bots[i];
        if (!b) continue;
        if (aid && String(b.agent_id || "") === aid) return b;
        if (login && String(b.account_login || "") === login) return b;
        if (ig && String(b.display_name || b.id || "").toLowerCase() === ig) return b;
      }
      return null;
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
        const parts = [
          officeEsc(agent.location || "?"),
          agent.host_hint ? officeEsc(agent.host_hint) : "",
        ];
        if (officeIsBridgeAgent(agent)) {
          const login = agent.account_login || agent.persona || "";
          const ig = agent.mmo_player || "";
          const studio = agent.linked_studio_display || "";
          const bot = officeHubBotForBridge(agent);
          if (login) parts.push("login=" + officeEsc(login));
          if (ig) parts.push("IG=" + officeEsc(ig));
          if (studio) parts.push("↔ " + officeEsc(studio));
          if (bot) {
            const zone = bot.zone_display || bot.zone || bot.play_mode || "hub";
            parts.push(bot.online ? ("en hub · " + officeEsc(String(zone))) : "hors hub");
            if (bot.admin_level != null) parts.push("admin=" + officeEsc(String(bot.admin_level)));
          } else {
            parts.push("hub: —");
          }
        } else if (agent.mmo_player || agent.mmo_account_login) {
          if (agent.mmo_player) parts.push("IG=" + officeEsc(String(agent.mmo_player)));
          if (agent.mmo_account_login) parts.push("login=" + officeEsc(String(agent.mmo_account_login)));
          if (agent.bridge_agent_id) parts.push("pont=" + officeEsc(String(agent.bridge_agent_id)));
        }
        if (tid) {
          parts.push(
            '<a href="' + officeEsc(teamTaskHref(tid)) + '" title="Ouvrir la tâche">' +
              "#" + officeEsc(tid.slice(0, 8)) + "</a>"
          );
        }
        meta.innerHTML = parts.filter(Boolean).join(" · ");
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
      (__officeFleetL2 || []).forEach(function (t) {
        if (!t || typeof t !== "object") return;
        const tid = String(t.id || t.task_id || "");
        if (!tid || seen.has(tid)) return;
        seen.add(tid);
        const st = String(t.status || "").toLowerCase();
        const awaitingRun = st === "queued" && t.approval_required && t.stored_approval_token;
        rows.push({
          task_id: tid,
          label: t.role_label || t.role || "Team",
          role: t.role || "",
          action: (t.objective || "Validation L2").slice(0, 120),
          location: "fleet",
          awaiting_run: !!awaitingRun,
          awaiting_human_approval: st === "review" || (t.approval_required && !awaitingRun),
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

    function officeBridgeStripHtml(agents) {
      const list = Array.isArray(agents) ? agents.filter(officeIsBridgeAgent) : [];
      const rt = __officePlayerIa;
      const hubOk = !rt || rt.sidecar_ok !== false;
      let linked = 0;
      list.forEach(function (a) { if (officeHubBotForBridge(a)) linked += 1; });
      const head = hubOk
        ? (linked + "/" + list.length + " liés hub")
        : "prime-hub KO";
      const chips = list.length
        ? list.map(officeBridgeChipHtml).join("")
        : '<span class="muted" style="font-size:0.72rem;">aucun pont</span>';
      return (
        '<div class="office-pia-strip office-pia-strip--compact office-bridge-strip" title="Personas out-game — login=*_bridge · pont In↔Out">' +
          '<span class="office-pia-label">Ponts out-game</span>' +
          '<span class="office-pia-count' + (hubOk ? "" : " office-pia-count--ko") + '">' + officeEsc(head) + "</span>" +
          '<div class="office-pia-chips">' + chips + "</div>" +
        "</div>"
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
              const isBridge = officeIsBridgeAgent(a);
              const hubBot = isBridge ? officeHubBotForBridge(a) : null;
              const login = isBridge ? (a.account_login || a.persona || "") : "";
              const ig = isBridge ? (a.mmo_player || "") : "";
              const studioLink = isBridge ? (a.linked_studio_display || "") : "";
              const roleTag = isBridge
                ? (login ? ("login " + login) : (a.role || a.agent_id))
                : (a.role || a.agent_id);
              const actionTxt = isBridge
                ? (
                    (ig ? ("IG " + ig) : "Pont out-game") +
                    (studioLink ? (" ↔ " + studioLink) : "") +
                    (hubBot && hubBot.online
                      ? (" · " + (hubBot.zone_display || hubBot.zone || hubBot.play_mode || "hub"))
                      : " · hors hub")
                  )
                : (a.current_action || "—");
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
                  (isBridge ? " office-card--bridge" : "") +
                  (hubBot && hubBot.online ? " office-card--hub-on" : "") +
                  '" data-agent-id="' + officeEsc(a.agent_id) + '">' +
                  '<div class="office-avatar" aria-hidden="true">' +
                    officeEsc(officeInitials(ig || a.display_name || a.agent_id)) +
                    '<span class="busy-ring"></span>' +
                  "</div>" +
                  '<div class="office-card-main">' +
                    '<div class="name">' + officeEsc(a.display_name || a.agent_id) + "</div>" +
                    '<div class="role-tag">' + officeEsc(roleTag) + "</div>" +
                    '<div class="action">' + officeEsc(actionTxt) + "</div>" +
                    '<div class="host">' + officeEsc(a.host_hint || "") +
                    (tid
                      ? (' · <a href="' + officeEsc(href) + '" title="Ouvrir la tâche #' + officeEsc(tid) + '">#' +
                        officeEsc(tid) + "</a>")
                      : "") +
                    "</div>" +
                    approvalHtml +
                  "</div>" +
                  '<span class="office-status">' + officeEsc(isBridge ? (hubBot && hubBot.online ? "hub" : "idle") : st) + "</span>" +
                "</article>"
              );
            }).join("")
          : '<div class="office-empty"><span class="ghost" aria-hidden="true">∅</span>salle vide</div>';
        const piaStrip = id === "zone_prime" ? officePlayerIaStripHtml(true) : "";
        const bridgeStrip = id === "zone_games" ? officeBridgeStripHtml(list) : "";
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
            bridgeStrip +
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
      floor.querySelectorAll("[data-office-bridge]").forEach(function (chip) {
        chip.addEventListener("click", function (ev) {
          ev.preventDefault();
          ev.stopPropagation();
          const agentId = chip.getAttribute("data-office-bridge");
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
      try {
        const fr = await fetch(base + "/v1/pilot/team/fleet");
        const fleet = await fr.json();
        const pending = (fleet && fleet.team && fleet.team.l2_pending) || [];
        __officeFleetL2 = Array.isArray(pending) ? pending : [];
        officeRenderValidationDesk();
      } catch (_) {
        __officeFleetL2 = [];
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