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
