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
