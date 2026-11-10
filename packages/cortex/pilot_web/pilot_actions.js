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
        textEl.value = "vérifie l'état du backend Studio (Pilot / orch)";
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
      if (seg === "team" && parts[1] === "brain") return "team_brain";
      if (seg === "brain") return "team_brain";
      if (seg === "team" && parts[1] === "metrics") return "team_metrics";
      if (seg === "topology" || (seg === "team" && parts[1] === "topology")) return "topology";
      if (seg === "team") return "team";
      if (seg === "ops") return "ops";
      if (seg === "pm") return "pm";
      if (seg === "lyra") return "lyra";
      if (seg === "desktop") return "desktop";
      if (seg === "hunt" || seg === "chasse") return "hunt";
      if (seg === "agents" && parts[1] === "map") return "agents_map";
      if (seg === "providers") return "providers";
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