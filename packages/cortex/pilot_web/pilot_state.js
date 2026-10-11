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
