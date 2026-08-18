    // --------------------------
    // Lyra (standalone) page
    // --------------------------
    const STORAGE_LYRA_KEY = "lbg_pilot_lyra_state_v1";
    const STORAGE_LYRA_MODE_KEY = "lbg_pilot_lyra_mode_v1";
    let __lyraAutoTimer = null;

    function clamp01(n) {
      const x = Number(n);
      if (!Number.isFinite(x)) return 0;
      if (x < 0) return 0;
      if (x > 1) return 1;
      return x;
    }

    function clamp0100(n, fallback) {
      const x = Number(n);
      if (!Number.isFinite(x)) return (fallback != null ? fallback : 0);
      if (x < 0) return 0;
      if (x > 100) return 100;
      return x;
    }

    function lyraDefaultState() {
      return {
        dt_s: 60,
        // jauges "besoins" (monde) — UI alignée 0–100 (conversion 0–1 au bord)
        gauges: { hunger: 25, thirst: 25, fatigue: 25 },
        // jauges "ton" 0–100 (assistant) — affichées ici, mais non envoyées dans context.lyra (évite mélange d’échelles)
        confiance_100: 70,
        assistant_gauges_100: { chaleur: 70, energie: 60, patience: 70, confiance: 70 },
        version: "Lyra 2.0",
      };
    }

    function lyraLoadState() {
      try {
        const raw = localStorage.getItem(STORAGE_LYRA_KEY);
        if (!raw) return lyraDefaultState();
        const j = JSON.parse(raw);
        const d = lyraDefaultState();
        if (j && typeof j === "object") {
          if (j.dt_s != null) d.dt_s = Number(j.dt_s) || d.dt_s;
          if (j.version) d.version = String(j.version);
          if (j.gauges && typeof j.gauges === "object") d.gauges = { ...d.gauges, ...j.gauges };
          if (j.confiance_100 != null) d.confiance_100 = clamp0100(j.confiance_100, d.confiance_100);
          if (j.assistant_gauges_100 && typeof j.assistant_gauges_100 === "object")
            d.assistant_gauges_100 = { ...d.assistant_gauges_100, ...j.assistant_gauges_100 };
        }
        return d;
      } catch (_) {
        return lyraDefaultState();
      }
    }

    function lyraGetMode() {
      const world = document.getElementById("lyra-mode-world");
      const asst = document.getElementById("lyra-mode-assistant");
      if (asst && asst.checked) return "assistant";
      if (world && world.checked) return "world";
      try {
        const m = localStorage.getItem(STORAGE_LYRA_MODE_KEY);
        if (m === "assistant" || m === "world") return m;
      } catch (_) {}
      return "world";
    }

    function lyraSetMode(mode) {
      try { localStorage.setItem(STORAGE_LYRA_MODE_KEY, mode); } catch (_) {}
      const world = document.getElementById("lyra-mode-world");
      const asst = document.getElementById("lyra-mode-assistant");
      if (world) world.checked = mode === "world";
      if (asst) asst.checked = mode === "assistant";
    }

    function lyraSaveState(st) {
      try {
        localStorage.setItem(STORAGE_LYRA_KEY, JSON.stringify(st));
      } catch (_) {}
    }

    function lyraGaugeColor(v01) {
      const v = clamp01(v01);
      if (v >= 0.75) return "#f87171"; // high = red (stress/fatigue/hunger)
      if (v >= 0.45) return "#facc15"; // yellow
      return "#4ade80"; // green
    }

    function lyraNeedsTo01(needs100) {
      const g = needs100 && typeof needs100 === "object" ? needs100 : {};
      return {
        hunger: clamp0100(g.hunger != null ? g.hunger : 0, 0) / 100.0,
        thirst: clamp0100(g.thirst != null ? g.thirst : 0, 0) / 100.0,
        fatigue: clamp0100(g.fatigue != null ? g.fatigue : 0, 0) / 100.0,
      };
    }

    function lyraNeedsFrom01(needs01) {
      const g = needs01 && typeof needs01 === "object" ? needs01 : {};
      return {
        hunger: Math.round(clamp01(g.hunger != null ? g.hunger : 0) * 100),
        thirst: Math.round(clamp01(g.thirst != null ? g.thirst : 0) * 100),
        fatigue: Math.round(clamp01(g.fatigue != null ? g.fatigue : 0) * 100),
      };
    }

    function lyraComputeEnergy100(needs01) {
      const g = needs01 && typeof needs01 === "object" ? needs01 : {};
      const h = clamp01(g.hunger != null ? g.hunger : 0);
      const t = clamp01(g.thirst != null ? g.thirst : 0);
      const f = clamp01(g.fatigue != null ? g.fatigue : 0);
      const mean = (h + t + f) / 3.0;
      return Math.round(100 * (1.0 - mean));
    }

    function lyraRenderGaugeBlock(containerId, gauges, opts) {
      const el = document.getElementById(containerId);
      if (!el) return;
      const interactive = !!(opts && opts.interactive);
      const mode = (opts && opts.mode) || "world";
      const g = gauges && typeof gauges === "object" ? gauges : {};
      const items =
        mode === "assistant"
          ? [
              ["chaleur", "Chaleur"],
              ["energie", "Énergie"],
              ["patience", "Patience"],
              ["confiance", "Confiance"],
            ]
          : [
              ["hunger", "Faim"],
              ["thirst", "Soif"],
              ["fatigue", "Fatigue"],
            ];
      el.innerHTML = items
        .map(function (it) {
          const k = it[0];
          const label = it[1];
          const v01 =
            mode === "assistant"
              ? clamp0100(g[k] != null ? g[k] : 0, 0) / 100.0
              : clamp0100(g[k] != null ? g[k] : 0, 0) / 100.0;
          const pct = Math.round(v01 * 100);
          const bar = "<div class=\"lyra-bar\"><div style=\"width:" + pct + "%;background:" + lyraGaugeColor(v01) + "\"></div></div>";
          const controls = interactive
            ? "<div class=\"lyra-controls\">" +
              (mode === "assistant"
                ? "<button type=\"button\" data-lyra-inc=\"" + k + "\">+5</button>" +
                  "<button type=\"button\" data-lyra-dec=\"" + k + "\">-5</button>"
                : "<button type=\"button\" data-lyra-inc=\"" + k + "\">+0.05</button>" +
                  "<button type=\"button\" data-lyra-dec=\"" + k + "\">-0.05</button>") +
              "<span class=\"muted\">" + pct + "%</span>" +
              "</div>"
            : "<div class=\"lyra-controls\"><span class=\"muted\">" + pct + "%</span></div>";
          return (
            "<div class=\"lyra-gauge\">" +
            "<div class=\"lyra-gauge-head\"><strong>" +
            escapeHtmlPm(label) +
            "</strong><span class=\"muted\">" +
            escapeHtmlPm(k) +
            "</span></div>" +
            bar +
            controls +
            "</div>"
          );
        })
        .join("");
    }

    function lyraBuildContext() {
      const st = lyraLoadState();
      const dtEl = document.getElementById("lyra-dt");
      const dt = dtEl ? Number(dtEl.value) : st.dt_s;
      st.dt_s = Number.isFinite(dt) ? dt : st.dt_s;
      // normalize needs gauges (0–100)
      Object.keys(st.gauges || {}).forEach(function (k) {
        st.gauges[k] = clamp0100(st.gauges[k], 25);
      });
      // normalize confiance (0–100)
      st.confiance_100 = clamp0100(st.confiance_100, 70);
      // normalize assistant gauges (0–100)
      if (st.assistant_gauges_100 && typeof st.assistant_gauges_100 === "object") {
        ["chaleur", "energie", "patience", "confiance"].forEach(function (k) {
          st.assistant_gauges_100[k] = clamp0100(st.assistant_gauges_100[k], 70);
        });
      }
      lyraSaveState(st);
      const mode = lyraGetMode();
      const needs01 = lyraNeedsTo01(st.gauges);
      const ctx = {
        lyra: {
          version: st.version,
          dt_s: st.dt_s,
          kind: mode === "assistant" ? "assistant" : "npc_world",
          // On garde le contrat PNJ monde en 0–1 côté backend/agents (conversion UI 0–100 → payload 0–1).
          gauges: mode === "assistant" ? st.assistant_gauges_100 : needs01,
          meta: { source: mode === "assistant" ? "pilot_assistant" : "pilot_standalone" },
        },
        history: [],
      };
      return { st, ctx };
    }

    function lyraExtractOut(resp) {
      if (!resp || typeof resp !== "object") return null;
      // Accept a few possible envelopes.
      if (resp.lyra && typeof resp.lyra === "object") return resp.lyra;
      const r = resp.result;
      if (r && typeof r === "object") {
        const o = r.output;
        if (o && typeof o === "object" && o.lyra && typeof o.lyra === "object") return o.lyra;
      }
      return null;
    }

    function lyraRegLogLoad() {
      try {
        const raw = localStorage.getItem(STORAGE_LYRA_REG_LOG_KEY);
        if (!raw) return [];
        const arr = JSON.parse(raw);
        return Array.isArray(arr) ? arr : [];
      } catch (_) {
        return [];
      }
    }

    function lyraRegLogSave(entries) {
      try { localStorage.setItem(STORAGE_LYRA_REG_LOG_KEY, JSON.stringify(Array.isArray(entries) ? entries : [])); } catch (_) {}
    }

    function lyraRegFilterLoad() {
      try {
        const v = String(localStorage.getItem(STORAGE_LYRA_REG_FILTER_KEY) || "all").toLowerCase();
        if (v === "warn" || v === "critical" || v === "all") return v;
      } catch (_) {}
      return "all";
    }

    function lyraRegFilterSave(v) {
      try {
        const x = String(v || "all").toLowerCase();
        localStorage.setItem(STORAGE_LYRA_REG_FILTER_KEY, x);
      } catch (_) {}
    }

    function lyraRegMatchesFilter(entry, filter) {
      const f = String(filter || "all").toLowerCase();
      if (f === "all") return true;
      const sev = String((entry && entry.severity) || "info").toLowerCase();
      if (f === "critical") return sev === "critical";
      if (f === "warn") return sev === "warn" || sev === "warning";
      return true;
    }

    function lyraRegLogLines(entries) {
      return entries.map(function (e) {
        const ts = e && e.ts ? String(e.ts) : "-";
        const sev = e && e.severity ? String(e.severity).toUpperCase() : "INFO";
        const mode = e && e.mode ? String(e.mode) : "lyra";
        const action = e && e.action ? String(e.action) : "none";
        const reason = e && e.reason ? String(e.reason) : "";
        const applied = e && e.applied === true ? "applique" : "skip";
        return "[" + ts + "] [" + sev + "] " + mode + " :: " + action + " (" + applied + ")" + (reason ? " - " + reason : "");
      });
    }

    function lyraRegLogRender() {
      const out = document.getElementById("lyra-reg-log");
      const hint = document.getElementById("lyra-reg-hint");
      const filterSel = document.getElementById("lyra-reg-filter");
      if (!out) return;
      const entries = lyraRegLogLoad();
      const filter = filterSel ? String(filterSel.value || "all").toLowerCase() : lyraRegFilterLoad();
      const filtered = entries.filter(function (e) { return lyraRegMatchesFilter(e, filter); });
      if (!filtered.length) {
        out.textContent = "—";
      } else {
        // Rendu lisible avec badge couleur par sévérité.
        const htmlLines = filtered.map(function (e) {
          const ts = e && e.ts ? String(e.ts) : "-";
          const sevRaw = e && e.severity ? String(e.severity) : "info";
          const sev = sevRaw.toUpperCase();
          const sevLower = sevRaw.toLowerCase();
          const mode = e && e.mode ? String(e.mode) : "lyra";
          const action = e && e.action ? String(e.action) : "none";
          const reason = e && e.reason ? String(e.reason) : "";
          const applied = e && e.applied === true ? "applique" : "skip";

          let color = "#6b7280"; // INFO / défaut
          if (sevLower === "warn" || sevLower === "warning") color = "#f97316";
          if (sevLower === "critical") color = "#dc2626";

          const badge =
            '<span style="display:inline-block;min-width:70px;padding:0 4px;border-radius:3px;font-weight:600;color:white;background:' +
            color +
            ';">' +
            escapeHtmlPm(sev) +
            "</span>";

          const main =
            "[" +
            escapeHtmlPm(ts) +
            "] " +
            badge +
            " " +
            escapeHtmlPm(mode) +
            " :: " +
            escapeHtmlPm(action) +
            " (" +
            escapeHtmlPm(applied) +
            ")" +
            (reason ? " - " + escapeHtmlPm(reason) : "");

          return main;
        });
        out.innerHTML = htmlLines.join("\n");
      }
      if (hint) hint.textContent = entries.length ? (filtered.length + "/" + entries.length + " entrées") : "0 entrée";
    }

    function lyraRegExportTxt() {
      const entries = lyraRegLogLoad();
      const filterSel = document.getElementById("lyra-reg-filter");
      const filter = filterSel ? String(filterSel.value || "all").toLowerCase() : lyraRegFilterLoad();
      const filtered = entries.filter(function (e) { return lyraRegMatchesFilter(e, filter); });
      const lines = lyraRegLogLines(filtered);
      const txt = lines.length ? lines.join("\n") + "\n" : "Journal vide.\n";
      const stamp = new Date().toISOString().replace(/[:]/g, "-");
      const blob = new Blob([txt], { type: "text/plain;charset=utf-8" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = "lyra-regulation-log-" + filter + "-" + stamp + ".txt";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(a.href);
    }

    function lyraRegLogAppend(entry) {
      if (!entry || typeof entry !== "object") return;
      const arr = lyraRegLogLoad();
      arr.unshift(entry);
      lyraRegLogSave(arr.slice(0, 30));
      lyraRegLogRender();
    }

    function lyraRenderIn() {
      const { st, ctx } = lyraBuildContext();
      const mode = lyraGetMode();
      lyraRenderGaugeBlock(
        "lyra-in-gauges",
        mode === "assistant" ? st.assistant_gauges_100 : st.gauges,
        { interactive: true, mode: mode }
      );
      // derived energy + alias stress from confiance
      const eEl = document.getElementById("lyra-in-energy");
      const cEl = document.getElementById("lyra-in-confiance");
      const sEl = document.getElementById("lyra-in-stress");
      const c = mode === "assistant" ? clamp0100(st.assistant_gauges_100.confiance, 70) : clamp0100(st.confiance_100, 70);
      const s = 100 - c;
      const e =
        mode === "assistant"
          ? clamp0100(st.assistant_gauges_100.energie, 60)
          : lyraComputeEnergy100(lyraNeedsTo01(st.gauges));
      if (eEl) eEl.textContent = String(e) + "%";
      if (cEl) cEl.textContent = String(c) + "%";
      if (sEl) sEl.textContent = String(s) + "%";
      const raw = document.getElementById("lyra-in-raw");
      if (raw) raw.textContent = JSON.stringify(ctx, null, 2);
    }

    function lyraRenderOut(resp) {
      const out = lyraExtractOut(resp);
      const raw = document.getElementById("lyra-out-raw");
      if (raw) raw.textContent = resp ? JSON.stringify(resp, null, 2) : "—";
      const metaEl = document.getElementById("lyra-out-meta");
      if (!out) {
        lyraRenderGaugeBlock("lyra-out-gauges", {}, { interactive: false, mode: lyraGetMode() });
        if (metaEl) metaEl.textContent = "—";
        const eEl = document.getElementById("lyra-out-energy");
        if (eEl) eEl.textContent = "—";
        return;
      }
      const gRaw = out.gauges && typeof out.gauges === "object" ? out.gauges : {};
      const mode = out.kind === "assistant" ? "assistant" : "world";
      const g = mode === "assistant" ? gRaw : lyraNeedsFrom01(gRaw);
      lyraRenderGaugeBlock("lyra-out-gauges", g, { interactive: false, mode: mode });
      const eEl = document.getElementById("lyra-out-energy");
      if (eEl) {
        if (mode === "assistant") eEl.textContent = String(clamp0100(gRaw.energie != null ? gRaw.energie : 0, 0)) + "%";
        else eEl.textContent = String(lyraComputeEnergy100(gRaw)) + "%";
      }
      const meta = out.meta && typeof out.meta === "object" ? out.meta : {};
      if (metaEl) metaEl.textContent = JSON.stringify(meta, null, 2);
      const reg = meta.lyra_regulation && typeof meta.lyra_regulation === "object" ? meta.lyra_regulation : null;
      if (reg) {
        lyraRegLogAppend({
          ts: new Date().toISOString(),
          mode: out.kind || "npc_world",
          action: reg.action || null,
          applied: reg.applied === true,
          reason: reg.reason || null,
          severity: reg.severity || null,
          detail: reg,
        });
      }
    }

    function lyraRenderBrainGauges(gauges) {
      const el = document.getElementById("lyra-brain-gauges");
      if (!el) return;
      const g = gauges && typeof gauges === "object" ? gauges : {};
      const items = [
        ["confidence", "Confiance"],
        ["stress", "Stress"],
        ["fatigue", "Fatigue"],
        ["curiosity", "Curiosité"],
      ];
      el.innerHTML = items
        .map(function (it) {
          const key = it[0];
          const label = it[1];
          const v = clamp0100(g[key] != null ? g[key] : 0, 0);
          const pct = Math.round(v);
          const bar = "<div class=\"lyra-bar\"><div style=\"width:" + pct + "%;background:" + lyraGaugeColor(v / 100.0) + "\"></div></div>";
          return (
            "<div class=\"lyra-gauge\">" +
            "<div class=\"lyra-gauge-head\"><strong>" + escapeHtmlPm(label) + "</strong><span class=\"muted\">" + escapeHtmlPm(key) + "</span></div>" +
            bar +
            "<div class=\"lyra-controls\"><span class=\"muted\">" + pct + "%</span></div>" +
            "</div>"
          );
        })
        .join("");
    }

    function lyraRenderBrainStatus(data) {
      const sum = document.getElementById("lyra-brain-summary");
      const raw = document.getElementById("lyra-brain-raw");
      if (raw) raw.textContent = data ? JSON.stringify(data, null, 2) : "—";
      if (!data || typeof data !== "object") {
        if (sum) sum.textContent = "—";
        lyraRenderBrainGauges({});
        return;
      }
      lyraRenderBrainGauges(data.gauges);
      if (sum) {
        const on = data.enabled === true ? "actif" : "inactif";
        const intent = data.intent ? String(data.intent) : "monitor";
        const nar = data.narrative ? String(data.narrative) : "";
        sum.innerHTML =
          "<strong>" + escapeHtmlPm(on) + "</strong>" +
          " · intent <code>" + escapeHtmlPm(intent) + "</code>" +
          (nar ? " · " + escapeHtmlPm(nar) : "");
      }
    }

    async function lyraRefreshBrain() {
      const base = getBase();
      try {
        const r = await fetch(base + "/v1/pilot/orchestrator/brain/status");
        const j = await r.json();
        if (j && j.ok === true) lyraRenderBrainStatus(j);
        else lyraRenderBrainStatus(j || null);
      } catch (e) {
        lyraRenderBrainStatus({ error: String(e) });
      }
    }

    async function lyraStepOnce() {
      lyraRenderIn();
      const base = getBase();
      const built = lyraBuildContext();
      const payload = { actor_id: "svc:pilot-lyra", text: "lyra test", context: built.ctx };
      const out = await postJson(base + "/v1/pilot/route", payload);
      if (out && out.json) {
        // best-effort: if we get gauges back, reuse them as new input
        const ly = lyraExtractOut(out.json);
        if (ly && ly.gauges && typeof ly.gauges === "object") {
          const st = lyraLoadState();
          // IMPORTANT: côté backend, `npc_world` est en 0–1 ; l'UI stocke `world` en 0–100.
          // On reconvertit donc avant de fusionner dans l'état local.
          if (ly.kind === "assistant") {
            if (!st.assistant_gauges_100) st.assistant_gauges_100 = { chaleur: 70, energie: 60, patience: 70, confiance: 70 };
            st.assistant_gauges_100 = { ...st.assistant_gauges_100, ...ly.gauges };
            // miroir confiance (utilisé pour la vue stress)
            if (ly.gauges.confiance != null) st.confiance_100 = clamp0100(ly.gauges.confiance, st.confiance_100);
          } else {
            const nextNeeds100 = lyraNeedsFrom01(ly.gauges);
            st.gauges = { ...st.gauges, ...nextNeeds100 };
          }
          lyraSaveState(st);
        }
        lyraRenderOut(out.json);
      } else {
        lyraRenderOut(null);
        const raw = document.getElementById("lyra-out-raw");
        if (raw) raw.textContent = "HTTP " + out.status + "\n" + (out.text || "");
      }
    }

    function lyraReset() {
      const st = lyraDefaultState();
      lyraSaveState(st);
      const dtEl = document.getElementById("lyra-dt");
      if (dtEl) dtEl.value = String(st.dt_s);
      const cEl = document.getElementById("lyra-confiance");
      if (cEl) cEl.value = String(st.confiance_100);
      lyraRenderIn();
    }

    function lyraApplyStressPreset() {
      const st = lyraLoadState();
      const mode = lyraGetMode();
      if (mode === "assistant") {
        st.assistant_gauges_100 = {
          ...st.assistant_gauges_100,
          chaleur: 40,
          energie: 20,
          patience: 35,
          confiance: 30,
        };
        st.confiance_100 = clamp0100(st.assistant_gauges_100.confiance, 30);
      } else {
        st.gauges = {
          ...st.gauges,
          hunger: 85,
          thirst: 70,
          fatigue: 90,
        };
      }
      lyraSaveState(st);
      const cEl = document.getElementById("lyra-confiance");
      if (cEl) cEl.value = String(st.confiance_100);
      lyraRenderIn();
    }

    function lyraSleep(ms) {
      return new Promise(function (resolve) { setTimeout(resolve, ms); });
    }

    async function lyraRunChaosLoop(steps) {
      const n = Number(steps) > 0 ? Math.min(20, Math.floor(Number(steps))) : 8;
      lyraApplyStressPreset();
      for (let i = 0; i < n; i += 1) {
        await lyraStepOnce();
        if (i < n - 1) await lyraSleep(220);
      }
    }

    function lyraBindControls() {
      const page = document.getElementById("pilot-page-lyra");
      if (!page) return;
      page.addEventListener("click", function (ev) {
        const inc = ev.target.closest("[data-lyra-inc]");
        const dec = ev.target.closest("[data-lyra-dec]");
        if (!inc && !dec) return;
        const key = (inc || dec).getAttribute(inc ? "data-lyra-inc" : "data-lyra-dec");
        if (!key) return;
        const st = lyraLoadState();
        const mode = lyraGetMode();
        if (mode === "assistant") {
          const d = inc ? 5 : -5;
          if (!st.assistant_gauges_100) st.assistant_gauges_100 = { chaleur: 70, energie: 60, patience: 70, confiance: 70 };
          st.assistant_gauges_100[key] = clamp0100((st.assistant_gauges_100[key] != null ? st.assistant_gauges_100[key] : 0) + d, 70);
          if (key === "confiance") {
            st.confiance_100 = st.assistant_gauges_100.confiance;
            const cEl = document.getElementById("lyra-confiance");
            if (cEl) cEl.value = String(st.confiance_100);
          }
        } else {
          const d = inc ? 5 : -5;
          st.gauges[key] = clamp0100((st.gauges[key] != null ? st.gauges[key] : 0) + d, 25);
        }
        lyraSaveState(st);
        lyraRenderIn();
      });
    }

    function renderPmCards(resp) {
      const ms = document.getElementById("pm-milestones");
      const ts = document.getElementById("pm-tasks");
      const raw = document.getElementById("pm-raw");
      if (raw) raw.textContent = JSON.stringify(resp, null, 2);
      const brief = pmExtractBrief(resp);
      window.__pm_last_brief = brief && typeof brief === "object" ? brief : null;
      renderPmEncarts(brief);
      const mlist = brief && Array.isArray(brief.milestones) ? brief.milestones : [];
      const tlist = brief && Array.isArray(brief.tasks) ? brief.tasks : [];
      if (ms) {
        ms.innerHTML = mlist.length
          ? mlist
              .map(function (m) {
                const d = escapeHtmlPm((m && m.date) || "");
                const body = pmRichFormat((m && m.summary) || "");
                return "<li><strong>" + d + "</strong> — " + body + "</li>";
              })
              .join("")
          : "<li class=\"muted\">(aucun jalon — plan absent sur la VM, ou réponse sans <code>result.output.brief</code>)</li>";
      }
      if (ts) {
        ts.innerHTML = tlist.length
          ? tlist
              .map(function (t) {
                const ti = pmRichFormat((t && t.title) || "");
                const sr = escapeHtmlPm((t && t.source) || "");
                return "<li>" + ti + " <span class=\"src\">(" + sr + ")</span></li>";
              })
              .join("")
          : "<li class=\"muted\">(aucune tâche)</li>";
      }
    }

    async function pilotPmSend() {
      const base = getBase();
      let text = (document.getElementById("pm-text") && document.getElementById("pm-text").value) || "";
      text = text.trim();
      if (!text) text = "jalons et tâches du plan de route";
      let ctx;
      try {
        ctx = JSON.parse((document.getElementById("pm-context") && document.getElementById("pm-context").value) || "{}");
      } catch (e) {
        pilotInlineHint("pm-route-hint", "JSON contexte invalide", true);
        return;
      }
      pilotInlineHint("pm-route-hint", "…", false);
      const payload = { actor_id: "svc:pilot-pm", text: text, context: ctx };
      const out = await postJson(base + "/v1/pilot/route", payload);
      if (out.json) {
        renderPmCards(out.json);
        pilotInlineHint("pm-route-hint", "OK", false);
      } else {
        const rawEl = document.getElementById("pm-raw");
        if (rawEl) rawEl.textContent = "HTTP " + out.status + "\n" + (out.text || "");
        window.__pm_last_brief = null;
        renderPmEncarts(null);
        const ms = document.getElementById("pm-milestones");
        const ts = document.getElementById("pm-tasks");
        if (ms) ms.innerHTML = "<li class=\"muted\">—</li>";
        if (ts) ts.innerHTML = "<li class=\"muted\">—</li>";
        pilotInlineHint("pm-route-hint", "HTTP " + out.status, true);
      }
    }

    async function pilotPmHealth() {
      const base = getBase();
      pilotInlineHint("pm-health-hint", "…", false);
      try {
        const r = await fetch(base + "/v1/pilot/agent-pm/healthz");
        const t = await r.text();
        pilotInlineHint("pm-health-hint", "HTTP " + r.status + " " + t.slice(0, 160), r.status !== 200);
      } catch (e) {
        pilotInlineHint("pm-health-hint", "Erreur : " + e, true);
      }
    }

    const LBG_PILOT_MMO_SUMMARY_KEY = "lbg_pilot_mmo_session_summary_json";
    const LBG_PILOT_DESKTOP_NOTEPAD_DEFAULT = "C:\\\\Users\\\\Public\\\\lbg_desktop.txt";
    const LBG_PILOT_DESKTOP_DRY_RUN_KEY = "lbg_pilot_desktop_dry_run_v1";
    const LBG_PILOT_DESKTOP_PIPELINE_KEY = "lbg_pilot_desktop_pipeline_v1";

