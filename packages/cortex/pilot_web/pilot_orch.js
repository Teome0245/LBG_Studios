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
        if (infra.desktop_agent_down === true || infra.ad_agent_down === true) flags.push("agent desktop down");
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
