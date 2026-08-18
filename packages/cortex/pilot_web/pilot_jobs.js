    function jobsGetActor() {
      const el = document.getElementById("jobs-actor");
      return (el && el.value ? el.value.trim() : "") || "pilot:jobs";
    }

    function jobsManualAdvance() {
      const el = document.getElementById("jobs-manual-advance");
      return !!(el && el.checked);
    }

    function jobsHint(msg, isError) {
      pilotInlineHint("jobs-create-hint", msg || "—", !!isError);
    }

    function jobsIsTerminal(status) {
      return status === "done" || status === "failed" || status === "cancelled" || status === "waiting_approval";
    }

    async function pilotFetchWithTimeout(url, opts, timeoutMs) {
      const ms = typeof timeoutMs === "number" && timeoutMs > 0 ? timeoutMs : 20000;
      const ctrl = new AbortController();
      const tid = window.setTimeout(function () { ctrl.abort(); }, ms);
      try {
        return await fetch(url, Object.assign({}, opts || {}, { signal: ctrl.signal }));
      } finally {
        window.clearTimeout(tid);
      }
    }

    async function jobsGet(url) {
      let r;
      try {
        r = await pilotFetchWithTimeout(url, { method: "GET" }, 15000);
      } catch (e) {
        const msg = e && e.name === "AbortError" ? "délai dépassé (15s)" : String(e && e.message ? e.message : e);
        return { status: 0, json: { ok: false, error: msg } };
      }
      const t = await r.text();
      let j = null;
      try { j = t ? JSON.parse(t) : null; } catch (_) {}
      return { status: r.status, json: j };
    }

    function jobsResetDetailPanel(msg) {
      __jobsSelectedId = null;
      const empty = document.getElementById("jobs-detail-empty");
      const detail = document.getElementById("jobs-detail");
      if (detail) detail.hidden = true;
      if (empty) {
        empty.hidden = false;
        empty.textContent = msg || "Sélectionne un job dans la liste pour voir son plan, sa timeline et agir dessus.";
        empty.classList.remove("err");
        if (msg && msg.indexOf("introuvable") >= 0) empty.classList.add("err");
      }
      document.querySelectorAll(".jobs-card").forEach(function (c) { c.classList.remove("jobs-card--active"); });
    }

    async function jobsCreate() {
      const objectiveEl = document.getElementById("jobs-objective");
      const objective = objectiveEl && objectiveEl.value ? objectiveEl.value.trim() : "";
      if (!objective) { jobsHint("Objectif vide.", true); return; }
      let context = {};
      try {
        const raw = (document.getElementById("jobs-context") || {}).value || "{}";
        context = raw.trim() ? JSON.parse(raw) : {};
        if (typeof context !== "object" || Array.isArray(context)) throw new Error("context doit être un objet JSON");
      } catch (e) { jobsHint("context JSON invalide : " + e.message, true); return; }
      const token = (document.getElementById("jobs-token") || {}).value || "";
      const autoStart = !!(document.getElementById("jobs-autostart") || {}).checked;
      const modelEl = document.getElementById("jobs-model");
      const model = modelEl ? modelEl.value : "";
      const plannerEl = document.getElementById("jobs-planner");
      const planner = plannerEl ? plannerEl.value : "";
      
      jobsHint("Création…");
      const payload = { actor_id: jobsGetActor(), objective: objective, context: context, auto_start: autoStart };
      if (token.trim()) payload.approval_token = token.trim();
      if (model) payload.model = model;
      if (planner) payload.planner = planner;
      const out = await postJson(getBase() + "/v1/pilot/jobs", payload, 60000);
      if (out.status !== 200 || !out.json || out.json.ok === false) {
        jobsHint("Échec création : " + ((out.json && (out.json.error || out.json.detail)) || out.status), true);
        return;
      }
      const job = out.json;
      jobsHint("Job créé (" + (job.plan_source || "?") + ", " + (job.steps ? job.steps.length : 0) + " étape(s)).");
      __jobsSelectedId = job.id;
      if (autoStart && jobsManualAdvance()) {
        await jobsAdvanceLoop(job.id);
      }
      await jobsListRefresh();
      await jobsSelect(job.id);
    }

    async function jobsListRefresh() {
      const listEl = document.getElementById("jobs-list");
      if (!listEl) return;
      const mine = !!(document.getElementById("jobs-filter-mine") || {}).checked;
      let url = getBase() + "/v1/pilot/jobs";
      if (mine) url += "?actor_id=" + encodeURIComponent(jobsGetActor());
      const out = await jobsGet(url);
      if (out.status !== 200 || !out.json || out.json.ok === false) {
        listEl.innerHTML = '<span class="err">Liste indisponible (' + ((out.json && out.json.error) || out.status) + ").</span>";
        return;
      }
      const jobs = (out.json.jobs || []);
      jobsRenderList(jobs);
      if (__jobsSelectedId && !jobs.some(function (j) { return j && j.id === __jobsSelectedId; })) {
        jobsResetDetailPanel("Le job sélectionné n’existe plus (serveur redémarré ou liste réinitialisée). Choisis-en un autre ou relance un objectif.");
      }
    }

    function jobsRenderList(jobs) {
      const listEl = document.getElementById("jobs-list");
      if (!listEl) return;
      if (!jobs.length) { listEl.innerHTML = '<span class="muted">Aucun job.</span>'; return; }
      listEl.innerHTML = jobs
        .map(function (j) {
          const active = j.id === __jobsSelectedId ? " jobs-card--active" : "";
          const st = String(j.status || "");
          return (
            '<div class="jobs-card' + active + '" data-job-id="' + escapeHtml(j.id) + '">' +
            '<div class="jobs-card-obj">' + escapeHtml(j.objective || "(sans objectif)") + "</div>" +
            '<div class="jobs-card-meta">' +
            '<span class="jobs-badge jobs-badge--' + escapeHtml(st) + '">' + escapeHtml(st) + "</span> " +
            escapeHtml(String(j.n_steps || 0)) + " étape(s) · " + escapeHtml(String(j.plan_source || "?")) +
            (j.result_summary ? " · " + escapeHtml(j.result_summary) : "") +
            "</div></div>"
          );
        })
        .join("");
      listEl.querySelectorAll(".jobs-card").forEach(function (card) {
        card.addEventListener("click", function () { jobsSelect(card.getAttribute("data-job-id")); });
      });
    }

    async function jobsSelect(id, skipEventSource) {
      if (!id) return;
      __jobsSelectedId = id;
      const out = await jobsGet(getBase() + "/v1/pilot/jobs/" + encodeURIComponent(id));
      if (out.status !== 200 || !out.json || out.json.ok === false) {
        const err = (out.json && (out.json.error || out.json.detail)) || ("HTTP " + out.status);
        jobsResetDetailPanel("Détail indisponible : " + err + ". Vérifiez l’URL du backend (même origine que le pilot si Nginx proxy /v1/).");
        return;
      }
      jobsRenderDetail(out.json);
      // Met en évidence la carte sélectionnée.
      document.querySelectorAll(".jobs-card").forEach(function (c) {
        c.classList.toggle("jobs-card--active", c.getAttribute("data-job-id") === id);
      });

      if (!skipEventSource) {
        if (__jobsEventSource) {
          __jobsEventSource.close();
          __jobsEventSource = null;
        }
        try {
          __jobsEventSource = new EventSource(getBase() + "/v1/pilot/jobs/" + encodeURIComponent(id) + "/events");
          __jobsEventSource.onmessage = function (e) {
            jobsSelect(id, true).catch(function () {});
            jobsListRefresh().catch(function () {});
          };
        } catch (err) {
          console.error("SSE EventSource error:", err);
        }
      }
    }

    function jobsPickString(obj, keys) {
      if (!obj || typeof obj !== "object") return "";
      for (let i = 0; i < keys.length; i++) {
        const v = obj[keys[i]];
        if (typeof v === "string" && v.trim()) return v.trim();
      }
      return "";
    }

    function jobsExtractStepReply(step) {
      const r = step && step.result;
      if (!r || typeof r !== "object") return "";
      let reply = jobsPickString(r, ["reply", "assistant_reply", "text"]);
      const remote = r.remote;
      if (!reply && remote && typeof remote === "object") {
        reply = jobsPickString(remote, ["reply", "text", "assistant_reply", "narration"]);
        if (!reply && Array.isArray(remote.lines)) {
          reply = remote.lines
            .map(function (ln) {
              if (typeof ln === "string") return ln;
              if (ln && typeof ln === "object" && typeof ln.text === "string") return ln.text;
              return "";
            })
            .filter(Boolean)
            .join("\n");
        }
      }
      if (!reply && r.lyra && typeof r.lyra === "object") {
        reply = jobsPickString(r.lyra, ["reply", "narration", "text"]);
      }
      if (!reply && typeof r.echo === "string") reply = r.echo;
      if (!reply && r.agent === "minimal_stub") {
        if (step && step.capability === "unknown") {
          return (
            "Aucune action technique reconnue pour cette formulation — le job s'est contenté de noter l'objectif. " +
            "Essayez par ex. « selfcheck », « chemin du fichier X », « ajoute des logs avec rétention 30j », " +
            "ou précisez le fichier dans le contexte JSON."
          );
        }
        return "(agent dialogue non joignable — vérifier lbg-agent-dialogue sur le core, port 8020)";
      }
      if (!reply && typeof r.text_snippet === "string" && r.text_snippet.trim()) {
        return "(stub) " + r.text_snippet.trim();
      }
      return reply;
    }

    function jobsExtractSelfcheckText(step) {
      if (!step || step.capability !== "devops_probe") return "";
      const r = step.result;
      if (!r || typeof r !== "object") return "";
      let inner = r.result;
      if (!inner || typeof inner !== "object") inner = r;
      const lines = [];
      const ok = inner.ok;
      const dry = inner.dry_run;
      lines.push("Selfcheck : " + (ok === true ? "OK" : ok === false ? "KO" : "?") + (dry ? " (simulation dry-run)" : ""));
      const hints = inner.remediation_hints;
      if (Array.isArray(hints) && hints.length) {
        lines.push("");
        lines.push("Pistes d'amélioration :");
        hints.forEach(function (h) {
          if (typeof h === "string" && h.trim()) lines.push("• " + h.trim());
        });
      }
      const scSteps = inner.steps;
      if (Array.isArray(scSteps)) {
        const bad = scSteps.filter(function (st) { return st && st.healthy === false; });
        if (bad.length) {
          lines.push("");
          lines.push("Éléments non sains :");
          bad.forEach(function (st) {
            const label = st.kind || st.url || st.unit || "étape";
            const err = st.result && st.result.error ? " — " + st.result.error : "";
            lines.push("• " + label + err);
          });
        }
      }
      return lines.join("\n");
    }

    function jobsBuildCapabilitiesCatalogTable(catalog) {
      if (!Array.isArray(catalog) || !catalog.length) return "";
      const rows = catalog
        .map(function (row) {
          if (!row || typeof row !== "object") return "";
          const tags = Array.isArray(row.tags) ? row.tags.join(", ") : "";
          return (
            "<tr><td><code>" + escapeHtml(String(row.capability || "")) + "</code></td>" +
            "<td><code>" + escapeHtml(String(row.routed_to || "")) + "</code></td>" +
            "<td>" + escapeHtml(String(row.risk_level || "")) + "</td>" +
            "<td>" + escapeHtml(String(row.mode || "")) + "</td>" +
            "<td>" + escapeHtml(String(row.action_context_key || "—")) + "</td>" +
            "<td class=\"muted\">" + escapeHtml(String(row.description || "")) + (tags ? " [" + escapeHtml(tags) + "]" : "") + "</td></tr>"
          );
        })
        .join("");
      return (
        '<table class="jobs-cap-table"><thead><tr>' +
        "<th>Capability</th><th>Agent (routed_to)</th><th>Risque</th><th>Mode</th><th>Action key</th><th>Description</th>" +
        "</tr></thead><tbody>" + rows + "</tbody></table>"
      );
    }

    function jobsExtractNetworkInventoryStep(step) {
      const r = step && step.result;
      if (!r || typeof r !== "object") return null;
      const devices = r.devices;
      if (!Array.isArray(devices) || !devices.length) return null;
      const exportRows = r.devices_export;
      return {
        devices: devices,
        devicesExport: Array.isArray(exportRows) && exportRows.length ? exportRows : devices,
        n: r.n_devices || devices.length,
        ts: r.ts,
        scan_cidr: r.scan_cidr,
        reply: typeof r.reply === "string" ? r.reply : "",
      };
    }

    function jobsExtractActionMatrixStep(step) {
      const r = step && step.result;
      if (!r || typeof r !== "object") return null;
      const matrix = r.action_matrix;
      if (!Array.isArray(matrix) || !matrix.length) return null;
      return { matrix: matrix, n: r.n_action_matrix_rows || matrix.length };
    }

    function jobsBuildActionMatrixTable(matrix) {
      if (!Array.isArray(matrix) || !matrix.length) return "";
      const rows = matrix.map(function (row) {
        const caps = (row.suggested_capabilities || []).map(function (c) {
          const risk = c.risk_level ? (" <span class=\"muted\">(" + escapeHtml(String(c.risk_level)) + ")</span>") : "";
          return "<code>" + escapeHtml(String(c.capability || "")) + "</code>→<code>" + escapeHtml(String(c.routed_to || "")) + "</code>" + risk;
        }).join("<br>");
        const host = row.host || "—";
        const hn = row.hostname ? ("<br><span class=\"muted\">" + escapeHtml(String(row.hostname)) + "</span>") : "";
        return (
          "<tr><td>" + escapeHtml(String(row.label || row.host || "—")) + "</td>" +
          "<td><code>" + escapeHtml(String(host)) + "</code>" + hn + "</td>" +
          "<td class=\"muted\">" + (caps || "—") + "</td></tr>"
        );
      }).join("");
      return (
        "<table class=\"jobs-cap-table\"><thead><tr>" +
        "<th>Appareil</th><th>IP / hostname</th><th>Capabilities suggérées</th>" +
        "</tr></thead><tbody>" + rows + "</tbody></table>"
      );
    }

    function jobsBuildNetworkDevicesTable(devices) {
      if (!Array.isArray(devices) || !devices.length) return "";
      const rows = devices.map(function (d) {
        const ok = d.reachable ? "OK" : "KO";
        const label = d.label || d.server_id || "—";
        const hint = d.device_hint ? (" <span class=\"muted\">[" + escapeHtml(String(d.device_hint)) + "]</span>") : "";
        const ports = Array.isArray(d.open_ports) && d.open_ports.length
          ? d.open_ports.join(", ")
          : (d.probe_results || []).filter(function (p) { return p.kind === "tcp" && p.ok; }).map(function (p) { return p.port; }).join(", ");
        const probes = (d.probe_results || []).map(function (p) {
          const lbl = p.label || p.kind || "?";
          if (p.kind === "http") return lbl + (p.ok ? " OK" : " KO");
          if (p.kind === "tcp") return lbl + " :" + p.port + (p.ok ? " open" : " closed");
          return lbl;
        }).join(", ");
        const detail = ports ? ("ports: " + ports) : probes;
        const hn = d.hostname ? ("<br><span class=\"muted\">" + escapeHtml(String(d.hostname)) + "</span>") : "";
        const caps = Array.isArray(d.action_suggestions) && d.action_suggestions.length
          ? d.action_suggestions.map(function (c) { return "<code>" + escapeHtml(String(c)) + "</code>"; }).join(" ")
          : "";
        return "<tr><td>" + escapeHtml(String(label)) + hint + "</td><td><code>" + escapeHtml(String(d.host || "")) + "</code>" + hn + "</td>" +
          "<td>" + ok + "</td><td class=\"muted\">" + escapeHtml(detail || "—") + "</td>" +
          "<td>" + (caps || "<span class=\"muted\">—</span>") + "</td></tr>";
      }).join("");
      return (
        "<table class=\"jobs-cap-table\"><thead><tr>" +
        "<th>Appareil</th><th>IP / hostname</th><th>État</th><th>Ports / sondes</th><th>Actions</th>" +
        "</tr></thead><tbody>" + rows + "</tbody></table>"
      );
    }

    function jobsExtractCapabilitiesCatalogStep(step) {
      const r = step && step.result;
      if (!r || typeof r !== "object") return null;
      const catalog = r.capabilities_catalog;
      if (!Array.isArray(catalog) || !catalog.length) return null;
      return {
        catalog: catalog,
        n: r.n_capabilities || catalog.length,
        ts: r.ts,
        reply: typeof r.reply === "string" ? r.reply : "",
      };
    }

    function jobsBuildReadableBlocks(job) {
      const blocks = [];
      const steps = job.steps || [];
      for (let c = 0; c < steps.length; c++) {
        const net = jobsExtractNetworkInventoryStep(steps[c]);
        if (net) {
          blocks.push({
            title: "Appareils LAN (instantané T — " + net.n + " hôte(s)" + (net.scan_cidr ? " · " + net.scan_cidr : "") + ")",
            html: jobsBuildNetworkDevicesTable(net.devices),
            devicesJson: JSON.stringify(net.devicesExport, null, 2),
            isHtml: true,
            primary: true,
          });
          if (net.reply) {
            blocks.push({ title: "Inventaire réseau (texte)", text: net.reply, primary: false });
          }
        }
        const inv = jobsExtractCapabilitiesCatalogStep(steps[c]);
        if (inv) {
          blocks.push({
            title: "Inventaire agents / capabilities (instantané T — " + inv.n + " entrées)",
            html: jobsBuildCapabilitiesCatalogTable(inv.catalog),
            catalogJson: JSON.stringify(inv.catalog, null, 2),
            isHtml: true,
            primary: !blocks.some(function (b) { return b.primary; }),
          });
          const mx = jobsExtractActionMatrixStep(steps[c]);
          if (mx) {
            blocks.push({
              title: "Matrice LAN × capabilities (" + mx.n + " appareil(s))",
              html: jobsBuildActionMatrixTable(mx.matrix),
              isHtml: true,
              primary: false,
            });
          }
          if (inv.reply) {
            blocks.push({ title: "Liste texte (copiable)", text: inv.reply, primary: false });
          }
          break;
        }
      }
      let synthesis = "";
      for (let i = steps.length - 1; i >= 0; i--) {
        if (steps[i].capability === "npc_dialogue" || steps[i].context_patch && steps[i].context_patch._job_synthesis) {
          synthesis = jobsExtractStepReply(steps[i]);
          if (synthesis) break;
        }
      }
      if (!synthesis) {
        for (let j = steps.length - 1; j >= 0; j--) {
          if (jobsExtractCapabilitiesCatalogStep(steps[j])) continue;
          synthesis = jobsExtractStepReply(steps[j]);
          if (synthesis) break;
        }
      }
      if (synthesis && !blocks.some(function (b) { return b.primary; })) {
        blocks.push({ title: "Synthèse", text: synthesis, primary: true });
      } else if (synthesis && blocks.length) {
        blocks.push({ title: "Synthèse", text: synthesis, primary: false });
      }
      for (let k = 0; k < steps.length; k++) {
        const sc = jobsExtractSelfcheckText(steps[k]);
        if (sc) blocks.push({ title: "Diagnostic DevOps", text: sc, primary: false });
      }
      if (!blocks.length && job.result_summary) {
        blocks.push({ title: "Résumé", text: String(job.result_summary), primary: true });
      }
      return blocks;
    }

    async function jobsCopyTextToClipboard(json, emptyMsg, okPrefix) {
      const hint = document.getElementById("jobs-catalog-copy-hint");
      if (!json) {
        if (hint) hint.textContent = emptyMsg;
        return;
      }
      const setHint = function (msg, err) {
        if (hint) {
          hint.textContent = msg;
          hint.style.color = err ? "#b91c1c" : "";
        }
      };
      setHint("Copie…", false);
      try {
        if (navigator.clipboard && navigator.clipboard.writeText) {
          await navigator.clipboard.writeText(json);
          setHint(okPrefix + " (" + json.length + " car.).", false);
          return;
        }
      } catch (_) {}
      try {
        const ta = document.createElement("textarea");
        ta.value = json;
        ta.setAttribute("readonly", "");
        ta.style.position = "fixed";
        ta.style.left = "-9999px";
        document.body.appendChild(ta);
        ta.select();
        const ok = document.execCommand("copy");
        document.body.removeChild(ta);
        if (ok) {
          setHint(okPrefix + " (" + json.length + " car.).", false);
          return;
        }
      } catch (_) {}
      setHint("Copie impossible (HTTPS ou permission presse-papiers).", true);
    }

    async function jobsCopyCatalogJson() {
      await jobsCopyTextToClipboard(__jobsCatalogJsonCopy, "Aucun catalogue à copier.", "JSON catalogue copié");
    }

    async function jobsCopyDevicesJson() {
      await jobsCopyTextToClipboard(__jobsDevicesJsonCopy, "Aucun inventaire appareils à copier.", "JSON appareils copié");
    }

    function jobsRenderReadable(job) {
      const wrap = document.getElementById("jobs-detail-readable");
      const body = document.getElementById("jobs-detail-readable-body");
      const toolbar = document.getElementById("jobs-detail-readable-toolbar");
      const copyHint = document.getElementById("jobs-catalog-copy-hint");
      if (!wrap || !body) return;
      const blocks = jobsBuildReadableBlocks(job);
      __jobsCatalogJsonCopy = null;
      __jobsDevicesJsonCopy = null;
      blocks.forEach(function (b) {
        if (b.catalogJson) __jobsCatalogJsonCopy = b.catalogJson;
        if (b.devicesJson) __jobsDevicesJsonCopy = b.devicesJson;
      });
      if (!blocks.length) {
        wrap.hidden = true;
        if (toolbar) toolbar.hidden = true;
        return;
      }
      wrap.hidden = false;
      if (toolbar) toolbar.hidden = !(__jobsCatalogJsonCopy || __jobsDevicesJsonCopy);
      if (copyHint && !__jobsCatalogJsonCopy && !__jobsDevicesJsonCopy) copyHint.textContent = "—";
      const copyDevBtn = document.getElementById("btn-jobs-copy-devices");
      const copyCatBtn = document.getElementById("btn-jobs-copy-catalog");
      if (copyDevBtn) copyDevBtn.style.display = __jobsDevicesJsonCopy ? "" : "none";
      if (copyCatBtn) copyCatBtn.style.display = __jobsCatalogJsonCopy ? "" : "none";
      wrap.classList.toggle("jobs-readable--muted", !blocks.some(function (b) { return b.primary; }));
      body.innerHTML = blocks
        .map(function (b) {
          const bodyHtml = b.isHtml && b.html
            ? '<div class="jobs-readable-text">' + b.html + "</div>"
            : '<div class="jobs-readable-text">' + escapeHtml(b.text || "") + "</div>";
          return (
            '<div class="jobs-readable-block">' +
            '<div class="jobs-readable-kicker">' + escapeHtml(b.title) + "</div>" +
            bodyHtml + "</div>"
          );
        })
        .join("");
    }

    function jobsRenderDetail(job) {
      __jobsSelectedJob = job;
      const empty = document.getElementById("jobs-detail-empty");
      const detail = document.getElementById("jobs-detail");
      if (!detail || !empty) return;
      empty.hidden = true;
      detail.hidden = false;

      const badge = document.getElementById("jobs-detail-status");
      if (badge) {
        badge.hidden = false;
        badge.textContent = job.status;
        badge.className = "assistant-route-badge jobs-badge jobs-badge--" + String(job.status || "");
      }
      const obj = document.getElementById("jobs-detail-objective");
      if (obj) obj.innerHTML = "<strong>Objectif :</strong> " + escapeHtml(job.objective || "") +
        " <span class='muted'>(" + escapeHtml(String(job.plan_source || "?")) + (job.pre_authorized ? ", pré-autorisé" : "") + ")</span>" +
        (job.result_summary ? "<br><span class='muted'>" + escapeHtml(job.result_summary) + "</span>" : "");

      // Boutons selon l'état.
      const approveBtn = document.getElementById("btn-jobs-approve");
      const approveTok = document.getElementById("jobs-approve-token");
      const advBtn = document.getElementById("btn-jobs-advance");
      const cancelBtn = document.getElementById("btn-jobs-cancel");
      const waiting = job.status === "waiting_approval";
      const terminal = job.status === "done" || job.status === "failed" || job.status === "cancelled";
      if (approveBtn) approveBtn.style.display = waiting ? "" : "none";
      if (approveTok) approveTok.style.display = waiting ? "" : "none";
      if (advBtn) advBtn.disabled = terminal || waiting;
      if (cancelBtn) cancelBtn.disabled = terminal;

      // Étapes.
      const stepsEl = document.getElementById("jobs-detail-steps");
      if (stepsEl) {
        const steps = job.steps || [];
        stepsEl.innerHTML = steps.length
          ? steps.map(function (s, i) {
              const dec = s.policy && s.policy.decision ? s.policy.decision : "";
              const att = s.max_attempts ? (s.attempts || 0) + "/" + s.max_attempts : (s.attempts || 0);
              let snippet = "";
              if (s.status === "done" && s.result) {
                if (s.capability === "devops_probe") snippet = jobsExtractSelfcheckText(s);
                else snippet = jobsExtractStepReply(s);
                if (snippet && snippet.length > 400) snippet = snippet.slice(0, 397) + "…";
              }
              
              let logHtml = "";
              if (s.error || (s.result && (s.result.stdout || s.result.stderr || s.result.error || s.result.exception || s.result.reply))) {
                let logText = "";
                if (s.error) logText += "Error: " + s.error + "\n";
                if (s.result) {
                  if (s.result.error) logText += "Result Error: " + s.result.error + "\n";
                  if (s.result.exception) logText += "Exception: " + s.result.exception + "\n";
                  if (s.result.stdout) logText += "STDOUT:\n" + s.result.stdout + "\n";
                  if (s.result.stderr) logText += "STDERR:\n" + s.result.stderr + "\n";
                  if (s.result.reply) {
                    logText += "Reply: " + (typeof s.result.reply === "object" ? JSON.stringify(s.result.reply, null, 2) : s.result.reply) + "\n";
                  }
                }
                if (logText.trim()) {
                  logHtml = '<details class="jobs-step-logs" style="margin-top: 0.4rem;">' +
                            '<summary style="font-size: 0.76rem; cursor: pointer; color: #38bdf8; font-weight: 600;">Afficher les logs de l\'étape</summary>' +
                            '<pre style="background: #1e293b; color: #f8fafc; padding: 0.5rem; border-radius: 4px; font-family: ui-monospace, monospace; font-size: 0.78rem; overflow-x: auto; margin-top: 0.25rem; white-space: pre-wrap; word-break: break-all; text-align: left;">' +
                            escapeHtml(logText.trim()) +
                            '</pre></details>';
                }
              }
              
              return (
                '<div class="jobs-step jobs-step--' + escapeHtml(String(s.status || "")) + '">' +
                "<strong>#" + (i + 1) + "</strong> " + escapeHtml(s.summary || s.capability || "") +
                ' <span class="jobs-step-cap">[' + escapeHtml(s.capability || "") + "]</span>" +
                ' <span class="jobs-badge jobs-badge--' + escapeHtml(String(s.status || "")) + '">' + escapeHtml(String(s.status || "")) + "</span>" +
                '<div class="muted" style="font-size:0.76rem;margin-top:0.15rem;">tentatives ' + escapeHtml(String(att)) +
                (dec ? " · policy " + escapeHtml(dec) : "") +
                (s.error ? ' · <span class="err">' + escapeHtml(s.error) + "</span>" : "") + "</div>" +
                (snippet ? '<div class="jobs-step-snippet">' + escapeHtml(snippet) + "</div>" : "") +
                logHtml +
                "</div>"
              );
            }).join("")
          : '<span class="muted">Aucune étape.</span>';
      }

      jobsRenderReadable(job);

      // Timeline.
      const tlEl = document.getElementById("jobs-detail-timeline");
      if (tlEl) {
        const events = (job.events || []).slice(-24);
        tlEl.innerHTML = events.length
          ? events.map(function (e) {
              const when = e.ts ? new Date(e.ts * 1000).toLocaleTimeString() : "";
              const extra = [];
              if (e.capability) extra.push(e.capability);
              if (e.decision) extra.push(e.decision);
              if (e.error) extra.push(e.error);
              if (typeof e.attempt !== "undefined") extra.push("essai " + e.attempt);
              return '<div class="jobs-tl-row"><code>' + escapeHtml(when) + "</code> · <strong>" +
                escapeHtml(e.kind || "") + "</strong>" + (extra.length ? " — " + escapeHtml(extra.join(" · ")) : "") + "</div>";
            }).join("")
          : '<span class="muted">—</span>';
      }

      const raw = document.getElementById("jobs-detail-raw");
      if (raw) raw.textContent = JSON.stringify(job, null, 2);
    }

    async function jobsAdvanceOnce(id) {
      const out = await postJson(getBase() + "/v1/pilot/jobs/" + encodeURIComponent(id) + "/advance", {});
      return out.json && out.json.ok !== false ? out.json : null;
    }

    async function jobsAdvanceLoop(id) {
      for (let i = 0; i < 24; i++) {
        const job = await jobsAdvanceOnce(id);
        if (!job) break;
        jobsRenderDetail(job);
        if (jobsIsTerminal(job.status)) break;
      }
    }

    async function jobsApprove() {
      if (!__jobsSelectedId) return;
      const tok = (document.getElementById("jobs-approve-token") || {}).value || "";
      if (!tok.trim()) { jobsHint("Token d'approbation requis.", true); return; }
      const out = await postJson(getBase() + "/v1/pilot/jobs/" + encodeURIComponent(__jobsSelectedId) + "/approve", { token: tok.trim() });
      if (out.status !== 200 || !out.json || out.json.ok === false) { jobsHint("Approbation refusée.", true); return; }
      jobsHint("Approuvé.");
      if (jobsManualAdvance()) await jobsAdvanceLoop(__jobsSelectedId);
      await jobsSelect(__jobsSelectedId);
      await jobsListRefresh();
    }

    async function jobsCancel() {
      if (!__jobsSelectedId) return;
      const out = await postJson(getBase() + "/v1/pilot/jobs/" + encodeURIComponent(__jobsSelectedId) + "/cancel", {});
      if (out.json && out.json.ok !== false) {
        await jobsSelect(__jobsSelectedId);
        await jobsListRefresh();
      }
    }

    function jobsClone() {
      if (!__jobsSelectedJob) return;
      const objEl = document.getElementById("jobs-objective");
      const ctxEl = document.getElementById("jobs-context");
      const modelEl = document.getElementById("jobs-model");
      const plannerEl = document.getElementById("jobs-planner");
      
      if (objEl) objEl.value = __jobsSelectedJob.objective || "";
      if (ctxEl) {
        const cleanContext = {};
        if (__jobsSelectedJob.base_context && typeof __jobsSelectedJob.base_context === "object") {
          for (const k in __jobsSelectedJob.base_context) {
            if (!k.startsWith("_")) {
              cleanContext[k] = __jobsSelectedJob.base_context[k];
            }
          }
        }
        ctxEl.value = JSON.stringify(cleanContext, null, 2);
      }
      
      if (__jobsSelectedJob.base_context) {
        const model = __jobsSelectedJob.base_context._planner_model || "";
        const planner = __jobsSelectedJob.base_context._planner || "";
        if (modelEl) modelEl.value = model;
        if (plannerEl) plannerEl.value = planner;
      }
      
      jobsHint("Champs clonés depuis le job #" + __jobsSelectedJob.id.slice(0, 8));
    }

    async function jobsLoadModels() {
      const select = document.getElementById("jobs-model");
      if (!select) return;
      const url = getBase() + "/v1/pilot/ollama/tags";
      const out = await jobsGet(url);
      
      const currentVal = select.value;
      select.innerHTML = '<option value="">(Par défaut du serveur)</option>';
      
      if (out.status === 200 && out.json && Array.isArray(out.json.models)) {
        out.json.models.forEach(function (m) {
          if (m && m.name) {
            const opt = document.createElement("option");
            opt.value = m.name;
            opt.textContent = m.name;
            select.appendChild(opt);
          }
        });
      }
      select.value = currentVal;
    }

    async function checkWaitingApprovalJobsGlobal() {
      const badge = document.getElementById("jobs-nav-badge");
      if (!badge) return;
      const url = getBase() + "/v1/pilot/jobs";
      const out = await jobsGet(url);
      if (out.status === 200 && out.json && Array.isArray(out.json.jobs)) {
        const hasWaiting = out.json.jobs.some(function (j) {
          return j && j.status === "waiting_approval";
        });
        badge.style.display = hasWaiting ? "inline-block" : "none";
      } else {
        badge.style.display = "none";
      }
    }

    function jobsBindPage() {
      if (__jobsBound) return;
      __jobsBound = true;
      const c = document.getElementById("btn-jobs-create");
      if (c) c.addEventListener("click", function () { jobsCreate().catch(function () {}); });
      const rf = document.getElementById("btn-jobs-refresh");
      if (rf) rf.addEventListener("click", function () { jobsListRefresh().catch(function () {}); });
      const ap = document.getElementById("btn-jobs-approve");
      if (ap) ap.addEventListener("click", function () { jobsApprove().catch(function () {}); });
      const ad = document.getElementById("btn-jobs-advance");
      if (ad) ad.addEventListener("click", function () {
        if (!__jobsSelectedId) return;
        jobsAdvanceOnce(__jobsSelectedId).then(function (j) { if (j) jobsRenderDetail(j); jobsListRefresh(); }).catch(function () {});
      });
      const cancel = document.getElementById("btn-jobs-cancel");
      if (cancel) cancel.addEventListener("click", function () { jobsCancel().catch(function () {}); });
      const clone = document.getElementById("btn-jobs-clone");
      if (clone) clone.addEventListener("click", jobsClone);
      const copyDev = document.getElementById("btn-jobs-copy-devices");
      if (copyDev) copyDev.addEventListener("click", function () { jobsCopyDevicesJson().catch(function () {}); });
      const copyCat = document.getElementById("btn-jobs-copy-catalog");
      if (copyCat) copyCat.addEventListener("click", function () { jobsCopyCatalogJson().catch(function () {}); });
      const filt = document.getElementById("jobs-filter-mine");
      if (filt) filt.addEventListener("change", function () { jobsListRefresh().catch(function () {}); });
    }

    function jobsPollStart() {
      jobsPollStop();
      __jobsPoll = window.setInterval(function () {
        jobsListRefresh().catch(function () {});
        if (__jobsSelectedId) jobsSelect(__jobsSelectedId, true).catch(function () {});
      }, 2800);
    }

    function jobsPollStop() {
      if (__jobsPoll) { window.clearInterval(__jobsPoll); __jobsPoll = null; }
      if (__jobsEventSource) { __jobsEventSource.close(); __jobsEventSource = null; }
    }

