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
      if (out && out.agentic) addKV("agentic", "yes");
      if (out && out.job_id) addKV("job_id", out.job_id);
      if (out && out.status && out.agentic) addKV("job_status", out.status);
      if (out && out.elevated_from) addKV("elevated_from", out.elevated_from);
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
      if (out && out.agentic && out.job_id) {
        const jid = String(out.job_id);
        const href = out.pilot_jobs_href || ("#/jobs?job=" + encodeURIComponent(jid));
        html +=
          '<div style="margin-top:0.5rem;padding:0.75rem;border:1px solid #9ec9b0;border-radius:6px;background:#f0faf4;">' +
          '<div style="font-weight:600;">Mode agentique — job de fond</div>' +
          '<div class="muted" style="margin-top:0.25rem;">' +
          escapeHtml(String(out.reply || "")) +
          "</div>" +
          '<div style="margin-top:0.45rem;"><a href="' +
          escapeHtml(href) +
          '">Ouvrir le job #' +
          escapeHtml(jid.slice(0, 8)) +
          "</a> · statut <code>" +
          escapeHtml(String(out.status || "?")) +
          "</code></div></div>";
      }
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

