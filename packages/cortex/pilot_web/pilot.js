    const STORAGE_KEY = "lbg_pilot_api_base";
    const STORAGE_CHAT_KEY = "lbg_pilot_chat_state_v1";
    const STORAGE_HISTORY_PREFIX = "lbg_pilot_history_v1:";
    const STORAGE_QUEST_PREFIX = "lbg_pilot_quest_state_v1:";
    const STORAGE_COMBAT_PREFIX = "lbg_pilot_encounter_state_v1:";
    const STORAGE_NO_CACHE_KEY = "lbg_pilot_no_cache_v1";
    const STORAGE_CACHE_LAT_KEY = "lbg_pilot_cache_lat_v1";
    const STORAGE_SERVICE_TOKEN_KEY = "lbg_pilot_service_token_v1";
    const STORAGE_METRICS_BEARER_KEY = "lbg_pilot_metrics_bearer_v1";
    const STORAGE_LYRA_REG_LOG_KEY = "lbg_pilot_lyra_reg_log_v1";
    const STORAGE_LYRA_REG_FILTER_KEY = "lbg_pilot_lyra_reg_filter_v1";
    const STORAGE_PANEL_LAYOUT_KEY = "lbg_pilot_panel_layout_v1";
    const STORAGE_ASSISTANT_HISTORY_KEY = "lbg_pilot_assistant_history_v1";
    const STORAGE_ASSISTANT_PREFS_KEY = "lbg_pilot_assistant_prefs_v1";
    const STORAGE_ASSISTANT_SESSION_NOTES_KEY = "lbg_pilot_assistant_session_notes_v1";
    const LBG_PILOT_MMO_SESSION_SUMMARY_STORAGE = "lbg_pilot_mmo_session_summary_json";
    const STORAGE_ASSISTANT_LYRA_KEY = "lbg_pilot_assistant_lyra_gauges_v1";
    const STORAGE_ASSISTANT_UI_ADVANCED_KEY = "lbg_pilot_assistant_ui_advanced_v1";

    /**
     * URL du backend FastAPI (lbg-backend) servant /v1/pilot/* .
     * Sur front LAN (Nginx proxy /v1/ sur :8080 ou :80), préférer la même origine
     * (pas de CORS, pas de blocage réseau cross-port vers :8000).
     * Surcharge optionnelle : définir window.__LBG_PILOT_DEFAULT_API_BASE__ avant ce script.
     */
    function pilotIsNginxPilotOrigin() {
      try {
        const port = String(window.location.port || "");
        return port === "8080" || port === "80" || port === "";
      } catch (_) {
        return false;
      }
    }

    function pilotMigrateApiBaseToSameOrigin(stored) {
      try {
        const vs = String(stored || "").trim().replace(/\/$/, "");
        const originNorm = String(window.location.origin || "").replace(/\/$/, "");
        if (!vs || !originNorm || !pilotIsNginxPilotOrigin()) return vs;
        const u = new URL(vs);
        const o = new URL(originNorm);
        if (u.hostname === o.hostname && u.port === "8000" && o.port === "8080") {
          return originNorm;
        }
        if (
          u.hostname === "192.168.0.140" &&
          u.port === "8000" &&
          o.hostname === "192.168.0.110" &&
          (o.port === "8080" || o.port === "80")
        ) {
          return originNorm;
        }
        return vs;
      } catch (_) {
        return String(stored || "").trim();
      }
    }

    function pilotInferDefaultApiBase() {
      try {
        if (
          typeof window.__LBG_PILOT_DEFAULT_API_BASE__ !== "undefined" &&
          window.__LBG_PILOT_DEFAULT_API_BASE__
        ) {
          const x = String(window.__LBG_PILOT_DEFAULT_API_BASE__)
            .trim()
            .replace(/\/$/, "");
          if (x) return x;
        }
      } catch (_) {}
      try {
        const originNorm = String(window.location.origin || "").replace(/\/$/, "");
        if (originNorm && pilotIsNginxPilotOrigin()) {
          return originNorm;
        }
      } catch (_) {}
      try {
        const o = String(window.location.origin || "").replace(/\/$/, "");
        return o || "http://127.0.0.1:8000";
      } catch (_) {
        return "http://127.0.0.1:8000";
      }
    }

    function getBase() {
      const el = document.getElementById("api-base");
      let fromInput = el && el.value ? String(el.value).trim() : "";
      if (fromInput) {
        fromInput = pilotMigrateApiBaseToSameOrigin(fromInput);
        if (el && fromInput !== String(el.value || "").trim()) {
          el.value = fromInput;
          try {
            localStorage.setItem(STORAGE_KEY, fromInput);
          } catch (_) {}
        }
        return fromInput.replace(/\/$/, "");
      }
      return pilotInferDefaultApiBase();
    }

    function pilotInlineHint(elementId, msg, isError) {
      const el = document.getElementById(elementId);
      if (!el) return;
      el.textContent = msg || "—";
      el.style.color = isError ? "#f87171" : "";
      el.style.fontWeight = isError ? "600" : "";
    }

    function loadStoredBase() {
      try {
        const v = localStorage.getItem(STORAGE_KEY);
        const el = document.getElementById("api-base");
        if (!el) return;
        if (v != null && String(v).trim() !== "") {
          let vs = pilotMigrateApiBaseToSameOrigin(String(v).trim());
          if (vs !== String(v).trim()) {
            try {
              localStorage.setItem(STORAGE_KEY, vs);
            } catch (_) {}
          }
          el.value = vs;
          return;
        }
        const inferred = pilotInferDefaultApiBase();
        const origin = String(window.location.origin || "").replace(/\/$/, "");
        if (inferred && (!origin || inferred !== origin)) {
          el.value = inferred;
        }
      } catch (_) {}
    }

    function loadStoredServiceToken() {
      try {
        const v = localStorage.getItem(STORAGE_SERVICE_TOKEN_KEY);
        if (v) document.getElementById("service-token").value = v;
      } catch (_) {}
    }

    function getMetricsBearer() {
      const el = document.getElementById("metrics-bearer");
      const v = (el && el.value) ? el.value.trim() : "";
      try {
        if (v) localStorage.setItem(STORAGE_METRICS_BEARER_KEY, v);
        else localStorage.removeItem(STORAGE_METRICS_BEARER_KEY);
      } catch (_) {}
      return v;
    }

    function loadStoredMetricsBearer() {
      try {
        const v = localStorage.getItem(STORAGE_METRICS_BEARER_KEY);
        if (v) document.getElementById("metrics-bearer").value = v;
      } catch (_) {}
    }

    function renderMetricsLinks() {
      const el = document.getElementById("metrics-links");
      if (!el) return;
      const base = getBase();
      const j = window.__last_health_json;
      const orchRaw = j && typeof j.orchestrator_url === "string" ? j.orchestrator_url.trim() : "";
      const orch = orchRaw.replace(/\/$/, "");
      const internalEl = document.getElementById("ws-internal-http");
      const internal = internalEl && internalEl.value ? internalEl.value.trim().replace(/\/$/, "") : "";
      const items = [];
      items.push(
        "<li><a href=\"" + escapeHtml(base + "/metrics") + "\" target=\"_blank\" rel=\"noreferrer\"><code>backend</code> /metrics</a></li>"
      );
      if (orch) {
        items.push(
          "<li><a href=\"" + escapeHtml(orch + "/metrics") + "\" target=\"_blank\" rel=\"noreferrer\"><code>orchestrator</code> /metrics</a> <span class=\"muted\">(URL depuis santé)</span></li>"
        );
      } else {
        items.push("<li class=\"muted\"><code>orchestrator</code> /metrics — recharge la santé (bouton Rafraîchir) pour afficher le lien.</li>");
      }
      if (internal) {
        items.push(
          "<li><a href=\"" + escapeHtml(internal + "/metrics") + "\" target=\"_blank\" rel=\"noreferrer\"><code>HTTP interne WS</code> /metrics</a> <span class=\"muted\">(champ WS → HTTP interne)</span></li>"
        );
      } else {
        items.push("<li class=\"muted\"><code>HTTP interne</code> /metrics — renseigne l’URL snapshot (colonne WS).</li>");
      }
      el.innerHTML = "<ul style=\"margin:0.25rem 0;padding-left:1.25rem\">" + items.join("") + "</ul>";
    }

    async function probeBackendMetrics() {
      const out = document.getElementById("metrics-probe-out");
      if (!out) return;
      out.textContent = "…";
      const base = getBase();
      const url = base + "/metrics";
      const tok = getMetricsBearer();
      const headers = {};
      if (tok) headers["Authorization"] = "Bearer " + tok;
      try {
        const r = await fetch(url, { headers });
        const t = await r.text();
        out.textContent = "HTTP " + r.status + " " + url + "\n" + t.slice(0, 6000);
      } catch (e) {
        out.textContent = "Erreur: " + e;
      }
    }

    function openOrchestratorMetrics() {
      const j = window.__last_health_json;
      const orchRaw = j && typeof j.orchestrator_url === "string" ? j.orchestrator_url.trim() : "";
      const orch = orchRaw.replace(/\/$/, "");
      if (!orch) {
        alert("Recharge d'abord la santé (Rafraîchir) pour obtenir orchestrator_url.");
        return;
      }
      window.open(orch + "/metrics", "_blank", "noopener,noreferrer");
    }

    function openInternalHttpMetrics() {
      const internalEl = document.getElementById("ws-internal-http");
      const internal = internalEl && internalEl.value ? internalEl.value.trim().replace(/\/$/, "") : "";
      if (!internal) {
        alert("Renseigne l'URL HTTP interne (colonne WS).");
        return;
      }
      window.open(internal + "/metrics", "_blank", "noopener,noreferrer");
    }

    function loadStoredChatState() {
      try {
        const raw = localStorage.getItem(STORAGE_CHAT_KEY);
        if (!raw) return;
        const j = JSON.parse(raw);
        if (j && typeof j === "object") {
          if (typeof j.actor_id === "string") document.getElementById("actor").value = j.actor_id;
          if (typeof j.text === "string") document.getElementById("text").value = j.text;
          if (typeof j.context_json === "string") document.getElementById("context-json").value = j.context_json;
        }
      } catch (_) {}
      try { refreshLyraContextPreview(); } catch (_) {}
    }

    function getServiceToken() {
      const el = document.getElementById("service-token");
      const v = (el && el.value) ? el.value.trim() : "";
      if (!v) return "";
      try { localStorage.setItem(STORAGE_SERVICE_TOKEN_KEY, v); } catch (_) {}
      return v;
    }

    function loadNoCacheToggle() {
      try {
        const v = localStorage.getItem(STORAGE_NO_CACHE_KEY);
        if (v === "1") document.getElementById("toggle-no-cache").checked = true;
      } catch (_) {}
    }

    function saveNoCacheToggle() {
      try {
        const el = document.getElementById("toggle-no-cache");
        localStorage.setItem(STORAGE_NO_CACHE_KEY, el && el.checked ? "1" : "0");
      } catch (_) {}
    }

    function saveBase() {
      try {
        const b = document.getElementById("api-base").value.trim();
        if (b) localStorage.setItem(STORAGE_KEY, b);
      } catch (_) {}
    }

    function saveChatState() {
      try {
        const st = {
          actor_id: document.getElementById("actor").value,
          text: document.getElementById("text").value,
          context_json: document.getElementById("context-json").value,
        };
        localStorage.setItem(STORAGE_CHAT_KEY, JSON.stringify(st));
      } catch (_) {}
      try { refreshLyraContextPreview(); } catch (_) {}
    }

    function panelLayoutLoad() {
      try {
        const raw = localStorage.getItem(STORAGE_PANEL_LAYOUT_KEY);
        if (!raw) return {};
        const parsed = JSON.parse(raw);
        return parsed && typeof parsed === "object" ? parsed : {};
      } catch (_) {
        return {};
      }
    }

    function panelLayoutSave(next) {
      try { localStorage.setItem(STORAGE_PANEL_LAYOUT_KEY, JSON.stringify(next || {})); } catch (_) {}
    }

    function panelGetColumnKeyFromEl(el) {
      const col = el && el.closest ? el.closest(".col") : null;
      if (!col) return "";
      if (col.id === "col-left") return "left";
      if (col.id === "col-center") return "center";
      if (col.id === "col-right") return "right";
      return "";
    }

    function panelSaveScreenLayout(screen) {
      const layout = panelLayoutLoad();
      const out = { left: [], center: [], right: [] };
      const wraps = document.querySelectorAll('#dashboard .col [data-pilot-screen="' + screen + '"]');
      wraps.forEach(function (w) {
        const colKey = panelGetColumnKeyFromEl(w);
        if (!colKey || !out[colKey]) return;
        out[colKey] = Array.from(w.querySelectorAll("section[data-panel-id]"))
          .map(function (s) { return s.getAttribute("data-panel-id") || ""; })
          .filter(Boolean);
      });
      layout[screen] = out;
      panelLayoutSave(layout);
    }

    function panelApplyScreenLayout(screen) {
      const layout = panelLayoutLoad();
      const conf = layout && layout[screen] && typeof layout[screen] === "object" ? layout[screen] : null;
      if (!conf) return;
      const wraps = {
        left: document.querySelector('#col-left [data-pilot-screen="' + screen + '"]'),
        center: document.querySelector('#col-center [data-pilot-screen="' + screen + '"]'),
        right: document.querySelector('#col-right [data-pilot-screen="' + screen + '"]'),
      };
      ["left", "center", "right"].forEach(function (key) {
        const wrap = wraps[key];
        const ids = Array.isArray(conf[key]) ? conf[key] : [];
        if (!wrap) return;
        ids.forEach(function (id) {
          const panel = document.querySelector('section[data-panel-id="' + id + '"]');
          if (!panel) return;
          const sc = panel.parentElement && panel.parentElement.getAttribute
            ? panel.parentElement.getAttribute("data-pilot-screen")
            : null;
          if (sc !== screen) return;
          wrap.appendChild(panel);
        });
      });
    }

    function panelApplyStoredLayout() {
      panelApplyScreenLayout("chat");
      panelApplyScreenLayout("ops");
    }

    function panelInitDnD() {
      let dragPanelId = null;
      const panels = document.querySelectorAll("#dashboard section[data-panel-id]");
      panels.forEach(function (panel) {
        panel.classList.add("panel-draggable");
        panel.setAttribute("draggable", "true");
        const title = panel.querySelector(".panel-title");
        if (title && !title.querySelector(".panel-drag-handle")) {
          const h = document.createElement("span");
          h.className = "panel-drag-handle";
          h.textContent = "↕ déplacer";
          title.appendChild(h);
        }
        panel.addEventListener("dragstart", function (ev) {
          dragPanelId = panel.getAttribute("data-panel-id");
          panel.classList.add("panel-dragging");
          try {
            if (ev.dataTransfer) {
              ev.dataTransfer.setData("text/plain", dragPanelId || "");
              ev.dataTransfer.effectAllowed = "move";
            }
          } catch (_) {}
        });
        panel.addEventListener("dragend", function () {
          panel.classList.remove("panel-dragging");
          dragPanelId = null;
          document.querySelectorAll(".panel-dropzone").forEach(function (z) { z.classList.remove("panel-drop-active"); });
        });
      });

      const zones = document.querySelectorAll("#dashboard [data-pilot-screen]");
      zones.forEach(function (zone) {
        zone.classList.add("panel-dropzone");
        zone.addEventListener("dragover", function (ev) {
          const pid = dragPanelId || (ev.dataTransfer ? ev.dataTransfer.getData("text/plain") : "");
          if (!pid) return;
          const panel = document.querySelector('section[data-panel-id="' + pid + '"]');
          if (!panel) return;
          const panelScreen = panel.parentElement && panel.parentElement.getAttribute
            ? panel.parentElement.getAttribute("data-pilot-screen")
            : "";
          const zoneScreen = zone.getAttribute("data-pilot-screen") || "";
          if (panelScreen !== zoneScreen) return;
          ev.preventDefault();
          zone.classList.add("panel-drop-active");
          try { if (ev.dataTransfer) ev.dataTransfer.dropEffect = "move"; } catch (_) {}
        });
        zone.addEventListener("dragleave", function () {
          zone.classList.remove("panel-drop-active");
        });
        zone.addEventListener("drop", function (ev) {
          ev.preventDefault();
          zone.classList.remove("panel-drop-active");
          const pid = dragPanelId || (ev.dataTransfer ? ev.dataTransfer.getData("text/plain") : "");
          if (!pid) return;
          const panel = document.querySelector('section[data-panel-id="' + pid + '"]');
          if (!panel) return;
          const panelScreen = panel.parentElement && panel.parentElement.getAttribute
            ? panel.parentElement.getAttribute("data-pilot-screen")
            : "";
          const zoneScreen = zone.getAttribute("data-pilot-screen") || "";
          if (panelScreen !== zoneScreen) return;
          zone.appendChild(panel);
          panelSaveScreenLayout(zoneScreen);
        });
      });
    }

    function healthStateClass(state) {
      if (state === "ok") return "ok";
      if (state === "skipped") return "muted";
      return "err";
    }

    async function refreshHealth() {
      const out = document.getElementById("health-out");
      const sum = document.getElementById("health-summary");
      const links = document.getElementById("services-links");
      out.textContent = "…";
      sum.textContent = "…";
      links.textContent = "…";
      try {
        const base = getBase();
        const r = await fetch(base + "/v1/pilot/status");
        const j = await r.json();
        window.__last_health_json = j;
        out.textContent = JSON.stringify(j, null, 2);
        const orch = j.orchestrator ?? "—";
        const dlg = j.agent_dialogue ?? "—";
        const qst = j.agent_quests ?? "—";
        const cbt = j.agent_combat ?? "—";
        const pm = j.agent_pm ?? "—";
        const dlgInfo = j.agent_dialogue_info;
        const qstInfo = j.agent_quests_info;
        const cbtInfo = j.agent_combat_info;
        const pmInfo = j.agent_pm_info;
        let dlgSuffix = "";
        if (dlgInfo && typeof dlgInfo === "object") {
          const parts = [];
          if (dlgInfo.service) parts.push(String(dlgInfo.service));
          if (dlgInfo.version != null) parts.push("v" + String(dlgInfo.version));
          if (dlgInfo.llm_model) parts.push("model " + String(dlgInfo.llm_model));
          const cache = dlgInfo.cache;
          if (cache && typeof cache === "object") {
            const enabled = cache.enabled === true ? "cache on" : "cache off";
            const size = cache.size != null ? ("size " + String(cache.size)) : "";
            const hits = cache.hits != null ? ("hits " + String(cache.hits)) : "";
            const misses = cache.misses != null ? ("miss " + String(cache.misses)) : "";
            parts.push([enabled, size, hits, misses].filter(Boolean).join(" · "));
          }
          if (parts.length) dlgSuffix = " <span class=\"muted\">(" + parts.map(escapeHtml).join(" · ") + ")</span>";
        }
        let qstSuffix = "";
        if (qstInfo && typeof qstInfo === "object") {
          const parts = [];
          if (qstInfo.service) parts.push(String(qstInfo.service));
          if (qstInfo.version != null) parts.push("v" + String(qstInfo.version));
          if (parts.length) qstSuffix = " <span class=\"muted\">(" + parts.map(escapeHtml).join(" · ") + ")</span>";
        }
        let cbtSuffix = "";
        if (cbtInfo && typeof cbtInfo === "object") {
          const parts = [];
          if (cbtInfo.service) parts.push(String(cbtInfo.service));
          if (cbtInfo.version != null) parts.push("v" + String(cbtInfo.version));
          if (parts.length) cbtSuffix = " <span class=\"muted\">(" + parts.map(escapeHtml).join(" · ") + ")</span>";
        }
        let pmSuffix = "";
        if (pmInfo && typeof pmInfo === "object") {
          const parts = [];
          if (pmInfo.service) parts.push(String(pmInfo.service));
          if (pmInfo.version != null) parts.push("v" + String(pmInfo.version));
          if (parts.length) pmSuffix = " <span class=\"muted\">(" + parts.map(escapeHtml).join(" · ") + ")</span>";
        }
        let extraHtml = "";
        if (j.infra_status) {
          extraHtml += '<div style="margin-top: 0.8rem; display: flex; gap: 0.5rem; flex-wrap: wrap; align-items: center; line-height: 1.8;">' +
            '<strong style="font-size:0.85rem;">Infra (VMs) :</strong> ' +
            '<span class="jobs-badge jobs-badge--" style="background: ' + (j.infra_status.vm140 === "ok" ? "#d1fae5; color: #065f46" : "#fee2e2; color: #991b1b") + ';">VM 140 Core</span>' +
            '<span class="jobs-badge jobs-badge--" style="background: ' + (j.infra_status.vm110 === "ok" ? "#d1fae5; color: #065f46" : "#fee2e2; color: #991b1b") + ';">VM 110 Ollama</span>' +
            '<span class="jobs-badge jobs-badge--" style="background: ' + (j.infra_status.vm245 === "ok" ? "#d1fae5; color: #065f46" : "#fee2e2; color: #991b1b") + ';">VM 245 PreCU</span>' +
            '<span class="jobs-badge jobs-badge--" style="background: ' + (j.infra_status.vm246 === "ok" ? "#d1fae5; color: #065f46" : "#fee2e2; color: #991b1b") + ';">VM 246 Prime</span>' +
            '</div>';
        }
        if (j.game_status) {
          extraHtml += '<div style="margin-top: 0.5rem; display: flex; gap: 0.5rem; flex-wrap: wrap; align-items: center; line-height: 1.8;">' +
            '<strong style="font-size:0.85rem;">Mondes SWG :</strong> ' +
            '<span class="jobs-badge jobs-badge--" style="background: ' + (j.game_status.precu_game === "ok" ? "#d1fae5; color: #065f46" : "#fee2e2; color: #991b1b") + ';">PreCU (44453)</span>' +
            '<span class="jobs-badge jobs-badge--" style="background: ' + (j.game_status.prime_game === "ok" ? "#d1fae5; color: #065f46" : "#fee2e2; color: #991b1b") + ';">Prime (44553)</span>' +
            '</div>';
        }
        if (j.bots_status) {
          extraHtml += '<div style="margin-top: 0.5rem; display: flex; gap: 0.5rem; flex-wrap: wrap; align-items: center; line-height: 1.8;">' +
            '<strong style="font-size:0.85rem;">Bots joueurs :</strong> ' +
            '<span class="jobs-badge jobs-badge--" style="background: ' + (j.bots_status.lia === "online" ? "#d1fae5; color: #065f46" : "#fee2e2; color: #991b1b") + ';">Lia (' + j.bots_status.lia + ')</span>' +
            '<span class="jobs-badge jobs-badge--" style="background: ' + (j.bots_status.nix === "online" ? "#d1fae5; color: #065f46" : "#fee2e2; color: #991b1b") + ';">Nix (' + j.bots_status.nix + ')</span>' +
            '<span class="jobs-badge jobs-badge--" style="background: ' + (j.bots_status.mira === "online" ? "#d1fae5; color: #065f46" : "#fee2e2; color: #991b1b") + ';">Mira (' + j.bots_status.mira + ')</span>' +
            '</div>';
        }
        if (j.economy_metrics || j.chronicler_metrics) {
          extraHtml += '<div style="margin-top: 0.5rem; display: flex; gap: 0.5rem; flex-wrap: wrap; align-items: center; line-height: 1.8;">' +
            '<strong style="font-size:0.85rem;">Monde (Météo/Éco) :</strong> ';
          if (j.economy_metrics && !j.economy_metrics.error) {
            extraHtml += '<span class="jobs-badge jobs-badge--" style="background: #e0f2fe; color: #0369a1;">Signaux Éco : ' + j.economy_metrics.signal_count + ' (Alertes: ' + j.economy_metrics.evaluation_count + ')</span>';
          }
          if (j.chronicler_metrics && !j.chronicler_metrics.error) {
            extraHtml += '<span class="jobs-badge jobs-badge--" style="background: #faf5ff; color: #6b21a8;">Factions Chroniques : ' + j.chronicler_metrics.active_goal_count + ' buts actifs</span>';
          }
          extraHtml += '</div>';
        }

        sum.innerHTML =
          "Backend: <span class=\"" + healthStateClass(j.backend) + "\">" + j.backend + "</span> · " +
          "Orchestrator: <span class=\"" + healthStateClass(orch) + "\">" + orch + "</span> · " +
          "Agent dialogue: <span class=\"" + healthStateClass(dlg) + "\">" + dlg + "</span>" + dlgSuffix + " · " +
          "Agent quests: <span class=\"" + healthStateClass(qst) + "\">" + qst + "</span>" + qstSuffix + " · " +
          "Agent combat: <span class=\"" + healthStateClass(cbt) + "\">" + cbt + "</span>" + cbtSuffix + " · " +
          "Agent PM: <span class=\"" + healthStateClass(pm) + "\">" + pm + "</span>" + pmSuffix +
          extraHtml;

        const b = base;
        const items = [];
        if (j.agent_dialogue && j.agent_dialogue !== "skipped") {
          const href = b + "/v1/pilot/agent-dialogue/healthz";
          items.push("<a href=\"" + escapeHtml(href) + "\" target=\"_blank\" rel=\"noreferrer\">healthz dialogue (proxy)</a>");
        }
        if (j.agent_quests && j.agent_quests !== "skipped") {
          const href = b + "/v1/pilot/agent-quests/healthz";
          items.push("<a href=\"" + escapeHtml(href) + "\" target=\"_blank\" rel=\"noreferrer\">healthz quests (proxy)</a>");
        }
        if (j.agent_combat && j.agent_combat !== "skipped") {
          const href = b + "/v1/pilot/agent-combat/healthz";
          items.push("<a href=\"" + escapeHtml(href) + "\" target=\"_blank\" rel=\"noreferrer\">healthz combat (proxy)</a>");
        }
        if (j.agent_pm && j.agent_pm !== "skipped") {
          const href = b + "/v1/pilot/agent-pm/healthz";
          items.push("<a href=\"" + escapeHtml(href) + "\" target=\"_blank\" rel=\"noreferrer\">healthz PM (proxy)</a>");
        }
        if (items.length) {
          links.innerHTML =
            "Services : " + items.join(" · ") +
            "<br><span class=\"muted\" style=\"font-size:0.85rem\">Même origine que le backend : pas besoin d’ouvrir 8020/8030/8040/8055 sur le pare-feu du poste client.</span>";
        } else {
          links.textContent = "Services : —";
        }
        try { renderMetricsLinks(); } catch (_) {}
      } catch (e) {
        out.textContent = "Erreur: " + e;
        sum.textContent = "Erreur: " + e;
        links.textContent = "Erreur: " + e;
        window.__last_health_json = null;
        try { renderMetricsLinks(); } catch (_) {}
      }
    }

    async function refreshCapabilities() {
      const wrap = document.getElementById("cap-table-wrap");
      const raw = document.getElementById("cap-raw");
      wrap.innerHTML = "<p>Chargement…</p>";
      raw.textContent = "—";
      try {
        const base = getBase();
        const r = await fetch(base + "/v1/pilot/capabilities");
        const j = await r.json();
        raw.textContent = JSON.stringify(j, null, 2);
        if (!j.ok) {
          wrap.innerHTML = "<p class=\"err\">Erreur proxy : " + (j.error || JSON.stringify(j)) + "</p>";
          return;
        }
        const caps = j.capabilities || [];
        if (caps.length === 0) {
          wrap.innerHTML = "<p>Aucune capability.</p>";
          return;
        }
        let html = "<table style=\"width:100%;border-collapse:collapse\"><thead><tr><th style=\"text-align:left;border:1px solid #ccc;padding:0.35rem\">name</th><th style=\"text-align:left;border:1px solid #ccc;padding:0.35rem\">routed_to</th><th style=\"text-align:left;border:1px solid #ccc;padding:0.35rem\">description</th></tr></thead><tbody>";
        for (const c of caps) {
          html += "<tr><td style=\"border:1px solid #ccc;padding:0.35rem\">" + escapeHtml(c.name) + "</td><td style=\"border:1px solid #ccc;padding:0.35rem\"><code>" + escapeHtml(c.routed_to) + "</code></td><td style=\"border:1px solid #ccc;padding:0.35rem\">" + escapeHtml(c.description || "") + "</td></tr>";
        }
        html += "</tbody></table>";
        wrap.innerHTML = html;
      } catch (e) {
        wrap.innerHTML = "<p class=\"err\">Erreur: " + escapeHtml(String(e)) + "</p>";
      }
    }

    function escapeHtml(s) {
      const d = document.createElement("div");
      d.textContent = s;
      return d.innerHTML;
    }

    async function refreshBrain() {
      const out = document.getElementById("brain-out");
      const hint = document.getElementById("brain-hint");
      const approvals = document.getElementById("brain-approvals");
      if (!out || !hint) return;
      out.textContent = "…";
      hint.textContent = "…";
      if (approvals) approvals.textContent = "…";
      try {
        const base = getBase();
        const r = await fetch(base + "/v1/pilot/orchestrator/brain/status");
        const j = await r.json();
        out.textContent = JSON.stringify(j, null, 2);
        if (j && j.ok === true) {
          const on = j.enabled === true;
          const last = j.last_tick_ts ? ("dernier tick: " + new Date(j.last_tick_ts * 1000).toLocaleString()) : "jamais tické";
          const g = (j.gauges && typeof j.gauges === "object") ? j.gauges : {};
          const conf = (g.confidence != null) ? Math.round(Number(g.confidence)) : null;
          const stress = (g.stress != null) ? Math.round(Number(g.stress)) : null;
          const fatigue = (g.fatigue != null) ? Math.round(Number(g.fatigue)) : null;
          const curiosity = (g.curiosity != null) ? Math.round(Number(g.curiosity)) : null;
          const gaugesTxt = [conf != null ? ("conf " + conf) : "", stress != null ? ("stress " + stress) : "", fatigue != null ? ("fatigue " + fatigue) : "", curiosity != null ? ("curiosité " + curiosity) : ""].filter(Boolean).join(" · ");
          const intent = j.intent ? (" · intent: <code>" + escapeHtml(String(j.intent)) + "</code>") : "";
          const nar = j.narrative ? ("<br><span class=\"muted\" style=\"font-size:0.85rem\">" + escapeHtml(String(j.narrative)) + "</span>") : "";
          hint.innerHTML =
            "État: <strong class=\"" + (on ? "ok" : "muted") + "\">" + (on ? "actif" : "inactif") + "</strong>" +
            " · " + escapeHtml(last) +
            (gaugesTxt ? ("<br>Jauges: <span class=\"muted\">" + escapeHtml(gaugesTxt) + "</span>") : "") +
            intent +
            (j.last_tick_ok === false ? " · <span class=\"err\">last_tick_ok=false</span>" : "") +
            nar;

          try {
            const reqs = Array.isArray(j.approval_requests) ? j.approval_requests : [];
            const pending = reqs.filter((x) => x && typeof x === "object" && x.done !== true);
            if (approvals) {
              if (!pending.length) {
                approvals.innerHTML = "<strong>Approvals</strong> : —";
              } else {
                let html = "<strong>Approvals</strong> :<br>";
                for (const pr of pending.slice(0, 5)) {
                  const rid = pr.id ? String(pr.id) : "";
                  const unit = pr.unit ? String(pr.unit) : "";
                  const approved = pr.approved === true;
                  html +=
                    "<div style=\"margin-top:0.25rem;padding:0.4rem 0.5rem;border:1px solid #e4e4e4;border-radius:6px;background:#fff\">" +
                    "<code>" + escapeHtml(unit || "—") + "</code>" +
                    " <span class=\"muted\">(" + escapeHtml(pr.reason || "restart demandé") + ")</span>" +
                    "<br>" +
                    (approved
                      ? "<span class=\"ok\">approuvé</span>"
                      : "<button type=\"button\" class=\"btn-brain-approve\" data-request-id=\"" + escapeHtml(rid) + "\">Approuver</button>") +
                    "</div>";
                }
                approvals.innerHTML = html;
                approvals.querySelectorAll("button.btn-brain-approve").forEach((btn) => {
                  btn.addEventListener("click", async () => {
                    const rid = btn.getAttribute("data-request-id") || "";
                    await approveBrain(rid);
                  });
                });
              }
            }
          } catch (_) {}
        } else {
          hint.textContent = "Erreur proxy (voir JSON).";
          if (approvals) approvals.textContent = "—";
        }
      } catch (e) {
        out.textContent = "Erreur: " + e;
        hint.textContent = "Erreur: " + e;
        if (approvals) approvals.textContent = "Erreur: " + e;
      }
    }

    async function approveBrain(requestId) {
      const out = document.getElementById("brain-out");
      const hint = document.getElementById("brain-hint");
      if (!requestId) return;
      if (hint) hint.textContent = "…";
      try {
        const base = getBase();
        const res = await postJson(base + "/v1/pilot/orchestrator/brain/approve", { request_id: String(requestId) });
        if (out) out.textContent = JSON.stringify(res.json || { status: res.status, text: res.text }, null, 2);
        try { await refreshBrain(); } catch (_) {}
      } catch (e) {
        if (hint) hint.textContent = "Erreur: " + e;
      }
    }

    async function toggleBrain(enabled) {
      const out = document.getElementById("brain-out");
      const hint = document.getElementById("brain-hint");
      if (!out || !hint) return;
      hint.textContent = "…";
      try {
        const base = getBase();
        const res = await postJson(base + "/v1/pilot/orchestrator/brain/toggle", { enabled: !!enabled });
        out.textContent = JSON.stringify(res.json || { status: res.status, text: res.text }, null, 2);
        try { await refreshBrain(); } catch (_) {}
      } catch (e) {
        hint.textContent = "Erreur: " + e;
      }
    }

    function refreshLyraContextPreview() {
      const box = document.getElementById("lyra-context-preview");
      if (!box) return;
      let ctx = {};
      try {
        const raw = document.getElementById("context-json").value.trim();
        if (raw) ctx = JSON.parse(raw);
      } catch (_) {
        box.style.display = "none";
        box.innerHTML = "";
        return;
      }
      const lyra = ctx.lyra;
      if (lyra && typeof lyra === "object" && !Array.isArray(lyra)) {
        box.style.display = "";
        box.innerHTML =
          "<div class=\"muted\" style=\"margin-bottom:0.25rem;\">Lyra (contexte — aperçu)</div>" +
          "<pre style=\"margin:0;white-space:pre-wrap;font-size:0.82rem;\">" +
          escapeHtml(JSON.stringify(lyra, null, 2)) +
          "</pre>";
      } else {
        box.style.display = "none";
        box.innerHTML = "";
      }
    }

    async function sendIntent() {
      saveBase();
      saveChatState();
      const out = document.getElementById("intent-out");
      const pretty = document.getElementById("intent-pretty");
      const histPretty = document.getElementById("history-pretty");
      const hint = document.getElementById("copy-hint");
      out.textContent = "…";
      pretty.innerHTML = "";
      histPretty.innerHTML = "";
      hint.textContent = "—";
      try {
        const request = buildPilotRouteRequest();
        const r = await fetch(getBase() + "/v1/pilot/route", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(request),
        });
        const rawText = await r.text();
        let parsed = null;
        try { parsed = JSON.parse(rawText); } catch (_) {}
        if (parsed && typeof parsed === "object") {
          const ms = parsed.elapsed_ms;
          const head = "HTTP " + r.status + " " + r.statusText + (ms != null ? (" · elapsed_ms=" + ms) : "");
          out.textContent = head + "\n" + JSON.stringify(parsed, null, 2);
          window.__last_intent_json = parsed;
          try { pretty.innerHTML = renderPretty(parsed); } catch (_) {}
          try {
            try { recordCacheLatencySample(parsed); } catch (_) {}
            maybeAppendHistory(request, parsed);
            maybePersistQuestState(request, parsed);
            maybePersistEncounterState(request, parsed);
            histPretty.innerHTML = renderHistoryPretty();
          } catch (_) {}
        } else {
          out.textContent = "HTTP " + r.status + " " + r.statusText + "\n" + rawText;
          window.__last_intent_json = null;
        }
      } catch (e) {
        out.textContent = "Erreur: " + e;
        window.__last_intent_json = null;
      }
    }

    function maybePersistQuestState(request, response) {
      const res = response && response.result;
      const out = res && res.output;
      const questState = out && out.quest_state;
      if (!questState || typeof questState !== "object" || Array.isArray(questState)) return;
      if (typeof questState.quest_id !== "string" || !questState.quest_id.trim()) return;

      const ctx = request.context || {};
      const npcKey = getNpcKeyFromContext(ctx);
      saveQuestState(npcKey, questState);

      // refléter dans la textarea context
      const nextContext = { ...ctx, quest_state: questState };
      document.getElementById("context-json").value = JSON.stringify(nextContext, null, 2);
      saveChatState();
    }

    function maybePersistEncounterState(request, response) {
      const res = response && response.result;
      if (!res || res.routed_to !== "agent.combat") return;
      const out = res && res.output;
      const encounter = out && out.encounter;
      if (!encounter || typeof encounter !== "object" || Array.isArray(encounter)) return;
      const eid = encounter.encounter_id;
      if (typeof eid !== "string" || !eid.trim()) return;

      const ctx = request.context || {};
      const combatKey = getCombatKeyFromContext(ctx);
      const st = encounter.status;
      const terminal =
        st === "victory" || st === "defeat" || st === "fled";

      if (terminal) {
        saveEncounterState(combatKey, null);
        const nextContext = { ...ctx };
        delete nextContext.encounter_state;
        document.getElementById("context-json").value = JSON.stringify(nextContext, null, 2);
        saveChatState();
        return;
      }

      const compact = {
        encounter_id: eid.trim(),
        round: encounter.round,
        opponent: encounter.opponent,
        hp: encounter.hp && typeof encounter.hp === "object" ? encounter.hp : {},
      };
      if (st) compact.status = st;
      saveEncounterState(combatKey, compact);
      const nextContext = { ...ctx, encounter_state: compact };
      document.getElementById("context-json").value = JSON.stringify(nextContext, null, 2);
      saveChatState();
    }

    function getNpcKeyFromContext(context) {
      const npc = context && typeof context === "object" ? context.npc_name : null;
      if (typeof npc === "string" && npc.trim()) return npc.trim();
      return "global";
    }

    function getCombatKeyFromContext(context) {
      const c = context && typeof context === "object" ? context : {};
      for (const k of ["enemy_name", "target_name", "opponent"]) {
        const v = c[k];
        if (typeof v === "string" && v.trim()) return v.trim();
      }
      return "global";
    }

    function historyStorageKey(npcKey) {
      return STORAGE_HISTORY_PREFIX + npcKey;
    }

    function questStorageKey(npcKey) {
      return STORAGE_QUEST_PREFIX + npcKey;
    }

    function combatStorageKey(combatKey) {
      return STORAGE_COMBAT_PREFIX + combatKey;
    }

    function loadEncounterState(combatKey) {
      try {
        const raw = localStorage.getItem(combatStorageKey(combatKey));
        if (!raw) return null;
        const j = JSON.parse(raw);
        return j && typeof j === "object" && !Array.isArray(j) ? j : null;
      } catch (_) {
        return null;
      }
    }

    function saveEncounterState(combatKey, encounterState) {
      try {
        if (!encounterState) {
          localStorage.removeItem(combatStorageKey(combatKey));
          return;
        }
        localStorage.setItem(combatStorageKey(combatKey), JSON.stringify(encounterState));
      } catch (_) {}
    }

    function loadHistory(npcKey) {
      try {
        const raw = localStorage.getItem(historyStorageKey(npcKey));
        if (!raw) return [];
        const j = JSON.parse(raw);
        return Array.isArray(j) ? j : [];
      } catch (_) {
        return [];
      }
    }

    function saveHistory(npcKey, history) {
      try {
        localStorage.setItem(historyStorageKey(npcKey), JSON.stringify(history));
      } catch (_) {}
    }

    function loadQuestState(npcKey) {
      try {
        const raw = localStorage.getItem(questStorageKey(npcKey));
        if (!raw) return null;
        const j = JSON.parse(raw);
        return j && typeof j === "object" && !Array.isArray(j) ? j : null;
      } catch (_) {
        return null;
      }
    }

    function saveQuestState(npcKey, questState) {
      try {
        if (!questState) {
          localStorage.removeItem(questStorageKey(npcKey));
          return;
        }
        localStorage.setItem(questStorageKey(npcKey), JSON.stringify(questState));
      } catch (_) {}
    }

    function normalizeHistory(history) {
      if (!Array.isArray(history)) return [];
      const out = [];
      for (const m of history) {
        if (!m || typeof m !== "object") continue;
        const role = m.role;
        const content = m.content;
        if ((role !== "user" && role !== "assistant") || typeof content !== "string") continue;
        const c = content.trim();
        if (!c) continue;
        out.push({ role, content: c });
      }
      // cap léger côté UI
      if (out.length > 24) return out.slice(out.length - 24);
      return out;
    }

    function buildPilotRouteRequest() {
      const ctxRaw = document.getElementById("context-json").value.trim();
      let context = {};
      if (ctxRaw) {
        let parsed;
        try {
          parsed = JSON.parse(ctxRaw);
        } catch (e) {
          const detail = e instanceof Error ? e.message : String(e);
          throw new Error(
            "context JSON invalide : " + detail +
            ". Vérifie les virgules, guillemets droits \", et n’utilise pas le symbole | comme séparateur (JSON interdit). Exemple valide : {\"npc_name\":\"Hagen\",\"history\":[{\"role\":\"user\",\"content\":\"…\"}]}"
          );
        }
        if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed)) {
          throw new Error("context doit être un objet JSON (pas un tableau ni une valeur seule).");
        }
        context = parsed;
      }

      // Injecter l'history persistée si absente ou non-array
      const npcKey = getNpcKeyFromContext(context);
      const storedHistory = loadHistory(npcKey);
      if (!Array.isArray(context.history)) {
        context.history = storedHistory;
      } else {
        // si l'utilisateur l'a modifié à la main, on le normalise et on resynchronise
        context.history = normalizeHistory(context.history);
        saveHistory(npcKey, context.history);
      }

      // Injecter le quest_state persisté si absent ou invalide
      const storedQuestState = loadQuestState(npcKey);
      if (context.quest_state == null) {
        if (storedQuestState) context.quest_state = storedQuestState;
      } else if (typeof context.quest_state === "object" && !Array.isArray(context.quest_state)) {
        saveQuestState(npcKey, context.quest_state);
      } else {
        delete context.quest_state;
        saveQuestState(npcKey, null);
      }

      const combatKey = getCombatKeyFromContext(context);
      const storedEncounter = loadEncounterState(combatKey);
      if (context.encounter_state == null) {
        if (storedEncounter) context.encounter_state = storedEncounter;
      } else if (typeof context.encounter_state === "object" && !Array.isArray(context.encounter_state)) {
        saveEncounterState(combatKey, context.encounter_state);
      } else {
        delete context.encounter_state;
        saveEncounterState(combatKey, null);
      }

      const dryDev = document.getElementById("toggle-devops-dry-run");
      if (dryDev && dryDev.checked) {
        context.devops_dry_run = true;
      }

      const agentic = document.getElementById("toggle-agentic");
      if (agentic && agentic.checked) {
        context.prefer_agentic = true;
      } else if (context && typeof context === "object") {
        delete context.prefer_agentic;
      }

      const noCache = document.getElementById("toggle-no-cache");
      if (noCache && noCache.checked) {
        context._no_cache = true;
      } else if (context && typeof context === "object") {
        delete context._no_cache;
      }

      return {
        actor_id: document.getElementById("actor").value.trim() || "test:1",
        text: document.getElementById("text").value.trim(),
        context,
      };
    }

    function maybeAppendHistory(request, response) {
      const auto = document.getElementById("toggle-auto-history").checked;
      if (!auto) return;
      const res = response && response.result;
      const out = res && res.output;
      const remote = out && out.remote;
      const assistantReply =
        remote && typeof remote === "object" && typeof remote.reply === "string" ? remote.reply.trim() : "";
      if (!assistantReply) return; // pas un tour dialogue (ou pas de reply)

      const ctx = request.context || {};
      const npcKey = getNpcKeyFromContext(ctx);
      const history = normalizeHistory(loadHistory(npcKey));
      history.push({ role: "user", content: String(request.text || "").trim() || "(…)" });
      history.push({ role: "assistant", content: assistantReply });
      const capped = normalizeHistory(history);
      saveHistory(npcKey, capped);

      // refléter dans la textarea context
      const nextContext = { ...ctx, history: capped };
      document.getElementById("context-json").value = JSON.stringify(nextContext, null, 2);
      saveChatState();
    }

    function renderHistoryPretty() {
      let context = {};
      try {
        const raw = document.getElementById("context-json").value.trim();
        if (raw) context = JSON.parse(raw);
      } catch (_) {}
      const npcKey = getNpcKeyFromContext(context);
      const history = normalizeHistory(loadHistory(npcKey));
      if (!history.length) return "";
      let html = "<div style=\"padding:0.75rem;border:1px solid #ddd;border-radius:6px;background:#fcfcfc;\">" +
        "<div class=\"muted\" style=\"margin-bottom:0.35rem;\">Historique (" + escapeHtml(npcKey) + ")</div>";
      for (const m of history) {
        const roleLabel = m.role === "user" ? "Joueur" : "PNJ";
        html += "<div style=\"margin-top:0.35rem\"><b>" + roleLabel + ":</b> " + escapeHtml(m.content) + "</div>";
      }
      html += "</div>";
      return html;
    }

    function renderPretty(root) {
      const res = root && root.result;
      const out = res && res.output;
      const rows = [];

      function addKV(k, v) {
        rows.push("<tr><td style=\"border:1px solid #ddd;padding:0.35rem;white-space:nowrap;\"><b>" + escapeHtml(k) + "</b></td><td style=\"border:1px solid #ddd;padding:0.35rem;\">" + escapeHtml(String(v)) + "</td></tr>");
      }

      if (root && root.trace_id) addKV("trace_id", root.trace_id);
      if (root && typeof root.elapsed_ms === "number") addKV("elapsed_ms", root.elapsed_ms);
      if (res && res.intent) addKV("intent", res.intent);
      if (res && res.routed_to) addKV("routed_to", res.routed_to);
      if (res && typeof res.confidence === "number") addKV("confidence", res.confidence);
      if (out && out.agent) addKV("agent", out.agent);
      if (out && out.dialogue_profile_resolved) {
        addKV("dialogue_profile_resolved", out.dialogue_profile_resolved);
      }
      if (root && root.commit_result && typeof root.commit_result === "object") {
        const cr = root.commit_result;
        const attempted = cr.attempted === true ? "yes" : "no";
        const ok = cr.ok === true ? "yes" : "no";
        const accepted = cr.accepted === true ? "yes" : (cr.accepted === false ? "no" : "—");
        addKV("commit_attempted", attempted);
        addKV("commit_ok", ok);
        addKV("commit_accepted", accepted);
        if (cr.reason) addKV("commit_reason", cr.reason);
      }

      // Résultat "monde" (aid) : /v1/pilot/aid → world_result
      if (root && root.world_result && typeof root.world_result === "object") {
        const wr = root.world_result;
        const ly = wr.lyra;
        if (ly && typeof ly === "object") {
          const gm = ly.meta;
          const gg = ly.gauges;
          if (gm && typeof gm === "object") {
            if (gm.source) addKV("world_source", gm.source);
            const rep = gm.reputation;
            if (rep && typeof rep === "object" && rep.value != null) addKV("world_reputation_value", rep.value);
          }
          if (gg && typeof gg === "object") {
            if (gg.hunger != null) addKV("world_hunger", gg.hunger);
            if (gg.thirst != null) addKV("world_thirst", gg.thirst);
            if (gg.fatigue != null) addKV("world_fatigue", gg.fatigue);
          }
        }
      }

      // Lyra meta injectée côté backend (monde / snapshot interne) : ex. réputation locale.
      if (root && root.lyra_meta && typeof root.lyra_meta === "object") {
        const lm = root.lyra_meta;
        if (lm.source) addKV("lyra_source", lm.source);
        const rep = lm.reputation;
        if (rep && typeof rep === "object" && rep.value != null) {
          addKV("reputation_value", rep.value);
        }
      }

      let html = "";
      if (rows.length) {
        html += "<table style=\"width:100%;border-collapse:collapse;margin-top:0.25rem;\"><tbody>" + rows.join("") + "</tbody></table>";
      }

      const remote = out && out.remote;
      const quest =
        (out && out.quest) ||
        (remote && typeof remote === "object" && remote.quest) ||
        null;
      const questState =
        (out && out.quest_state) ||
        (remote && typeof remote === "object" && remote.quest_state) ||
        null;
      const proposedCommit =
        (out && out.commit) ||
        (remote && typeof remote === "object" && remote.commit) ||
        null;
      const encounter =
        (out && out.encounter) ||
        (remote && typeof remote === "object" && remote.encounter) ||
        null;

      if (remote && typeof remote === "object") {
        if (remote.reply) {
          html += "<div style=\"margin-top:0.75rem;padding:0.75rem;border:1px solid #ddd;border-radius:6px;background:#fcfcfc;\">" +
            "<div class=\"muted\" style=\"margin-bottom:0.25rem;\">Réplique</div>" +
            "<div style=\"font-size:1.05rem;\">" + escapeHtml(String(remote.reply)) + "</div>" +
          "</div>";
        }
        const rmeta = remote.meta;
        if (rmeta && typeof rmeta === "object") {
          const bits = [];
          if (rmeta.cache_hit != null) {
            bits.push("cache_hit: <code>" + escapeHtml(String(rmeta.cache_hit)) + "</code>");
          }
          if (rmeta.dialogue_profile_resolved != null && String(rmeta.dialogue_profile_resolved).trim() !== "") {
            bits.push("profil résolu: <code>" + escapeHtml(String(rmeta.dialogue_profile_resolved)) + "</code>");
          }
          if (bits.length) {
            html += "<div class=\"muted\" style=\"margin-top:0.35rem\">" + bits.join(" · ") + "</div>";
          }
        }
        if (Array.isArray(remote.lines) && remote.lines.length) {
          html += "<div style=\"margin-top:0.5rem\" class=\"muted\">lines: " + escapeHtml(remote.lines.join(" | ")) + "</div>";
        }
      }

      if (quest && typeof quest === "object") {
        const title = quest.title || "Quête";
        const giver = quest.giver || "—";
        const objectives = Array.isArray(quest.objectives) ? quest.objectives : [];
        const rewards = quest.rewards && typeof quest.rewards === "object" ? quest.rewards : {};
        html += "<div style=\"margin-top:0.75rem;padding:0.75rem;border:1px solid #ddd;border-radius:6px;background:#fcfcfc;\">" +
          "<div class=\"muted\" style=\"margin-bottom:0.25rem;\">Quête</div>" +
          "<div style=\"font-size:1.05rem;\"><b>" + escapeHtml(String(title)) + "</b></div>" +
          "<div class=\"muted\" style=\"margin-top:0.15rem;\">Donneur : " + escapeHtml(String(giver)) + "</div>";
        if (objectives.length) {
          html += "<div style=\"margin-top:0.5rem\"><b>Objectifs</b><ul style=\"margin:0.25rem 0 0 1.25rem\">";
          for (const o of objectives) {
            const txt = o && o.text ? String(o.text) : JSON.stringify(o);
            html += "<li>" + escapeHtml(txt) + "</li>";
          }
          html += "</ul></div>";
        }
        const rewardParts = [];
        if (typeof rewards.gold === "number") rewardParts.push(rewards.gold + "g");
        if (typeof rewards.xp === "number") rewardParts.push(rewards.xp + "xp");
        if (Array.isArray(rewards.items) && rewards.items.length) rewardParts.push(rewards.items.join(", "));
        if (rewardParts.length) {
          html += "<div style=\"margin-top:0.5rem\"><b>Récompenses</b> : " + escapeHtml(rewardParts.join(" · ")) + "</div>";
        }
        html += "</div>";
      }

      if (questState && typeof questState === "object") {
        const qid = questState.quest_id || "—";
        const st = questState.status || "—";
        const step = questState.step != null ? String(questState.step) : "—";
        html += "<div class=\"muted\" style=\"margin-top:0.5rem\">quest_state: <code>" +
          escapeHtml(String(qid)) + "</code> · status=" + escapeHtml(String(st)) + " · step=" + escapeHtml(step) +
          "</div>";
      }

      if (proposedCommit && typeof proposedCommit === "object") {
        html += "<div style=\"margin-top:0.75rem;padding:0.75rem;border:1px solid #ddd;border-radius:6px;background:#fff8f0;\">" +
          "<div class=\"muted\" style=\"margin-bottom:0.25rem;\">Commit proposé (agent → monde)</div>" +
          "<pre style=\"margin:0;white-space:pre-wrap;font-size:0.85rem;\">" +
          escapeHtml(JSON.stringify(proposedCommit, null, 2)) +
          "</pre></div>";
      }

      const lyraOut =
        (out && out.lyra) ||
        (remote && typeof remote === "object" && remote.lyra) ||
        null;
      if (lyraOut && typeof lyraOut === "object" && !Array.isArray(lyraOut)) {
        html += "<div style=\"margin-top:0.75rem;padding:0.75rem;border:1px solid #ddd;border-radius:6px;background:#f6fcf8;\">" +
          "<div class=\"muted\" style=\"margin-bottom:0.25rem;\">Lyra (output)</div>" +
          "<pre style=\"margin:0;white-space:pre-wrap;font-size:0.85rem;\">" +
          escapeHtml(JSON.stringify(lyraOut, null, 2)) +
          "</pre></div>";
      }

      const dres = out && out.result;
      if (
        dres &&
        typeof dres === "object" &&
        (dres.kind === "http_get" || dres.kind === "read_log_tail")
      ) {
        const ok = dres.ok === true ? "ok" : "erreur";
        const lines = [];
        lines.push("kind=" + String(dres.kind));
        if (dres.url) lines.push("url=" + String(dres.url));
        if (dres.path) lines.push("path=" + String(dres.path));
        if (dres.status_code != null) lines.push("HTTP " + String(dres.status_code));
        if (dres.dry_run === true) lines.push("dry-run");
        if (dres.approval_required === true) lines.push("approbation requise (voir LBG_DEVOPS_APPROVAL_TOKEN)");
        if (dres.note) lines.push(String(dres.note));
        if (dres.error) lines.push(String(dres.error));
        if (dres.body_preview) lines.push("corps: " + String(dres.body_preview).slice(0, 500));
        if (dres.tail_preview) lines.push("fin fichier: " + String(dres.tail_preview).slice(0, 500));
        const m = out && out.meta;
        if (m && m.dry_run === true && m.dry_run_source) {
          lines.push("source dry-run: " + String(m.dry_run_source));
        }
        html +=
          "<div style=\"margin-top:0.75rem;padding:0.75rem;border:1px solid #ddd;border-radius:6px;background:#f8f6ff;\">" +
          "<div class=\"muted\" style=\"margin-bottom:0.25rem;\">DevOps (liste blanche)</div>" +
          "<div><b>" + escapeHtml(ok) + "</b> · " + escapeHtml(lines.join(" · ")) + "</div></div>";
      }

      if (encounter && typeof encounter === "object") {
        const opp = encounter.opponent || "—";
        const rnd = encounter.round != null ? String(encounter.round) : "—";
        const hp = encounter.hp && typeof encounter.hp === "object" ? encounter.hp : {};
        const php = hp.player != null ? String(hp.player) : "—";
        const ohp = hp.opponent != null ? String(hp.opponent) : "—";
        const stEnc = encounter.status != null ? String(encounter.status) : "";
        const narr = encounter.narrative ? String(encounter.narrative) : "";
        const actions = Array.isArray(encounter.suggested_actions) ? encounter.suggested_actions : [];
        html += "<div style=\"margin-top:0.75rem;padding:0.75rem;border:1px solid #ddd;border-radius:6px;background:#fcfcfc;\">" +
          "<div class=\"muted\" style=\"margin-bottom:0.25rem;\">Combat</div>" +
          "<div style=\"font-size:1.05rem;\"><b>" + escapeHtml(opp) + "</b> · tour " + escapeHtml(rnd) +
          (stEnc ? " · <span class=\"muted\">" + escapeHtml(stEnc) + "</span>" : "") + "</div>" +
          "<div class=\"muted\" style=\"margin-top:0.35rem;\">PV joueur : " + escapeHtml(php) + " · PV adversaire : " + escapeHtml(ohp) + "</div>";
        if (narr) {
          html += "<div style=\"margin-top:0.5rem\">" + escapeHtml(narr) + "</div>";
        }
        if (actions.length) {
          html += "<div style=\"margin-top:0.5rem\"><b>Actions suggérées</b> : " + escapeHtml(actions.join(", ")) + "</div>";
        }
        html += "</div>";
      }

      if (!html) return "";
      return html;
    }

    function sleep(ms) { return new Promise((res) => setTimeout(res, ms)); }

    function percentile(sortedNums, p) {
      if (!sortedNums.length) return null;
      const idx = Math.min(sortedNums.length - 1, Math.max(0, Math.ceil(p * sortedNums.length) - 1));
      return sortedNums[idx];
    }

    function loadCacheLatencyStats() {
      try {
        const raw = localStorage.getItem(STORAGE_CACHE_LAT_KEY);
        if (!raw) return { hit: [], miss: [] };
        const j = JSON.parse(raw);
        const hit = Array.isArray(j.hit) ? j.hit.filter((x) => typeof x === "number") : [];
        const miss = Array.isArray(j.miss) ? j.miss.filter((x) => typeof x === "number") : [];
        return { hit, miss };
      } catch (_) {
        return { hit: [], miss: [] };
      }
    }

    function saveCacheLatencyStats(st) {
      try {
        localStorage.setItem(STORAGE_CACHE_LAT_KEY, JSON.stringify(st));
      } catch (_) {}
    }

    function recordCacheLatencySample(resp) {
      if (!resp || typeof resp !== "object") return;
      if (typeof resp.elapsed_ms !== "number") return;
      const res = resp.result;
      const out = res && res.output;
      const remote = out && out.remote;
      const meta = remote && typeof remote === "object" ? remote.meta : null;
      const cacheHit = meta && typeof meta === "object" ? (meta.cache_hit === true) : false;
      const st = loadCacheLatencyStats();
      const bucket = cacheHit ? st.hit : st.miss;
      bucket.push(resp.elapsed_ms);
      // conserver les 200 derniers samples par bucket
      if (bucket.length > 200) bucket.splice(0, bucket.length - 200);
      saveCacheLatencyStats(st);
      renderCacheLatencyPanel();
    }

    function renderCacheLatencyPanel() {
      const el = document.getElementById("cache-lat-out");
      if (!el) return;
      const st = loadCacheLatencyStats();
      const hit = [...st.hit].sort((a, b) => a - b);
      const miss = [...st.miss].sort((a, b) => a - b);
      const summary = {
        hit: {
          n: hit.length,
          p50_ms: percentile(hit, 0.50),
          p95_ms: percentile(hit, 0.95),
          min_ms: hit.length ? hit[0] : null,
          max_ms: hit.length ? hit[hit.length - 1] : null,
        },
        miss: {
          n: miss.length,
          p50_ms: percentile(miss, 0.50),
          p95_ms: percentile(miss, 0.95),
          min_ms: miss.length ? miss[0] : null,
          max_ms: miss.length ? miss[miss.length - 1] : null,
        },
      };
      el.textContent = JSON.stringify(summary, null, 2);
    }

    function resetCacheLatencyPanel() {
      saveCacheLatencyStats({ hit: [], miss: [] });
      renderCacheLatencyPanel();
    }

    async function runBenchmark() {
      saveBase();
      const out = document.getElementById("bench-out");
      out.textContent = "…";

      const nRaw = document.getElementById("bench-n").value.trim();
      const sleepRaw = document.getElementById("bench-sleep-ms").value.trim();
      const n = Math.max(1, Math.min(200, parseInt(nRaw || "10", 10)));
      const pauseMs = Math.max(0, Math.min(5000, parseInt(sleepRaw || "0", 10)));

      const times = [];
      const errors = [];
      for (let i = 0; i < n; i++) {
        out.textContent = "Run " + (i + 1) + "/" + n + "…";
        try {
          const request = buildPilotRouteRequest();
          const r = await fetch(getBase() + "/v1/pilot/route", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(request),
          });
          const j = await r.json();
          if (!j || typeof j !== "object") throw new Error("réponse JSON invalide");
          if (j.ok !== true) throw new Error("ok=false: " + (j.error || "erreur inconnue"));
          if (typeof j.elapsed_ms !== "number") throw new Error("elapsed_ms manquant");
          times.push(j.elapsed_ms);
        } catch (e) {
          errors.push(String(e));
        }
        if (pauseMs) await sleep(pauseMs);
      }

      const sorted = [...times].sort((a, b) => a - b);
      const p50 = percentile(sorted, 0.50);
      const p95 = percentile(sorted, 0.95);
      const min = sorted.length ? sorted[0] : null;
      const max = sorted.length ? sorted[sorted.length - 1] : null;

      const summary = {
        n_requested: n,
        n_ok: times.length,
        n_errors: errors.length,
        min_ms: min,
        p50_ms: p50,
        p95_ms: p95,
        max_ms: max,
        target_vm: { p50_ms_lt: 2000, p95_ms_lt: 6000 },
        errors: errors.slice(0, 5),
        samples_ms: sorted.slice(0, 50),
      };
      out.textContent = JSON.stringify(summary, null, 2);
    }

    document.getElementById("btn-refresh").addEventListener("click", refreshHealth);
    try { document.getElementById("btn-brain-refresh").addEventListener("click", refreshBrain); } catch (_) {}
    try { document.getElementById("btn-brain-enable").addEventListener("click", () => toggleBrain(true)); } catch (_) {}
    try { document.getElementById("btn-brain-disable").addEventListener("click", () => toggleBrain(false)); } catch (_) {}
    try { document.getElementById("btn-metrics-probe-backend").addEventListener("click", probeBackendMetrics); } catch (_) {}
    try { document.getElementById("btn-metrics-open-orch").addEventListener("click", openOrchestratorMetrics); } catch (_) {}
    try { document.getElementById("btn-metrics-open-internal").addEventListener("click", openInternalHttpMetrics); } catch (_) {}
    try {
      const wsh = document.getElementById("ws-internal-http");
      if (wsh) wsh.addEventListener("input", renderMetricsLinks);
    } catch (_) {}
    try { document.getElementById("btn-assistant-converse").addEventListener("click", function () { assistantConverse().catch(function (e) { assistantUiHint(String(e), true); }); }); } catch (_) {}
    try { document.getElementById("btn-assistant-propose").addEventListener("click", assistantPropose); } catch (_) {}
    try { document.getElementById("btn-assistant-apply-proposal").addEventListener("click", assistantApplyProposalToContext); } catch (_) {}
    try {
      document.getElementById("btn-assistant-exec").addEventListener("click", function () {
        var t = document.getElementById("assistant-exec-real-toggle");
        var mode = t && t.checked ? "real" : "dry_run";
        assistantExecute(mode).catch(function (e) {
          assistantUiHint(String(e), true);
        });
      });
    } catch (_) {}
    try { document.getElementById("btn-assistant-preset-notepad").addEventListener("click", () => assistantPreset("notepad")); } catch (_) {}
    try { document.getElementById("btn-assistant-preset-web").addEventListener("click", () => assistantPreset("web")); } catch (_) {}
    try { document.getElementById("btn-assistant-preset-mail").addEventListener("click", () => assistantPreset("mail")); } catch (_) {}
    try { document.getElementById("btn-assistant-preset-selfcheck").addEventListener("click", () => assistantPreset("selfcheck")); } catch (_) {}
    try { document.getElementById("btn-assistant-save-prefs").addEventListener("click", assistantSavePrefs); } catch (_) {}
    try { document.getElementById("btn-assistant-history-clear").addEventListener("click", assistantHistoryClear); } catch (_) {}
    try { document.getElementById("btn-assistant-session-build").addEventListener("click", assistantSessionBuildSummary); } catch (_) {}
    try { document.getElementById("btn-assistant-session-copy").addEventListener("click", assistantSessionCopySummary); } catch (_) {}
    try { document.getElementById("btn-assistant-session-export-server").addEventListener("click", function () {
      assistantSessionExportViaServer().catch(function (e) { pilotInlineHint("assistant-session-hint", String(e), true); });
    }); } catch (_) {}
    try { document.getElementById("btn-assistant-session-mmo-bridge").addEventListener("click", function () {
      assistantSessionMmoBridgeApply().catch(function (e) { pilotInlineHint("assistant-session-hint", String(e), true); });
    }); } catch (_) {}
    try { document.getElementById("btn-assistant-caps-refresh").addEventListener("click", function () {
      assistantCapsRefresh().catch(function () {});
    }); } catch (_) {}
    try { document.getElementById("btn-assistant-session-state-refresh").addEventListener("click", assistantRenderSessionState); } catch (_) {}
    try { document.getElementById("btn-assistant-mmo-merge").addEventListener("click", assistantMmoMergeIntoContext); } catch (_) {}
    try { document.getElementById("btn-assistant-mmo-load-desktop-key").addEventListener("click", assistantMmoLoadFromSharedStorage); } catch (_) {}
    try { document.getElementById("btn-assistant-mmo-save-desktop-key").addEventListener("click", assistantMmoSaveToSharedStorage); } catch (_) {}
    try { document.getElementById("btn-assistant-preset-mmo-dev").addEventListener("click", () => assistantPreset("mmo_dev")); } catch (_) {}
    try {
      const asn = document.getElementById("assistant-session-notes");
      if (asn && !asn.dataset.lbgBound) {
        asn.dataset.lbgBound = "1";
        asn.addEventListener("blur", assistantSessionNotesPersist);
      }
    } catch (_) {}
    document.getElementById("btn-cap-refresh").addEventListener("click", refreshCapabilities);
    document.getElementById("btn-send").addEventListener("click", sendIntent);
    document.getElementById("btn-bench").addEventListener("click", runBenchmark);
    try { document.getElementById("btn-cache-lat-reset").addEventListener("click", resetCacheLatencyPanel); } catch (_) {}
    document.getElementById("btn-copy-json").addEventListener("click", async () => {
      const hint = document.getElementById("copy-hint");
      const j = window.__last_intent_json;
      if (!j) { hint.textContent = "Rien à copier (faites un envoi)."; return; }
      try {
        await navigator.clipboard.writeText(JSON.stringify(j, null, 2));
        hint.textContent = "Copié.";
      } catch (e) {
        hint.textContent = "Copie impossible: " + e;
      }
    });

    document.getElementById("btn-reset-history").addEventListener("click", () => {
      let context = {};
      try {
        const raw = document.getElementById("context-json").value.trim();
        if (raw) context = JSON.parse(raw);
      } catch (_) {}
      const npcKey = getNpcKeyFromContext(context);
      saveHistory(npcKey, []);
      const nextContext = { ...(context || {}), history: [] };
      document.getElementById("context-json").value = JSON.stringify(nextContext, null, 2);
      document.getElementById("history-pretty").innerHTML = "";
      saveChatState();
    });

    const PRESETS = {
      forge: {
        text: "Je veux parler au forgeron",
        context: { npc_name: "Hagen le forgeron", world_npc_id: "npc:smith", history: [] },
      },
      healer: {
        text: "Je ne me sens pas bien… peux-tu m'aider ?",
        context: { npc_name: "Guérisseuse du village", world_npc_id: "npc:healer", history: [] },
      },
      alchemist: {
        text: "Je cherche une potion ou un remède.",
        context: { npc_name: "Alchimiste", world_npc_id: "npc:alchemist", history: [] },
      },
      mayor: {
        text: "Y a-t-il des problèmes récents au village ?",
        context: { npc_name: "Maire", world_npc_id: "npc:mayor", history: [] },
      },
      auberge: {
        text: "Une chambre pour la nuit, s'il vous plaît.",
        context: { npc_name: "Mara l’aubergiste", world_npc_id: "npc:innkeeper", history: [] },
      },
      garde: {
        text: "Que se passe-t-il en ville ?",
        context: { npc_name: "Garde de la porte", world_npc_id: "npc:guard", history: [] },
      },
      scribe: {
        text: "Que racontent les rumeurs du jour ?",
        context: { npc_name: "Scribe du village", world_npc_id: "npc:scribe", history: [] },
      },
      quete: {
        text: "Je cherche une quête ou une mission.",
        context: { history: [] },
      },
      quete_npc: {
        text: "Aurais-tu une mission pour moi ?",
        context: { npc_name: "Mara l’aubergiste", history: [] },
      },
      quete_avancement: {
        text: "J'ai avancé sur la quête.",
        // Ne pas figer quest_state ici : on le réinjecte depuis le stockage local (voir applyPreset/buildPilotRouteRequest).
        context: { history: [] },
      },
      // Valide la phase 2 : l'agent propose output.commit, le backend tente dialogue-commit vers mmmorpg,
      // et la réponse pilot affiche commit_result.
      quete_commit: {
        text: "J'accepte la quête.",
        context: {
          npc_name: "Marchand civile",
          world_npc_id: "npc:merchant",
          history: [],
          // quest_state sera réinjecté du stockage si dispo (applyPreset ci-dessous).
        },
      },
      quete_commit_mayor: {
        text: "J'accepte la quête.",
        context: {
          npc_name: "Maire",
          world_npc_id: "npc:mayor",
          history: [],
          // quest_state sera réinjecté du stockage si dispo (applyPreset ci-dessous).
        },
      },
      quete_commit_healer: {
        text: "J'accepte la quête.",
        context: {
          npc_name: "Guérisseuse du village",
          world_npc_id: "npc:healer",
          history: [],
        },
      },
      quete_commit_alchemist: {
        text: "J'accepte la quête.",
        context: {
          npc_name: "Alchimiste",
          world_npc_id: "npc:alchemist",
          history: [],
        },
      },
      combat: {
        text: "Je veux attaquer le gobelin",
        context: { enemy_name: "Gobelin des égouts", history: [] },
      },
      combat_avancement: {
        text: "Je continue le combat en frappant",
        // encounter_state réinjecté depuis le stockage local (voir applyPreset / buildPilotRouteRequest).
        context: { history: [] },
      },
      devops_sonde: {
        text: "Sonde DevOps — healthz orchestrator",
        context: {
          devops_action: { kind: "http_get", url: "http://127.0.0.1:8010/healthz" },
          history: [],
        },
      },
      // Texte sans mots-clés quête / dialogue / combat / devops → intent "unknown" → agent.fallback → echo output.lyra
      lyra_test: {
        text: "Ping état Lyra (fallback)",
        context: {
          history: [],
          lyra: {
            gauges: { hunger: 0.1, thirst: 0.05, fatigue: 0.2 },
            dt_s: 3600,
            version: "0.1",
          },
        },
      },
      // Dialogue PNJ + world_npc_id : le backend appelle GET /v1/world/lyra sur LBG_MMO_SERVER_URL (jauges tick monde).
      lyra_mmo: {
        text: "Salut, quelle est ta journée au village ?",
        context: {
          npc_name: "Forgeron",
          world_npc_id: "npc:smith",
          history: [],
        },
      },
      aid_commit: {
        text: "Aide le PNJ (commit, sans LLM)",
        context: {
          world_npc_id: "npc:merchant",
          world_action: { kind: "aid", hunger_delta: -0.2, thirst_delta: -0.1, fatigue_delta: -0.2, reputation_delta: 5 },
          history: [],
        },
      },
      aid_llm: {
        text: "J'ai faim, soif et je suis épuisé. Peux-tu m'aider tout de suite ?",
        context: {
          npc_name: "Marchand civile",
          world_npc_id: "npc:merchant",
          history: [],
        },
      },
    };

    function applyPreset(key) {
      const src = PRESETS[key];
      if (!src) return;
      const p = { text: src.text, context: JSON.parse(JSON.stringify(src.context || {})) };
      // Convenience : si on veut tester l'avancement, injecter le dernier quest_id connu.
      if (key === "quete_avancement") {
        try {
          // 1) D'abord tenter via l'état persistant (global ou npc_name si présent).
          let ctx = {};
          try { ctx = JSON.parse(document.getElementById("context-json").value || "{}"); } catch (_) {}
          const npcKey = getNpcKeyFromContext(ctx);
          const stored = loadQuestState(npcKey) || loadQuestState("global");
          if (stored && stored.quest_id) {
            p.context.quest_state = stored;
          } else {
            // 2) Sinon fallback via la dernière réponse reçue.
            const last = window.__last_intent_json;
            const qid = last && last.result && last.result.output && last.result.output.quest_state && last.result.output.quest_state.quest_id;
            if (qid) p.context.quest_state = { quest_id: qid, status: "open", step: 0 };
          }
        } catch (_) {}
      }
      if (key === "quete_commit") {
        try {
          let ctx = {};
          try { ctx = JSON.parse(document.getElementById("context-json").value || "{}"); } catch (_) {}
          const npcKey = getNpcKeyFromContext(ctx);
          const stored = loadQuestState(npcKey) || loadQuestState("global");
          if (stored && stored.quest_id) {
            p.context.quest_state = stored;
          }
        } catch (_) {}
      }
      if (key === "combat_avancement") {
        try {
          let ctx = {};
          try { ctx = JSON.parse(document.getElementById("context-json").value || "{}"); } catch (_) {}
          const combatKey = getCombatKeyFromContext(ctx);
          const stored = loadEncounterState(combatKey) || loadEncounterState("global");
          if (stored && stored.encounter_id) {
            p.context.enemy_name = ctx.enemy_name || ctx.target_name || ctx.opponent || stored.opponent || "Adversaire";
            p.context.encounter_state = stored;
          } else {
            const last = window.__last_intent_json;
            const enc =
              last && last.result && last.result.output && last.result.output.encounter;
            if (enc && typeof enc === "object" && enc.encounter_id) {
              p.context.enemy_name =
                ctx.enemy_name || ctx.target_name || ctx.opponent || enc.opponent || "Adversaire";
              p.context.encounter_state = {
                encounter_id: enc.encounter_id,
                round: enc.round,
                opponent: enc.opponent,
                hp: enc.hp || {},
                status: enc.status || "ongoing",
              };
            }
          }
        } catch (_) {}
      }
      document.getElementById("text").value = p.text;
      document.getElementById("context-json").value = JSON.stringify(p.context, null, 2);
      saveChatState();
    }

    for (const btn of document.querySelectorAll("button.preset")) {
      btn.addEventListener("click", () => applyPreset(btn.dataset.preset));
    }

    async function postJson(url, payload, timeoutMs) {
      const token = getServiceToken();
      const headers = { "content-type": "application/json" };
      if (token) headers["X-LBG-Service-Token"] = token;
      let r;
      try {
        r = await pilotFetchWithTimeout(
          url,
          { method: "POST", headers: headers, body: JSON.stringify(payload) },
          timeoutMs || 120000
        );
      } catch (e) {
        const msg = e && e.name === "AbortError" ? "délai dépassé" : String(e && e.message ? e.message : e);
        return { status: 0, json: { ok: false, error: msg }, text: "" };
      }
      const t = await r.text();
      let j = null;
      try { j = t ? JSON.parse(t) : null; } catch (_) {}
      return { status: r.status, json: j, text: t };
    }

    function assistantUiHint(msg, isError) {
      pilotInlineHint("assistant-hint", msg || "—", !!isError);
      try {
        const el = document.getElementById("assistant-hint");
        if (el) el.classList.toggle("assistant-hint-err", !!isError);
      } catch (_) {}
    }

    function assistantStyleExecButtonForMode() {
      const t = document.getElementById("assistant-exec-real-toggle");
      const b = document.getElementById("btn-assistant-exec");
      if (!b) return;
      const real = t && t.checked;
      b.classList.toggle("assistant-btn-real", !!real);
      b.title = real
        ? "Exécuter avec effets réels (jeton d’approbation selon capability)"
        : "Exécuter en simulation (dry-run)";
    }

    function assistantLooksLikeStatusQuery(text) {
      const t = String(text || "").trim();
      if (!t) return false;
      if (
        /où\s+(?:en|on)\s+(?:est|êtes|es-t-on)|ou\s+en\s+est|on\s+en\s+est\s+où|quel\s+(?:est\s+)?(?:le\s+)?(?:statut|état|avancement)|point\s+sur|état\s+(?:du|de)|avancement\s+(?:du|de)|compte\s+rendu|actions?\s+en\s+cours/i.test(
          t
        )
      ) {
        return true;
      }
      return (
        /\b(?:statut|état|avancement|où|compte\s+rendu|actions?\s+en\s+cours)\b/i.test(t) &&
        /\b(?:lora|godot|tri|images?|sprites?|devops|équipe|equipe|team|zb-?1|pygmalion|infra|kohya|campus)\b/i.test(t)
      );
    }

    function extractPilotRouteReply(json) {
      const res = json && json.result;
      const out = res && res.output;
      if (!out || typeof out !== "object") return "";
      const remote = out.remote;
      if (remote && typeof remote === "object") {
        if (typeof remote.reply === "string" && remote.reply.trim()) return remote.reply.trim();
        if (Array.isArray(remote.lines) && remote.lines.length) {
          return remote.lines.map(String).join("\n").trim();
        }
      }
      if (typeof out.reply === "string" && out.reply.trim()) return out.reply.trim();
      return "";
    }

    function assistantRouteIntentMeta(routeJson) {
      const res = routeJson && routeJson.result ? routeJson.result : {};
      const out = res.output && typeof res.output === "object" ? res.output : {};
      const remote = out.remote && typeof out.remote === "object" ? out.remote : {};
      const rmeta = remote.meta && typeof remote.meta === "object" ? remote.meta : {};
      return {
        intent: res.intent || "",
        routed_to: res.routed_to || "",
        capability: out.capability || "",
        agent: out.agent || "",
        handler: out.handler || "",
        voice: out.voice && typeof out.voice === "object" ? out.voice : null,
        remote_meta: rmeta,
      };
    }

    function assistantShouldLlmFallbackAfterRoute(routeJson, reply, prefs) {
      if (!prefs || prefs.route_first_llm_fallback === false) return false;
      if (!routeJson || routeJson.ok === false) return true;
      const meta = assistantRouteIntentMeta(routeJson);
      if (!reply || !String(reply).trim()) return true;
      if (meta.intent === "unknown") return true;
      if (meta.intent === "npc_dialogue" && meta.agent === "minimal_stub") return true;
      return false;
    }

    function assistantSetRouteBadge(routeJson) {
      const el = document.getElementById("assistant-dialogue-badge");
      if (!el) return;
      const meta = assistantRouteIntentMeta(routeJson);
      const rmeta = meta.remote_meta || {};
      const voice = meta.voice || {};
      const skill = voice.skill || meta.intent || meta.capability || "route";
      el.hidden = false;
      el.className = "assistant-route-badge";
      if (meta.intent === "assistant_chat" || voice.first_contact) {
        el.textContent = "Accueil";
        el.classList.add("assistant-route-badge--factual");
        el.title = "Intro LBG-IA — premier contact.";
      } else if (rmeta.factual_status === true || meta.agent === "lbg_ia_voice" || meta.agent === "team_status") {
        el.textContent = String(skill).slice(0, 18);
        el.classList.add("assistant-route-badge--factual");
        el.title =
          "Compétence LBG-IA : " + String(skill) + " (intent=" + meta.intent + ") — routé sans LLM dialogue.";
      } else if (meta.intent === "npc_dialogue" || meta.routed_to === "agent.dialogue") {
        if (rmeta.llm === false) {
          el.textContent = "hors LLM";
          el.classList.add("assistant-route-badge--off");
          el.title = "Dialogue routé — LLM désactivé ou stub.";
        } else if (rmeta.stub === true) {
          el.textContent = "stub";
          el.classList.add("assistant-route-badge--stub");
          el.title = "Dialogue routé — réponse de secours.";
        } else {
          el.textContent = "LLM";
          el.classList.add("assistant-route-badge--llm");
          el.title = "Dialogue routé via orchestrateur → agent dialogue.";
        }
      } else {
        el.textContent = String(skill).slice(0, 18);
        el.classList.add("assistant-route-badge--factual");
        el.title =
          "Routé : " + meta.intent + " → " + (meta.routed_to || meta.capability || "—");
      }
    }

    function assistantSetFactualRouteBadge(routeJson) {
      assistantSetRouteBadge(routeJson);
    }

    function assistantCommitChatTurn(ctx, ctxEl, text, replyNorm) {
      if (!Array.isArray(ctx.history)) ctx.history = [];
      ctx.history = ctx.history.concat([
        { role: "user", content: text },
        { role: "assistant", content: replyNorm },
      ]);
      if (ctx.history.length > 24) ctx.history = ctx.history.slice(-24);
      ctx._lbg_ia_greeted = true;
      if (ctxEl) ctxEl.value = JSON.stringify(ctx, null, 2);
      assistantHistoryAdd({ kind: "chat_user", text: text.slice(0, 8000) });
      assistantHistoryAdd({ kind: "chat_assistant", text: replyNorm.slice(0, 8000) });
    }

    function assistantAvatarSay(replyNorm) {
      try {
        if (window.OrchestratorAvatar && OrchestratorAvatar.ready) OrchestratorAvatar.say(replyNorm);
      } catch (_) {}
      try {
        if (window.FaceRig && FaceRig.ready) FaceRig.say(replyNorm);
      } catch (_) {}
    }

    function assistantRenderRouteJson(routeOut, rawEl, prettyEl) {
      if (rawEl) rawEl.textContent = routeOut.json ? JSON.stringify(routeOut.json, null, 2) : "";
      if (prettyEl) {
        try {
          prettyEl.innerHTML = routeOut.json ? renderPretty(routeOut.json) : "";
        } catch (_) {
          prettyEl.innerHTML = "";
        }
      }
    }

    function assistantClearDialogueRouteBadge() {
      const el = document.getElementById("assistant-dialogue-badge");
      if (!el) return;
      el.hidden = true;
      el.textContent = "";
      el.title = "";
      el.className = "assistant-route-badge";
    }

    function assistantSetDialogueRouteBadge(out) {
      const el = document.getElementById("assistant-dialogue-badge");
      if (!el) return;
      if (!out || out.status !== 200 || !out.json) {
        el.hidden = true;
        return;
      }
      const meta = out.json.meta && typeof out.json.meta === "object" ? out.json.meta : {};
      const stub = meta.stub === true;
      const llmOn = meta.llm !== false;
      const factual = meta.factual_status === true;
      el.hidden = false;
      el.className = "assistant-route-badge";
      if (factual) {
        el.textContent = "FAIT";
        el.classList.add("assistant-route-badge--factual");
        el.title =
          "Réponse factuelle (sondes locales) — intent=" +
          String(meta.status_intent || "status") +
          " — pas de LLM.";
      } else if (!llmOn) {
        el.textContent = "hors LLM";
        el.classList.add("assistant-route-badge--off");
        el.title =
          "Côté agent : pas de route LLM active (ex. LBG_DIALOGUE_LLM_BASE_URL / LBG_DIALOGUE_LLM désactivé).";
      } else if (stub) {
        el.textContent = "stub";
        el.classList.add("assistant-route-badge--stub");
        var err = typeof meta.llm_error === "string" ? meta.llm_error.trim() : "";
        el.title = err ? ("Réponse de secours — " + err.slice(0, 420)) : "Réponse de secours (stub).";
      } else {
        el.textContent = "LLM";
        el.classList.add("assistant-route-badge--llm");
        el.title = "Tour issu du modèle configuré sur le service dialogue (Ollama / OpenAI-compatible).";
      }
    }

    function assistantPersistExecToggle() {
      try {
        const prefs = assistantReadPrefsFromUi();
        localStorage.setItem(STORAGE_ASSISTANT_PREFS_KEY, JSON.stringify(prefs));
      } catch (_) {}
    }

    function assistantDefaultPrefs() {
      return {
        notepad_path: "C:\\Users\\Public\\lbg_desktop.txt",
        dry_run_default: true,
        exec_real: false,
        auto_simulate_after_propose: true,
        auto_real_after_sim_ok: true,
        dialogue_desktop_plan: false,
        route_first: true,
        route_first_llm_fallback: true,
      };
    }

    function assistantLoadPrefs() {
      const defaults = assistantDefaultPrefs();
      try {
        const raw = localStorage.getItem(STORAGE_ASSISTANT_PREFS_KEY);
        if (!raw) return defaults;
        const parsed = JSON.parse(raw);
        if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return defaults;
        return {
          ...defaults,
          notepad_path: typeof parsed.notepad_path === "string" && parsed.notepad_path.trim()
            ? parsed.notepad_path.trim()
            : defaults.notepad_path,
          dry_run_default: parsed.dry_run_default !== false,
          exec_real: parsed.exec_real === true,
          auto_simulate_after_propose: parsed.auto_simulate_after_propose !== false,
          auto_real_after_sim_ok: parsed.auto_real_after_sim_ok !== false,
          dialogue_desktop_plan: parsed.dialogue_desktop_plan === true,
          route_first: parsed.route_first !== false,
          route_first_llm_fallback: parsed.route_first_llm_fallback !== false,
        };
      } catch (_) {
        return defaults;
      }
    }

    function assistantApplyPrefsToUi() {
      const prefs = assistantLoadPrefs();
      const pathEl = document.getElementById("assistant-pref-notepad-path");
      const dryEl = document.getElementById("assistant-pref-dry-run");
      const execTgl = document.getElementById("assistant-exec-real-toggle");
      const autoSimEl = document.getElementById("assistant-pref-auto-sim-after-propose");
      const autoRealEl = document.getElementById("assistant-pref-auto-real-after-sim");
      const deskPlanEl = document.getElementById("assistant-pref-dialogue-desktop-plan");
      const routeFirstEl = document.getElementById("assistant-pref-route-first");
      const routeLlmEl = document.getElementById("assistant-pref-route-llm-fallback");
      if (pathEl) pathEl.value = prefs.notepad_path;
      if (dryEl) dryEl.checked = prefs.dry_run_default !== false;
      if (execTgl) execTgl.checked = prefs.exec_real === true;
      if (autoSimEl) autoSimEl.checked = prefs.auto_simulate_after_propose !== false;
      if (autoRealEl) autoRealEl.checked = prefs.auto_real_after_sim_ok !== false;
      if (deskPlanEl) deskPlanEl.checked = prefs.dialogue_desktop_plan === true;
      if (routeFirstEl) routeFirstEl.checked = prefs.route_first !== false;
      if (routeLlmEl) routeLlmEl.checked = prefs.route_first_llm_fallback !== false;
      assistantStyleExecButtonForMode();
    }

    function assistantReadPrefsFromUi() {
      const defaults = assistantDefaultPrefs();
      const pathEl = document.getElementById("assistant-pref-notepad-path");
      const dryEl = document.getElementById("assistant-pref-dry-run");
      const execTgl = document.getElementById("assistant-exec-real-toggle");
      const autoSimEl = document.getElementById("assistant-pref-auto-sim-after-propose");
      const autoRealEl = document.getElementById("assistant-pref-auto-real-after-sim");
      const deskPlanEl = document.getElementById("assistant-pref-dialogue-desktop-plan");
      const routeFirstEl = document.getElementById("assistant-pref-route-first");
      const routeLlmEl = document.getElementById("assistant-pref-route-llm-fallback");
      const path = pathEl && pathEl.value ? String(pathEl.value).trim() : "";
      return {
        notepad_path: path || defaults.notepad_path,
        dry_run_default: !(dryEl && dryEl.checked === false),
        exec_real: !!(execTgl && execTgl.checked),
        auto_simulate_after_propose: !(autoSimEl && autoSimEl.checked === false),
        auto_real_after_sim_ok: !(autoRealEl && autoRealEl.checked === false),
        dialogue_desktop_plan: !!(deskPlanEl && deskPlanEl.checked),
        route_first: !(routeFirstEl && routeFirstEl.checked === false),
        route_first_llm_fallback: !(routeLlmEl && routeLlmEl.checked === false),
      };
    }

    function assistantSavePrefs() {
      const prefs = assistantReadPrefsFromUi();
      try {
        localStorage.setItem(STORAGE_ASSISTANT_PREFS_KEY, JSON.stringify(prefs));
        pilotInlineHint("assistant-pref-hint", "Préférences sauvées localement.", false);
      } catch (e) {
        pilotInlineHint("assistant-pref-hint", "Sauvegarde impossible: " + e, true);
      }
    }

    function assistantHistoryLoad() {
      try {
        const raw = localStorage.getItem(STORAGE_ASSISTANT_HISTORY_KEY);
        if (!raw) return [];
        const parsed = JSON.parse(raw);
        return Array.isArray(parsed) ? parsed.filter((x) => x && typeof x === "object").slice(0, 12) : [];
      } catch (_) {
        return [];
      }
    }

    function assistantLoadLyraGauges() {
      const d = assistantDefaultLyraGauges();
      try {
        const raw = localStorage.getItem(STORAGE_ASSISTANT_LYRA_KEY);
        if (!raw) return d;
        const o = JSON.parse(raw);
        if (!o || typeof o !== "object") return d;
        for (const k of Object.keys(d)) {
          const n = parseInt(String(o[k]), 10);
          if (!isNaN(n)) d[k] = Math.max(0, Math.min(100, n));
        }
        return d;
      } catch (_) {
        return d;
      }
    }

    function assistantSaveLyraGauges(g) {
      try {
        localStorage.setItem(STORAGE_ASSISTANT_LYRA_KEY, JSON.stringify(g));
      } catch (_) {}
    }

    function assistantMotivationText(g) {
      const c = g.confiance;
      const e = g.energie;
      const p = g.patience;
      if (c >= 75 && p >= 65) return "Motivation · allant calme : vous pouvez enchaîner propositions puis dry-run.";
      if (c < 45) return "Motivation · prudence : relire le JSON, garder dry-run et approvals visibles.";
      if (p < 45) return "Motivation · patience basse : clarifier la demande avant toute exécution réelle.";
      if (e < 40) return "Motivation · rythme léger : privilégier des tours courts et des contrôles simples.";
      return "Motivation · équilibre : proposer → dry-run → décider avec jeton si besoin.";
    }

    /**
     * Alimente context.lyra pour l'agent dialogue : jauges Pilot → clés lues par dialogue_llm._format_lyra_for_prompt
     * (fatigue 0–1, patience/stress 0–100) + texte de motivation pour le ton.
     */
    function assistantBuildLyraContextForDialogue() {
      const g = assistantLoadLyraGauges();
      const chaleur = g.chaleur != null ? g.chaleur : 70;
      const energie = g.energie != null ? g.energie : 60;
      const patience = g.patience != null ? g.patience : 70;
      const confiance = g.confiance != null ? g.confiance : 70;
      return {
        version: "pilot_assistant_v1",
        meta: {
          source: "pilot_web#/assistant",
          pilot_motivation: assistantMotivationText(g),
          gauges_raw: { chaleur: chaleur, energie: energie, patience: patience, confiance: confiance },
        },
        gauges: {
          fatigue: Math.max(0, Math.min(1, (100 - energie) / 100)),
          patience: patience,
          stress: Math.max(0, Math.min(100, 100 - confiance)),
        },
      };
    }

    function assistantRenderLyraPanel() {
      const host = document.getElementById("assistant-lyra-panel");
      const mot = document.getElementById("assistant-motivation-line");
      if (!host) return;
      const g = assistantLoadLyraGauges();
      const keys = [
        ["chaleur", "Chaleur"],
        ["energie", "Énergie"],
        ["patience", "Patience"],
        ["confiance", "Confiance"],
      ];
      var html = "<div class=\"assistant-lyra-mini\">";
      for (var i = 0; i < keys.length; i++) {
        var key = keys[i][0];
        var lab = keys[i][1];
        var v = g[key] != null ? g[key] : 70;
        html +=
          "<div class=\"assistant-lyra-row\"><span>" +
          escapeHtml(lab) +
          "</span><input type=\"range\" min=\"0\" max=\"100\" data-lyra-k=\"" +
          escapeHtml(key) +
          "\" value=\"" +
          v +
          "\" /><span class=\"assistant-lyra-val\">" +
          v +
          "</span></div>";
      }
      html += "</div>";
      host.innerHTML = html;
      var inputs = host.querySelectorAll("input[type=range]");
      for (var j = 0; j < inputs.length; j++) {
        (function (inp) {
          inp.addEventListener("input", function () {
            var k = inp.getAttribute("data-lyra-k");
            var gg = assistantLoadLyraGauges();
            if (k && gg) {
              gg[k] = parseInt(inp.value, 10) || 0;
              assistantSaveLyraGauges(gg);
              var row = inp.closest(".assistant-lyra-row");
              var vv = row && row.querySelector(".assistant-lyra-val");
              if (vv) vv.textContent = String(gg[k]);
              if (mot) mot.textContent = assistantMotivationText(gg);
            }
          });
        })(inputs[j]);
      }
      if (mot) mot.textContent = assistantMotivationText(g);
    }

    function assistantNudgeLyraFromPolicy(decision, metaKind) {
      const gg = assistantLoadLyraGauges();
      const d = String(decision || "");
      if (d === "approval_required") {
        gg.patience = Math.max(15, (gg.patience || 70) - 5);
        gg.confiance = Math.max(20, (gg.confiance || 70) - 4);
      } else if (d === "forbidden") {
        gg.confiance = Math.max(25, (gg.confiance || 70) - 6);
        gg.patience = Math.max(20, (gg.patience || 70) - 3);
      } else if (d === "dry_run") {
        gg.energie = Math.min(100, (gg.energie || 60) + 3);
        gg.chaleur = Math.min(100, (gg.chaleur || 70) + 2);
      } else if (d === "safe_read" || d === "approved_action") {
        gg.confiance = Math.min(100, (gg.confiance || 70) + 2);
      }
      if (metaKind === "proposal") {
        gg.chaleur = Math.min(100, (gg.chaleur || 70) + 1);
      }
      assistantSaveLyraGauges(gg);
      assistantRenderLyraPanel();
    }

    function assistantChatScrollToEnd() {
      const stream = document.getElementById("assistant-chat-stream");
      if (stream) stream.scrollTop = stream.scrollHeight;
    }

    function assistantBindAssistantPage() {
      if (document.body.dataset.assistantUxBound) return;
      document.body.dataset.assistantUxBound = "1";
      const cb = document.getElementById("assistant-opt-advanced");
      const det = document.getElementById("assistant-details-advanced");
      if (cb && det) {
        cb.addEventListener("change", function () {
          det.open = !!cb.checked;
          try {
            localStorage.setItem(STORAGE_ASSISTANT_UI_ADVANCED_KEY, cb.checked ? "1" : "0");
          } catch (_) {}
        });
      }
      const ta = document.getElementById("assistant-text");
      if (ta && !ta.dataset.composerKeys) {
        ta.dataset.composerKeys = "1";
        ta.addEventListener("keydown", function (e) {
          if (e.key !== "Enter") return;
          if (e.shiftKey) return;
          if (e.ctrlKey || e.metaKey) {
            e.preventDefault();
            assistantPropose().catch(function (err) {
              assistantUiHint(String(err), true);
            });
            return;
          }
          e.preventDefault();
          assistantConverse().catch(function (err) {
            assistantUiHint(String(err), true);
          });
        });
      }
      const exTgl = document.getElementById("assistant-exec-real-toggle");
      if (exTgl && !exTgl.dataset.persistBound) {
        exTgl.dataset.persistBound = "1";
        exTgl.addEventListener("change", function () {
          assistantStyleExecButtonForMode();
          assistantPersistExecToggle();
        });
      }
      const pipeS = document.getElementById("assistant-pref-auto-sim-after-propose");
      const pipeR = document.getElementById("assistant-pref-auto-real-after-sim");
      function bindPipe(cb) {
        if (cb && !cb.dataset.persistBound) {
          cb.dataset.persistBound = "1";
          cb.addEventListener("change", assistantPersistExecToggle);
        }
      }
      bindPipe(pipeS);
      bindPipe(pipeR);
      const deskPlanCb = document.getElementById("assistant-pref-dialogue-desktop-plan");
      if (deskPlanCb && !deskPlanCb.dataset.persistBound) {
        deskPlanCb.dataset.persistBound = "1";
        deskPlanCb.addEventListener("change", assistantPersistExecToggle);
      }
      const moodBtn = document.getElementById("btn-assistant-orch-mood-refresh");
      if (moodBtn && !moodBtn.dataset.bound) {
        moodBtn.dataset.bound = "1";
        moodBtn.addEventListener("click", function () {
          assistantOrchMoodRefresh().catch(function () {});
        });
      }
    }

    function assistantSyncAdvancedPanel() {
      try {
        const cb = document.getElementById("assistant-opt-advanced");
        const det = document.getElementById("assistant-details-advanced");
        if (!cb || !det) return;
        const v = localStorage.getItem(STORAGE_ASSISTANT_UI_ADVANCED_KEY);
        const on = v === "1";
        cb.checked = on;
        det.open = on;
      } catch (_) {}
    }

    function assistantDefaultLyraGauges() {
      return { chaleur: 70, energie: 60, patience: 70, confiance: 70 };
    }

    function assistantHistorySave(items) {
      try {
        localStorage.setItem(STORAGE_ASSISTANT_HISTORY_KEY, JSON.stringify((items || []).slice(0, 12)));
      } catch (_) {}
    }

    function assistantHistoryAdd(item) {
      const items = assistantHistoryLoad();
      const next = [
        {
          ts: new Date().toISOString(),
          ...item,
        },
      ].concat(items).slice(0, 12);
      assistantHistorySave(next);
      assistantHistoryRender();
    }

    function assistantHistoryClear() {
      assistantHistorySave([]);
      assistantHistoryRender();
      pilotInlineHint("assistant-history-hint", "Historique vidé.", false);
      try {
        const ctxEl = document.getElementById("assistant-context");
        if (!ctxEl) return;
        let o = assistantParseJsonTextarea("assistant-context", {});
        if (o && typeof o === "object" && !Array.isArray(o)) {
          o.history = [];
          ctxEl.value = JSON.stringify(o, null, 2);
        }
      } catch (_) {}
    }

    function assistantHistoryRender() {
      const stream = document.getElementById("assistant-chat-stream");
      const hiddenHist = document.getElementById("assistant-history");
      if (hiddenHist) hiddenHist.innerHTML = "";
      const items = assistantHistoryLoad();
      if (!stream) return;
      if (!items.length) {
        stream.innerHTML =
          '<div class="assistant-chat-empty">' +
          '<svg width="44" height="44" viewBox="0 0 24 24" fill="none" aria-hidden="true" style="margin:0 auto 1rem;display:block;opacity:.75">' +
          '<path fill="#2dd4bf" fill-opacity=".35" d="M12 2l1.09 6.26L18 10l-5.91 1.74L12 18l-1.09-6.26L5 10l5.91-1.74L12 2z"/>' +
          '<circle cx="8" cy="7" r="1.2" fill="#5eead4"/>' +
          '<circle cx="15" cy="16" r="1" fill="#64748b"/>' +
          "</svg>" +
          "<strong>Bienvenue — Compagnon</strong><br>" +
          "Je suis là pour dialoguer, concevoir et agir sous ton contrôle. " +
          "Pose une question en langage naturel : je route vers la bonne compétence " +
          "(équipe, projet, Godot, infra…) et je réponds factuellement. " +
          "<strong>Envoyer</strong> pour parler, <strong>Proposer une action</strong> (mode Ops) pour exécuter avec garde-fous.</div>";
        return;
      }
      const parts = [];
      for (const it of items) {
        const when = it.ts ? new Date(String(it.ts)).toLocaleTimeString() : "";
        const kind = it.kind || "event";
        const text = it.text || it.summary || "";
        const cap = it.capability ? String(it.capability) : "";
        const dec = it.policy_decision ? String(it.policy_decision) : "";
        let msgClass = "assistant-msg--proposal";
        if (kind === "execute_dry_run") msgClass = "assistant-msg--execute_dry_run";
        else if (kind === "execute_real") msgClass = "assistant-msg--execute_real";
        else if (kind === "chat_user") msgClass = "assistant-msg--chat_user";
        else if (kind === "chat_assistant") msgClass = "assistant-msg--chat_assistant";
        const kindLabel =
          kind === "proposal"
            ? "Proposition"
            : kind === "execute_dry_run"
              ? "Exécution dry-run"
              : kind === "execute_real"
                ? "Exécution réelle"
                : kind === "chat_user"
                  ? "Vous"
                  : kind === "chat_assistant"
                    ? "Assistant"
                    : kind;
        const metaLine = when + " · " + kindLabel + (cap ? " · " + cap : "");
        const policyHtml = dec
          ? "<span class=\"assistant-msg-policy\">policy · " + escapeHtml(dec) + "</span>"
          : "";
        const summaryExtra =
          kind === "proposal" && it.summary && String(it.summary) !== String(text)
            ? "<p class=\"assistant-msg-detail\">" + escapeHtml(String(it.summary).slice(0, 320)) + "</p>"
            : "";
        const textMax =
          kind === "chat_user" || kind === "chat_assistant" ? 4000 : 800;
        if (kind === "chat_user" || kind === "chat_assistant") {
          const rowClass =
            kind === "chat_user"
              ? "assistant-chat-row assistant-chat-row--user"
              : "assistant-chat-row assistant-chat-row--bot";
          const avShort = kind === "chat_user" ? "toi" : "ia";
          parts.push(
            '<div class="' +
              rowClass +
              '">' +
              '<div class="assistant-chat-avatar">' +
              escapeHtml(avShort) +
              "</div>" +
              '<div class="assistant-chat-col">' +
              '<div class="assistant-msg ' +
              msgClass +
              '">' +
              '<div class="assistant-msg-meta">' +
              escapeHtml(metaLine) +
              "</div>" +
              '<p class="assistant-msg-query">' +
              escapeHtml(String(text).slice(0, textMax)) +
              "</p>" +
              summaryExtra +
              policyHtml +
              "</div>" +
              "</div>" +
              "</div>"
          );
          continue;
        }
        parts.push(
          '<div class="assistant-msg ' +
            msgClass +
            '">' +
            '<div class="assistant-msg-meta">' +
            escapeHtml(metaLine) +
            "</div>" +
            '<p class="assistant-msg-query">' +
            escapeHtml(String(text).slice(0, textMax)) +
            "</p>" +
            summaryExtra +
            policyHtml +
            "</div>"
        );
      }
      stream.innerHTML = parts.join("");
      assistantChatScrollToEnd();
      try { assistantRenderSessionState(); } catch (_) {}
    }

    const ASSISTANT_CAP_DOC_MAP = {
      desktop_control: "docs/desktop_hybride.md",
      devops_probe: "docs/fusion_env_lan.md",
      prototype_game: "docs/adr/0003-opengame-forge-prototypes.md",
      npc_dialogue: "docs/adr/0004-assistant-local-vs-persona-mmo.md",
      project_pm: "docs/plan_de_route.md",
      network_inventory: "docs/fusion_env_lan.md",
    };

    const ASSISTANT_DOC_REFS = [
      { label: "Plan Assistant Core", path: "docs/assistant_core_plan.md" },
      { label: "ADR 0004 — local vs persona (legacy)", path: "docs/adr/0004-assistant-local-vs-persona-mmo.md" },
      { label: "ADR 0003 — forge OpenGame", path: "docs/adr/0003-opengame-forge-prototypes.md" },
      { label: "Desktop hybride", path: "docs/desktop_hybride.md" },
      { label: "Fusion protocole agents", path: "docs/fusion_spec_agents.md" },
      { label: "Protocole session_summary", path: "docs/mmmorpg_PROTOCOL.md" },
    ];

    function assistantDocChipHtml(path) {
      const p = String(path || "").trim();
      if (!p) return "";
      return (
        '<button type="button" class="assistant-doc-chip" data-copy="' +
        escapeHtml(p) +
        '" title="Copier le chemin">' +
        escapeHtml(p) +
        "</button>"
      );
    }

    function assistantBindDocChips(root) {
      if (!root) return;
      root.querySelectorAll(".assistant-doc-chip[data-copy]").forEach(function (btn) {
        if (btn.dataset.lbgBound) return;
        btn.dataset.lbgBound = "1";
        btn.addEventListener("click", function () {
          const p = btn.getAttribute("data-copy") || "";
          if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(p).catch(function () {});
          }
        });
      });
    }

    function assistantRenderDocRefs() {
      const ul = document.getElementById("assistant-doc-refs");
      if (!ul) return;
      ul.innerHTML = ASSISTANT_DOC_REFS.map(function (ref) {
        return "<li>" + escapeHtml(ref.label) + assistantDocChipHtml(ref.path) + "</li>";
      }).join("");
      assistantBindDocChips(ul);
    }

    function assistantCapDocLink(name) {
      const p = ASSISTANT_CAP_DOC_MAP[name];
      return p ? assistantDocChipHtml(p) : "";
    }

    function assistantBuildCapsTableHtml(caps) {
      if (!Array.isArray(caps) || !caps.length) return '<p class="assistant-muted">Aucune capability.</p>';
      const sorted = caps.slice().sort(function (a, b) {
        const ma = (a && a.mode) || "";
        const mb = (b && b.mode) || "";
        if (ma !== mb) {
          if (ma === "local_assistant") return -1;
          if (mb === "local_assistant") return 1;
          if (ma === "mixed") return -1;
          if (mb === "mixed") return 1;
        }
        return String((a && a.name) || "").localeCompare(String((b && b.name) || ""));
      });
      let html =
        '<table class="assistant-cap-table"><thead><tr>' +
        "<th>Capability</th><th>Mode</th><th>Risque</th><th>Agent</th><th>Doc</th>" +
        "</tr></thead><tbody>";
      for (let i = 0; i < sorted.length; i++) {
        const c = sorted[i];
        if (!c || typeof c !== "object") continue;
        const name = String(c.name || "");
        const risk = String(c.risk_level || "—");
        const riskCls =
          risk === "high" ? "assistant-cap-risk--high" : risk === "medium" ? "assistant-cap-risk--medium" : "assistant-cap-risk--low";
        html +=
          "<tr><td><code>" +
          escapeHtml(name) +
          "</code></td>" +
          "<td>" +
          escapeHtml(String(c.mode || "—")) +
          "</td>" +
          '<td class="' +
          riskCls +
          '">' +
          escapeHtml(risk) +
          "</td>" +
          "<td><code>" +
          escapeHtml(String(c.routed_to || "—")) +
          "</code></td>" +
          "<td>" +
          (assistantCapDocLink(name) || '<span class="assistant-muted">—</span>') +
          "</td></tr>";
      }
      html += "</tbody></table>";
      return html;
    }

    async function assistantCapsRefresh() {
      const hint = document.getElementById("assistant-caps-hint");
      const body = document.getElementById("assistant-caps-body");
      if (!body) return;
      if (hint) hint.textContent = "Chargement…";
      body.innerHTML = "";
      try {
        const base = getBase();
        const r = await fetch(base + "/v1/pilot/capabilities");
        const j = await r.json();
        if (!j.ok) {
          if (hint) hint.textContent = "Erreur : " + (j.error || "proxy");
          body.innerHTML = '<p class="assistant-lbgia-muted">' + escapeHtml(JSON.stringify(j).slice(0, 280)) + "</p>";
          return;
        }
        const caps = j.capabilities || [];
        const localN = caps.filter(function (c) {
          return c && (c.mode === "local_assistant" || c.mode === "mixed" || c.mode === "system");
        }).length;
        if (hint) {
          hint.textContent =
            caps.length + " entrée(s) — " + localN + " orientées assistant local / système.";
        }
        body.innerHTML = assistantBuildCapsTableHtml(caps);
        assistantBindDocChips(body);
      } catch (e) {
        if (hint) hint.textContent = "Erreur réseau.";
        body.innerHTML = '<p class="assistant-lbgia-muted">' + escapeHtml(String(e)) + "</p>";
      }
    }

    function assistantCollectSessionPayloadForExport() {
      assistantSessionNotesPersist();
      const notesEl = document.getElementById("assistant-session-notes");
      const notes = notesEl && notesEl.value ? String(notesEl.value).trim() : "";
      const hist = assistantHistoryLoad();
      let sessionSummary = null;
      let mmoBridge = null;
      try {
        const ctx = assistantParseJsonTextarea("assistant-context", {});
        if (ctx && typeof ctx === "object") {
          if (ctx.session_summary && typeof ctx.session_summary === "object") sessionSummary = ctx.session_summary;
          if (ctx.mmo_bridge && typeof ctx.mmo_bridge === "object") mmoBridge = ctx.mmo_bridge;
        }
      } catch (_) {}
      if (!sessionSummary) {
        try {
          const raw = localStorage.getItem(LBG_PILOT_MMO_SESSION_SUMMARY_STORAGE);
          if (raw && raw.trim()) sessionSummary = JSON.parse(raw);
        } catch (_) {}
      }
      return {
        notes: notes || undefined,
        history: hist.map(function (x) {
          return {
            ts: x.ts,
            kind: x.kind,
            capability: x.capability,
            policy_decision: x.policy_decision,
            text: (x.text || x.summary || "").slice(0, 500),
          };
        }),
        session_summary: sessionSummary || undefined,
        mmo_bridge: mmoBridge || undefined,
      };
    }

    function assistantRenderSessionState() {
      const el = document.getElementById("assistant-session-state");
      if (!el) return;
      const hist = assistantHistoryLoad();
      let notesLen = 0;
      try {
        const n = localStorage.getItem(STORAGE_ASSISTANT_SESSION_NOTES_KEY);
        notesLen = n ? String(n).trim().length : 0;
      } catch (_) {}
      let mmoStored = false;
      let mmoKeys = [];
      try {
        const raw = localStorage.getItem(LBG_PILOT_MMO_SESSION_SUMMARY_STORAGE);
        if (raw && raw.trim()) {
          mmoStored = true;
          const o = JSON.parse(raw);
          if (o && typeof o === "object" && !Array.isArray(o)) {
            mmoKeys = Object.keys(o).slice(0, 8);
          }
        }
      } catch (_) {}
      let ctxSs = false;
      let bridgeSrc = "";
      try {
        const ctx = assistantParseJsonTextarea("assistant-context", {});
        if (ctx && ctx.session_summary && typeof ctx.session_summary === "object") ctxSs = true;
        if (ctx && ctx.mmo_bridge && typeof ctx.mmo_bridge === "object") {
          bridgeSrc = String(ctx.mmo_bridge.source || "").trim();
        }
      } catch (_) {}
      el.innerHTML =
        "<div><dt>Fil local :</dt><dd>" +
        escapeHtml(String(hist.length)) +
        " entrée(s)</dd></div>" +
        "<div><dt>Notes :</dt><dd>" +
        (notesLen ? escapeHtml(String(notesLen) + " car.") : "—") +
        "</dd></div>" +
        "<div><dt>MMO stocké :</dt><dd>" +
        (mmoStored ? "oui" + (mmoKeys.length ? " (" + escapeHtml(mmoKeys.join(", ")) + ")" : "") : "non") +
        "</dd></div>" +
        "<div><dt>Contexte session_summary :</dt><dd>" +
        (ctxSs ? "présent" : "absent") +
        "</dd></div>" +
        "<div><dt>mmo_bridge :</dt><dd>" +
        (bridgeSrc ? escapeHtml(bridgeSrc) : "—") +
        "</dd></div>";
    }

    async function assistantSessionExportViaServer() {
      const outEl = document.getElementById("assistant-session-summary-out");
      pilotInlineHint("assistant-session-hint", "Validation serveur…", false);
      const payload = assistantCollectSessionPayloadForExport();
      try {
        const base = getBase();
        const out = await postJson(base + "/v1/pilot/assistant/session-summary/export", payload);
        if (out.status !== 200 || !out.json || out.json.ok !== true) {
          pilotInlineHint(
            "assistant-session-hint",
            "API export HTTP " + out.status + (out.json && out.json.error ? " — " + out.json.error : ""),
            true
          );
          return;
        }
        const exportObj = out.json.export || {};
        assistantLastVoluntarySummaryJson = JSON.stringify(exportObj, null, 2);
        if (outEl) outEl.textContent = assistantLastVoluntarySummaryJson;
        pilotInlineHint("assistant-session-hint", "Export validé (sanitisé, non persisté serveur).", false);
      } catch (e) {
        pilotInlineHint("assistant-session-hint", "Erreur : " + e, true);
      }
    }

    async function assistantSessionMmoBridgeApply() {
      const ctxEl = document.getElementById("assistant-context");
      const mmoTa = document.getElementById("assistant-mmo-session-import");
      pilotInlineHint("assistant-session-hint", "Pont session (API)…", false);
      const payload = assistantCollectSessionPayloadForExport();
      try {
        const base = getBase();
        const out = await postJson(base + "/v1/pilot/assistant/session-summary/mmo-bridge", payload);
        if (out.status !== 200 || !out.json || out.json.ok !== true) {
          pilotInlineHint(
            "assistant-session-hint",
            "API mmo-bridge HTTP " + out.status + (out.json && out.json.error ? " — " + out.json.error : ""),
            true
          );
          return;
        }
        const patch = out.json.context_patch || {};
        let ctx = assistantParseJsonTextarea("assistant-context", {});
        if (!ctx || typeof ctx !== "object" || Array.isArray(ctx)) ctx = {};
        if (patch.session_summary && typeof patch.session_summary === "object") {
          ctx.session_summary = patch.session_summary;
        }
        if (patch.mmo_bridge && typeof patch.mmo_bridge === "object") {
          ctx.mmo_bridge = patch.mmo_bridge;
        }
        if (ctxEl) ctxEl.value = JSON.stringify(ctx, null, 2);
        if (patch.session_summary && mmoTa) {
          mmoTa.value = JSON.stringify(patch.session_summary, null, 2);
          try {
            localStorage.setItem(LBG_PILOT_MMO_SESSION_SUMMARY_STORAGE, mmoTa.value || "");
          } catch (_) {}
        }
        const exportObj = out.json.export || {};
        assistantLastVoluntarySummaryJson = JSON.stringify(exportObj, null, 2);
        const outEl = document.getElementById("assistant-session-summary-out");
        if (outEl) outEl.textContent = assistantLastVoluntarySummaryJson;
        pilotInlineHint(
          "assistant-session-hint",
          out.json.hint || "context_patch appliqué au contexte assistant.",
          false
        );
        assistantUiHint("Pont session appliqué — vous pouvez Proposer ou Router.", false);
        try { assistantRenderSessionState(); } catch (_) {}
      } catch (e) {
        pilotInlineHint("assistant-session-hint", "Erreur : " + e, true);
      }
    }

    let __assistantLbgiaPoll = null;
    let __assistantOrchMoodPoll = null;

    function assistantLbgiaPollStop() {
      if (__assistantLbgiaPoll !== null) {
        clearInterval(__assistantLbgiaPoll);
        __assistantLbgiaPoll = null;
      }
      if (__assistantOrchMoodPoll !== null) {
        clearInterval(__assistantOrchMoodPoll);
        __assistantOrchMoodPoll = null;
      }
    }

    function assistantLbgiaFormatRamLine(usedMb, totalMb) {
      const u = usedMb == null ? NaN : Number(usedMb);
      const t = totalMb == null ? NaN : Number(totalMb);
      if (!Number.isFinite(u) || !Number.isFinite(t) || t <= 0) return "";
      return (u / 1024).toFixed(1) + " / " + (t / 1024).toFixed(1) + " Go RAM";
    }

    function assistantLbgiaBarHtml(labelKey, pct, gradientCss) {
      const pRaw = pct == null ? NaN : Number(pct);
      const p =
        typeof pRaw === "number" && Number.isFinite(pRaw) ? Math.max(0, Math.min(100, pRaw)) : null;
      const valTxt = p == null ? "—" : Math.round(p) + "%";
      const inner =
        p == null
          ? ""
          : '<div class="assistant-lbgia-bar-fill" style="width:' +
            String(Math.round(p)) +
            "%;background:" +
            (gradientCss || "linear-gradient(90deg,#2dd4bf,#0d9488)") +
            ';"></div>';
      return (
        '<div class="assistant-lbgia-bar-row">' +
        '<span class="assistant-lbgia-bar-label">' +
        escapeHtml(labelKey) +
        "</span>" +
        '<div class="assistant-lbgia-bar-track">' +
        inner +
        "</div>" +
        '<span class="assistant-lbgia-bar-val">' +
        escapeHtml(valTxt) +
        "</span></div>"
      );
    }

    function orchMoodDerive(proactive, brain) {
      const p = proactive && typeof proactive === "object" ? proactive : {};
      const b = brain && typeof brain === "object" ? brain : {};
      const gauges = b.gauges && typeof b.gauges === "object" ? b.gauges : {};
      const tension = typeof p.tension === "number" ? p.tension : 0;
      const curiosite = typeof p.curiosite === "number" ? p.curiosite : 0;
      const silence = typeof p.silence_seconds_est === "number" ? p.silence_seconds_est : 0;
      const mode = typeof p.mode === "string" ? p.mode : "inconnu";
      const stress = typeof gauges.stress === "number" ? gauges.stress / 100 : 0;
      const fatigue = typeof gauges.fatigue === "number" ? gauges.fatigue / 100 : 0;
      const confidence = typeof gauges.confidence === "number" ? gauges.confidence / 100 : 0.7;

      let tone = "serene";
      let label = "Serein";
      let voice = "Je suis calme et à l’écoute — mode léger, peu de tension.";

      if (p.enabled === false && b.enabled === false) {
        return {
          tone: "off",
          label: "En veille",
          voice: "Couches proactive et brain inactives — je ne « ressens » pas grand-chose côté orchestration.",
          mode: mode,
          tension: tension,
          curiosite: curiosite,
          silence: silence,
          stress: stress,
          fatigue: fatigue,
          confidence: confidence,
        };
      }

      if (mode === "autonome" || tension >= 0.75 || stress >= 0.65) {
        tone = "tense";
        label = "Sous pression";
        voice =
          "Je suis en tension élevée" +
          (mode === "autonome" ? " et en mode autonome" : "") +
          " — je pousse pour débloquer ou relancer sans attendre.";
      } else if (silence >= 600 || (silence >= 120 && tension >= 0.45)) {
        tone = "waiting";
        label = "En attente";
        voice =
          "Le silence dure — " +
          Math.round(silence) +
          "s sans interaction. La curiosité et la tension montent un peu.";
      } else if (curiosite >= 0.6 || (gauges.curiosity != null && gauges.curiosity >= 55)) {
        tone = "curious";
        label = "Curieux";
        voice = "Je suis curieux : j’aimerais clarifier l’objectif ou explorer ce qui manque.";
      } else if (tension >= 0.4 || stress >= 0.4 || mode === "proactif_avance") {
        tone = "vigilant";
        label = "Vigilant";
        voice = "Je reste vigilant — mode " + mode.replace(/_/g, " ") + ", prêt à proposer une suite.";
      } else if (fatigue >= 0.55) {
        tone = "waiting";
        label = "Fatigué";
        voice = "La fatigue brain est notable — privilégier des actions courtes et dry-run.";
      } else {
        tone = "serene";
        label = "Serein";
        voice =
          "Je suis serein (mode " +
          mode.replace(/_/g, " ") +
          "). Tension basse, je peux accompagner sans forcer.";
      }

      return {
        tone: tone,
        label: label,
        voice: voice,
        mode: mode,
        tension: tension,
        curiosite: curiosite,
        silence: silence,
        stress: stress,
        fatigue: fatigue,
        confidence: confidence,
        enabled: p.enabled === true,
        brain_enabled: b.enabled === true,
      };
    }

    function orchMoodBarHtml(label, value01, color) {
      const pct = Math.max(0, Math.min(100, Math.round((value01 || 0) * 100)));
      return (
        '<div class="orch-mood-bar-row"><span>' +
        escapeHtml(label) +
        '</span><div class="orch-mood-bar-track"><div class="orch-mood-bar-fill" style="width:' +
        pct +
        "%;background:" +
        (color || "#2dd4bf") +
        ';"></div></div><span>' +
        pct +
        "%</span></div>"
      );
    }

    function orchMoodFormatSilence(s) {
      if (s == null || isNaN(s)) return "—";
      if (s < 60) return Math.round(s) + "s";
      if (s < 3600) return Math.round(s / 60) + " min";
      return (s / 3600).toFixed(1) + " h";
    }

    function orchMoodApplyChip(mood) {
      const chip = document.getElementById("assistant-orch-mood-chip");
      if (!chip) return;
      const lab = chip.querySelector(".orch-mood-chip-label");
      chip.hidden = false;
      chip.className = "orch-mood-chip orch-mood-chip--" + (mood.tone || "off");
      if (lab) lab.textContent = mood.label || "—";
      chip.title =
        "Mode " +
        String(mood.mode || "?") +
        " · tension " +
        Math.round((mood.tension || 0) * 100) +
        "% · curiosité " +
        Math.round((mood.curiosite || 0) * 100) +
        "%";
    }

    function orchMoodRender(proactive, brain) {
      const hint = document.getElementById("assistant-orch-mood-hint");
      const body = document.getElementById("assistant-orch-mood-body");
      if (!hint || !body) return;
      const mood = orchMoodDerive(proactive, brain);
      orchMoodApplyChip(mood);

      const pOk = proactive && proactive.ok !== false && typeof proactive.tension === "number";
      const bOk = brain && (brain.ok === true || brain.gauges);
      if (!pOk && !bOk) {
        hint.textContent = "Orchestrateur injoignable ou endpoints absents.";
        body.innerHTML =
          '<p class="assistant-muted">Vérifier backend → <code>/v1/pilot/orchestrator/proactive/status</code> et brain/status.</p>';
        return;
      }

      hint.textContent =
        (mood.enabled ? "Proactive active" : "Proactive off") +
        " · brain " +
        (mood.brain_enabled ? "actif" : "inactif") +
        " · silence " +
        orchMoodFormatSilence(mood.silence);

      let html = '<p class="orch-mood-voice">« ' + escapeHtml(mood.voice) + ' »</p>';
      html +=
        '<div class="orch-mood-meta">' +
        "<span>Mode <code>" +
        escapeHtml(String(mood.mode || "—")) +
        "</code></span>" +
        "<span>Humeur <strong>" +
        escapeHtml(mood.label) +
        "</strong></span>" +
        "</div>";
      html += '<div class="orch-mood-bars">';
      html += orchMoodBarHtml("Tension", mood.tension, "linear-gradient(90deg,#fbbf24,#ef4444)");
      html += orchMoodBarHtml("Curiosité", mood.curiosite, "linear-gradient(90deg,#22d3ee,#3b82f6)");
      html += orchMoodBarHtml("Stress", mood.stress, "linear-gradient(90deg,#fb7185,#be123c)");
      html += orchMoodBarHtml("Fatigue", mood.fatigue, "linear-gradient(90deg,#a78bfa,#6366f1)");
      html += "</div>";

      const last = proactive && proactive.last_action && typeof proactive.last_action === "object"
        ? proactive.last_action
        : null;
      if (last && typeof last.message === "string" && last.message.trim()) {
        html +=
          '<div class="orch-mood-action"><strong>Dernière impulsion</strong> (' +
          escapeHtml(String(last.kind || "action")) +
          ") — " +
          escapeHtml(last.message.trim().slice(0, 220)) +
          "</div>";
      }
      const infra = proactive && proactive.infra_signals && typeof proactive.infra_signals === "object"
        ? proactive.infra_signals
        : null;
      if (infra) {
        const flags = [];
        if (infra.ad_agent_down === true) flags.push("agent AD down");
        if (infra.orchestrator_reachable === false) flags.push("orch injoignable");
        if (infra.mmo_sidecar_reachable === false) flags.push("sidecar MMO off");
        if (flags.length) {
          html +=
            '<p class="assistant-muted" style="margin-top:0.55rem">Signaux infra : ' +
            escapeHtml(flags.join(" · ")) +
            "</p>";
        }
      }
      body.innerHTML = html;
      try {
        if (window.OrchestratorAvatar && OrchestratorAvatar.ready) {
          OrchestratorAvatar.setMood(mood);
        }
      } catch (_) {}
      try {
        if (window.FaceRig && FaceRig.ready) {
          FaceRig.setMood(mood);
        }
      } catch (_) {}
    }

    function faceRigInit() {
      if (!window.FaceRig) {
        if (!faceRigInit._retries) faceRigInit._retries = 0;
        if (faceRigInit._retries < 40) {
          faceRigInit._retries += 1;
          window.setTimeout(faceRigInit, 150);
        }
        return;
      }
      if (FaceRig.ready) return;
      const host = document.getElementById("face-rig-host");
      if (!host) return;
      FaceRig.init("face-rig-host", { characterId: "lyra_assistant" });
    }

    function orchestratorAvatarInit() {
      if (!window.THREE || !window.THREE.GLTFLoader || !window.OrchestratorAvatar) {
        if (!orchestratorAvatarInit._retries) orchestratorAvatarInit._retries = 0;
        if (orchestratorAvatarInit._retries < 40) {
          orchestratorAvatarInit._retries += 1;
          window.setTimeout(orchestratorAvatarInit, 150);
        }
        return;
      }
      if (OrchestratorAvatar.ready) return;
      const host = document.getElementById("orch-avatar-canvas");
      if (!host) return;
      // Même origine que la page (110:8080/ ou 140:8000/pilot/) — pas via api-base
      let modelUrl;
      try {
        modelUrl = new URL("orchestrator_avatar/models/base_female.glb", window.location.href).href;
        if (!String(window.location.pathname || "").endsWith("/") &&
            String(window.location.pathname || "").indexOf(".") < 0) {
          const u = new URL(window.location.href);
          modelUrl = u.origin + (u.pathname.replace(/\/?$/, "/")) + "orchestrator_avatar/models/base_female.glb";
        }
      } catch (_) {
        modelUrl = "orchestrator_avatar/models/base_female.glb";
      }
      OrchestratorAvatar.init("orch-avatar-canvas", { modelUrl: modelUrl });
    }

    async function assistantOrchMoodRefresh() {
      const base = getBase();
      let proactive = null;
      let brain = null;
      try {
        const [rp, rb] = await Promise.all([
          fetch(base + "/v1/pilot/orchestrator/proactive/status"),
          fetch(base + "/v1/pilot/orchestrator/brain/status"),
        ]);
        try {
          proactive = await rp.json();
        } catch (_) {
          proactive = { ok: false };
        }
        try {
          brain = await rb.json();
        } catch (_) {
          brain = { ok: false };
        }
      } catch (e) {
        orchMoodRender({ ok: false, error: String(e) }, { ok: false });
        return;
      }
      orchMoodRender(proactive, brain);
    }

    async function assistantLbgiaRefresh() {
      const hint = document.getElementById("assistant-lbgia-hint");
      const body = document.getElementById("assistant-lbgia-body");
      if (!hint || !body) return;
      const base = getBase();
      try {
        const r = await fetch(base + "/v1/pilot/lbg-ia/status");
        let j = null;
        try {
          j = await r.json();
        } catch (_) {
          j = null;
        }
        if (!j || typeof j !== "object") {
          hint.textContent = r.status >= 400 ? "Backend injoignable ou mauvaise URL." : "Réponse invalide.";
          body.innerHTML =
            '<p class="assistant-lbgia-muted">' +
            "Contrôlez le champ <strong>Backend</strong> en haut (ex. LAN : <code>http://192.168.0.140:8000</code>). " +
            "Depuis un pilot sur <strong>110:8080</strong>, sans proxy <code>/v1</code>, l’API n’est pas sur l’origine de la page. " +
            "HTTP <strong>" +
            escapeHtml(String(r.status)) +
            "</strong>.</p>";
          return;
        }
        if (j.disabled) {
          hint.textContent =
            "Proxy désactivé : LBG_PILOT_LBGIA_BACKEND_URL ou LBG_IA_BACKEND_URL sur le backend Cortex.";
          body.innerHTML =
            '<p class="assistant-lbgia-muted">Même VM (ex. 110) : URL interne FastAPI projet LBG_IA, sans CORS depuis le navigateur.</p>';
          return;
        }
        if (!j.ok) {
          const ue = j.upstream_errors && typeof j.upstream_errors === "object" ? j.upstream_errors : {};
          const bits = [];
          if (j.detail) bits.push(String(j.detail));
          if (ue.metrics_http != null && ue.metrics_http !== 200) bits.push("metrics HTTP " + String(ue.metrics_http));
          if (ue.agents_http != null && ue.agents_http !== 200) bits.push("agents HTTP " + String(ue.agents_http));
          if (ue.metrics_detail) bits.push(String(ue.metrics_detail).slice(0, 140));
          if (ue.agents_detail) bits.push(String(ue.agents_detail).slice(0, 140));
          hint.textContent = "LBG IA amont indisponible.";
          body.innerHTML =
            '<p class="assistant-lbgia-muted">' + escapeHtml(bits.join(" · ") || "Erreur proxy") + "</p>";
          return;
        }
        const metricsRoot = j.metrics && typeof j.metrics === "object" ? j.metrics : {};
        const sysObj =
          metricsRoot.system && typeof metricsRoot.system === "object"
            ? metricsRoot.system
            : metricsRoot.System && typeof metricsRoot.System === "object"
              ? metricsRoot.System
              : {};
        const cpu = sysObj.cpu_usage_pct != null ? sysObj.cpu_usage_pct : metricsRoot.cpu_usage_pct;
        const memPct =
          sysObj.memory_usage_pct != null ? sysObj.memory_usage_pct : metricsRoot.memory_usage_pct;
        const memUsed =
          sysObj.memory_used_mb != null ? sysObj.memory_used_mb : metricsRoot.memory_used_mb;
        const memTot =
          sysObj.memory_total_mb != null ? sysObj.memory_total_mb : metricsRoot.memory_total_mb;
        const ramLine = assistantLbgiaFormatRamLine(memUsed, memTot);
        const baseShort =
          typeof j.upstream_base === "string" && j.upstream_base.trim()
            ? j.upstream_base.trim()
            : "";
        hint.textContent =
          (baseShort ? "Connecté · " + baseShort : "Connecté") + (ramLine ? " · " + ramLine : "");
        let html = '<div class="assistant-lbgia-bars">';
        html += assistantLbgiaBarHtml("cpu", cpu, "linear-gradient(90deg,#60a5fa,#2563eb)");
        html += assistantLbgiaBarHtml("ram", memPct, "linear-gradient(90deg,#34d399,#059669)");
        html += "</div>";
        const mon = j.agents_monitor && typeof j.agents_monitor === "object" ? j.agents_monitor : {};
        const agents = Array.isArray(mon.agents)
          ? mon.agents
          : mon.data && typeof mon.data === "object" && !Array.isArray(mon.data) && Array.isArray(mon.data.agents)
            ? mon.data.agents
            : [];
        if (agents.length) {
          html += '<div class="assistant-lbgia-agents"><strong>Agents</strong>';
          let nShown = 0;
          for (let i = 0; i < agents.length && nShown < 8; i++) {
            const ag = agents[i];
            if (!ag || typeof ag !== "object") continue;
            const name =
              (typeof ag.label === "string" && ag.label.trim()) ||
              (typeof ag.name === "string" && ag.name.trim()) ||
              (typeof ag.id === "string" && ag.id.trim()) ||
              "agent";
            const stRaw =
              ag.status !== undefined && ag.status !== null
                ? ag.status
                : ag.state !== undefined && ag.state !== null
                  ? ag.state
                  : ag.health !== undefined && ag.health !== null
                    ? ag.health
                    : "—";
            const st = String(stRaw).slice(0, 48);
            html +=
              '<div class="assistant-lbgia-agent-line">' +
              '<span class="assistant-lbgia-agent-id" title="' +
              escapeHtml(name) +
              '">' +
              escapeHtml(name) +
              "</span>" +
              "<span>" +
              escapeHtml(st) +
              "</span></div>";
            nShown++;
          }
          html += "</div>";
        } else {
          html +=
            '<p class="assistant-lbgia-muted">' +
            "Réponse agents reçue (aucune entrée listée)." +
            "</p>";
        }
        body.innerHTML = html;
      } catch (e) {
        hint.textContent = "Erreur réseau.";
        body.innerHTML = '<p class="assistant-lbgia-muted">' + escapeHtml(String(e)) + "</p>";
      }
    }

    let assistantLastVoluntarySummaryJson = "";

    function assistantSessionNotesLoad() {
      try {
        const ta = document.getElementById("assistant-session-notes");
        if (!ta) return;
        const v = localStorage.getItem(STORAGE_ASSISTANT_SESSION_NOTES_KEY);
        if (v) ta.value = v;
      } catch (_) {}
    }

    function assistantSessionNotesPersist() {
      try {
        const ta = document.getElementById("assistant-session-notes");
        const raw = ta && ta.value ? String(ta.value) : "";
        localStorage.setItem(STORAGE_ASSISTANT_SESSION_NOTES_KEY, raw);
      } catch (_) {}
    }

    function assistantSessionBuildSummary() {
      assistantSessionNotesPersist();
      const notesEl = document.getElementById("assistant-session-notes");
      const outEl = document.getElementById("assistant-session-summary-out");
      const hist = assistantHistoryLoad();
      const notes = notesEl && notesEl.value ? String(notesEl.value).trim() : "";
      const payload = {
        kind: "assistant_voluntary_session_summary",
        generated_at: new Date().toISOString(),
        voluntary: true,
        pilot_view: "#/assistant",
        notes: notes || undefined,
        history: hist.map((x) => ({
          ts: x.ts,
          kind: x.kind,
          capability: x.capability,
          policy_decision: x.policy_decision,
          text: (x.text || x.summary || "").slice(0, 500),
        })),
      };
      assistantLastVoluntarySummaryJson = JSON.stringify(payload, null, 2);
      if (outEl) outEl.textContent = assistantLastVoluntarySummaryJson;
      pilotInlineHint("assistant-session-hint", "Résumé généré (local uniquement).", false);
      try { assistantRenderSessionState(); } catch (_) {}
    }

    function assistantSessionCopySummary() {
      const outEl = document.getElementById("assistant-session-summary-out");
      const cur = (outEl && outEl.textContent ? String(outEl.textContent) : "").trim();
      if (!cur || cur === "—") {
        assistantSessionBuildSummary();
      }
      const text = assistantLastVoluntarySummaryJson ||
        (outEl && outEl.textContent ? String(outEl.textContent) : "") ||
        "";
      if (!String(text).trim() || String(text).trim() === "—") {
        pilotInlineHint("assistant-session-hint", "Générez d'abord un résumé.", true);
        return;
      }
      assistantLastVoluntarySummaryJson = String(text).trim();
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(assistantLastVoluntarySummaryJson).then(
          function () { pilotInlineHint("assistant-session-hint", "Copié dans le presse-papiers.", false); },
          function () { pilotInlineHint("assistant-session-hint", "Copie impossible (navigateur).", true); }
        );
      } else {
        pilotInlineHint("assistant-session-hint", "Clipboard API indisponible.", true);
      }
    }

    function assistantMmoMergeIntoContext() {
      const ta = document.getElementById("assistant-mmo-session-import");
      const ctxEl = document.getElementById("assistant-context");
      let o = null;
      try {
        const raw = ta && ta.value ? String(ta.value).trim() : "";
        if (!raw) {
          pilotInlineHint("assistant-mmo-hint", "Collez un JSON session_summary.", true);
          return;
        }
        o = JSON.parse(raw);
        if (!o || typeof o !== "object" || Array.isArray(o)) throw new Error("attendu: objet JSON");
      } catch (e) {
        pilotInlineHint("assistant-mmo-hint", "JSON invalide : " + e, true);
        return;
      }
      let ctx = assistantParseJsonTextarea("assistant-context", {});
      if (!ctx || typeof ctx !== "object") ctx = {};
      ctx.session_summary = o;
      ctx.mmo_bridge = {
        source: "mmo_session_summary",
        imported_at: new Date().toISOString(),
        via: "pilot_assistant",
      };
      if (ctxEl) ctxEl.value = JSON.stringify(ctx, null, 2);
      try {
        localStorage.setItem(LBG_PILOT_MMO_SESSION_SUMMARY_STORAGE, ta ? ta.value || "" : "");
      } catch (_) {}
      pilotInlineHint("assistant-mmo-hint", "Context mis à jour + trace mmo_bridge (import volontaire).", false);
      assistantUiHint("session_summary fusionné — vous pouvez Proposer (ex. forge prototype)", false);
      try { assistantRenderSessionState(); } catch (_) {}
    }

    function assistantMmoImportSilentLoad() {
      try {
        const ta = document.getElementById("assistant-mmo-session-import");
        const v = localStorage.getItem(LBG_PILOT_MMO_SESSION_SUMMARY_STORAGE);
        if (ta && v && !String(ta.value || "").trim()) ta.value = v;
      } catch (_) {}
    }

    function assistantMmoLoadFromSharedStorage() {
      const ta = document.getElementById("assistant-mmo-session-import");
      try {
        const v = localStorage.getItem(LBG_PILOT_MMO_SESSION_SUMMARY_STORAGE);
        if (ta && v) ta.value = v;
        pilotInlineHint("assistant-mmo-hint", v ? "Chargé depuis le stockage partagé." : "Stockage vide.", !v);
      } catch (e) {
        pilotInlineHint("assistant-mmo-hint", "Erreur : " + e, true);
      }
    }

    function assistantMmoSaveToSharedStorage() {
      const ta = document.getElementById("assistant-mmo-session-import");
      try {
        if (ta) localStorage.setItem(LBG_PILOT_MMO_SESSION_SUMMARY_STORAGE, ta.value || "");
        pilotInlineHint("assistant-mmo-hint", "Écrit vers le stockage Desktop partagé.", false);
      } catch (e) {
        pilotInlineHint("assistant-mmo-hint", "Erreur : " + e, true);
      }
    }

    function assistantRenderSuggestions(items) {
      const el = document.getElementById("assistant-suggestions");
      if (!el) return;
      const list = Array.isArray(items) ? items.filter(Boolean) : [];
      if (!list.length) {
        el.innerHTML = "<span class=\"assistant-muted\">—</span>";
        return;
      }
      el.innerHTML = "<ul style=\"margin:0;padding-left:1.1rem\">" + list
        .map((x) => "<li>" + escapeHtml(String(x)) + "</li>")
        .join("") + "</ul>";
    }

    function assistantSuggestionsForProposal(proposal) {
      if (!proposal || typeof proposal !== "object") return ["Demander une précision avant toute action."];
      const cap = proposal.capability || "";
      const action = proposal.action && typeof proposal.action === "object" ? proposal.action : {};
      const kind = action.kind || "";
      const out = ["Relire le JSON proposé avant exécution."];
      if (cap === "desktop_control") out.push("Tester en dry-run avant toute action réelle sur le poste.");
      if (kind === "mail_imap_preview") out.push("Garder la lecture mail en aperçu borné ; ne pas exposer de contenu privé au MMO.");
      if (kind === "notepad_append") out.push("Vérifier que le chemin Notepad est dans l'allowlist du worker.");
      if (cap === "devops_probe") out.push("Conserver le selfcheck en lecture seule tant qu'aucun correctif humain n'est décidé.");
      if (cap === "prototype_game") {
        out.push("La forge écrit en sandbox isolée ; aucun merge vers Prime / Godot sans revue humaine (ADR 0003).");
        if (proposal.source === "mmo_session_bridge" || (proposal.mmo_trace && typeof proposal.mmo_trace === "object")) {
          out.push("Trace MMO : idée issue d'un session_summary importé — ne pas renvoyer de données poste vers le persona MMO.");
        }
      }
      return out;
    }

    function assistantSuggestionsForResult(result) {
      const res = result && result.result;
      const out = res && res.output ? res.output : {};
      const policy = out && out.policy ? out.policy : null;
      const decision = policy && policy.decision ? String(policy.decision) : "";
      const suggestions = [];
      if (decision === "dry_run") suggestions.push("Dry-run OK : relire le résultat avant de fournir un approval pour une exécution réelle.");
      if (decision === "approval_required") suggestions.push("Action bloquée : ajouter un approval ou repasser par un dry-run.");
      if (decision === "forbidden") suggestions.push("Action refusée : reformuler avec une capability déclarée ou enrichir le registry/policy.");
      if (decision === "safe_read") suggestions.push("Lecture sûre effectuée : transformer les constats en plan, pas en correction automatique.");
      if (!suggestions.length) suggestions.push("Archiver le résultat utile dans l'historique court ou lancer un nouveau dry-run.");
      return suggestions;
    }

    function assistantParseJsonTextarea(id, fallback) {
      const el = document.getElementById(id);
      const raw = (el && el.value ? String(el.value) : "").trim();
      if (!raw) return fallback;
      const parsed = JSON.parse(raw);
      if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
        throw new Error(id + " doit contenir un objet JSON");
      }
      return parsed;
    }

    async function assistantConverse() {
      const base = getBase();
      const actorEl = document.getElementById("assistant-actor");
      const textEl = document.getElementById("assistant-text");
      const ctxEl = document.getElementById("assistant-context");
      const rawEl = document.getElementById("assistant-raw");
      const prettyEl = document.getElementById("assistant-pretty");
      assistantClearDialogueRouteBadge();
      assistantUiHint("…", false);
      const text = textEl && textEl.value ? String(textEl.value).trim() : "";
      if (!text) {
        assistantUiHint("Message vide", true);
        return;
      }
      const actorId = (actorEl && actorEl.value ? String(actorEl.value).trim() : "") || "ui:assistant";
      let ctx;
      try {
        ctx = assistantParseJsonTextarea("assistant-context", {});
      } catch (e) {
        assistantUiHint("Contexte JSON invalide : " + e, true);
        return;
      }
      var payloadCtx;
      try {
        payloadCtx = JSON.parse(JSON.stringify(ctx));
      } catch (_) {
        assistantUiHint("Contexte impossible à cloner", true);
        return;
      }
      if (!Array.isArray(payloadCtx.history)) payloadCtx.history = [];
      payloadCtx.lyra_engagement = "local_assistant";
      delete payloadCtx.world_npc_id;
      var wantDlgDesktop = false;
      try {
        var _ddc = document.getElementById("assistant-pref-dialogue-desktop-plan");
        wantDlgDesktop = !!(_ddc && _ddc.checked);
      } catch (_) {}
      if (!wantDlgDesktop) {
        delete payloadCtx._desktop_plan;
        delete payloadCtx._require_desktop_json;
      } else {
        payloadCtx._desktop_plan = true;
      }
      if (typeof payloadCtx.dialogue_target !== "string" || !String(payloadCtx.dialogue_target).trim()) {
        payloadCtx.dialogue_target = "fast";
      }
      payloadCtx.lyra = assistantBuildLyraContextForDialogue();
      const payload = { actor_id: actorId, text: text, context: payloadCtx };
      const prefs = assistantReadPrefsFromUi();

      if (prefs.route_first !== false && payloadCtx._skip_route_first !== true) {
        var routeOut;
        try {
          routeOut = await postJson(base + "/v1/pilot/route", {
            actor_id: actorId,
            text: text,
            context: payloadCtx,
          });
        } catch (e) {
          assistantUiHint("Routeur : " + e, true);
          routeOut = null;
        }
        if (routeOut) {
          const routeReply = extractPilotRouteReply(routeOut.json);
          const useRoute =
            routeOut.status === 200 &&
            routeReply &&
            !assistantShouldLlmFallbackAfterRoute(routeOut.json, routeReply, prefs);
          if (useRoute) {
            assistantRenderRouteJson(routeOut, rawEl, prettyEl);
            assistantCommitChatTurn(ctx, ctxEl, text, routeReply);
            assistantSetRouteBadge(routeOut.json);
            assistantUiHint("Routé via orchestrateur (compétence LBG-IA)", false);
            assistantAvatarSay(routeReply);
            return;
          }
        }
      }

      var out;
      try {
        out = await postJson(base + "/v1/pilot/agent-dialogue/invoke", payload);
      } catch (e) {
        assistantUiHint("Réseau : " + e, true);
        assistantClearDialogueRouteBadge();
        return;
      }
      if (rawEl) rawEl.textContent = out.json ? JSON.stringify(out.json, null, 2) : ("HTTP " + out.status + "\n" + (out.text || ""));
      if (prettyEl) {
        try { prettyEl.innerHTML = out.json ? renderPretty(out.json) : ""; } catch (_) { prettyEl.innerHTML = ""; }
      }
      if (out.status !== 200) {
        assistantUiHint("Dialogue impossible (HTTP " + out.status + ")", true);
        assistantClearDialogueRouteBadge();
        return;
      }
      try {
        var _md = out.json && out.json.meta && typeof out.json.meta === "object" ? out.json.meta : null;
        var _dap = _md && _md.desktop_action_proposal && typeof _md.desktop_action_proposal === "object";
        if (_dap) {
          assistantUiHint(
            "Proposition desktop reçue : voir meta.desktop_action_proposal — enchaîner avec #/desktop ou Proposer une action après relecture.",
            false
          );
        }
      } catch (_) {}
      var reply = "";
      if (out.json) {
        if (typeof out.json.reply === "string") reply = out.json.reply;
        else if (Array.isArray(out.json.lines)) reply = out.json.lines.join("\n");
      }
      const replyNorm = String(reply || "").trim() || "(réponse vide)";
      ctx.lyra_engagement = "local_assistant";
      delete ctx.world_npc_id;
      delete ctx._desktop_plan;
      delete ctx._require_desktop_json;
      assistantCommitChatTurn(ctx, ctxEl, text, replyNorm);
      try {
        assistantNudgeLyraFromPolicy("safe_read", "proposal");
      } catch (_) {}
      assistantSetDialogueRouteBadge(out);
      assistantUiHint("LLM dialogue (repli ou conversation libre)", false);
      assistantAvatarSay(replyNorm);
    }

    async function assistantPropose() {
      const actorEl = document.getElementById("assistant-actor");
      const textEl = document.getElementById("assistant-text");
      const actionEl = document.getElementById("assistant-action");
      const rawEl = document.getElementById("assistant-raw");
      const prettyEl = document.getElementById("assistant-pretty");
      assistantClearDialogueRouteBadge();
      assistantUiHint("…", false);
      try {
        const actorId = (actorEl && actorEl.value ? actorEl.value.trim() : "") || "ui:assistant";
        const text = (textEl && textEl.value ? textEl.value.trim() : "");
        if (!text) {
          assistantUiHint("Demande vide", true);
          return;
        }
        const ctx = assistantParseJsonTextarea("assistant-context", {});
        const prefs = assistantReadPrefsFromUi();
        if (prefs.notepad_path && !ctx.desktop_default_notepad_path) ctx.desktop_default_notepad_path = prefs.notepad_path;
        const out = await postJson(getBase() + "/v1/pilot/action-proposal", { actor_id: actorId, text, context: ctx });
        if (rawEl) rawEl.textContent = out.json ? JSON.stringify(out.json, null, 2) : ("HTTP " + out.status + "\n" + (out.text || ""));
        if (prettyEl) {
          try { prettyEl.innerHTML = out.json ? renderPretty(out.json) : ""; } catch (_) { prettyEl.innerHTML = ""; }
        }
        if (out.status !== 200 || !out.json || out.json.ok === false) {
          assistantUiHint("Proposition impossible (HTTP/proxy)", true);
          return;
        }
        const proposal = out.json.proposal;
        if (proposal && typeof proposal === "object") {
          if (actionEl) actionEl.value = JSON.stringify(proposal, null, 2);
          assistantHistoryAdd({
            kind: "proposal",
            text,
            capability: proposal.capability || "",
            summary: proposal.summary || "",
          });
          assistantRenderSuggestions(assistantSuggestionsForProposal(proposal));
          const pipePrefs = assistantReadPrefsFromUi();
          if (pipePrefs.auto_simulate_after_propose !== false) {
            try {
              const sim = await assistantRunRouteFromProposal(proposal, "dry_run");
              const simOk = assistantRouteLooksSuccessful(sim.json);
              if (pipePrefs.auto_real_after_sim_ok && pipePrefs.exec_real && simOk) {
                await assistantRunRouteFromProposal(proposal, "real");
              } else if (!simOk) {
                assistantRenderSuggestions([
                  "Contrôler réseau, worker desktop / DevOps et le détail JSON (policy, erreur agent).",
                  "Pour le poste : renseigner le jeton d'approbation si l'exécution réelle est refusée, ou rester en dry-run.",
                  "Reformuler la demande de façon plus explicite si aucune action sûre n'est reconnue.",
                ]);
              }
            } catch (ePipe) {
              assistantUiHint("Enchaînement après proposition : " + ePipe, true);
            }
          } else {
            try {
              assistantNudgeLyraFromPolicy("", "proposal");
            } catch (_) {}
            assistantUiHint("Proposition prête — relire/éditer puis appliquer ou exécuter", false);
          }
        } else {
          assistantRenderSuggestions(["Demander une précision ou rester en conversation sans action."]);
          assistantUiHint(out.json.reason || "Aucune proposition", false);
        }
      } catch (e) {
        assistantUiHint("Erreur: " + e, true);
      }
    }

    function assistantReadProposal() {
      const obj = assistantParseJsonTextarea("assistant-action", {});
      if (obj.proposal && typeof obj.proposal === "object") return obj.proposal;
      return obj;
    }

    function assistantContextFromProposal(proposal, mode) {
      let ctx = assistantParseJsonTextarea("assistant-context", {});
      const patch = proposal && proposal.context_patch && typeof proposal.context_patch === "object" ? proposal.context_patch : {};
      ctx = { ...ctx, ...patch };
      const key = proposal && typeof proposal.action_context_key === "string" ? proposal.action_context_key : "";
      const action = proposal && proposal.action && typeof proposal.action === "object" ? proposal.action : null;
      if (key && action) ctx[key] = action;

      const approval = (document.getElementById("assistant-approval") || {}).value || "";
      const capability = proposal && typeof proposal.capability === "string" ? proposal.capability : "";
      const prefs = assistantReadPrefsFromUi();
      if (capability === "desktop_control" && prefs.dry_run_default !== false && mode !== "real") {
        ctx.desktop_dry_run = true;
      }
      if (mode === "dry_run") {
        if (capability === "desktop_control") ctx.desktop_dry_run = true;
        if (capability === "devops_probe") ctx.devops_dry_run = true;
        if (capability === "prototype_game") ctx.opengame_dry_run = true;
      } else if (mode === "real") {
        if (capability === "desktop_control") delete ctx.desktop_dry_run;
        if (capability === "devops_probe") delete ctx.devops_dry_run;
        if (capability === "prototype_game") ctx.opengame_dry_run = false;
        const token = String(approval || "").trim();
        if (token) {
          if (capability === "desktop_control") ctx.desktop_approval = token;
          else if (capability === "devops_probe") ctx.devops_approval = token;
          else if (capability === "prototype_game") ctx.opengame_approval = token;
        }
      }
      return ctx;
    }

    function assistantRouteLooksSuccessful(routePayload) {
      if (!routePayload || routePayload.ok === false) return false;
      const out = routePayload.result && routePayload.result.output;
      if (!out || out.ok === false) return false;
      const pol = out.policy;
      if (pol && pol.allowed === false) return false;
      return true;
    }

    async function assistantRunRouteFromProposal(proposal, mode) {
      const rawEl = document.getElementById("assistant-raw");
      const prettyEl = document.getElementById("assistant-pretty");
      assistantClearDialogueRouteBadge();
      const actorEl = document.getElementById("assistant-actor");
      const textEl = document.getElementById("assistant-text");
      const actorId = (actorEl && actorEl.value ? actorEl.value.trim() : "") || "ui:assistant";
      const text =
        (textEl && textEl.value ? textEl.value.trim() : "") ||
        String((proposal && proposal.summary) || "assistant action");
      const ctx = assistantContextFromProposal(proposal, mode);
      const payload = { actor_id: actorId, text: text, context: ctx };
      const out = await postJson(getBase() + "/v1/pilot/route", payload);
      if (rawEl) {
        out.json
          ? (rawEl.textContent = JSON.stringify(out.json, null, 2))
          : (rawEl.textContent = "HTTP " + out.status + "\n" + (out.text || ""));
      }
      if (prettyEl) {
        try {
          prettyEl.innerHTML = out.json ? renderPretty(out.json) : "";
        } catch (_) {
          prettyEl.innerHTML = "";
        }
      }
      const policy = out.json && out.json.result && out.json.result.output ? out.json.result.output.policy : null;
      const dec = policy && policy.decision ? String(policy.decision) : "";
      if (out.json) {
        assistantHistoryAdd({
          kind: mode === "real" ? "execute_real" : "execute_dry_run",
          text: text,
          capability: proposal && proposal.capability ? proposal.capability : "",
          policy_decision: dec,
          summary: proposal && proposal.summary ? proposal.summary : "",
        });
        assistantRenderSuggestions(assistantSuggestionsForResult(out.json));
      }
      try {
        assistantNudgeLyraFromPolicy(dec, "execute");
      } catch (_) {}
      const okUi = out.status === 200 && assistantRouteLooksSuccessful(out.json);
      assistantUiHint(
        out.status !== 200
          ? "HTTP " + out.status
          : okUi
            ? "OK" + (dec ? " · policy=" + dec : "")
            : "Échec ou refus (policy / agent) — voir détail ci-dessous",
        out.status !== 200 || !okUi
      );
      return { status: out.status, json: out.json };
    }

    function assistantApplyProposalToContext() {
      try {
        const proposal = assistantReadProposal();
        const ctx = assistantContextFromProposal(proposal, "keep");
        const ctxEl = document.getElementById("assistant-context");
        if (ctxEl) ctxEl.value = JSON.stringify(ctx, null, 2);
        assistantUiHint("Proposition appliquée au context JSON", false);
      } catch (e) {
        assistantUiHint("Erreur: " + e, true);
      }
    }

    async function assistantExecute(mode) {
      assistantUiHint("…", false);
      try {
        const proposal = assistantReadProposal();
        if (!proposal || typeof proposal !== "object" || !proposal.action) {
          assistantUiHint("Aucune ActionProposal valide à exécuter", true);
          return;
        }
        await assistantRunRouteFromProposal(proposal, mode);
      } catch (e) {
        assistantUiHint("Erreur: " + e, true);
      }
    }

    function assistantPreset(kind) {
      const textEl = document.getElementById("assistant-text");
      const ctxEl = document.getElementById("assistant-context");
      if (!textEl || !ctxEl) return;
      const prefs = assistantReadPrefsFromUi();
      if (kind === "notepad") {
        textEl.value = "ouvre notepad et écris ceci est un test de l'Assistant Core";
        ctxEl.value = JSON.stringify({ history: [], desktop_default_notepad_path: prefs.notepad_path }, null, 2);
      } else if (kind === "web") {
        textEl.value = "cherche sur internet le site de Cursor AI";
        ctxEl.value = JSON.stringify({ history: [] }, null, 2);
      } else if (kind === "mail") {
        textEl.value = "regarde si j'ai un mail de Intel";
        ctxEl.value = JSON.stringify({ history: [] }, null, 2);
      } else if (kind === "selfcheck") {
        textEl.value = "vérifie l'état du backend et de l'orchestrateur";
        ctxEl.value = JSON.stringify({ history: [] }, null, 2);
      } else if (kind === "mmo_dev") {
        textEl.value =
          "forge un prototype OpenGame pour Prime / Godot à partir du session_summary — dry-run uniquement, pas de merge vers le tronc";
        let baseCtx = assistantParseJsonTextarea("assistant-context", {});
        if (!baseCtx || typeof baseCtx !== "object") baseCtx = {};
        if (!baseCtx.session_summary || typeof baseCtx.session_summary !== "object") {
          pilotInlineHint(
            "assistant-hint",
            "Importez un session_summary (Résumé de session) puis « Fusionner dans contexte » avant ce preset.",
            true
          );
        }
        ctxEl.value = JSON.stringify(baseCtx, null, 2);
      }
      assistantUiHint("Preset chargé — cliquer Proposer", false);
    }

    async function worldContentRefresh() {
      const base = getBase();
      const out = document.getElementById("world-content-out");
      const hint = document.getElementById("world-content-hint");
      if (hint) hint.textContent = "chargement…";
      try {
        const url = base + "/v1/pilot/agent-dialogue/world-content";
        const r = await fetch(url);
        const t = await r.text();
        let j = null;
        try { j = t ? JSON.parse(t) : null; } catch (_) {}
        if (out) out.textContent = j ? JSON.stringify(j, null, 2) : (t || "—");
        if (hint) hint.textContent = r.status === 200 ? "ok" : ("HTTP " + r.status);
      } catch (e) {
        if (out) out.textContent = String(e);
        if (hint) hint.textContent = "erreur";
      }
    }

    async function npcRegistryRefresh() {
      const base = getBase();
      const out = document.getElementById("npc-reg-out");
      const hint = document.getElementById("npc-reg-hint");
      const idEl = document.getElementById("npc-reg-id");
      const applyBtn = document.getElementById("btn-npc-reg-apply");
      const npcId = idEl ? String(idEl.value || "").trim() : "";
      if (hint) hint.textContent = "chargement…";
      try { window.__npc_reg_last_entry = null; } catch (_) {}
      if (applyBtn) applyBtn.disabled = true;
      try {
        const url = base + "/v1/pilot/agent-dialogue/npc-registry" + (npcId ? ("?npc_id=" + encodeURIComponent(npcId)) : "");
        const r = await fetch(url);
        const t = await r.text();
        let j = null;
        try { j = t ? JSON.parse(t) : null; } catch (_) {}
        if (out) out.textContent = j ? JSON.stringify(j, null, 2) : (t || "—");
        if (hint) hint.textContent = r.status === 200 ? "ok" : ("HTTP " + r.status);
        // Activer "Appliquer" uniquement si une entrée PNJ unique est chargée.
        try {
          let entry = null;
          if (j && typeof j === "object") {
            if (j.npc && typeof j.npc === "object") entry = j.npc;
            else if (Array.isArray(j.npcs) && j.npcs.length === 1 && j.npcs[0] && typeof j.npcs[0] === "object") entry = j.npcs[0];
          }
          window.__npc_reg_last_entry = entry;
          if (applyBtn) applyBtn.disabled = !entry;
        } catch (_) {}
      } catch (e) {
        if (out) out.textContent = String(e);
        if (hint) hint.textContent = "erreur";
      }
    }

    function npcRegistryApplyToContext() {
      const entry = window.__npc_reg_last_entry;
      if (!entry || typeof entry !== "object") {
        alert("Aucune fiche PNJ chargée.");
        return;
      }
      const npcId = entry.id ? String(entry.id) : "";
      if (!npcId.trim()) {
        alert("Fiche PNJ invalide (id manquant).");
        return;
      }
      const npcName = entry.name ? String(entry.name) : "";
      const tone = entry.tone ? String(entry.tone) : "";

      let ctx = {};
      try { ctx = JSON.parse(document.getElementById("context-json").value || "{}"); } catch (_) { ctx = {}; }
      const next = { ...(ctx || {}), world_npc_id: npcId.trim() };
      if (npcName.trim()) next.npc_name = npcName.trim();
      if (tone.trim()) next.dialogue_profile = tone.trim().toLowerCase();
      if (!Array.isArray(next.history)) next.history = [];

      document.getElementById("context-json").value = JSON.stringify(next, null, 2);
      saveChatState();
      try { refreshLyraContextPreview(); } catch (_) {}
    }

    function pilotParseRoute() {
      const raw = (location.hash || "").replace(/^#/, "").replace(/^\//, "");
      const pathOnly = raw.split("?")[0];
      const parts = pathOnly.split("/").filter(function (s) { return s; });
      const seg = parts[0] || "";
      if (!seg) return "home";
      if (seg === "chat") return "chat";
      if (seg === "assistant") return "assistant";
      if (seg === "jobs") return "jobs";
      if (seg === "team" && parts[1] === "office") return "team_office";
      if (seg === "team" && parts[1] === "metrics") return "team_metrics";
      if (seg === "team") return "team";
      if (seg === "ops") return "ops";
      if (seg === "pm") return "pm";
      if (seg === "lyra") return "lyra";
      if (seg === "desktop") return "desktop";
      if (seg === "home") return "home";
      return "home";
    }

    /* ===================== Équipe virtuelle (phase A) ===================== */
    function pilotHashQuery() {
      const raw = (location.hash || "").replace(/^#/, "");
      const qIdx = raw.indexOf("?");
      if (qIdx < 0) return new URLSearchParams();
      return new URLSearchParams(raw.slice(qIdx + 1));
    }

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
      ["zone_coffee", "Pause café"],
    ];
    let __officePing = null;
    let __officeAnim = {};
    let __officeView = "map";
    let __officeMapReady = false;
    let __officeSelectedId = null;
    let __officeSelectedTaskId = null;

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
      if (btnMap) btnMap.classList.toggle("is-active", __officeView === "map");
      if (btnClassic) btnClassic.classList.toggle("is-active", __officeView === "classic");
      if (__officeView === "classic") {
        try { if (window.LbgOfficeMap) LbgOfficeMap.stop(); } catch (_) {}
        __officeMapReady = false;
        officeRender();
      } else {
        officeEnsureMap();
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
      officeSetConn("Tâche: " + st);
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
        const list = byZone[id] || [];
        const flags = [];
        list.forEach(function (a) {
          if (a.status === "busy") flags.push("has-busy");
          if (a.status === "failed") flags.push("has-failed");
          if (a.status === "review") flags.push("has-review");
        });
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
        return (
          '<section class="' + zoneClass + '" data-zone="' + officeEsc(id) + '">' +
            '<div class="office-zone-head">' +
              '<div class="office-zone-ico" title="' + officeEsc(meta.short) + '">' + meta.ico + "</div>" +
              '<div class="office-zone-titles">' +
                "<h2>" + officeEsc(label) + "</h2>" +
                '<span class="ip">' + officeEsc(meta.ip) + "</span>" +
              "</div>" +
              '<span class="count" title="agents">' + list.length + "</span>" +
            "</div>" +
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
        __officeZones = snap.zones
          .slice()
          .sort(function (a, b) { return (a.sort_order || 0) - (b.sort_order || 0); })
          .map(function (z) { return [z.id, z.label || z.id]; });
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
      if (typeof __officeLyraPoll !== "undefined" && __officeLyraPoll) {
        window.clearInterval(__officeLyraPoll);
        __officeLyraPoll = null;
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
      godot_supervise: "Supervise client Godot — sidecar 246, miroir M1, readiness lbg-ws/2",
      godot_lbg_ws2: "Audit lbg-ws/2 gateway Godot Prime — gaps et proposition forge",
      infographiste_ia: "Audit pipeline assets Infographiste IA — manifest GLB Godot et prochain export Blender",
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
      godot_supervise: { role: "qa", objectiveKey: "godot_supervise", godotSupervisor: true, autoRun: true },
      godot_lbg_ws2: { role: "dev_game", objectiveKey: "godot_lbg_ws2", godotTrack: true, autoRun: true },
      infographiste_ia: { role: "dev_game", objectiveKey: "infographiste_ia", infographiste: true, autoRun: true },
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
      __teamGodotSupervisor = !!preset.godotSupervisor;
      __teamGodotTrack = !!preset.godotTrack;
      __teamInfographiste = !!preset.infographiste;
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
          el.textContent =
            "Miroir / leçons : " +
            nLessons +
            " leçon(s) · golden " +
            nGolden +
            " · dernier juge score=" +
            score +
            " (" +
            passed +
            ")";
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
        __teamGodotSupervisor = false;
        __teamGodotTrack = false;
        __teamInfographiste = false;
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

    /* ===================== Jobs autonomes ("type Cowork") ===================== */
    let __jobsPoll = null;
    let __jobsSelectedId = null;
    let __jobsSelectedJob = null;
    let __jobsEventSource = null;
    let __jobsBound = false;
    let __jobsCatalogJsonCopy = null;
    let __jobsDevicesJsonCopy = null;

    function jobsGetActor() {
      const el = document.getElementById("jobs-actor");
      return (el && el.value ? el.value.trim() : "") || "pilot:jobs";
    }

    function jobsManualAdvance() {
      const el = document.getElementById("jobs-manual-advance");
      return !!(el && el.checked);
    }

    function jobsHint(msg, isError) {
      pilotInlineHint("jobs-create-hint", msg || "—", !!isError);
    }

    function jobsIsTerminal(status) {
      return status === "done" || status === "failed" || status === "cancelled" || status === "waiting_approval";
    }

    async function pilotFetchWithTimeout(url, opts, timeoutMs) {
      const ms = typeof timeoutMs === "number" && timeoutMs > 0 ? timeoutMs : 20000;
      const ctrl = new AbortController();
      const tid = window.setTimeout(function () { ctrl.abort(); }, ms);
      try {
        return await fetch(url, Object.assign({}, opts || {}, { signal: ctrl.signal }));
      } finally {
        window.clearTimeout(tid);
      }
    }

    async function jobsGet(url) {
      let r;
      try {
        r = await pilotFetchWithTimeout(url, { method: "GET" }, 15000);
      } catch (e) {
        const msg = e && e.name === "AbortError" ? "délai dépassé (15s)" : String(e && e.message ? e.message : e);
        return { status: 0, json: { ok: false, error: msg } };
      }
      const t = await r.text();
      let j = null;
      try { j = t ? JSON.parse(t) : null; } catch (_) {}
      return { status: r.status, json: j };
    }

    function jobsResetDetailPanel(msg) {
      __jobsSelectedId = null;
      const empty = document.getElementById("jobs-detail-empty");
      const detail = document.getElementById("jobs-detail");
      if (detail) detail.hidden = true;
      if (empty) {
        empty.hidden = false;
        empty.textContent = msg || "Sélectionne un job dans la liste pour voir son plan, sa timeline et agir dessus.";
        empty.classList.remove("err");
        if (msg && msg.indexOf("introuvable") >= 0) empty.classList.add("err");
      }
      document.querySelectorAll(".jobs-card").forEach(function (c) { c.classList.remove("jobs-card--active"); });
    }

    async function jobsCreate() {
      const objectiveEl = document.getElementById("jobs-objective");
      const objective = objectiveEl && objectiveEl.value ? objectiveEl.value.trim() : "";
      if (!objective) { jobsHint("Objectif vide.", true); return; }
      let context = {};
      try {
        const raw = (document.getElementById("jobs-context") || {}).value || "{}";
        context = raw.trim() ? JSON.parse(raw) : {};
        if (typeof context !== "object" || Array.isArray(context)) throw new Error("context doit être un objet JSON");
      } catch (e) { jobsHint("context JSON invalide : " + e.message, true); return; }
      const token = (document.getElementById("jobs-token") || {}).value || "";
      const autoStart = !!(document.getElementById("jobs-autostart") || {}).checked;
      const modelEl = document.getElementById("jobs-model");
      const model = modelEl ? modelEl.value : "";
      const plannerEl = document.getElementById("jobs-planner");
      const planner = plannerEl ? plannerEl.value : "";
      
      jobsHint("Création…");
      const payload = { actor_id: jobsGetActor(), objective: objective, context: context, auto_start: autoStart };
      if (token.trim()) payload.approval_token = token.trim();
      if (model) payload.model = model;
      if (planner) payload.planner = planner;
      const out = await postJson(getBase() + "/v1/pilot/jobs", payload, 60000);
      if (out.status !== 200 || !out.json || out.json.ok === false) {
        jobsHint("Échec création : " + ((out.json && (out.json.error || out.json.detail)) || out.status), true);
        return;
      }
      const job = out.json;
      jobsHint("Job créé (" + (job.plan_source || "?") + ", " + (job.steps ? job.steps.length : 0) + " étape(s)).");
      __jobsSelectedId = job.id;
      if (autoStart && jobsManualAdvance()) {
        await jobsAdvanceLoop(job.id);
      }
      await jobsListRefresh();
      await jobsSelect(job.id);
    }

    async function jobsListRefresh() {
      const listEl = document.getElementById("jobs-list");
      if (!listEl) return;
      const mine = !!(document.getElementById("jobs-filter-mine") || {}).checked;
      let url = getBase() + "/v1/pilot/jobs";
      if (mine) url += "?actor_id=" + encodeURIComponent(jobsGetActor());
      const out = await jobsGet(url);
      if (out.status !== 200 || !out.json || out.json.ok === false) {
        listEl.innerHTML = '<span class="err">Liste indisponible (' + ((out.json && out.json.error) || out.status) + ").</span>";
        return;
      }
      const jobs = (out.json.jobs || []);
      jobsRenderList(jobs);
      if (__jobsSelectedId && !jobs.some(function (j) { return j && j.id === __jobsSelectedId; })) {
        jobsResetDetailPanel("Le job sélectionné n’existe plus (serveur redémarré ou liste réinitialisée). Choisis-en un autre ou relance un objectif.");
      }
    }

    function jobsRenderList(jobs) {
      const listEl = document.getElementById("jobs-list");
      if (!listEl) return;
      if (!jobs.length) { listEl.innerHTML = '<span class="muted">Aucun job.</span>'; return; }
      listEl.innerHTML = jobs
        .map(function (j) {
          const active = j.id === __jobsSelectedId ? " jobs-card--active" : "";
          const st = String(j.status || "");
          return (
            '<div class="jobs-card' + active + '" data-job-id="' + escapeHtml(j.id) + '">' +
            '<div class="jobs-card-obj">' + escapeHtml(j.objective || "(sans objectif)") + "</div>" +
            '<div class="jobs-card-meta">' +
            '<span class="jobs-badge jobs-badge--' + escapeHtml(st) + '">' + escapeHtml(st) + "</span> " +
            escapeHtml(String(j.n_steps || 0)) + " étape(s) · " + escapeHtml(String(j.plan_source || "?")) +
            (j.result_summary ? " · " + escapeHtml(j.result_summary) : "") +
            "</div></div>"
          );
        })
        .join("");
      listEl.querySelectorAll(".jobs-card").forEach(function (card) {
        card.addEventListener("click", function () { jobsSelect(card.getAttribute("data-job-id")); });
      });
    }

    async function jobsSelect(id, skipEventSource) {
      if (!id) return;
      __jobsSelectedId = id;
      const out = await jobsGet(getBase() + "/v1/pilot/jobs/" + encodeURIComponent(id));
      if (out.status !== 200 || !out.json || out.json.ok === false) {
        const err = (out.json && (out.json.error || out.json.detail)) || ("HTTP " + out.status);
        jobsResetDetailPanel("Détail indisponible : " + err + ". Vérifiez l’URL du backend (même origine que le pilot si Nginx proxy /v1/).");
        return;
      }
      jobsRenderDetail(out.json);
      // Met en évidence la carte sélectionnée.
      document.querySelectorAll(".jobs-card").forEach(function (c) {
        c.classList.toggle("jobs-card--active", c.getAttribute("data-job-id") === id);
      });

      if (!skipEventSource) {
        if (__jobsEventSource) {
          __jobsEventSource.close();
          __jobsEventSource = null;
        }
        try {
          __jobsEventSource = new EventSource(getBase() + "/v1/pilot/jobs/" + encodeURIComponent(id) + "/events");
          __jobsEventSource.onmessage = function (e) {
            jobsSelect(id, true).catch(function () {});
            jobsListRefresh().catch(function () {});
          };
        } catch (err) {
          console.error("SSE EventSource error:", err);
        }
      }
    }

    function jobsPickString(obj, keys) {
      if (!obj || typeof obj !== "object") return "";
      for (let i = 0; i < keys.length; i++) {
        const v = obj[keys[i]];
        if (typeof v === "string" && v.trim()) return v.trim();
      }
      return "";
    }

    function jobsExtractStepReply(step) {
      const r = step && step.result;
      if (!r || typeof r !== "object") return "";
      let reply = jobsPickString(r, ["reply", "assistant_reply", "text"]);
      const remote = r.remote;
      if (!reply && remote && typeof remote === "object") {
        reply = jobsPickString(remote, ["reply", "text", "assistant_reply", "narration"]);
        if (!reply && Array.isArray(remote.lines)) {
          reply = remote.lines
            .map(function (ln) {
              if (typeof ln === "string") return ln;
              if (ln && typeof ln === "object" && typeof ln.text === "string") return ln.text;
              return "";
            })
            .filter(Boolean)
            .join("\n");
        }
      }
      if (!reply && r.lyra && typeof r.lyra === "object") {
        reply = jobsPickString(r.lyra, ["reply", "narration", "text"]);
      }
      if (!reply && typeof r.echo === "string") reply = r.echo;
      if (!reply && r.agent === "minimal_stub") {
        if (step && step.capability === "unknown") {
          return (
            "Aucune action technique reconnue pour cette formulation — le job s'est contenté de noter l'objectif. " +
            "Essayez par ex. « selfcheck », « chemin du fichier X », « ajoute des logs avec rétention 30j », " +
            "ou précisez le fichier dans le contexte JSON."
          );
        }
        return "(agent dialogue non joignable — vérifier lbg-agent-dialogue sur le core, port 8020)";
      }
      if (!reply && typeof r.text_snippet === "string" && r.text_snippet.trim()) {
        return "(stub) " + r.text_snippet.trim();
      }
      return reply;
    }

    function jobsExtractSelfcheckText(step) {
      if (!step || step.capability !== "devops_probe") return "";
      const r = step.result;
      if (!r || typeof r !== "object") return "";
      let inner = r.result;
      if (!inner || typeof inner !== "object") inner = r;
      const lines = [];
      const ok = inner.ok;
      const dry = inner.dry_run;
      lines.push("Selfcheck : " + (ok === true ? "OK" : ok === false ? "KO" : "?") + (dry ? " (simulation dry-run)" : ""));
      const hints = inner.remediation_hints;
      if (Array.isArray(hints) && hints.length) {
        lines.push("");
        lines.push("Pistes d'amélioration :");
        hints.forEach(function (h) {
          if (typeof h === "string" && h.trim()) lines.push("• " + h.trim());
        });
      }
      const scSteps = inner.steps;
      if (Array.isArray(scSteps)) {
        const bad = scSteps.filter(function (st) { return st && st.healthy === false; });
        if (bad.length) {
          lines.push("");
          lines.push("Éléments non sains :");
          bad.forEach(function (st) {
            const label = st.kind || st.url || st.unit || "étape";
            const err = st.result && st.result.error ? " — " + st.result.error : "";
            lines.push("• " + label + err);
          });
        }
      }
      return lines.join("\n");
    }

    function jobsBuildCapabilitiesCatalogTable(catalog) {
      if (!Array.isArray(catalog) || !catalog.length) return "";
      const rows = catalog
        .map(function (row) {
          if (!row || typeof row !== "object") return "";
          const tags = Array.isArray(row.tags) ? row.tags.join(", ") : "";
          return (
            "<tr><td><code>" + escapeHtml(String(row.capability || "")) + "</code></td>" +
            "<td><code>" + escapeHtml(String(row.routed_to || "")) + "</code></td>" +
            "<td>" + escapeHtml(String(row.risk_level || "")) + "</td>" +
            "<td>" + escapeHtml(String(row.mode || "")) + "</td>" +
            "<td>" + escapeHtml(String(row.action_context_key || "—")) + "</td>" +
            "<td class=\"muted\">" + escapeHtml(String(row.description || "")) + (tags ? " [" + escapeHtml(tags) + "]" : "") + "</td></tr>"
          );
        })
        .join("");
      return (
        '<table class="jobs-cap-table"><thead><tr>' +
        "<th>Capability</th><th>Agent (routed_to)</th><th>Risque</th><th>Mode</th><th>Action key</th><th>Description</th>" +
        "</tr></thead><tbody>" + rows + "</tbody></table>"
      );
    }

    function jobsExtractNetworkInventoryStep(step) {
      const r = step && step.result;
      if (!r || typeof r !== "object") return null;
      const devices = r.devices;
      if (!Array.isArray(devices) || !devices.length) return null;
      const exportRows = r.devices_export;
      return {
        devices: devices,
        devicesExport: Array.isArray(exportRows) && exportRows.length ? exportRows : devices,
        n: r.n_devices || devices.length,
        ts: r.ts,
        scan_cidr: r.scan_cidr,
        reply: typeof r.reply === "string" ? r.reply : "",
      };
    }

    function jobsExtractActionMatrixStep(step) {
      const r = step && step.result;
      if (!r || typeof r !== "object") return null;
      const matrix = r.action_matrix;
      if (!Array.isArray(matrix) || !matrix.length) return null;
      return { matrix: matrix, n: r.n_action_matrix_rows || matrix.length };
    }

    function jobsBuildActionMatrixTable(matrix) {
      if (!Array.isArray(matrix) || !matrix.length) return "";
      const rows = matrix.map(function (row) {
        const caps = (row.suggested_capabilities || []).map(function (c) {
          const risk = c.risk_level ? (" <span class=\"muted\">(" + escapeHtml(String(c.risk_level)) + ")</span>") : "";
          return "<code>" + escapeHtml(String(c.capability || "")) + "</code>→<code>" + escapeHtml(String(c.routed_to || "")) + "</code>" + risk;
        }).join("<br>");
        const host = row.host || "—";
        const hn = row.hostname ? ("<br><span class=\"muted\">" + escapeHtml(String(row.hostname)) + "</span>") : "";
        return (
          "<tr><td>" + escapeHtml(String(row.label || row.host || "—")) + "</td>" +
          "<td><code>" + escapeHtml(String(host)) + "</code>" + hn + "</td>" +
          "<td class=\"muted\">" + (caps || "—") + "</td></tr>"
        );
      }).join("");
      return (
        "<table class=\"jobs-cap-table\"><thead><tr>" +
        "<th>Appareil</th><th>IP / hostname</th><th>Capabilities suggérées</th>" +
        "</tr></thead><tbody>" + rows + "</tbody></table>"
      );
    }

    function jobsBuildNetworkDevicesTable(devices) {
      if (!Array.isArray(devices) || !devices.length) return "";
      const rows = devices.map(function (d) {
        const ok = d.reachable ? "OK" : "KO";
        const label = d.label || d.server_id || "—";
        const hint = d.device_hint ? (" <span class=\"muted\">[" + escapeHtml(String(d.device_hint)) + "]</span>") : "";
        const ports = Array.isArray(d.open_ports) && d.open_ports.length
          ? d.open_ports.join(", ")
          : (d.probe_results || []).filter(function (p) { return p.kind === "tcp" && p.ok; }).map(function (p) { return p.port; }).join(", ");
        const probes = (d.probe_results || []).map(function (p) {
          const lbl = p.label || p.kind || "?";
          if (p.kind === "http") return lbl + (p.ok ? " OK" : " KO");
          if (p.kind === "tcp") return lbl + " :" + p.port + (p.ok ? " open" : " closed");
          return lbl;
        }).join(", ");
        const detail = ports ? ("ports: " + ports) : probes;
        const hn = d.hostname ? ("<br><span class=\"muted\">" + escapeHtml(String(d.hostname)) + "</span>") : "";
        const caps = Array.isArray(d.action_suggestions) && d.action_suggestions.length
          ? d.action_suggestions.map(function (c) { return "<code>" + escapeHtml(String(c)) + "</code>"; }).join(" ")
          : "";
        return "<tr><td>" + escapeHtml(String(label)) + hint + "</td><td><code>" + escapeHtml(String(d.host || "")) + "</code>" + hn + "</td>" +
          "<td>" + ok + "</td><td class=\"muted\">" + escapeHtml(detail || "—") + "</td>" +
          "<td>" + (caps || "<span class=\"muted\">—</span>") + "</td></tr>";
      }).join("");
      return (
        "<table class=\"jobs-cap-table\"><thead><tr>" +
        "<th>Appareil</th><th>IP / hostname</th><th>État</th><th>Ports / sondes</th><th>Actions</th>" +
        "</tr></thead><tbody>" + rows + "</tbody></table>"
      );
    }

    function jobsExtractCapabilitiesCatalogStep(step) {
      const r = step && step.result;
      if (!r || typeof r !== "object") return null;
      const catalog = r.capabilities_catalog;
      if (!Array.isArray(catalog) || !catalog.length) return null;
      return {
        catalog: catalog,
        n: r.n_capabilities || catalog.length,
        ts: r.ts,
        reply: typeof r.reply === "string" ? r.reply : "",
      };
    }

    function jobsBuildReadableBlocks(job) {
      const blocks = [];
      const steps = job.steps || [];
      for (let c = 0; c < steps.length; c++) {
        const net = jobsExtractNetworkInventoryStep(steps[c]);
        if (net) {
          blocks.push({
            title: "Appareils LAN (instantané T — " + net.n + " hôte(s)" + (net.scan_cidr ? " · " + net.scan_cidr : "") + ")",
            html: jobsBuildNetworkDevicesTable(net.devices),
            devicesJson: JSON.stringify(net.devicesExport, null, 2),
            isHtml: true,
            primary: true,
          });
          if (net.reply) {
            blocks.push({ title: "Inventaire réseau (texte)", text: net.reply, primary: false });
          }
        }
        const inv = jobsExtractCapabilitiesCatalogStep(steps[c]);
        if (inv) {
          blocks.push({
            title: "Inventaire agents / capabilities (instantané T — " + inv.n + " entrées)",
            html: jobsBuildCapabilitiesCatalogTable(inv.catalog),
            catalogJson: JSON.stringify(inv.catalog, null, 2),
            isHtml: true,
            primary: !blocks.some(function (b) { return b.primary; }),
          });
          const mx = jobsExtractActionMatrixStep(steps[c]);
          if (mx) {
            blocks.push({
              title: "Matrice LAN × capabilities (" + mx.n + " appareil(s))",
              html: jobsBuildActionMatrixTable(mx.matrix),
              isHtml: true,
              primary: false,
            });
          }
          if (inv.reply) {
            blocks.push({ title: "Liste texte (copiable)", text: inv.reply, primary: false });
          }
          break;
        }
      }
      let synthesis = "";
      for (let i = steps.length - 1; i >= 0; i--) {
        if (steps[i].capability === "npc_dialogue" || steps[i].context_patch && steps[i].context_patch._job_synthesis) {
          synthesis = jobsExtractStepReply(steps[i]);
          if (synthesis) break;
        }
      }
      if (!synthesis) {
        for (let j = steps.length - 1; j >= 0; j--) {
          if (jobsExtractCapabilitiesCatalogStep(steps[j])) continue;
          synthesis = jobsExtractStepReply(steps[j]);
          if (synthesis) break;
        }
      }
      if (synthesis && !blocks.some(function (b) { return b.primary; })) {
        blocks.push({ title: "Synthèse", text: synthesis, primary: true });
      } else if (synthesis && blocks.length) {
        blocks.push({ title: "Synthèse", text: synthesis, primary: false });
      }
      for (let k = 0; k < steps.length; k++) {
        const sc = jobsExtractSelfcheckText(steps[k]);
        if (sc) blocks.push({ title: "Diagnostic DevOps", text: sc, primary: false });
      }
      if (!blocks.length && job.result_summary) {
        blocks.push({ title: "Résumé", text: String(job.result_summary), primary: true });
      }
      return blocks;
    }

    async function jobsCopyTextToClipboard(json, emptyMsg, okPrefix) {
      const hint = document.getElementById("jobs-catalog-copy-hint");
      if (!json) {
        if (hint) hint.textContent = emptyMsg;
        return;
      }
      const setHint = function (msg, err) {
        if (hint) {
          hint.textContent = msg;
          hint.style.color = err ? "#b91c1c" : "";
        }
      };
      setHint("Copie…", false);
      try {
        if (navigator.clipboard && navigator.clipboard.writeText) {
          await navigator.clipboard.writeText(json);
          setHint(okPrefix + " (" + json.length + " car.).", false);
          return;
        }
      } catch (_) {}
      try {
        const ta = document.createElement("textarea");
        ta.value = json;
        ta.setAttribute("readonly", "");
        ta.style.position = "fixed";
        ta.style.left = "-9999px";
        document.body.appendChild(ta);
        ta.select();
        const ok = document.execCommand("copy");
        document.body.removeChild(ta);
        if (ok) {
          setHint(okPrefix + " (" + json.length + " car.).", false);
          return;
        }
      } catch (_) {}
      setHint("Copie impossible (HTTPS ou permission presse-papiers).", true);
    }

    async function jobsCopyCatalogJson() {
      await jobsCopyTextToClipboard(__jobsCatalogJsonCopy, "Aucun catalogue à copier.", "JSON catalogue copié");
    }

    async function jobsCopyDevicesJson() {
      await jobsCopyTextToClipboard(__jobsDevicesJsonCopy, "Aucun inventaire appareils à copier.", "JSON appareils copié");
    }

    function jobsRenderReadable(job) {
      const wrap = document.getElementById("jobs-detail-readable");
      const body = document.getElementById("jobs-detail-readable-body");
      const toolbar = document.getElementById("jobs-detail-readable-toolbar");
      const copyHint = document.getElementById("jobs-catalog-copy-hint");
      if (!wrap || !body) return;
      const blocks = jobsBuildReadableBlocks(job);
      __jobsCatalogJsonCopy = null;
      __jobsDevicesJsonCopy = null;
      blocks.forEach(function (b) {
        if (b.catalogJson) __jobsCatalogJsonCopy = b.catalogJson;
        if (b.devicesJson) __jobsDevicesJsonCopy = b.devicesJson;
      });
      if (!blocks.length) {
        wrap.hidden = true;
        if (toolbar) toolbar.hidden = true;
        return;
      }
      wrap.hidden = false;
      if (toolbar) toolbar.hidden = !(__jobsCatalogJsonCopy || __jobsDevicesJsonCopy);
      if (copyHint && !__jobsCatalogJsonCopy && !__jobsDevicesJsonCopy) copyHint.textContent = "—";
      const copyDevBtn = document.getElementById("btn-jobs-copy-devices");
      const copyCatBtn = document.getElementById("btn-jobs-copy-catalog");
      if (copyDevBtn) copyDevBtn.style.display = __jobsDevicesJsonCopy ? "" : "none";
      if (copyCatBtn) copyCatBtn.style.display = __jobsCatalogJsonCopy ? "" : "none";
      wrap.classList.toggle("jobs-readable--muted", !blocks.some(function (b) { return b.primary; }));
      body.innerHTML = blocks
        .map(function (b) {
          const bodyHtml = b.isHtml && b.html
            ? '<div class="jobs-readable-text">' + b.html + "</div>"
            : '<div class="jobs-readable-text">' + escapeHtml(b.text || "") + "</div>";
          return (
            '<div class="jobs-readable-block">' +
            '<div class="jobs-readable-kicker">' + escapeHtml(b.title) + "</div>" +
            bodyHtml + "</div>"
          );
        })
        .join("");
    }

    function jobsRenderDetail(job) {
      __jobsSelectedJob = job;
      const empty = document.getElementById("jobs-detail-empty");
      const detail = document.getElementById("jobs-detail");
      if (!detail || !empty) return;
      empty.hidden = true;
      detail.hidden = false;

      const badge = document.getElementById("jobs-detail-status");
      if (badge) {
        badge.hidden = false;
        badge.textContent = job.status;
        badge.className = "assistant-route-badge jobs-badge jobs-badge--" + String(job.status || "");
      }
      const obj = document.getElementById("jobs-detail-objective");
      if (obj) obj.innerHTML = "<strong>Objectif :</strong> " + escapeHtml(job.objective || "") +
        " <span class='muted'>(" + escapeHtml(String(job.plan_source || "?")) + (job.pre_authorized ? ", pré-autorisé" : "") + ")</span>" +
        (job.result_summary ? "<br><span class='muted'>" + escapeHtml(job.result_summary) + "</span>" : "");

      // Boutons selon l'état.
      const approveBtn = document.getElementById("btn-jobs-approve");
      const approveTok = document.getElementById("jobs-approve-token");
      const advBtn = document.getElementById("btn-jobs-advance");
      const cancelBtn = document.getElementById("btn-jobs-cancel");
      const waiting = job.status === "waiting_approval";
      const terminal = job.status === "done" || job.status === "failed" || job.status === "cancelled";
      if (approveBtn) approveBtn.style.display = waiting ? "" : "none";
      if (approveTok) approveTok.style.display = waiting ? "" : "none";
      if (advBtn) advBtn.disabled = terminal || waiting;
      if (cancelBtn) cancelBtn.disabled = terminal;

      // Étapes.
      const stepsEl = document.getElementById("jobs-detail-steps");
      if (stepsEl) {
        const steps = job.steps || [];
        stepsEl.innerHTML = steps.length
          ? steps.map(function (s, i) {
              const dec = s.policy && s.policy.decision ? s.policy.decision : "";
              const att = s.max_attempts ? (s.attempts || 0) + "/" + s.max_attempts : (s.attempts || 0);
              let snippet = "";
              if (s.status === "done" && s.result) {
                if (s.capability === "devops_probe") snippet = jobsExtractSelfcheckText(s);
                else snippet = jobsExtractStepReply(s);
                if (snippet && snippet.length > 400) snippet = snippet.slice(0, 397) + "…";
              }
              
              let logHtml = "";
              if (s.error || (s.result && (s.result.stdout || s.result.stderr || s.result.error || s.result.exception || s.result.reply))) {
                let logText = "";
                if (s.error) logText += "Error: " + s.error + "\n";
                if (s.result) {
                  if (s.result.error) logText += "Result Error: " + s.result.error + "\n";
                  if (s.result.exception) logText += "Exception: " + s.result.exception + "\n";
                  if (s.result.stdout) logText += "STDOUT:\n" + s.result.stdout + "\n";
                  if (s.result.stderr) logText += "STDERR:\n" + s.result.stderr + "\n";
                  if (s.result.reply) {
                    logText += "Reply: " + (typeof s.result.reply === "object" ? JSON.stringify(s.result.reply, null, 2) : s.result.reply) + "\n";
                  }
                }
                if (logText.trim()) {
                  logHtml = '<details class="jobs-step-logs" style="margin-top: 0.4rem;">' +
                            '<summary style="font-size: 0.76rem; cursor: pointer; color: #38bdf8; font-weight: 600;">Afficher les logs de l\'étape</summary>' +
                            '<pre style="background: #1e293b; color: #f8fafc; padding: 0.5rem; border-radius: 4px; font-family: ui-monospace, monospace; font-size: 0.78rem; overflow-x: auto; margin-top: 0.25rem; white-space: pre-wrap; word-break: break-all; text-align: left;">' +
                            escapeHtml(logText.trim()) +
                            '</pre></details>';
                }
              }
              
              return (
                '<div class="jobs-step jobs-step--' + escapeHtml(String(s.status || "")) + '">' +
                "<strong>#" + (i + 1) + "</strong> " + escapeHtml(s.summary || s.capability || "") +
                ' <span class="jobs-step-cap">[' + escapeHtml(s.capability || "") + "]</span>" +
                ' <span class="jobs-badge jobs-badge--' + escapeHtml(String(s.status || "")) + '">' + escapeHtml(String(s.status || "")) + "</span>" +
                '<div class="muted" style="font-size:0.76rem;margin-top:0.15rem;">tentatives ' + escapeHtml(String(att)) +
                (dec ? " · policy " + escapeHtml(dec) : "") +
                (s.error ? ' · <span class="err">' + escapeHtml(s.error) + "</span>" : "") + "</div>" +
                (snippet ? '<div class="jobs-step-snippet">' + escapeHtml(snippet) + "</div>" : "") +
                logHtml +
                "</div>"
              );
            }).join("")
          : '<span class="muted">Aucune étape.</span>';
      }

      jobsRenderReadable(job);

      // Timeline.
      const tlEl = document.getElementById("jobs-detail-timeline");
      if (tlEl) {
        const events = (job.events || []).slice(-24);
        tlEl.innerHTML = events.length
          ? events.map(function (e) {
              const when = e.ts ? new Date(e.ts * 1000).toLocaleTimeString() : "";
              const extra = [];
              if (e.capability) extra.push(e.capability);
              if (e.decision) extra.push(e.decision);
              if (e.error) extra.push(e.error);
              if (typeof e.attempt !== "undefined") extra.push("essai " + e.attempt);
              return '<div class="jobs-tl-row"><code>' + escapeHtml(when) + "</code> · <strong>" +
                escapeHtml(e.kind || "") + "</strong>" + (extra.length ? " — " + escapeHtml(extra.join(" · ")) : "") + "</div>";
            }).join("")
          : '<span class="muted">—</span>';
      }

      const raw = document.getElementById("jobs-detail-raw");
      if (raw) raw.textContent = JSON.stringify(job, null, 2);
    }

    async function jobsAdvanceOnce(id) {
      const out = await postJson(getBase() + "/v1/pilot/jobs/" + encodeURIComponent(id) + "/advance", {});
      return out.json && out.json.ok !== false ? out.json : null;
    }

    async function jobsAdvanceLoop(id) {
      for (let i = 0; i < 24; i++) {
        const job = await jobsAdvanceOnce(id);
        if (!job) break;
        jobsRenderDetail(job);
        if (jobsIsTerminal(job.status)) break;
      }
    }

    async function jobsApprove() {
      if (!__jobsSelectedId) return;
      const tok = (document.getElementById("jobs-approve-token") || {}).value || "";
      if (!tok.trim()) { jobsHint("Token d'approbation requis.", true); return; }
      const out = await postJson(getBase() + "/v1/pilot/jobs/" + encodeURIComponent(__jobsSelectedId) + "/approve", { token: tok.trim() });
      if (out.status !== 200 || !out.json || out.json.ok === false) { jobsHint("Approbation refusée.", true); return; }
      jobsHint("Approuvé.");
      if (jobsManualAdvance()) await jobsAdvanceLoop(__jobsSelectedId);
      await jobsSelect(__jobsSelectedId);
      await jobsListRefresh();
    }

    async function jobsCancel() {
      if (!__jobsSelectedId) return;
      const out = await postJson(getBase() + "/v1/pilot/jobs/" + encodeURIComponent(__jobsSelectedId) + "/cancel", {});
      if (out.json && out.json.ok !== false) {
        await jobsSelect(__jobsSelectedId);
        await jobsListRefresh();
      }
    }

    function jobsClone() {
      if (!__jobsSelectedJob) return;
      const objEl = document.getElementById("jobs-objective");
      const ctxEl = document.getElementById("jobs-context");
      const modelEl = document.getElementById("jobs-model");
      const plannerEl = document.getElementById("jobs-planner");
      
      if (objEl) objEl.value = __jobsSelectedJob.objective || "";
      if (ctxEl) {
        const cleanContext = {};
        if (__jobsSelectedJob.base_context && typeof __jobsSelectedJob.base_context === "object") {
          for (const k in __jobsSelectedJob.base_context) {
            if (!k.startsWith("_")) {
              cleanContext[k] = __jobsSelectedJob.base_context[k];
            }
          }
        }
        ctxEl.value = JSON.stringify(cleanContext, null, 2);
      }
      
      if (__jobsSelectedJob.base_context) {
        const model = __jobsSelectedJob.base_context._planner_model || "";
        const planner = __jobsSelectedJob.base_context._planner || "";
        if (modelEl) modelEl.value = model;
        if (plannerEl) plannerEl.value = planner;
      }
      
      jobsHint("Champs clonés depuis le job #" + __jobsSelectedJob.id.slice(0, 8));
    }

    async function jobsLoadModels() {
      const select = document.getElementById("jobs-model");
      if (!select) return;
      const url = getBase() + "/v1/pilot/ollama/tags";
      const out = await jobsGet(url);
      
      const currentVal = select.value;
      select.innerHTML = '<option value="">(Par défaut du serveur)</option>';
      
      if (out.status === 200 && out.json && Array.isArray(out.json.models)) {
        out.json.models.forEach(function (m) {
          if (m && m.name) {
            const opt = document.createElement("option");
            opt.value = m.name;
            opt.textContent = m.name;
            select.appendChild(opt);
          }
        });
      }
      select.value = currentVal;
    }

    async function checkWaitingApprovalJobsGlobal() {
      const badge = document.getElementById("jobs-nav-badge");
      if (!badge) return;
      const url = getBase() + "/v1/pilot/jobs";
      const out = await jobsGet(url);
      if (out.status === 200 && out.json && Array.isArray(out.json.jobs)) {
        const hasWaiting = out.json.jobs.some(function (j) {
          return j && j.status === "waiting_approval";
        });
        badge.style.display = hasWaiting ? "inline-block" : "none";
      } else {
        badge.style.display = "none";
      }
    }

    function jobsBindPage() {
      if (__jobsBound) return;
      __jobsBound = true;
      const c = document.getElementById("btn-jobs-create");
      if (c) c.addEventListener("click", function () { jobsCreate().catch(function () {}); });
      const rf = document.getElementById("btn-jobs-refresh");
      if (rf) rf.addEventListener("click", function () { jobsListRefresh().catch(function () {}); });
      const ap = document.getElementById("btn-jobs-approve");
      if (ap) ap.addEventListener("click", function () { jobsApprove().catch(function () {}); });
      const ad = document.getElementById("btn-jobs-advance");
      if (ad) ad.addEventListener("click", function () {
        if (!__jobsSelectedId) return;
        jobsAdvanceOnce(__jobsSelectedId).then(function (j) { if (j) jobsRenderDetail(j); jobsListRefresh(); }).catch(function () {});
      });
      const cancel = document.getElementById("btn-jobs-cancel");
      if (cancel) cancel.addEventListener("click", function () { jobsCancel().catch(function () {}); });
      const clone = document.getElementById("btn-jobs-clone");
      if (clone) clone.addEventListener("click", jobsClone);
      const copyDev = document.getElementById("btn-jobs-copy-devices");
      if (copyDev) copyDev.addEventListener("click", function () { jobsCopyDevicesJson().catch(function () {}); });
      const copyCat = document.getElementById("btn-jobs-copy-catalog");
      if (copyCat) copyCat.addEventListener("click", function () { jobsCopyCatalogJson().catch(function () {}); });
      const filt = document.getElementById("jobs-filter-mine");
      if (filt) filt.addEventListener("change", function () { jobsListRefresh().catch(function () {}); });
    }

    function jobsPollStart() {
      jobsPollStop();
      __jobsPoll = window.setInterval(function () {
        jobsListRefresh().catch(function () {});
        if (__jobsSelectedId) jobsSelect(__jobsSelectedId, true).catch(function () {});
      }, 2800);
    }

    function jobsPollStop() {
      if (__jobsPoll) { window.clearInterval(__jobsPoll); __jobsPoll = null; }
      if (__jobsEventSource) { __jobsEventSource.close(); __jobsEventSource = null; }
    }

    function pilotApplyRoute() {
      try {
        assistantLbgiaPollStop();
      } catch (_) {}
      try { jobsPollStop(); } catch (_) {}
      const r = pilotParseRoute();
      document.body.dataset.pilotRoute = r;
      const home = document.getElementById("pilot-page-home");
      const work = document.getElementById("pilot-page-work");
      const assistantPage = document.getElementById("pilot-page-assistant");
      const jobsPage = document.getElementById("pilot-page-jobs");
      const teamPage = document.getElementById("pilot-page-team");
      const teamOfficePage = document.getElementById("pilot-page-team-office");
      const pm = document.getElementById("pilot-page-pm");
      const ly = document.getElementById("pilot-page-lyra");
      const de = document.getElementById("pilot-page-desktop");
      if (home) home.hidden = r !== "home";
      if (work) work.hidden = r !== "chat" && r !== "ops";
      if (assistantPage) assistantPage.hidden = r !== "assistant";
      if (jobsPage) jobsPage.hidden = r !== "jobs";
      if (teamPage) teamPage.hidden = r !== "team";
      if (teamOfficePage) teamOfficePage.hidden = r !== "team_office";
      if (pm) pm.hidden = r !== "pm";
      if (ly) ly.hidden = r !== "lyra";
      if (de) de.hidden = r !== "desktop";
      if (r === "jobs") {
        try { jobsBindPage(); } catch (_) {}
        try { jobsLoadModels(); } catch (_) {}
        try { jobsListRefresh(); } catch (_) {}
        try { jobsPollStart(); } catch (_) {}
      }
      if (r === "team") {
        try { teamBindPage(); } catch (_) {}
        const deepTask = (pilotHashQuery().get("task") || "").trim();
        try {
          teamListRefresh().then(function () {
            if (deepTask) return teamSelect(deepTask, { skipHash: true });
          }).catch(function () {});
        } catch (_) {}
      }
      if (r === "team_office") {
        try { officeBindPage(); } catch (_) {}
      } else {
        try { officeStop(); } catch (_) {}
      }
      if (r === "desktop") {
        try { pilotDesktopRefreshConfigHint(); } catch (_) {}
        try { pilotDesktopLoadMmoSummaryFromStorage(); } catch (_) {}
        try { pilotDesktopLoadDryRunToggleFromStorage(); } catch (_) {}
        try { pilotDesktopApplyPipelinePrefsToUi(); } catch (_) {}
        try { pilotDesktopBindPipelinePrefs(); } catch (_) {}
        try { pilotDesktopBindDryRunTogglePersist(); } catch (_) {}
        try { pilotDesktopSetupSpeech(); } catch (_) {}
        try { pilotDesktopApplyHomeLaunchPreset(); } catch (_) {}
      }
      if (r === "assistant") {
        try { assistantBindAssistantPage(); } catch (_) {}
        try { assistantApplyPrefsToUi(); } catch (_) {}
        try { assistantSyncAdvancedPanel(); } catch (_) {}
        try { assistantSessionNotesLoad(); } catch (_) {}
        try { assistantMmoImportSilentLoad(); } catch (_) {}
        try { assistantRenderLyraPanel(); } catch (_) {}
        try { assistantHistoryRender(); } catch (_) {}
        try { assistantRenderSuggestions([]); } catch (_) {}
        try { assistantRenderDocRefs(); } catch (_) {}
        try { assistantRenderSessionState(); } catch (_) {}
        try { assistantCapsRefresh(); } catch (_) {}
        try {
          assistantLbgiaRefresh();
          __assistantLbgiaPoll = window.setInterval(assistantLbgiaRefresh, 2800);
        } catch (_) {}
        try {
          orchestratorAvatarInit();
          faceRigInit();
          assistantOrchMoodRefresh();
          __assistantOrchMoodPoll = window.setInterval(assistantOrchMoodRefresh, 5000);
        } catch (_) {}
      }
      const title = document.getElementById("pilot-work-title");
      const sub = document.getElementById("pilot-work-sub");
      if (title && sub && (r === "chat" || r === "ops")) {
        if (r === "ops") {
          title.textContent = "Ops & santé";
          sub.textContent =
            "Benchmark, cache, monitoring agrégé, capabilities, métriques — même backend que la barre du haut.";
          try {
            const rt = document.getElementById("toggle-right");
            const cr = document.getElementById("col-right");
            if (rt && cr) {
              rt.checked = true;
              cr.style.display = "";
            }
          } catch (_) {}
        } else {
          title.textContent = "Chat & presets";
          sub.textContent =
            "Studio — intention agents (POST /v1/pilot/route). Lab sandbox WS / commits monde : Legacy lab.";
        }
      }
      document.querySelectorAll("#pilot-nav a").forEach(function (a) {
        const route = a.getAttribute("data-nav-route") || "";
        let active = false;
        if (route === "home") active = r === "home";
        else if (route === "team_office") active = r === "team_office";
        else if (route) active = r === route;
        a.classList.toggle("pilot-nav-active", !!active);
      });
      const groupOf = {
        chat: "studio",
        assistant: "studio",
        jobs: "studio",
        team: "campus",
        team_office: "campus",
        ops: "ops",
        desktop: "ops",
        pm: "projet",
        lyra: "projet",
      };
      const gActive = groupOf[r] || "";
      document.querySelectorAll("#pilot-nav .pilot-nav-group").forEach(function (g) {
        const gid = g.getAttribute("data-nav-group") || "";
        g.classList.toggle("pilot-nav-active", !!gActive && gid === gActive);
      });
    }

    (function pilotNavMenus() {
      const nav = document.getElementById("pilot-nav");
      if (!nav || nav._menusBound) return;
      nav._menusBound = true;
      nav.querySelectorAll(".pilot-nav-group").forEach(function (g) {
        g.addEventListener("toggle", function () {
          if (!g.open) return;
          nav.querySelectorAll(".pilot-nav-group").forEach(function (other) {
            if (other !== g) other.open = false;
          });
        });
      });
      document.addEventListener("click", function (ev) {
        if (nav.contains(ev.target)) return;
        nav.querySelectorAll(".pilot-nav-group").forEach(function (g) { g.open = false; });
      });
    })();

    function escapeHtmlPm(s) {
      return String(s || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\"/g, "&quot;");
    }

    /**
     * Texte brut → HTML sûr : échappement + liens http(s) + pastilles « copier » pour chemins docs/ / infra/.
     */
    function pmRichFormat(raw) {
      const s = String(raw || "");
      const re = /(https?:\/\/[^\s<]+)|(\b(?:docs|infra)\/[A-Za-z0-9_.\/-]+(?:\.md|\.sh)?\b)/g;
      const chunks = [];
      let idx = 0;
      let m;
      while ((m = re.exec(s)) !== null) {
        if (m.index > idx) chunks.push({ type: "t", v: s.slice(idx, m.index) });
        if (m[1]) chunks.push({ type: "url", v: m[1] });
        else if (m[2]) chunks.push({ type: "path", v: m[2] });
        idx = m.index + m[0].length;
      }
      if (idx < s.length) chunks.push({ type: "t", v: s.slice(idx) });
      return chunks
        .map(function (c) {
          if (c.type === "t") return escapeHtmlPm(c.v).replace(/\n/g, "<br>");
          if (c.type === "url") {
            const u = c.v;
            const href = u.replace(/"/g, "%22");
            return (
              '<a href="' +
              href +
              '" target="_blank" rel="noopener noreferrer">' +
              escapeHtmlPm(u) +
              "</a>"
            );
          }
          const p = c.v;
          return (
            '<button type="button" class="pm-path-chip" data-copy="' +
            escapeHtmlPm(p) +
            '" title="Copier le chemin (repo LBG_Studios)">' +
            escapeHtmlPm(p) +
            "</button>"
          );
        })
        .join("");
    }

    function renderPmEncarts(brief) {
      const wrap = document.getElementById("pm-encarts");
      const wStep = document.getElementById("pm-encart-step-wrap");
      const wFa = document.getElementById("pm-encart-fa-wrap");
      const elStep = document.getElementById("pm-encart-step");
      const elFa = document.getElementById("pm-encart-fa");
      if (!wrap || !wStep || !wFa || !elStep || !elFa) return;
      if (!brief || typeof brief !== "object") {
        wrap.style.display = "none";
        wStep.hidden = true;
        wFa.hidden = true;
        return;
      }
      const step = typeof brief.current_step === "string" ? brief.current_step.trim() : "";
      const fa = typeof brief.file_attente === "string" ? brief.file_attente.trim() : "";
      let any = false;
      if (step) {
        wStep.hidden = false;
        elStep.innerHTML = pmRichFormat(step);
        any = true;
      } else {
        wStep.hidden = true;
        elStep.innerHTML = "";
      }
      if (fa) {
        wFa.hidden = false;
        elFa.innerHTML = pmRichFormat(fa);
        any = true;
      } else {
        wFa.hidden = true;
        elFa.innerHTML = "";
      }
      wrap.style.display = any ? "grid" : "none";
    }

    function buildPmMarkdownFromBrief(brief) {
      if (!brief || typeof brief !== "object") return "# Brief chef de projet\n\n_(vide)_\n";
      let md = "# Brief chef de projet\n\n";
      md += "_Généré depuis le stub PM (pilot)._\n\n";
      if (brief.current_step) md += "## Étape actuelle\n\n" + String(brief.current_step).trim() + "\n\n";
      if (brief.file_attente) md += "## File d'attente\n\n" + String(brief.file_attente).trim() + "\n\n";
      const ms = brief.milestones;
      if (Array.isArray(ms) && ms.length) {
        md += "## Jalons\n\n";
        ms.forEach(function (m) {
          md += "- **" + (m.date || "") + "** — " + (m.summary || "").replace(/\n/g, " ") + "\n";
        });
        md += "\n";
      }
      const ts = brief.tasks;
      if (Array.isArray(ts) && ts.length) {
        md += "## Tâches\n\n";
        ts.forEach(function (t) {
          md += "- [ ] " + (t.title || "") + " _" + (t.source || "") + "_\n";
        });
        md += "\n";
      }
      return md;
    }

    function pmExtractBrief(resp) {
      if (!resp || typeof resp !== "object") return null;
      if (resp.brief && typeof resp.brief === "object") return resp.brief;
      if (resp.output && typeof resp.output === "object" && resp.output.brief && typeof resp.output.brief === "object")
        return resp.output.brief;
      const r = resp.result;
      if (
        r &&
        typeof r === "object" &&
        r.output &&
        typeof r.output === "object" &&
        r.output.brief &&
        typeof r.output.brief === "object"
      )
        return r.output.brief;
      return null;
    }

    // --------------------------
    // Lyra (standalone) page
    // --------------------------
    const STORAGE_LYRA_KEY = "lbg_pilot_lyra_state_v1";
    const STORAGE_LYRA_MODE_KEY = "lbg_pilot_lyra_mode_v1";
    let __lyraAutoTimer = null;

    function clamp01(n) {
      const x = Number(n);
      if (!Number.isFinite(x)) return 0;
      if (x < 0) return 0;
      if (x > 1) return 1;
      return x;
    }

    function clamp0100(n, fallback) {
      const x = Number(n);
      if (!Number.isFinite(x)) return (fallback != null ? fallback : 0);
      if (x < 0) return 0;
      if (x > 100) return 100;
      return x;
    }

    function lyraDefaultState() {
      return {
        dt_s: 60,
        // jauges "besoins" (monde) — UI alignée 0–100 (conversion 0–1 au bord)
        gauges: { hunger: 25, thirst: 25, fatigue: 25 },
        // jauges "ton" 0–100 (assistant) — affichées ici, mais non envoyées dans context.lyra (évite mélange d’échelles)
        confiance_100: 70,
        assistant_gauges_100: { chaleur: 70, energie: 60, patience: 70, confiance: 70 },
        version: "Lyra 2.0",
      };
    }

    function lyraLoadState() {
      try {
        const raw = localStorage.getItem(STORAGE_LYRA_KEY);
        if (!raw) return lyraDefaultState();
        const j = JSON.parse(raw);
        const d = lyraDefaultState();
        if (j && typeof j === "object") {
          if (j.dt_s != null) d.dt_s = Number(j.dt_s) || d.dt_s;
          if (j.version) d.version = String(j.version);
          if (j.gauges && typeof j.gauges === "object") d.gauges = { ...d.gauges, ...j.gauges };
          if (j.confiance_100 != null) d.confiance_100 = clamp0100(j.confiance_100, d.confiance_100);
          if (j.assistant_gauges_100 && typeof j.assistant_gauges_100 === "object")
            d.assistant_gauges_100 = { ...d.assistant_gauges_100, ...j.assistant_gauges_100 };
        }
        return d;
      } catch (_) {
        return lyraDefaultState();
      }
    }

    function lyraGetMode() {
      const world = document.getElementById("lyra-mode-world");
      const asst = document.getElementById("lyra-mode-assistant");
      if (asst && asst.checked) return "assistant";
      if (world && world.checked) return "world";
      try {
        const m = localStorage.getItem(STORAGE_LYRA_MODE_KEY);
        if (m === "assistant" || m === "world") return m;
      } catch (_) {}
      return "world";
    }

    function lyraSetMode(mode) {
      try { localStorage.setItem(STORAGE_LYRA_MODE_KEY, mode); } catch (_) {}
      const world = document.getElementById("lyra-mode-world");
      const asst = document.getElementById("lyra-mode-assistant");
      if (world) world.checked = mode === "world";
      if (asst) asst.checked = mode === "assistant";
    }

    function lyraSaveState(st) {
      try {
        localStorage.setItem(STORAGE_LYRA_KEY, JSON.stringify(st));
      } catch (_) {}
    }

    function lyraGaugeColor(v01) {
      const v = clamp01(v01);
      if (v >= 0.75) return "#f87171"; // high = red (stress/fatigue/hunger)
      if (v >= 0.45) return "#facc15"; // yellow
      return "#4ade80"; // green
    }

    function lyraNeedsTo01(needs100) {
      const g = needs100 && typeof needs100 === "object" ? needs100 : {};
      return {
        hunger: clamp0100(g.hunger != null ? g.hunger : 0, 0) / 100.0,
        thirst: clamp0100(g.thirst != null ? g.thirst : 0, 0) / 100.0,
        fatigue: clamp0100(g.fatigue != null ? g.fatigue : 0, 0) / 100.0,
      };
    }

    function lyraNeedsFrom01(needs01) {
      const g = needs01 && typeof needs01 === "object" ? needs01 : {};
      return {
        hunger: Math.round(clamp01(g.hunger != null ? g.hunger : 0) * 100),
        thirst: Math.round(clamp01(g.thirst != null ? g.thirst : 0) * 100),
        fatigue: Math.round(clamp01(g.fatigue != null ? g.fatigue : 0) * 100),
      };
    }

    function lyraComputeEnergy100(needs01) {
      const g = needs01 && typeof needs01 === "object" ? needs01 : {};
      const h = clamp01(g.hunger != null ? g.hunger : 0);
      const t = clamp01(g.thirst != null ? g.thirst : 0);
      const f = clamp01(g.fatigue != null ? g.fatigue : 0);
      const mean = (h + t + f) / 3.0;
      return Math.round(100 * (1.0 - mean));
    }

    function lyraRenderGaugeBlock(containerId, gauges, opts) {
      const el = document.getElementById(containerId);
      if (!el) return;
      const interactive = !!(opts && opts.interactive);
      const mode = (opts && opts.mode) || "world";
      const g = gauges && typeof gauges === "object" ? gauges : {};
      const items =
        mode === "assistant"
          ? [
              ["chaleur", "Chaleur"],
              ["energie", "Énergie"],
              ["patience", "Patience"],
              ["confiance", "Confiance"],
            ]
          : [
              ["hunger", "Faim"],
              ["thirst", "Soif"],
              ["fatigue", "Fatigue"],
            ];
      el.innerHTML = items
        .map(function (it) {
          const k = it[0];
          const label = it[1];
          const v01 =
            mode === "assistant"
              ? clamp0100(g[k] != null ? g[k] : 0, 0) / 100.0
              : clamp0100(g[k] != null ? g[k] : 0, 0) / 100.0;
          const pct = Math.round(v01 * 100);
          const bar = "<div class=\"lyra-bar\"><div style=\"width:" + pct + "%;background:" + lyraGaugeColor(v01) + "\"></div></div>";
          const controls = interactive
            ? "<div class=\"lyra-controls\">" +
              (mode === "assistant"
                ? "<button type=\"button\" data-lyra-inc=\"" + k + "\">+5</button>" +
                  "<button type=\"button\" data-lyra-dec=\"" + k + "\">-5</button>"
                : "<button type=\"button\" data-lyra-inc=\"" + k + "\">+0.05</button>" +
                  "<button type=\"button\" data-lyra-dec=\"" + k + "\">-0.05</button>") +
              "<span class=\"muted\">" + pct + "%</span>" +
              "</div>"
            : "<div class=\"lyra-controls\"><span class=\"muted\">" + pct + "%</span></div>";
          return (
            "<div class=\"lyra-gauge\">" +
            "<div class=\"lyra-gauge-head\"><strong>" +
            escapeHtmlPm(label) +
            "</strong><span class=\"muted\">" +
            escapeHtmlPm(k) +
            "</span></div>" +
            bar +
            controls +
            "</div>"
          );
        })
        .join("");
    }

    function lyraBuildContext() {
      const st = lyraLoadState();
      const dtEl = document.getElementById("lyra-dt");
      const dt = dtEl ? Number(dtEl.value) : st.dt_s;
      st.dt_s = Number.isFinite(dt) ? dt : st.dt_s;
      // normalize needs gauges (0–100)
      Object.keys(st.gauges || {}).forEach(function (k) {
        st.gauges[k] = clamp0100(st.gauges[k], 25);
      });
      // normalize confiance (0–100)
      st.confiance_100 = clamp0100(st.confiance_100, 70);
      // normalize assistant gauges (0–100)
      if (st.assistant_gauges_100 && typeof st.assistant_gauges_100 === "object") {
        ["chaleur", "energie", "patience", "confiance"].forEach(function (k) {
          st.assistant_gauges_100[k] = clamp0100(st.assistant_gauges_100[k], 70);
        });
      }
      lyraSaveState(st);
      const mode = lyraGetMode();
      const needs01 = lyraNeedsTo01(st.gauges);
      const ctx = {
        lyra: {
          version: st.version,
          dt_s: st.dt_s,
          kind: mode === "assistant" ? "assistant" : "npc_world",
          // On garde le contrat PNJ monde en 0–1 côté backend/agents (conversion UI 0–100 → payload 0–1).
          gauges: mode === "assistant" ? st.assistant_gauges_100 : needs01,
          meta: { source: mode === "assistant" ? "pilot_assistant" : "pilot_standalone" },
        },
        history: [],
      };
      return { st, ctx };
    }

    function lyraExtractOut(resp) {
      if (!resp || typeof resp !== "object") return null;
      // Accept a few possible envelopes.
      if (resp.lyra && typeof resp.lyra === "object") return resp.lyra;
      const r = resp.result;
      if (r && typeof r === "object") {
        const o = r.output;
        if (o && typeof o === "object" && o.lyra && typeof o.lyra === "object") return o.lyra;
      }
      return null;
    }

    function lyraRegLogLoad() {
      try {
        const raw = localStorage.getItem(STORAGE_LYRA_REG_LOG_KEY);
        if (!raw) return [];
        const arr = JSON.parse(raw);
        return Array.isArray(arr) ? arr : [];
      } catch (_) {
        return [];
      }
    }

    function lyraRegLogSave(entries) {
      try { localStorage.setItem(STORAGE_LYRA_REG_LOG_KEY, JSON.stringify(Array.isArray(entries) ? entries : [])); } catch (_) {}
    }

    function lyraRegFilterLoad() {
      try {
        const v = String(localStorage.getItem(STORAGE_LYRA_REG_FILTER_KEY) || "all").toLowerCase();
        if (v === "warn" || v === "critical" || v === "all") return v;
      } catch (_) {}
      return "all";
    }

    function lyraRegFilterSave(v) {
      try {
        const x = String(v || "all").toLowerCase();
        localStorage.setItem(STORAGE_LYRA_REG_FILTER_KEY, x);
      } catch (_) {}
    }

    function lyraRegMatchesFilter(entry, filter) {
      const f = String(filter || "all").toLowerCase();
      if (f === "all") return true;
      const sev = String((entry && entry.severity) || "info").toLowerCase();
      if (f === "critical") return sev === "critical";
      if (f === "warn") return sev === "warn" || sev === "warning";
      return true;
    }

    function lyraRegLogLines(entries) {
      return entries.map(function (e) {
        const ts = e && e.ts ? String(e.ts) : "-";
        const sev = e && e.severity ? String(e.severity).toUpperCase() : "INFO";
        const mode = e && e.mode ? String(e.mode) : "lyra";
        const action = e && e.action ? String(e.action) : "none";
        const reason = e && e.reason ? String(e.reason) : "";
        const applied = e && e.applied === true ? "applique" : "skip";
        return "[" + ts + "] [" + sev + "] " + mode + " :: " + action + " (" + applied + ")" + (reason ? " - " + reason : "");
      });
    }

    function lyraRegLogRender() {
      const out = document.getElementById("lyra-reg-log");
      const hint = document.getElementById("lyra-reg-hint");
      const filterSel = document.getElementById("lyra-reg-filter");
      if (!out) return;
      const entries = lyraRegLogLoad();
      const filter = filterSel ? String(filterSel.value || "all").toLowerCase() : lyraRegFilterLoad();
      const filtered = entries.filter(function (e) { return lyraRegMatchesFilter(e, filter); });
      if (!filtered.length) {
        out.textContent = "—";
      } else {
        // Rendu lisible avec badge couleur par sévérité.
        const htmlLines = filtered.map(function (e) {
          const ts = e && e.ts ? String(e.ts) : "-";
          const sevRaw = e && e.severity ? String(e.severity) : "info";
          const sev = sevRaw.toUpperCase();
          const sevLower = sevRaw.toLowerCase();
          const mode = e && e.mode ? String(e.mode) : "lyra";
          const action = e && e.action ? String(e.action) : "none";
          const reason = e && e.reason ? String(e.reason) : "";
          const applied = e && e.applied === true ? "applique" : "skip";

          let color = "#6b7280"; // INFO / défaut
          if (sevLower === "warn" || sevLower === "warning") color = "#f97316";
          if (sevLower === "critical") color = "#dc2626";

          const badge =
            '<span style="display:inline-block;min-width:70px;padding:0 4px;border-radius:3px;font-weight:600;color:white;background:' +
            color +
            ';">' +
            escapeHtmlPm(sev) +
            "</span>";

          const main =
            "[" +
            escapeHtmlPm(ts) +
            "] " +
            badge +
            " " +
            escapeHtmlPm(mode) +
            " :: " +
            escapeHtmlPm(action) +
            " (" +
            escapeHtmlPm(applied) +
            ")" +
            (reason ? " - " + escapeHtmlPm(reason) : "");

          return main;
        });
        out.innerHTML = htmlLines.join("\n");
      }
      if (hint) hint.textContent = entries.length ? (filtered.length + "/" + entries.length + " entrées") : "0 entrée";
    }

    function lyraRegExportTxt() {
      const entries = lyraRegLogLoad();
      const filterSel = document.getElementById("lyra-reg-filter");
      const filter = filterSel ? String(filterSel.value || "all").toLowerCase() : lyraRegFilterLoad();
      const filtered = entries.filter(function (e) { return lyraRegMatchesFilter(e, filter); });
      const lines = lyraRegLogLines(filtered);
      const txt = lines.length ? lines.join("\n") + "\n" : "Journal vide.\n";
      const stamp = new Date().toISOString().replace(/[:]/g, "-");
      const blob = new Blob([txt], { type: "text/plain;charset=utf-8" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = "lyra-regulation-log-" + filter + "-" + stamp + ".txt";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(a.href);
    }

    function lyraRegLogAppend(entry) {
      if (!entry || typeof entry !== "object") return;
      const arr = lyraRegLogLoad();
      arr.unshift(entry);
      lyraRegLogSave(arr.slice(0, 30));
      lyraRegLogRender();
    }

    function lyraRenderIn() {
      const { st, ctx } = lyraBuildContext();
      const mode = lyraGetMode();
      lyraRenderGaugeBlock(
        "lyra-in-gauges",
        mode === "assistant" ? st.assistant_gauges_100 : st.gauges,
        { interactive: true, mode: mode }
      );
      // derived energy + alias stress from confiance
      const eEl = document.getElementById("lyra-in-energy");
      const cEl = document.getElementById("lyra-in-confiance");
      const sEl = document.getElementById("lyra-in-stress");
      const c = mode === "assistant" ? clamp0100(st.assistant_gauges_100.confiance, 70) : clamp0100(st.confiance_100, 70);
      const s = 100 - c;
      const e =
        mode === "assistant"
          ? clamp0100(st.assistant_gauges_100.energie, 60)
          : lyraComputeEnergy100(lyraNeedsTo01(st.gauges));
      if (eEl) eEl.textContent = String(e) + "%";
      if (cEl) cEl.textContent = String(c) + "%";
      if (sEl) sEl.textContent = String(s) + "%";
      const raw = document.getElementById("lyra-in-raw");
      if (raw) raw.textContent = JSON.stringify(ctx, null, 2);
    }

    function lyraRenderOut(resp) {
      const out = lyraExtractOut(resp);
      const raw = document.getElementById("lyra-out-raw");
      if (raw) raw.textContent = resp ? JSON.stringify(resp, null, 2) : "—";
      const metaEl = document.getElementById("lyra-out-meta");
      if (!out) {
        lyraRenderGaugeBlock("lyra-out-gauges", {}, { interactive: false, mode: lyraGetMode() });
        if (metaEl) metaEl.textContent = "—";
        const eEl = document.getElementById("lyra-out-energy");
        if (eEl) eEl.textContent = "—";
        return;
      }
      const gRaw = out.gauges && typeof out.gauges === "object" ? out.gauges : {};
      const mode = out.kind === "assistant" ? "assistant" : "world";
      const g = mode === "assistant" ? gRaw : lyraNeedsFrom01(gRaw);
      lyraRenderGaugeBlock("lyra-out-gauges", g, { interactive: false, mode: mode });
      const eEl = document.getElementById("lyra-out-energy");
      if (eEl) {
        if (mode === "assistant") eEl.textContent = String(clamp0100(gRaw.energie != null ? gRaw.energie : 0, 0)) + "%";
        else eEl.textContent = String(lyraComputeEnergy100(gRaw)) + "%";
      }
      const meta = out.meta && typeof out.meta === "object" ? out.meta : {};
      if (metaEl) metaEl.textContent = JSON.stringify(meta, null, 2);
      const reg = meta.lyra_regulation && typeof meta.lyra_regulation === "object" ? meta.lyra_regulation : null;
      if (reg) {
        lyraRegLogAppend({
          ts: new Date().toISOString(),
          mode: out.kind || "npc_world",
          action: reg.action || null,
          applied: reg.applied === true,
          reason: reg.reason || null,
          severity: reg.severity || null,
          detail: reg,
        });
      }
    }

    function lyraRenderBrainGauges(gauges) {
      const el = document.getElementById("lyra-brain-gauges");
      if (!el) return;
      const g = gauges && typeof gauges === "object" ? gauges : {};
      const items = [
        ["confidence", "Confiance"],
        ["stress", "Stress"],
        ["fatigue", "Fatigue"],
        ["curiosity", "Curiosité"],
      ];
      el.innerHTML = items
        .map(function (it) {
          const key = it[0];
          const label = it[1];
          const v = clamp0100(g[key] != null ? g[key] : 0, 0);
          const pct = Math.round(v);
          const bar = "<div class=\"lyra-bar\"><div style=\"width:" + pct + "%;background:" + lyraGaugeColor(v / 100.0) + "\"></div></div>";
          return (
            "<div class=\"lyra-gauge\">" +
            "<div class=\"lyra-gauge-head\"><strong>" + escapeHtmlPm(label) + "</strong><span class=\"muted\">" + escapeHtmlPm(key) + "</span></div>" +
            bar +
            "<div class=\"lyra-controls\"><span class=\"muted\">" + pct + "%</span></div>" +
            "</div>"
          );
        })
        .join("");
    }

    function lyraRenderBrainStatus(data) {
      const sum = document.getElementById("lyra-brain-summary");
      const raw = document.getElementById("lyra-brain-raw");
      if (raw) raw.textContent = data ? JSON.stringify(data, null, 2) : "—";
      if (!data || typeof data !== "object") {
        if (sum) sum.textContent = "—";
        lyraRenderBrainGauges({});
        return;
      }
      lyraRenderBrainGauges(data.gauges);
      if (sum) {
        const on = data.enabled === true ? "actif" : "inactif";
        const intent = data.intent ? String(data.intent) : "monitor";
        const nar = data.narrative ? String(data.narrative) : "";
        sum.innerHTML =
          "<strong>" + escapeHtmlPm(on) + "</strong>" +
          " · intent <code>" + escapeHtmlPm(intent) + "</code>" +
          (nar ? " · " + escapeHtmlPm(nar) : "");
      }
    }

    async function lyraRefreshBrain() {
      const base = getBase();
      try {
        const r = await fetch(base + "/v1/pilot/orchestrator/brain/status");
        const j = await r.json();
        if (j && j.ok === true) lyraRenderBrainStatus(j);
        else lyraRenderBrainStatus(j || null);
      } catch (e) {
        lyraRenderBrainStatus({ error: String(e) });
      }
    }

    async function lyraStepOnce() {
      lyraRenderIn();
      const base = getBase();
      const built = lyraBuildContext();
      const payload = { actor_id: "svc:pilot-lyra", text: "lyra test", context: built.ctx };
      const out = await postJson(base + "/v1/pilot/route", payload);
      if (out && out.json) {
        // best-effort: if we get gauges back, reuse them as new input
        const ly = lyraExtractOut(out.json);
        if (ly && ly.gauges && typeof ly.gauges === "object") {
          const st = lyraLoadState();
          // IMPORTANT: côté backend, `npc_world` est en 0–1 ; l'UI stocke `world` en 0–100.
          // On reconvertit donc avant de fusionner dans l'état local.
          if (ly.kind === "assistant") {
            if (!st.assistant_gauges_100) st.assistant_gauges_100 = { chaleur: 70, energie: 60, patience: 70, confiance: 70 };
            st.assistant_gauges_100 = { ...st.assistant_gauges_100, ...ly.gauges };
            // miroir confiance (utilisé pour la vue stress)
            if (ly.gauges.confiance != null) st.confiance_100 = clamp0100(ly.gauges.confiance, st.confiance_100);
          } else {
            const nextNeeds100 = lyraNeedsFrom01(ly.gauges);
            st.gauges = { ...st.gauges, ...nextNeeds100 };
          }
          lyraSaveState(st);
        }
        lyraRenderOut(out.json);
      } else {
        lyraRenderOut(null);
        const raw = document.getElementById("lyra-out-raw");
        if (raw) raw.textContent = "HTTP " + out.status + "\n" + (out.text || "");
      }
    }

    function lyraReset() {
      const st = lyraDefaultState();
      lyraSaveState(st);
      const dtEl = document.getElementById("lyra-dt");
      if (dtEl) dtEl.value = String(st.dt_s);
      const cEl = document.getElementById("lyra-confiance");
      if (cEl) cEl.value = String(st.confiance_100);
      lyraRenderIn();
    }

    function lyraApplyStressPreset() {
      const st = lyraLoadState();
      const mode = lyraGetMode();
      if (mode === "assistant") {
        st.assistant_gauges_100 = {
          ...st.assistant_gauges_100,
          chaleur: 40,
          energie: 20,
          patience: 35,
          confiance: 30,
        };
        st.confiance_100 = clamp0100(st.assistant_gauges_100.confiance, 30);
      } else {
        st.gauges = {
          ...st.gauges,
          hunger: 85,
          thirst: 70,
          fatigue: 90,
        };
      }
      lyraSaveState(st);
      const cEl = document.getElementById("lyra-confiance");
      if (cEl) cEl.value = String(st.confiance_100);
      lyraRenderIn();
    }

    function lyraSleep(ms) {
      return new Promise(function (resolve) { setTimeout(resolve, ms); });
    }

    async function lyraRunChaosLoop(steps) {
      const n = Number(steps) > 0 ? Math.min(20, Math.floor(Number(steps))) : 8;
      lyraApplyStressPreset();
      for (let i = 0; i < n; i += 1) {
        await lyraStepOnce();
        if (i < n - 1) await lyraSleep(220);
      }
    }

    function lyraBindControls() {
      const page = document.getElementById("pilot-page-lyra");
      if (!page) return;
      page.addEventListener("click", function (ev) {
        const inc = ev.target.closest("[data-lyra-inc]");
        const dec = ev.target.closest("[data-lyra-dec]");
        if (!inc && !dec) return;
        const key = (inc || dec).getAttribute(inc ? "data-lyra-inc" : "data-lyra-dec");
        if (!key) return;
        const st = lyraLoadState();
        const mode = lyraGetMode();
        if (mode === "assistant") {
          const d = inc ? 5 : -5;
          if (!st.assistant_gauges_100) st.assistant_gauges_100 = { chaleur: 70, energie: 60, patience: 70, confiance: 70 };
          st.assistant_gauges_100[key] = clamp0100((st.assistant_gauges_100[key] != null ? st.assistant_gauges_100[key] : 0) + d, 70);
          if (key === "confiance") {
            st.confiance_100 = st.assistant_gauges_100.confiance;
            const cEl = document.getElementById("lyra-confiance");
            if (cEl) cEl.value = String(st.confiance_100);
          }
        } else {
          const d = inc ? 5 : -5;
          st.gauges[key] = clamp0100((st.gauges[key] != null ? st.gauges[key] : 0) + d, 25);
        }
        lyraSaveState(st);
        lyraRenderIn();
      });
    }

    function renderPmCards(resp) {
      const ms = document.getElementById("pm-milestones");
      const ts = document.getElementById("pm-tasks");
      const raw = document.getElementById("pm-raw");
      if (raw) raw.textContent = JSON.stringify(resp, null, 2);
      const brief = pmExtractBrief(resp);
      window.__pm_last_brief = brief && typeof brief === "object" ? brief : null;
      renderPmEncarts(brief);
      const mlist = brief && Array.isArray(brief.milestones) ? brief.milestones : [];
      const tlist = brief && Array.isArray(brief.tasks) ? brief.tasks : [];
      if (ms) {
        ms.innerHTML = mlist.length
          ? mlist
              .map(function (m) {
                const d = escapeHtmlPm((m && m.date) || "");
                const body = pmRichFormat((m && m.summary) || "");
                return "<li><strong>" + d + "</strong> — " + body + "</li>";
              })
              .join("")
          : "<li class=\"muted\">(aucun jalon — plan absent sur la VM, ou réponse sans <code>result.output.brief</code>)</li>";
      }
      if (ts) {
        ts.innerHTML = tlist.length
          ? tlist
              .map(function (t) {
                const ti = pmRichFormat((t && t.title) || "");
                const sr = escapeHtmlPm((t && t.source) || "");
                return "<li>" + ti + " <span class=\"src\">(" + sr + ")</span></li>";
              })
              .join("")
          : "<li class=\"muted\">(aucune tâche)</li>";
      }
    }

    async function pilotPmSend() {
      const base = getBase();
      let text = (document.getElementById("pm-text") && document.getElementById("pm-text").value) || "";
      text = text.trim();
      if (!text) text = "jalons et tâches du plan de route";
      let ctx;
      try {
        ctx = JSON.parse((document.getElementById("pm-context") && document.getElementById("pm-context").value) || "{}");
      } catch (e) {
        pilotInlineHint("pm-route-hint", "JSON contexte invalide", true);
        return;
      }
      pilotInlineHint("pm-route-hint", "…", false);
      const payload = { actor_id: "svc:pilot-pm", text: text, context: ctx };
      const out = await postJson(base + "/v1/pilot/route", payload);
      if (out.json) {
        renderPmCards(out.json);
        pilotInlineHint("pm-route-hint", "OK", false);
      } else {
        const rawEl = document.getElementById("pm-raw");
        if (rawEl) rawEl.textContent = "HTTP " + out.status + "\n" + (out.text || "");
        window.__pm_last_brief = null;
        renderPmEncarts(null);
        const ms = document.getElementById("pm-milestones");
        const ts = document.getElementById("pm-tasks");
        if (ms) ms.innerHTML = "<li class=\"muted\">—</li>";
        if (ts) ts.innerHTML = "<li class=\"muted\">—</li>";
        pilotInlineHint("pm-route-hint", "HTTP " + out.status, true);
      }
    }

    async function pilotPmHealth() {
      const base = getBase();
      pilotInlineHint("pm-health-hint", "…", false);
      try {
        const r = await fetch(base + "/v1/pilot/agent-pm/healthz");
        const t = await r.text();
        pilotInlineHint("pm-health-hint", "HTTP " + r.status + " " + t.slice(0, 160), r.status !== 200);
      } catch (e) {
        pilotInlineHint("pm-health-hint", "Erreur : " + e, true);
      }
    }

    const LBG_PILOT_MMO_SUMMARY_KEY = "lbg_pilot_mmo_session_summary_json";
    const LBG_PILOT_DESKTOP_NOTEPAD_DEFAULT = "C:\\\\Users\\\\Public\\\\lbg_desktop.txt";
    const LBG_PILOT_DESKTOP_DRY_RUN_KEY = "lbg_pilot_desktop_dry_run_v1";
    const LBG_PILOT_DESKTOP_PIPELINE_KEY = "lbg_pilot_desktop_pipeline_v1";

    function pilotDesktopDefaultPipelinePrefs() {
      return { auto_simulate: true, auto_real: true, exec_real: false };
    }

    function pilotDesktopLoadPipelinePrefs() {
      const d = pilotDesktopDefaultPipelinePrefs();
      try {
        const raw = localStorage.getItem(LBG_PILOT_DESKTOP_PIPELINE_KEY);
        if (!raw) return d;
        const o = JSON.parse(raw);
        if (!o || typeof o !== "object") return d;
        return {
          auto_simulate: o.auto_simulate !== false,
          auto_real: o.auto_real !== false,
          exec_real: o.exec_real === true,
        };
      } catch (_) {
        return d;
      }
    }

    function pilotDesktopReadPipelinePrefsFromUi() {
      const sim = document.getElementById("desktop-pipeline-auto-sim");
      const ar = document.getElementById("desktop-pipeline-auto-real");
      const rt = document.getElementById("desktop-pipeline-real-toggle");
      return {
        auto_simulate: !(sim && sim.checked === false),
        auto_real: !(ar && ar.checked === false),
        exec_real: !!(rt && rt.checked),
      };
    }

    function pilotDesktopApplyPipelinePrefsToUi() {
      const p = pilotDesktopLoadPipelinePrefs();
      const sim = document.getElementById("desktop-pipeline-auto-sim");
      const ar = document.getElementById("desktop-pipeline-auto-real");
      const rt = document.getElementById("desktop-pipeline-real-toggle");
      if (sim) sim.checked = p.auto_simulate !== false;
      if (ar) ar.checked = p.auto_real !== false;
      if (rt) rt.checked = p.exec_real === true;
    }

    function pilotDesktopPersistPipelinePrefs() {
      try {
        const p = pilotDesktopReadPipelinePrefsFromUi();
        localStorage.setItem(LBG_PILOT_DESKTOP_PIPELINE_KEY, JSON.stringify(p));
      } catch (_) {}
    }

    function pilotDesktopBindPipelinePrefs() {
      function bind(el) {
        if (!el || el.dataset.lbgPipe) return;
        el.dataset.lbgPipe = "1";
        el.addEventListener("change", pilotDesktopPersistPipelinePrefs);
      }
      bind(document.getElementById("desktop-pipeline-auto-sim"));
      bind(document.getElementById("desktop-pipeline-auto-real"));
      bind(document.getElementById("desktop-pipeline-real-toggle"));
    }

    function pilotDesktopRoutePayloadLooksSuccessful(routePayload) {
      if (!routePayload || routePayload.ok === false) return false;
      const out = routePayload.result && routePayload.result.output;
      if (!out) return false;
      if (out.ok === false) return false;
      const pol = out.policy;
      if (pol && pol.allowed === false) return false;
      return true;
    }

    function pilotDesktopMergeProposalIntoUi(proposal) {
      if (!proposal || typeof proposal !== "object") return;
      const aEl = document.getElementById("desktop-action");
      const cEl = document.getElementById("desktop-context");
      let ctx = {};
      try {
        ctx = JSON.parse((cEl && cEl.value) || "{}");
      } catch (_) {
        ctx = {};
      }
      if (!ctx || typeof ctx !== "object") ctx = {};
      delete ctx.desktop_action;
      delete ctx.devops_action;
      delete ctx.opengame_action;
      const patch = proposal.context_patch && typeof proposal.context_patch === "object" ? proposal.context_patch : {};
      ctx = { ...ctx, ...patch };
      if (proposal.capability === "desktop_control" && proposal.action && typeof proposal.action === "object" && aEl) {
        aEl.value = JSON.stringify(proposal.action, null, 2);
      } else if (aEl) {
        aEl.value = "{}";
      }
      if (cEl) cEl.value = JSON.stringify(ctx, null, 2);
    }

    function pilotDesktopUiHint(msg, isError) {
      pilotInlineHint("desktop-hint", msg, isError);
    }

    async function pilotDesktopPostRouteWithOptions(opts) {
      opts = opts || {};
      const base = getBase();
      const rawEl = document.getElementById("desktop-raw");
      const prettyEl = document.getElementById("desktop-pretty");
      const forceDry = opts.forceDry === true;
      const forceReal = opts.forceReal === true;

      let text = (document.getElementById("desktop-text") && document.getElementById("desktop-text").value) || "";
      text = String(text || "").trim();
      if (!text) text = "desktop action";

      let action;
      try {
        action = JSON.parse((document.getElementById("desktop-action") && document.getElementById("desktop-action").value) || "{}");
      } catch (_) {
        pilotDesktopUiHint("desktop_action JSON invalide", true);
        return { status: 0, json: null };
      }
      if (!action || typeof action !== "object") {
        pilotDesktopUiHint("desktop_action doit être un objet JSON", true);
        return { status: 0, json: null };
      }

      let ctx;
      try {
        ctx = JSON.parse((document.getElementById("desktop-context") && document.getElementById("desktop-context").value) || "{}");
      } catch (_) {
        pilotDesktopUiHint("context JSON invalide", true);
        return { status: 0, json: null };
      }
      if (!ctx || typeof ctx !== "object") ctx = {};

      try {
        const ap = document.getElementById("desktop-approval");
        const v = ap && ap.value ? String(ap.value || "").trim() : "";
        if (!forceDry && v) {
          if (!ctx.desktop_approval) ctx.desktop_approval = v;
          if (!ctx.devops_approval) ctx.devops_approval = v;
          if (!ctx.opengame_approval) ctx.opengame_approval = v;
        }
      } catch (_) {}

      const actionKind = typeof action.kind === "string" ? action.kind.trim() : "";

      if (forceDry) {
        ctx.desktop_dry_run = true;
        ctx.devops_dry_run = true;
        ctx.opengame_dry_run = true;
        delete ctx.desktop_approval;
        delete ctx.devops_approval;
        delete ctx.opengame_approval;
      } else if (forceReal) {
        delete ctx.desktop_dry_run;
        delete ctx.devops_dry_run;
        ctx.opengame_dry_run = false;
      } else {
        pilotDesktopApplyDryRunToContext(ctx);
      }

      pilotDesktopMergeMmoSummaryIntoContext(ctx);

      if (actionKind) {
        ctx.desktop_action = action;
      }

      const payload = { actor_id: "ui:desktop", text: text, context: ctx };
      const out = await postJson(base + "/v1/pilot/route", payload);
      if (rawEl) {
        rawEl.textContent = out.json ? JSON.stringify(out.json, null, 2) : "HTTP " + out.status + "\n" + (out.text || "");
      }
      if (prettyEl) {
        try {
          prettyEl.innerHTML = out.json ? renderPretty(out.json) : "";
        } catch (_) {
          prettyEl.innerHTML = "";
        }
      }
      const ok = out.status === 200 && pilotDesktopRoutePayloadLooksSuccessful(out.json);
      pilotDesktopUiHint(
        out.status !== 200 ? "HTTP " + out.status : ok ? "OK" : "Refus ou erreur (voir JSON)",
        out.status !== 200 || !ok
      );
      return { status: out.status, json: out.json };
    }

    function pilotDesktopApplyDryRunToContext(ctx) {
      if (!ctx || typeof ctx !== "object") return;
      const el = document.getElementById("desktop-dry-run-toggle");
      if (el && el.checked) ctx.desktop_dry_run = true;
    }

    function pilotDesktopLoadDryRunToggleFromStorage() {
      try {
        const el = document.getElementById("desktop-dry-run-toggle");
        if (!el) return;
        const v = localStorage.getItem(LBG_PILOT_DESKTOP_DRY_RUN_KEY);
        if (v === "0") el.checked = false;
        else if (v === "1") el.checked = true;
      } catch (_) {}
    }

    function pilotDesktopBindDryRunTogglePersist() {
      const el = document.getElementById("desktop-dry-run-toggle");
      if (!el || el.dataset.lbgBound) return;
      el.dataset.lbgBound = "1";
      el.addEventListener("change", function () {
        try {
          localStorage.setItem(LBG_PILOT_DESKTOP_DRY_RUN_KEY, el.checked ? "1" : "0");
        } catch (_) {}
      });
    }

    let pilotDesktopRecog = null;

    function pilotDesktopSetupSpeech() {
      const dh = document.getElementById("desktop-dictation-hint");
      const dta = document.getElementById("desktop-dictation");
      const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SR) {
        if (dh) dh.textContent = "SpeechRecognition indisponible.";
        return;
      }
      const start = document.getElementById("btn-desktop-dictation-start");
      const stop = document.getElementById("btn-desktop-dictation-stop");
      const apply = document.getElementById("btn-desktop-dictation-apply");
      if (start)
        start.addEventListener("click", function () {
          try {
            if (pilotDesktopRecog) pilotDesktopRecog.stop();
          } catch (_) {}
          pilotDesktopRecog = new SR();
          pilotDesktopRecog.lang = "fr-FR";
          pilotDesktopRecog.continuous = true;
          pilotDesktopRecog.interimResults = false;
          pilotDesktopRecog.onresult = function (ev) {
            if (!dta) return;
            for (let i = ev.resultIndex; i < ev.results.length; i++) {
              if (!ev.results[i].isFinal) continue;
              const piece = String(ev.results[i][0].transcript || "").trim();
              if (!piece) continue;
              const sep = dta.value && !/[ \n]$/.test(dta.value) ? " " : "";
              dta.value = (dta.value || "") + sep + piece;
            }
          };
          pilotDesktopRecog.onerror = function (e) {
            const code = e && e.error ? String(e.error) : "?";
            const map = {
              "not-allowed": "Permission micro refusée (paramètres du navigateur).",
              "service-not-allowed": "Contexte non autorisé (HTTPS ou localhost requis).",
              "no-speech": "Pas de voix détectée.",
              "audio-capture": "Micro indisponible.",
              "network": "Erreur réseau du service de reconnaissance.",
            };
            const human = map[code] || code;
            if (dh) dh.textContent = "Reconnaissance : " + human;
          };
          pilotDesktopRecog.onend = function () {
            pilotDesktopRecog = null;
          };
          try {
            pilotDesktopRecog.start();
            if (dh) dh.textContent = "Écoute…";
          } catch (err) {
            if (dh) dh.textContent = "Démarr.err : " + err;
          }
        });
      if (stop)
        stop.addEventListener("click", function () {
          try {
            if (pilotDesktopRecog) pilotDesktopRecog.stop();
          } catch (_) {}
          pilotDesktopRecog = null;
          if (dh) dh.textContent = "Arrêt.";
        });
      if (apply)
        apply.addEventListener("click", function () {
          const raw = dta ? String(dta.value || "").trim() : "";
          if (!raw) {
            if (dh) dh.textContent = "Dictée vide.";
            return;
          }
          const aEl = document.getElementById("desktop-action");
          const tEl = document.getElementById("desktop-text");
          let path = LBG_PILOT_DESKTOP_NOTEPAD_DEFAULT;
          try {
            const cur = aEl && aEl.value ? JSON.parse(aEl.value) : null;
            if (cur && cur.kind === "notepad_append" && typeof cur.path === "string" && cur.path.trim())
              path = cur.path.trim();
          } catch (_) {}
          const textLine = raw.endsWith("\n") ? raw : raw + "\n";
          const action = { kind: "notepad_append", path: path, text: textLine };
          if (aEl) aEl.value = JSON.stringify(action, null, 2);
          if (tEl) tEl.value = "notepad_append : " + raw.slice(0, 200);
          try {
            desktopTrySyncActionFromText();
          } catch (_) {}
          if (dh) dh.textContent = "Action notepad_append mise à jour.";
        });
    }

    function pilotDesktopMergeMmoSummaryIntoContext(ctx) {
      if (!ctx || typeof ctx !== "object") return;
      const ta = document.getElementById("desktop-mmo-summary");
      const raw = ta && ta.value ? String(ta.value).trim() : "";
      try {
        if (raw) {
          const o = JSON.parse(raw);
          if (o && typeof o === "object" && !Array.isArray(o)) {
            ctx.session_summary = o;
          }
        }
      } catch (e) {
        console.warn("session_summary JSON invalide (desktop)", e);
      }
      try {
        if (ta) localStorage.setItem(LBG_PILOT_MMO_SUMMARY_KEY, ta.value || "");
      } catch (_) {}
    }

    /** Accueil → Desktop : préremplit open_app Godot / Launchpad (chemins PC Teome / J:). */
    function pilotDesktopApplyHomeLaunchPreset() {
      const launch = String((pilotHashQuery().get("launch") || "")).trim().toLowerCase();
      if (!launch) return;
      const a = document.getElementById("desktop-action");
      const t = document.getElementById("desktop-text");
      const hint = document.getElementById("desktop-hint");
      let action = null;
      let text = "";
      if (launch === "godot" || launch === "prime") {
        action = {
          kind: "open_app",
          app: "godot_prime",
          exe: "J:\\mmmorpg\\Godot_v4.6.1-stable_win64\\Godot_v4.6.1-stable_win64.exe",
          args: ["--path", "J:\\swgemu\\clients\\prime-client"],
          learn: true,
        };
        text = "lance Godot Prime Client (prime-client → 246)";
      } else if (launch === "launchpad" || launch === "lp") {
        action = {
          kind: "open_app",
          app: "lbg_launchpad",
          exe: "J:\\swgemu\\dist\\win-unpacked\\LBG Launchpad.exe",
          args: [],
          learn: true,
        };
        text = "lance LBG Launchpad (profil Prime / Godot)";
      } else {
        return;
      }
      if (a) a.value = JSON.stringify(action, null, 2);
      if (t) t.value = text;
      if (hint) {
        hint.textContent =
          "Preset Accueil « " +
          launch +
          " » — vérifier dry-run / approval, puis Envoyer. Chemins J: = PC Windows.";
      }
      try {
        desktopTrySyncTextFromAction();
      } catch (_) {}
    }

    function pilotDesktopLoadMmoSummaryFromStorage() {
      try {
        const ta = document.getElementById("desktop-mmo-summary");
        if (!ta || (ta.value && String(ta.value).trim())) return;
        const v = localStorage.getItem(LBG_PILOT_MMO_SUMMARY_KEY);
        if (v) ta.value = v;
      } catch (_) {}
    }

    async function pilotDesktopRefreshConfigHint() {
      const el = document.getElementById("desktop-config-hint");
      if (!el) return;
      const base = getBase();
      el.textContent = "Santé dialogue…";
      try {
        const r = await fetch(base + "/v1/pilot/status");
        const t = await r.text();
        let j = null;
        try { j = t ? JSON.parse(t) : null; } catch (_) {}
        if (!j || typeof j !== "object") {
          el.textContent = "Statut pilot indisponible (HTTP " + r.status + ").";
          return;
        }
        const st = j.agent_dialogue;
        const info = j.agent_dialogue_info;
        const dpe = info && typeof info.desktop_plan_env_enabled === "boolean" ? info.desktop_plan_env_enabled : null;
        const llm = info && typeof info.llm_configured === "boolean" ? info.llm_configured : null;
        if (st === "skipped") {
          el.textContent =
            "Dialogue : non configuré côté backend (LBG_AGENT_DIALOGUE_URL). « Proposer via IA » ne fonctionnera pas.";
          return;
        }
        if (st !== "ok") {
          el.textContent = "Dialogue : état « " + String(st || "?") + " » — vérifier l’agent (8020) et " + (j.agent_dialogue_detail || "réseau") + ".";
          return;
        }
        const parts = [];
        if (llm === false) parts.push("LLM non configuré sur l’agent (LBG_DIALOGUE_LLM_BASE_URL)");
        if (dpe === false) parts.push("Mode DESKTOP_JSON désactivé sur l’agent (LBG_DIALOGUE_DESKTOP_PLAN=1 requis pour les propositions structur.)");
        if (!parts.length) {
          el.textContent = "Dialogue : OK — LLM + plan desktop (env) actifs côté agent.";
        } else {
          el.textContent = "Dialogue : reachable mais — " + parts.join(" ; ") + ".";
        }
      } catch (e) {
        el.textContent = "Statut pilot : " + e;
      }
    }

    async function pilotDesktopProposeLlm() {
      const base = getBase();
      const rawEl = document.getElementById("desktop-raw");
      const prettyEl = document.getElementById("desktop-pretty");
      const aEl = document.getElementById("desktop-action");
      pilotDesktopUiHint("…", false);

      let text = (document.getElementById("desktop-text") && document.getElementById("desktop-text").value) || "";
      text = String(text || "").trim();
      if (!text) text = "Proposition d’action desktop";

      let ctx;
      try {
        ctx = JSON.parse((document.getElementById("desktop-context") && document.getElementById("desktop-context").value) || "{}");
      } catch (_) {
        pilotDesktopUiHint("context JSON invalide", true);
        return;
      }
      if (!ctx || typeof ctx !== "object") ctx = {};
      ctx._desktop_plan = true;
      if (!ctx.npc_name && !ctx.speaker) ctx.npc_name = "Assistant desktop";
      pilotDesktopMergeMmoSummaryIntoContext(ctx);
      pilotDesktopApplyDryRunToContext(ctx);

      const payload = { actor_id: "ui:desktop_llm", text: text, context: ctx };
      const out = await postJson(base + "/v1/pilot/agent-dialogue/invoke", payload);
      if (rawEl) rawEl.textContent = out.json ? JSON.stringify(out.json, null, 2) : ("HTTP " + out.status + "\n" + (out.text || ""));
      if (prettyEl) {
        try { prettyEl.innerHTML = out.json ? renderPretty(out.json) : ""; } catch (_) { prettyEl.innerHTML = ""; }
      }
      if (out.status !== 200) {
        pilotDesktopUiHint("invoke → HTTP " + out.status, true);
        return;
      }
      const prop =
        out.json && out.json.meta && typeof out.json.meta === "object"
          ? out.json.meta.desktop_action_proposal
          : null;
      if (prop && typeof prop === "object" && aEl) {
        aEl.value = JSON.stringify(prop, null, 2);
        try { desktopTrySyncTextFromAction(); } catch (_) {}
        pilotDesktopUiHint("OK — JSON proposé (relire puis Envoyer)", false);
      } else {
        const inferred = pilotDesktopInferActionFromText(text);
        if (inferred && aEl) {
          aEl.value = JSON.stringify(inferred, null, 2);
          try { desktopTrySyncTextFromAction(); } catch (_) {}
          pilotDesktopUiHint("LLM sans proposition valide — action déduite du texte (relire puis Envoyer)", false);
        } else {
          pilotDesktopUiHint("OK — pas de DESKTOP_JSON ni déduction possible (voir réponse brute)", false);
        }
      }
    }

    function pilotDesktopInferFromTextOnly() {
      const tEl = document.getElementById("desktop-text");
      const aEl = document.getElementById("desktop-action");
      const text = String((tEl && tEl.value) || "").trim();
      pilotDesktopUiHint("…", false);
      if (!text) {
        pilotDesktopUiHint("Texte vide — saisir une intention ou une URL", true);
        return;
      }
      const inferred = pilotDesktopInferActionFromText(text);
      if (!inferred || !aEl) {
        pilotDesktopUiHint("Impossible de déduire open_app / open_url à partir de ce texte", true);
        return;
      }
      aEl.value = JSON.stringify(inferred, null, 2);
      try { desktopTrySyncTextFromAction(); } catch (_) {}
      pilotDesktopUiHint("Action déduite — relire puis Envoyer", false);
    }

    async function pilotDesktopProposeBackend() {
      const base = getBase();
      pilotDesktopUiHint("…", false);
      let textRaw = String(
        ((document.getElementById("desktop-text") && document.getElementById("desktop-text").value) || "").trim()
      );
      if (!textRaw) {
        pilotDesktopUiHint("Texte vide — décrivez l’action souhaitée", true);
        return;
      }

      let ctx;
      try {
        ctx = JSON.parse((document.getElementById("desktop-context") && document.getElementById("desktop-context").value) || "{}");
      } catch (_) {
        pilotDesktopUiHint("context JSON invalide", true);
        return;
      }
      if (!ctx || typeof ctx !== "object") ctx = {};
      pilotDesktopMergeMmoSummaryIntoContext(ctx);

      try {
        const aprefs = assistantLoadPrefs();
        const np = aprefs && typeof aprefs.notepad_path === "string" ? aprefs.notepad_path.trim() : "";
        const cur = typeof ctx.desktop_default_notepad_path === "string" ? ctx.desktop_default_notepad_path.trim() : "";
        if (np && !cur) ctx.desktop_default_notepad_path = np;
      } catch (_) {}

      const rawEl = document.getElementById("desktop-raw");
      const prettyEl = document.getElementById("desktop-pretty");

      const out = await postJson(base + "/v1/pilot/action-proposal", {
        actor_id: "ui:desktop_backend",
        text: textRaw,
        context: ctx,
      });

      if (rawEl) {
        rawEl.textContent = out.json ? JSON.stringify(out.json, null, 2) : "HTTP " + out.status + "\n" + (out.text || "");
      }
      if (prettyEl) {
        try {
          prettyEl.innerHTML = out.json ? renderPretty(out.json) : "";
        } catch (_) {
          prettyEl.innerHTML = "";
        }
      }

      if (out.status !== 200 || !out.json || out.json.ok === false) {
        pilotDesktopUiHint("Action-proposal indisponible (HTTP ou proxy)", true);
        return;
      }
      const proposal = out.json.proposal;
      if (!proposal || typeof proposal !== "object") {
        pilotDesktopUiHint(out.json.reason || "Aucune proposition backend", false);
        return;
      }
      pilotDesktopMergeProposalIntoUi(proposal);

      const pp = pilotDesktopReadPipelinePrefsFromUi();
      if (pp.auto_simulate !== false) {
        const sim = await pilotDesktopPostRouteWithOptions({ forceDry: true });
        const okSim = pilotDesktopRoutePayloadLooksSuccessful(sim.json);
        if (pp.auto_real !== false && pp.exec_real && okSim) {
          await pilotDesktopPostRouteWithOptions({ forceReal: true });
        } else if (!okSim) {
          pilotDesktopUiHint("Simulation échouée — voir JSON (policy, erreur agent, worker…).", true);
        }
      } else {
        pilotDesktopUiHint("Proposition appliquée — lancez Envoyer ou activez simulation auto ci-dessus.", false);
      }
    }

    async function pilotDesktopSend() {
      pilotDesktopUiHint("…", false);
      await pilotDesktopPostRouteWithOptions({});
    }

    // Desktop UI helpers: garder `desktop_action` en phase avec le texte (évite la double saisie).
    function _extractFirstHttpUrl(s) {
      const m = String(s || "").match(/https?:\/\/[^\s<>"']+/i);
      return m ? m[0] : "";
    }

    /**
     * Heuristique locale : même intention que DESKTOP_JSON open_app / open_url pour les formulations courantes,
     * lorsque le dialogue LLM ne renvoie pas meta.desktop_action_proposal.
     */
    function pilotDesktopInferActionFromText(rawText) {
      const text = String(rawText || "").trim();
      if (!text) return null;
      const learn = /\(\s*learn\s*\)|\blearn\b/i.test(text);
      const wantsOpenVerb = /\b(ouvre|ouvrir|ouvrez|open|lance|lancer|lances|d[ée]marre|demarrer|start)\b/i.test(text);
      const mentionsAppWord = /\b(?:l['']|d[''])?(?:application|appli)\b/i.test(text);

      const url = _extractFirstHttpUrl(text);
      if (url && wantsOpenVerb) {
        if (!mentionsAppWord) {
          return { kind: "open_url", url: url };
        }
        const beforeUrl = text.slice(0, text.indexOf(url));
        if (!/\b(?:l['']|d[''])?(?:application|appli)\b/i.test(beforeUrl)) {
          return { kind: "open_url", url: url };
        }
      }

      let appId = null;
      let m = text.match(/\b(?:l['']|d[''])?(?:application|appli)\s+([A-Za-z0-9_.-]+)\b/i);
      if (m) appId = m[1];
      if (!appId) {
        m = text.match(
          /\b(?:ouvre|ouvrir|ouvrez|open|lance|lancer|d[ée]marre|demarrer|start)\s+(?:l['']|d[''])?(?:application|appli)\s+([A-Za-z0-9_.-]+)\b/i
        );
        if (m) appId = m[1];
      }
      if (!appId) {
        m = text.match(/\bopen\s+app\s+([A-Za-z0-9_.-]+)\b/i);
        if (m) appId = m[1];
      }
      if (appId) {
        const act = { kind: "open_app", app: appId, args: [] };
        if (learn) act.learn = true;
        return act;
      }

      if (url && wantsOpenVerb) {
        return { kind: "open_url", url: url };
      }
      return null;
    }

    function desktopTrySyncActionFromText() {
      const tEl = document.getElementById("desktop-text");
      const aEl = document.getElementById("desktop-action");
      if (!tEl || !aEl) return;
      const text = String(tEl.value || "");
      let act;
      try {
        act = JSON.parse(aEl.value || "{}");
      } catch (_) {
        return;
      }
      if (!act || typeof act !== "object") return;
      const kind = String(act.kind || "").trim();

      if (kind === "open_url") {
        const u = _extractFirstHttpUrl(text);
        if (u && act.url !== u) {
          act.url = u;
          aEl.value = JSON.stringify(act, null, 2);
        }
      } else if (kind === "open_app") {
        const inferred = pilotDesktopInferActionFromText(text);
        if (inferred && inferred.kind === "open_app" && inferred.app) {
          const learnNext = inferred.learn === true;
          if (act.app !== inferred.app || Boolean(act.learn) !== learnNext) {
            act.app = inferred.app;
            if (learnNext) act.learn = true;
            else delete act.learn;
            aEl.value = JSON.stringify(act, null, 2);
          }
        }
      } else if (kind === "notepad_append") {
        // On évite de réécrire `path`; on sync uniquement le contenu si l’utilisateur tape du texte libre.
        // Heuristique : si le texte ne ressemble pas à une commande, le mettre comme contenu.
        if (text && !/^\s*(ouvre|open)\b/i.test(text)) {
          if (act.text !== text) {
            act.text = text;
            aEl.value = JSON.stringify(act, null, 2);
          }
        }
      }
    }

    function desktopTrySyncTextFromAction() {
      const tEl = document.getElementById("desktop-text");
      const aEl = document.getElementById("desktop-action");
      if (!tEl || !aEl) return;
      let act;
      try {
        act = JSON.parse(aEl.value || "{}");
      } catch (_) {
        return;
      }
      if (!act || typeof act !== "object") return;
      const kind = String(act.kind || "").trim();
      if (kind === "open_url" && typeof act.url === "string" && act.url.trim()) {
        const want = "ouvre " + act.url.trim() + " dans le navigateur";
        if (String(tEl.value || "").trim() !== want) tEl.value = want;
      } else if (kind === "search_web_open" && typeof act.query === "string" && act.query.trim()) {
        const want = "recherche web : " + act.query.trim();
        if (String(tEl.value || "").trim() !== want) tEl.value = want;
      } else if (kind === "mail_imap_preview") {
        const parts = [];
        if (typeof act.from_contains === "string" && act.from_contains.trim())
          parts.push("expéditeur contient « " + act.from_contains.trim() + " »");
        if (typeof act.subject_contains === "string" && act.subject_contains.trim())
          parts.push("sujet contient « " + act.subject_contains.trim() + " »");
        const want =
          parts.length > 0 ? "aperçu mails IMAP (" + parts.join(" ; ") + ")" : "aperçu mails IMAP (INBOX)";
        if (String(tEl.value || "").trim() !== want) tEl.value = want;
      } else if (kind === "open_app" && typeof act.app === "string" && act.app.trim()) {
        const suffix = act.learn === true ? " (learn)" : "";
        const want = "ouvre l'application " + act.app.trim() + suffix;
        if (String(tEl.value || "").trim() !== want) tEl.value = want;
      }
    }

    async function pilotDesktopHealth() {
      const base = getBase();
      pilotDesktopUiHint("…", false);
      try {
        const r = await fetch(base + "/v1/pilot/agent-desktop/healthz");
        const t = await r.text();
        pilotDesktopUiHint("healthz → HTTP " + r.status + " " + t.slice(0, 160), r.status !== 200);
      } catch (e) {
        pilotDesktopUiHint("Erreur : " + e, true);
      }
    }

    if (!location.hash || location.hash === "#") {
      try {
        history.replaceState(null, "", "#/");
      } catch (_) {
        location.hash = "#/";
      }
    }
    window.addEventListener("hashchange", pilotApplyRoute);

    // --------------------------
    // WS test client (minimal)
    // --------------------------
    let __ws = null;
    const __wsMsgs = new Map(); // trace_id -> { text, status }
    const __WS_PLACEHOLDER = "…un instant.";

    function wsLog(line) {
      const el = document.getElementById("ws-out");
      if (!el) return;
      const now = new Date().toISOString().slice(11, 19);
      const prev = el.textContent === "—" ? "" : el.textContent;
      el.textContent = (prev ? (prev + "\n") : "") + "[" + now + "] " + line;
      // limiter taille
      if (el.textContent.length > 20000) {
        el.textContent = el.textContent.slice(el.textContent.length - 20000);
      }
    }

    function wsRenderThreads() {
      const rows = [];
      for (const [tid, v] of __wsMsgs.entries()) {
        rows.push({ tid, ...v });
      }
      rows.sort((a, b) => (a.tid < b.tid ? -1 : 1));
      if (!rows.length) {
        wsLog("threads: (vide)");
        return;
      }
      wsLog("threads: " + rows.map((r) => r.tid + ":" + r.status).join(" | "));
    }

    async function wsSnapshot(npcId, traceId, label) {
      const base = document.getElementById("ws-internal-http").value.trim().replace(/\/$/, "");
      if (!base) return null;
      const token = getServiceToken();
      const headers = {};
      if (token) headers["X-LBG-Service-Token"] = token;
      const url = base + "/internal/v1/npc/" + encodeURIComponent(npcId) + "/lyra-snapshot?trace_id=" + encodeURIComponent(traceId || "");
      try {
        const r = await fetch(url, { headers });
        const t = await r.text();
        let j = null;
        try { j = t ? JSON.parse(t) : null; } catch (_) {}
        if (r.status !== 200) {
          wsLog(label + " snapshot HTTP " + r.status + ": " + t.slice(0, 200));
          return null;
        }
        wsLog(label + " snapshot ok");
        return j;
      } catch (e) {
        wsLog(label + " snapshot error: " + e);
        return null;
      }
    }

    function wsConnect() {
      const url = document.getElementById("ws-url").value.trim();
      if (!url) { wsLog("WS URL vide"); return; }
      if (__ws) { try { __ws.close(); } catch (_) {} __ws = null; }
      wsLog("connect " + url);
      const ws = new WebSocket(url);
      __ws = ws;
      ws.addEventListener("open", () => wsLog("open"));
      ws.addEventListener("close", () => wsLog("close"));
      ws.addEventListener("error", () => wsLog("error"));
      ws.addEventListener("message", (ev) => {
        let msg = null;
        try { msg = JSON.parse(String(ev.data || "")); } catch (_) {}
        if (!msg || typeof msg !== "object") return;
        if (msg.type === "error") {
          wsLog("server error: " + (msg.message || JSON.stringify(msg)));
          return;
        }
        if (msg.type === "welcome") {
          wsLog("welcome player_id=" + msg.player_id);
          return;
        }
        if (msg.type === "world_tick") {
          const rep = typeof msg.npc_reply === "string" ? msg.npc_reply.trim() : "";
          const tid = typeof msg.trace_id === "string" ? msg.trace_id.trim() : "";
          if (rep && tid) {
            const isPlaceholder = rep.startsWith(__WS_PLACEHOLDER);
            const prev = __wsMsgs.get(tid);
            const status = isPlaceholder ? "placeholder" : "final";
            __wsMsgs.set(tid, { text: rep, status });
            if (prev && prev.status === "placeholder" && status === "final") {
              wsLog("replace placeholder -> final (trace_id=" + tid + ")");
            } else {
              wsLog("npc_reply (" + status + ", trace_id=" + tid + "): " + rep);
            }
            wsRenderThreads();
          }
          return;
        }
      });
    }

    function wsDisconnect() {
      if (!__ws) { wsLog("pas connecté"); return; }
      wsLog("disconnect");
      try { __ws.close(); } catch (_) {}
      __ws = null;
    }

    async function wsSendHello() {
      if (!__ws) { wsLog("pas connecté"); return; }
      const npcId = document.getElementById("ws-npc-id").value.trim() || "npc:merchant";
      const npcName = document.getElementById("ws-npc-name").value.trim() || "PNJ";
      const text = document.getElementById("ws-text").value.trim() || "(…)";
      const reqAction = document.getElementById("ws-require-action").checked;
      const noCache = document.getElementById("ws-no-cache").checked;
      const iaContext = {};
      if (reqAction) iaContext._require_action_json = true;
      if (noCache) iaContext._no_cache = true;

      // best-effort snapshot avant (trace_id vide => snapshot sans corrélation utile, mais lisible)
      try { await wsSnapshot(npcId, "ws_before", "avant"); } catch (_) {}

      const payload = {
        type: "hello",
        player_name: "pilot_web",
        world_npc_id: npcId,
        npc_name: npcName,
        text,
        ia_context: iaContext,
      };
      wsLog("send hello npc=" + npcId);
      try { __ws.send(JSON.stringify(payload)); } catch (e) { wsLog("send error: " + e); return; }

      // quand on reçoit un final, on tentera un snapshot après (on ne bloque pas l’UI ici)
      // => on observe le Map et on déclenche une fois.
      const t0 = Date.now();
      const poll = setInterval(async () => {
        if (Date.now() - t0 > 120000) { clearInterval(poll); return; }
        for (const [tid, v] of __wsMsgs.entries()) {
          if (v && v.status === "final") {
            clearInterval(poll);
            await wsSnapshot(npcId, tid, "après");
            return;
          }
        }
      }, 500);
    }

    function wsClear() {
      __wsMsgs.clear();
      document.getElementById("ws-out").textContent = "—";
    }

    function getWorldNpcIdOrDefault() {
      try {
        const raw = document.getElementById("context-json").value.trim();
        const ctx = raw ? JSON.parse(raw) : {};
        const id = (ctx && ctx.world_npc_id) ? String(ctx.world_npc_id).trim() : "";
        return id || "npc:merchant";
      } catch (_) {
        return "npc:merchant";
      }
    }

    async function refreshReputationPanel() {
      // Sans LLM : forcer l’intent devops_probe, mais laisser merge_mmo_lyra enrichir lyra_meta via world_npc_id.
      const npcId = getWorldNpcIdOrDefault();
      const base = getBase();
      const payload = {
        actor_id: "svc:pilot",
        text: "probe",
        context: {
          world_npc_id: npcId,
          devops_action: { kind: "http_get", url: "http://127.0.0.1:8010/healthz", max_bytes: 200 },
          devops_dry_run: true,
          history: [],
        },
      };
      const out = await postJson(base + "/v1/pilot/internal/route", payload);
      if (out.status !== 200 || !out.json) return;
      window.__last_intent_json = out.json;
      document.getElementById("intent-out").textContent = JSON.stringify(out.json, null, 2);
      try { document.getElementById("intent-pretty").innerHTML = renderPretty(out.json); } catch (_) {}
    }

    async function commitPlayerInventoryDelta(qtyDelta) {
      const npcId = getWorldNpcIdOrDefault();
      const base = getBase();
      const pid = (document.getElementById("pilot-inv-player-id") && String(document.getElementById("pilot-inv-player-id").value || "").trim()) || "";
      const itemId = (document.getElementById("pilot-inv-item-id") && String(document.getElementById("pilot-inv-item-id").value || "").trim()) || "";
      const qtyEl = document.getElementById("pilot-inv-qty");
      let q = qtyDelta;
      if (qtyDelta === null || qtyDelta === undefined) {
        try {
          q = qtyEl ? parseInt(String(qtyEl.value || "0"), 10) : 0;
        } catch (_) {
          q = 0;
        }
      }
      const labRaw = document.getElementById("pilot-inv-label") && String(document.getElementById("pilot-inv-label").value || "").trim();
      if (!pid) {
        alert("player_id requis (copier welcome.player_id depuis le client MMO ou les logs WS).");
        return;
      }
      if (!itemId) {
        alert("item_id requis.");
        return;
      }
      const body = { npc_id: npcId, player_id: pid, item_id: itemId, qty_delta: q };
      if (labRaw) body.label = labRaw;
      const out = await postJson(base + "/v1/pilot/player-inventory", body);
      if (out.json) {
        window.__last_intent_json = out.json;
        document.getElementById("intent-out").textContent = JSON.stringify(out.json, null, 2);
        try { document.getElementById("intent-pretty").innerHTML = renderPretty(out.json); } catch (_) {}
      } else if (out.status && out.status !== 200) {
        alert("player-inventory HTTP " + out.status + (out.text ? ": " + out.text.slice(0, 200) : ""));
      }
    }

    async function commitReputationDelta(delta) {
      const npcId = getWorldNpcIdOrDefault();
      const base = getBase();
      const out = await postJson(base + "/v1/pilot/reputation", { npc_id: npcId, delta });
      // Afficher le résultat commit dans le panneau principal.
      if (out.json) {
        window.__last_intent_json = out.json;
        document.getElementById("intent-out").textContent = JSON.stringify(out.json, null, 2);
        try { document.getElementById("intent-pretty").innerHTML = renderPretty(out.json); } catch (_) {}
      }
      // Rafraîchir la valeur (lecture via internal/route, sans LLM).
      try { await refreshReputationPanel(); } catch (_) {}
    }

    function getLastReputationValue() {
      const j = window.__last_intent_json;
      if (!j || typeof j !== "object") return null;
      const meta = j.lyra_meta;
      if (!meta || typeof meta !== "object") return null;
      const rep = meta.reputation;
      if (!rep || typeof rep !== "object") return null;
      const v = rep.value;
      return (typeof v === "number" && Number.isFinite(v)) ? Math.trunc(v) : null;
    }

    async function resetReputationToZero() {
      // On lit la valeur via internal/route (sans LLM), puis on applique un delta = -value.
      try { await refreshReputationPanel(); } catch (_) {}
      const v = getLastReputationValue();
      if (v === null) {
        alert("Impossible de lire la réputation (lyra_meta.reputation.value absent).");
        return;
      }
      if (v === 0) return;
      await commitReputationDelta(-v);
    }

    document.getElementById("btn-rep-plus").addEventListener("click", () => commitReputationDelta(11));
    document.getElementById("btn-rep-minus").addEventListener("click", () => commitReputationDelta(-5));
    document.getElementById("btn-rep-reset").addEventListener("click", () => resetReputationToZero());
    try {
      document.getElementById("btn-pilot-inv-preset-qty").addEventListener("click", () => commitPlayerInventoryDelta(null));
    } catch (_) {}
    try {
      document.getElementById("btn-pilot-inv-minus-one").addEventListener("click", () => commitPlayerInventoryDelta(-1));
    } catch (_) {}

    async function getWorldLyraSnapshot(npcId) {
      const base = getBase();
      const url = base + "/v1/pilot/mmo-server/world-lyra?npc_id=" + encodeURIComponent(String(npcId || "").trim());
      const r = await fetch(url);
      const t = await r.text();
      let j = null;
      try { j = t ? JSON.parse(t) : null; } catch (_) {}
      if (!j || typeof j !== "object") throw new Error("world-lyra: réponse non JSON");
      if (r.status !== 200) throw new Error("world-lyra HTTP " + r.status + ": " + t.slice(0, 500));
      return j;
    }

    async function postAid(payload) {
      const base = getBase();
      const out = await postJson(base + "/v1/pilot/aid", payload);
      if (out.json) {
        window.__last_intent_json = out.json;
        document.getElementById("intent-out").textContent = JSON.stringify(out.json, null, 2);
        try { document.getElementById("intent-pretty").innerHTML = renderPretty(out.json); } catch (_) {}
      } else {
        document.getElementById("intent-out").textContent = "HTTP " + out.status + "\n" + out.text;
      }
      // Relecture monde (proxy) pour visibilité immédiate.
      try {
        const npcId = payload.npc_id;
        const snap = await getWorldLyraSnapshot(npcId);
        const merged = { ...(out.json || {}), world_after: snap };
        window.__last_intent_json = merged;
        document.getElementById("intent-out").textContent = JSON.stringify(merged, null, 2);
      } catch (_) {}
    }

    async function aidHelp() {
      const npcId = getWorldNpcIdOrDefault();
      await postAid({ npc_id: npcId, hunger_delta: -0.2, thirst_delta: -0.1, fatigue_delta: -0.2, reputation_delta: 5 });
    }

    async function aidResetGaugesToZero() {
      const npcId = getWorldNpcIdOrDefault();
      let snap;
      try { snap = await getWorldLyraSnapshot(npcId); } catch (e) { alert("Impossible de relire le monde: " + e); return; }
      const g = (snap.lyra && snap.lyra.gauges) ? snap.lyra.gauges : {};
      const hunger = typeof g.hunger === "number" ? g.hunger : 0;
      const thirst = typeof g.thirst === "number" ? g.thirst : 0;
      const fatigue = typeof g.fatigue === "number" ? g.fatigue : 0;
      await postAid({ npc_id: npcId, hunger_delta: -hunger, thirst_delta: -thirst, fatigue_delta: -fatigue, reputation_delta: 0 });
    }

    document.getElementById("btn-aid-help").addEventListener("click", () => aidHelp());
    document.getElementById("btn-aid-reset").addEventListener("click", () => aidResetGaugesToZero());
    try { document.getElementById("btn-npc-reg-refresh").addEventListener("click", npcRegistryRefresh); } catch (_) {}
    try { document.getElementById("btn-world-content-refresh").addEventListener("click", worldContentRefresh); } catch (_) {}
    try { document.getElementById("btn-npc-reg-apply").addEventListener("click", npcRegistryApplyToContext); } catch (_) {}

    // WS buttons
    try { document.getElementById("btn-ws-connect").addEventListener("click", wsConnect); } catch (_) {}
    try { document.getElementById("btn-ws-disconnect").addEventListener("click", wsDisconnect); } catch (_) {}
    try { document.getElementById("btn-ws-send-hello").addEventListener("click", wsSendHello); } catch (_) {}
    try { document.getElementById("btn-ws-clear").addEventListener("click", wsClear); } catch (_) {}

    function applyNpcIdChip(npcId) {
      const id = (npcId || "").trim();
      if (!id) return;
      try {
        const raw = document.getElementById("context-json").value.trim();
        const ctx = raw ? JSON.parse(raw) : {};
        const next = { ...(ctx || {}), world_npc_id: id };
        if (!Array.isArray(next.history)) next.history = [];
        document.getElementById("context-json").value = JSON.stringify(next, null, 2);
        saveChatState();
        try { refreshLyraContextPreview(); } catch (_) {}
      } catch (_) {}
    }

    for (const btn of document.querySelectorAll("button.npc-chip")) {
      btn.addEventListener("click", () => applyNpcIdChip(btn.dataset.npcId));
    }

    // Dashboard toggles
    const leftToggle = document.getElementById("toggle-left");
    const rightToggle = document.getElementById("toggle-right");
    const colLeft = document.getElementById("col-left");
    const colRight = document.getElementById("col-right");
    function applyToggles() {
      colLeft.style.display = leftToggle.checked ? "" : "none";
      colRight.style.display = rightToggle.checked ? "" : "none";
      try {
        localStorage.setItem("lbg_pilot_dash_left", leftToggle.checked ? "1" : "0");
        localStorage.setItem("lbg_pilot_dash_right_v2", rightToggle.checked ? "1" : "0");
      } catch (_) {}
    }
    try {
      const vL = localStorage.getItem("lbg_pilot_dash_left");
      const vR = localStorage.getItem("lbg_pilot_dash_right_v2");
      if (vL === "0") leftToggle.checked = false;
      // v2 : défaut OFF (legacy WS masqué) — ignore l’ancienne clé dash_right
      if (vR === "1") rightToggle.checked = true;
      else rightToggle.checked = false;
    } catch (_) {}
    leftToggle.addEventListener("change", applyToggles);
    rightToggle.addEventListener("change", applyToggles);
    applyToggles();
    loadStoredBase();
    loadStoredServiceToken();
    loadStoredMetricsBearer();
    loadStoredChatState();
    loadNoCacheToggle();
    try { document.getElementById("toggle-no-cache").addEventListener("change", saveNoCacheToggle); } catch (_) {}
    try {
      document.getElementById("context-json").addEventListener("input", refreshLyraContextPreview);
    } catch (_) {}
    try { refreshLyraContextPreview(); } catch (_) {}
    try { document.getElementById("history-pretty").innerHTML = renderHistoryPretty(); } catch (_) {}
    try {
      document.getElementById("btn-pm-send").addEventListener("click", function () {
        pilotPmSend().catch(function (e) {
          pilotInlineHint("pm-route-hint", "PM : " + e, true);
        });
      });
    } catch (_) {}
    try {
      document.getElementById("btn-pm-health").addEventListener("click", pilotPmHealth);
    } catch (_) {}
    try {
      const pmPage = document.getElementById("pilot-page-pm");
      if (pmPage) {
        pmPage.addEventListener("click", function (ev) {
          const btn = ev.target.closest(".pm-path-chip");
          if (!btn) return;
          const p = btn.getAttribute("data-copy");
          if (!p) return;
          const done = function () {
            const old = btn.textContent;
            btn.textContent = "Copié !";
            setTimeout(function () {
              btn.textContent = old;
            }, 1200);
          };
          if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(p).then(done).catch(function () {
              prompt("Copier le chemin :", p);
            });
          } else {
            prompt("Copier le chemin :", p);
          }
        });
      }
    } catch (_) {}
    try {
      document.getElementById("btn-pm-export-md").addEventListener("click", function () {
        const b = window.__pm_last_brief;
        const md = buildPmMarkdownFromBrief(b || {});
        const hint = document.getElementById("pm-export-hint");
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard
            .writeText(md)
            .then(function () {
              if (hint) {
                hint.textContent = "Markdown copié dans le presse-papiers.";
                hint.style.color = "";
                hint.style.fontWeight = "";
              }
            })
            .catch(function () {
              pilotInlineHint("pm-export-hint", "Échec copie — voir la console (F12) pour le Markdown.", true);
              console.info("[pilot pm export markdown]\n" + md);
            });
        } else {
          pilotInlineHint("pm-export-hint", "Presse-papiers indisponible — voir la console (F12).", true);
          console.info("[pilot pm export markdown]\n" + md);
        }
      });
    } catch (_) {}

    // Desktop page bindings
    try {
      document.getElementById("btn-desktop-propose-llm").addEventListener("click", function () {
        pilotDesktopProposeLlm().catch(function (e) {
          pilotDesktopUiHint("Desktop LLM : " + e, true);
        });
      });
    } catch (_) {}
    try {
      document.getElementById("btn-desktop-infer-text").addEventListener("click", pilotDesktopInferFromTextOnly);
    } catch (_) {}
    try {
      document.getElementById("btn-desktop-propose-backend").addEventListener("click", function () {
        pilotDesktopProposeBackend().catch(function (e) {
          pilotDesktopUiHint("Orchestrateur : " + e, true);
        });
      });
    } catch (_) {}
    try {
      document.getElementById("btn-desktop-send").addEventListener("click", function () {
        pilotDesktopSend().catch(function (e) {
          pilotDesktopUiHint("Desktop : " + e, true);
        });
      });
    } catch (_) {}
    try { document.getElementById("btn-desktop-health").addEventListener("click", pilotDesktopHealth); } catch (_) {}
    try { document.getElementById("desktop-text").addEventListener("input", desktopTrySyncActionFromText); } catch (_) {}
    try { document.getElementById("desktop-action").addEventListener("input", desktopTrySyncTextFromAction); } catch (_) {}
    try {
      const DESKTOP_APPROVAL_KEY = "lbg_pilot_desktop_approval_v1";
      const ap = document.getElementById("desktop-approval");
      if (ap) {
        try {
          const raw = localStorage.getItem(DESKTOP_APPROVAL_KEY);
          if (raw) ap.value = raw;
        } catch (_) {}
        ap.addEventListener("input", function () {
          try {
            const v = String(ap.value || "");
            if (v) localStorage.setItem(DESKTOP_APPROVAL_KEY, v);
            else localStorage.removeItem(DESKTOP_APPROVAL_KEY);
          } catch (_) {}
        });
      }
    } catch (_) {}
    try {
      document.getElementById("btn-desktop-preset-open-url").addEventListener("click", function () {
        const a = document.getElementById("desktop-action");
        const t = document.getElementById("desktop-text");
        if (t) t.value = "ouvre https://example.org dans le navigateur";
        if (a) a.value = JSON.stringify({ kind: "open_url", url: "https://example.org" }, null, 2);
        try { desktopTrySyncTextFromAction(); } catch (_) {}
      });
    } catch (_) {}
    try {
      document.getElementById("btn-desktop-preset-notepad").addEventListener("click", function () {
        const a = document.getElementById("desktop-action");
        const t = document.getElementById("desktop-text");
        if (t) t.value = "ouvre notepad et ajoute une ligne";
        if (a) {
          a.value = JSON.stringify(
            { kind: "notepad_append", path: "C:\\\\Users\\\\Public\\\\lbg_desktop.txt", text: "Hello depuis Lyra\\n" },
            null,
            2
          );
        }
        try { desktopTrySyncActionFromText(); } catch (_) {}
      });
    } catch (_) {}
    try {
      document.getElementById("btn-desktop-preset-open-app-learn").addEventListener("click", function () {
        const a = document.getElementById("desktop-action");
        const t = document.getElementById("desktop-text");
        if (t) t.value = "ouvre l'application vlc (learn)";
        if (a) {
          a.value = JSON.stringify(
            { kind: "open_app", app: "vlc", args: [], learn: true },
            null,
            2
          );
        }
      });
    } catch (_) {}
    try {
      document.getElementById("btn-desktop-preset-search-web").addEventListener("click", function () {
        const a = document.getElementById("desktop-action");
        const t = document.getElementById("desktop-text");
        if (a) {
          a.value = JSON.stringify({ kind: "search_web_open", query: "exemple recherche pilot" }, null, 2);
        }
        try { desktopTrySyncTextFromAction(); } catch (_) {}
        if (t && !String(t.value || "").trim()) t.value = "recherche web : exemple recherche pilot";
      });
    } catch (_) {}
    try {
      document.getElementById("btn-desktop-preset-mail-imap").addEventListener("click", function () {
        const a = document.getElementById("desktop-action");
        const t = document.getElementById("desktop-text");
        if (a) {
          a.value = JSON.stringify(
            {
              kind: "mail_imap_preview",
              from_contains: "expéditeur",
              subject_contains: "sujet",
              max_messages: 3,
            },
            null,
            2
          );
        }
        try { desktopTrySyncTextFromAction(); } catch (_) {}
        if (t && !String(t.value || "").trim())
          t.value =
            "aperçu mails IMAP (expéditeur contient « expéditeur » ; sujet contient « sujet »)";
      });
    } catch (_) {}

    // Home (orchestrator chat) bindings
    try {
      const HOME_ORCH_KEY = "lbg_pilot_home_orch_v1";
      const tEl = document.getElementById("home-orch-text");
      const cEl = document.getElementById("home-orch-context");
      const outEl = document.getElementById("home-orch-out");
      const prettyEl = document.getElementById("home-orch-pretty");
      try {
        const raw = localStorage.getItem(HOME_ORCH_KEY);
        if (raw) {
          const st = JSON.parse(raw);
          if (st && typeof st === "object") {
            if (tEl && typeof st.text === "string") tEl.value = st.text;
            if (cEl && typeof st.context === "string") cEl.value = st.context;
          }
        }
      } catch (_) {}
      const HOME_ORCH_INTENT_MODE_KEY = "lbg_pilot_home_orch_intent_mode_v1";
      const modeEl = document.getElementById("home-orch-intent-mode");
      try {
        const mv = localStorage.getItem(HOME_ORCH_INTENT_MODE_KEY);
        if (mv && modeEl && (mv === "auto" || mv === "llm" || mv === "deterministic")) modeEl.value = mv;
      } catch (_) {}
      if (modeEl) {
        modeEl.addEventListener("change", function () {
          try {
            localStorage.setItem(HOME_ORCH_INTENT_MODE_KEY, modeEl.value);
          } catch (_) {}
        });
      }

      async function homeOrchSend() {
        pilotInlineHint("home-orch-hint", "…", false);
        const text = (tEl && tEl.value ? tEl.value : "").trim();
        let ctx = {};
        try {
          ctx = JSON.parse((cEl && cEl.value) ? cEl.value : "{}");
        } catch (_) {
          pilotInlineHint("home-orch-hint", "JSON context invalide", true);
          return;
        }
        const mode = modeEl && modeEl.value ? modeEl.value : "auto";
        if (mode === "llm") ctx._intent_classify = "llm";
        else if (mode === "deterministic") ctx._intent_classify = "deterministic";
        else delete ctx._intent_classify;
        try {
          localStorage.setItem(HOME_ORCH_KEY, JSON.stringify({ text, context: (cEl && cEl.value) ? cEl.value : "{}" }));
        } catch (_) {}
        const base = getBase();
        const payload = { actor_id: "ui:home", text: text || "diagnostic", context: ctx };
        const out = await postJson(base + "/v1/pilot/route", payload);
        if (outEl) outEl.textContent = out.json ? JSON.stringify(out.json, null, 2) : ("HTTP " + out.status + "\n" + (out.text || ""));
        if (prettyEl) {
          try { prettyEl.innerHTML = out.json ? renderPretty(out.json) : ""; } catch (_) { prettyEl.innerHTML = ""; }
        }
        let hintMsg = out.status === 200 ? "OK" : "HTTP " + out.status;
        let isErr = out.status !== 200;
        const j = out.json;
        if (j && j.ok === false && j.error) {
          hintMsg = String(j.error);
          isErr = true;
        } else if (j && j.result && j.result.output && j.result.output.orchestrator_route_meta) {
          const om = j.result.output.orchestrator_route_meta;
          const rep = om && typeof om.assistant_reply === "string" ? om.assistant_reply.trim() : "";
          const src = om && typeof om.intent_source === "string" ? om.intent_source : "";
          if (rep) hintMsg = rep + (src ? " (" + src + ")" : "") + " — " + hintMsg;
          else if (src && j.result.intent) hintMsg = "Intent « " + j.result.intent + " » (" + src + ") — " + hintMsg;
        }
        pilotInlineHint("home-orch-hint", hintMsg, isErr);
      }

      function homeOrchSet(text, ctxObj) {
        if (tEl) tEl.value = text;
        if (cEl) cEl.value = JSON.stringify(ctxObj || {}, null, 2);
        pilotInlineHint("home-orch-hint", "—", false);
      }

      async function homeQuickGet(path, label) {
        pilotInlineHint("home-orch-hint", "…", false);
        const base = getBase();
        const token = getServiceToken();
        const headers = {};
        if (token) headers["X-LBG-Service-Token"] = token;
        try {
          const r = await fetch(base + path, { headers });
          const t = await r.text();
          let j = null;
          try { j = t ? JSON.parse(t) : null; } catch (_) {}
          if (outEl) outEl.textContent = j ? JSON.stringify(j, null, 2) : ("HTTP " + r.status + "\n" + t);
          if (prettyEl) {
            try { prettyEl.innerHTML = j ? renderPretty(j) : ""; } catch (_) { prettyEl.innerHTML = ""; }
          }
          pilotInlineHint("home-orch-hint", (label || path) + " → HTTP " + r.status, r.status !== 200);
        } catch (e) {
          pilotInlineHint("home-orch-hint", "Erreur : " + e, true);
        }
      }

      function homeOrchClear() {
        if (tEl) tEl.value = "Fais un diagnostic rapide des services et propose la prochaine action concrète.";
        if (cEl) cEl.value = "{\n  \"history\": []\n}";
        if (outEl) outEl.textContent = "—";
        if (prettyEl) prettyEl.innerHTML = "";
        pilotInlineHint("home-orch-hint", "—", false);
        try { localStorage.removeItem(HOME_ORCH_KEY); } catch (_) {}
      }

      try { document.getElementById("btn-home-orch-send").addEventListener("click", () => homeOrchSend().catch((e) => pilotInlineHint("home-orch-hint", "Orchestrateur : " + e, true))); } catch (_) {}
      try { document.getElementById("btn-home-orch-clear").addEventListener("click", homeOrchClear); } catch (_) {}
      try { document.getElementById("btn-home-quick-status").addEventListener("click", () => homeQuickGet("/v1/pilot/status", "status")); } catch (_) {}
      try { document.getElementById("btn-home-quick-caps").addEventListener("click", () => homeQuickGet("/v1/pilot/capabilities", "capabilities")); } catch (_) {}
      try {
        document.getElementById("btn-home-quick-selfcheck").addEventListener("click", () => {
          homeOrchSet(
            "devops selfcheck (dry-run) : diagnostique et propose une action concrète.",
            { devops_action: { kind: "selfcheck" }, devops_dry_run: true, devops_selfcheck: true, history: [] }
          );
          homeOrchSend().catch((e) => pilotInlineHint("home-orch-hint", "Orchestrateur : " + e, true));
        });
      } catch (_) {}
      try {
        document.getElementById("btn-home-quick-pm").addEventListener("click", () => {
          homeOrchSet(
            "jalons et tâches du plan de route",
            { project_pm: true, pm_include_plan: true, pm_include_structure: true, history: [] }
          );
          homeOrchSend().catch((e) => pilotInlineHint("home-orch-hint", "Orchestrateur : " + e, true));
        });
      } catch (_) {}
      try {
        document.getElementById("btn-home-quick-desktop").addEventListener("click", () => {
          homeOrchSet(
            "desktop (dry-run) : ouvre example.org",
            {
              desktop_action: { kind: "open_url", url: "https://example.org" },
              desktop_dry_run: true,
              history: []
            }
          );
          homeOrchSend().catch((e) => pilotInlineHint("home-orch-hint", "Orchestrateur : " + e, true));
        });
      } catch (_) {}
    } catch (_) {}

    // Lyra page bindings
    try { lyraBindControls(); } catch (_) {}
    try { panelApplyStoredLayout(); } catch (_) {}
    try { panelInitDnD(); } catch (_) {}
    try {
      const st = lyraLoadState();
      const dtEl = document.getElementById("lyra-dt");
      if (dtEl) dtEl.value = String(st.dt_s || 60);
      const cEl = document.getElementById("lyra-confiance");
      if (cEl) cEl.value = String(st.confiance_100 != null ? st.confiance_100 : 70);
      const fEl = document.getElementById("lyra-reg-filter");
      if (fEl) fEl.value = lyraRegFilterLoad();
      // restore mode
      try {
        const m = localStorage.getItem(STORAGE_LYRA_MODE_KEY);
        if (m === "assistant" || m === "world") lyraSetMode(m);
      } catch (_) {}
      lyraRenderIn();
      lyraRenderOut(null);
      lyraRegLogRender();
      lyraRefreshBrain().catch(function () {});
    } catch (_) {}
    try {
      const cEl = document.getElementById("lyra-confiance");
      if (cEl) {
        cEl.addEventListener("input", function () {
          const st = lyraLoadState();
          st.confiance_100 = clamp0100(cEl.value, 70);
          if (st.assistant_gauges_100 && typeof st.assistant_gauges_100 === "object") {
            st.assistant_gauges_100.confiance = st.confiance_100;
          }
          lyraSaveState(st);
          lyraRenderIn();
        });
      }
    } catch (_) {}
    try {
      document.getElementById("lyra-mode-world").addEventListener("change", function () {
        lyraSetMode("world");
        lyraRenderIn();
      });
      document.getElementById("lyra-mode-assistant").addEventListener("change", function () {
        lyraSetMode("assistant");
        lyraRenderIn();
      });
    } catch (_) {}
    try {
      document.getElementById("btn-lyra-step").addEventListener("click", function () {
        lyraStepOnce().catch(function (e) {
          pilotInlineHint("lyra-step-hint", "Lyra : " + e, true);
        });
      });
    } catch (_) {}
    try { document.getElementById("btn-lyra-stress").addEventListener("click", lyraApplyStressPreset); } catch (_) {}
    try {
      document.getElementById("btn-lyra-chaos").addEventListener("click", async function () {
        const btn = document.getElementById("btn-lyra-chaos");
        const prev = btn ? btn.textContent : "";
        if (btn) {
          btn.disabled = true;
          btn.textContent = "Chaos en cours…";
        }
        try {
          await lyraRunChaosLoop(8);
          pilotInlineHint("lyra-step-hint", "Chaos : terminé", false);
        } catch (e) {
          pilotInlineHint("lyra-step-hint", "Chaos : " + e, true);
        } finally {
          if (btn) {
            btn.disabled = false;
            btn.textContent = prev || "Chaos loop x8";
          }
        }
      });
    } catch (_) {}
    try {
      document.getElementById("btn-lyra-brain-refresh").addEventListener("click", function () {
        lyraRefreshBrain().catch(function () {});
      });
    } catch (_) {}
    try { document.getElementById("btn-lyra-reset").addEventListener("click", lyraReset); } catch (_) {}
    try {
      document.getElementById("btn-lyra-reg-clear").addEventListener("click", function () {
        lyraRegLogSave([]);
        lyraRegLogRender();
      });
    } catch (_) {}
    try {
      document.getElementById("lyra-reg-filter").addEventListener("change", function (ev) {
        const v = ev && ev.target ? ev.target.value : "all";
        lyraRegFilterSave(v);
        lyraRegLogRender();
      });
    } catch (_) {}
    try { document.getElementById("btn-lyra-reg-export").addEventListener("click", lyraRegExportTxt); } catch (_) {}
    try {
      document.getElementById("lyra-auto").addEventListener("change", function (ev) {
        const on = !!(ev.target && ev.target.checked);
        if (__lyraAutoTimer) {
          clearInterval(__lyraAutoTimer);
          __lyraAutoTimer = null;
        }
        if (on) {
          __lyraAutoTimer = setInterval(function () {
            lyraStepOnce().catch(function () {});
          }, 5000);
        }
      });
    } catch (_) {}
    try {
      checkWaitingApprovalJobsGlobal().catch(function () {});
      window.setInterval(checkWaitingApprovalJobsGlobal, 10000);
    } catch (_) {}
    pilotApplyRoute();
    refreshHealth();
    try { renderMetricsLinks(); } catch (_) {}
    refreshCapabilities();
    try { renderCacheLatencyPanel(); } catch (_) {}
