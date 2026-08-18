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

