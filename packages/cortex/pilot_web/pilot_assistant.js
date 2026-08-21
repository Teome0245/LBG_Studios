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
          "<strong>Bienvenue — LBG-IA</strong><br>" +
          "Pose une question en langage naturel : je route vers la bonne compétence " +
          "(équipe, projet, Godot, infra…) et je réponds factuellement. " +
          "<strong>Dialoguer</strong> pour le LLM, <strong>Proposer une action</strong> pour exécuter avec garde-fous.</div>";
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

