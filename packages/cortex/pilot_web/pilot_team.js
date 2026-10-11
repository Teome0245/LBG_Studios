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
    let __teamPygmalionMesh = false;
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
    let __teamEvolutionSprint = false;


    const TEAM_ROLE_DEFAULTS = {
      qa: "Smoke LAN read-only (healthz + systemd via script si configuré)",
      ops: "Sonde santé orchestrateur et backend (read-only)",
      pm: "Brief jalons et prochaines tâches projet",
      pm_reunif: "Brief réunification sous-projets — jalons, statuts et prochaines actions (Thémis)",
      autoconsult: "Round autoconsultation Fable — Thémis + sondes Iris/Hermès/Pygmalion/Argus/Héphaïstos",
      evolution_sprint: "Sprint évolution 7j — audit full infra/Team/LLM/jeu + plan + L1 auto",
      godot_supervise: "Supervise client Godot — sidecar 246, miroir M1, readiness lbg-ws/2",
      godot_lbg_ws2: "Audit lbg-ws/2 gateway Godot Prime — gaps et proposition forge",
      infographiste_ia: "Audit pipeline assets Infographiste IA — manifest GLB Godot et prochain export Blender",
      mesh_3d: "Pygmalion — ComfyUI concept 2D + mesh TRELLIS.2 (worker GPU, L2 si activé)",
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
      evolution_sprint: { role: "pm", objectiveKey: "evolution_sprint", evolutionSprint: true, autoRun: true },
      godot_supervise: { role: "qa", objectiveKey: "godot_supervise", godotSupervisor: true, autoRun: true },
      godot_lbg_ws2: { role: "dev_game", objectiveKey: "godot_lbg_ws2", godotTrack: true, autoRun: true },
      infographiste_ia: { role: "dev_game", objectiveKey: "infographiste_ia", infographiste: true, autoRun: true },
      mesh_3d: { role: "dev_game", objectiveKey: "mesh_3d", infographiste: true, pygmalionMesh: true, autoRun: true },
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
      __teamEvolutionSprint = !!preset.evolutionSprint;
      __teamGodotSupervisor = !!preset.godotSupervisor;
      __teamGodotTrack = !!preset.godotTrack;
      __teamInfographiste = !!preset.infographiste;
      __teamPygmalionMesh = !!preset.pygmalionMesh;
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
      if (__teamEvolutionSprint || /sprint.?évolution|sprint.?evolution|evolution_sprint|amélioration continue/i.test(objective)) {
        ctx.evolution_sprint = true;
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
      if (__teamPygmalionMesh || /trellis|mesh.?3d|image.?to.?3d/i.test(objective)) {
        ctx.pygmalion_mesh = true;
        ctx.mesh_3d = true;
        ctx.pygmalion_generate = true;
        ctx.infographiste_ia = true;
        ctx.subproject = "infographiste_ia";
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
          const lastM = traces.last_mutation || {};
          const mut =
            lastM && lastM.candidate_ready
              ? " · mutation candidat"
              : lastM && lastM.run_id
                ? " · mutation ok"
                : "";
          const lastP = traces.last_proposal || {};
          const prop = lastP && lastP.slug ? " · proposal " + lastP.slug : "";
          el.textContent =
            "Miroir / leçons : " +
            nLessons +
            " leçon(s) · golden " +
            nGolden +
            " · dernier juge score=" +
            score +
            " (" +
            passed +
            ")" +
            mut +
            prop;
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
        __teamEvolutionSprint = false;
        __teamGodotSupervisor = false;
        __teamGodotTrack = false;
        __teamInfographiste = false;
        __teamPygmalionMesh = false;
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

    /* ===================== Métriques Team (#/team/metrics) ===================== */
    let __teamMetricsBound = false;

    function teamMetricsFmt(obj) {
      try {
        return JSON.stringify(obj == null ? {} : obj, null, 2);
      } catch (_) {
        return String(obj);
      }
    }

    async function teamMetricsRefresh() {
      const out = await jobsGet(getBase() + "/v1/pilot/team/meta");
      const feats = (out.json && out.json.features) || {};
      const traces = feats.traces || {};
      const judgeEl = document.getElementById("metrics-judge");
      const lessonsEl = document.getElementById("metrics-lessons");
      const mutEl = document.getElementById("metrics-mutation");
      const propEl = document.getElementById("metrics-proposal");
      const rawEl = document.getElementById("metrics-raw");
      if (judgeEl) {
        const j = traces.last_judge || (feats.outcome_judge && feats.outcome_judge.last_judge) || {};
        judgeEl.textContent =
          "golden_cases: " +
          (traces.golden_cases != null ? traces.golden_cases : "—") +
          "\nlast_judge.score: " +
          (j.score != null ? j.score : "—") +
          "\npass: " +
          (j.pass != null ? j.pass : "—") +
          "\nmode: " +
          (j.mode || "—") +
          "\ntask: " +
          (j.task_id || "—");
      }
      if (lessonsEl) {
        const L = feats.lessons_learned || {};
        lessonsEl.textContent =
          "count: " +
          (traces.lessons_count != null ? traces.lessons_count : L.count != null ? L.count : "—") +
          "\nenabled: " +
          (L.enabled != null ? L.enabled : "—") +
          "\npath: " +
          (L.path || "—");
      }
      if (mutEl) {
        const m = traces.last_mutation || {};
        mutEl.textContent =
          "run_id: " +
          (m.run_id || "—") +
          "\ncandidate: " +
          (m.candidate_ready != null ? m.candidate_ready : "—") +
          "\nwinner: " +
          ((m.winner && m.winner.id) || "—") +
          "\nΔscore: " +
          ((m.winner && m.winner.score_delta) || "—") +
          "\nsmoke_task: " +
          (m.smoke_task_id || "—") +
          "\nl2: " +
          (m.l2_task_id || "—");
      }
      if (propEl) {
        const p = traces.last_proposal || {};
        propEl.textContent =
          "slug: " +
          (p.slug || "—") +
          "\ntitle: " +
          (p.title || "—") +
          "\nbible_ok: " +
          (p.bible_ok != null ? p.bible_ok : "—") +
          "\nsmoke_task: " +
          (p.smoke_task_id || "—") +
          "\nl2: " +
          (p.l2_task_id || "—") +
          "\nbranch: " +
          ((p.branch && p.branch.branch) || "—");
      }
      if (rawEl) {
        rawEl.textContent = teamMetricsFmt({
          traces: traces,
          outcome_judge: feats.outcome_judge,
          lessons_learned: feats.lessons_learned,
          agent_mutator: feats.agent_mutator,
          feature_proposer: feats.feature_proposer,
        });
      }
    }

    function teamMetricsBindPage() {
      if (!__teamMetricsBound) {
        __teamMetricsBound = true;
        const btn = document.getElementById("btn-metrics-refresh");
        if (btn) btn.addEventListener("click", function () { teamMetricsRefresh().catch(function () {}); });
      }
      teamMetricsRefresh().catch(function () {});
    }

    /* ===================== Jobs autonomes ("type Cowork") ===================== */
    let __jobsPoll = null;
    let __jobsSelectedId = null;
    let __jobsSelectedJob = null;
    let __jobsEventSource = null;
    let __jobsBound = false;
    let __jobsCatalogJsonCopy = null;
    let __jobsDevicesJsonCopy = null;
