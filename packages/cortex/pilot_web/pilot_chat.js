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

