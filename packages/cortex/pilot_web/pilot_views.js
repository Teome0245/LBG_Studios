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
          "<strong>Bienvenue — Compagnon</strong><br>" +
          "Je suis là pour dialoguer, concevoir et agir sous ton contrôle. " +
          "Pose une question en langage naturel : je route vers la bonne compétence " +
          "(équipe, projet, Godot, infra…) et je réponds factuellement. " +
          "<strong>Envoyer</strong> pour parler, <strong>Proposer une action</strong> (mode Ops) pour exécuter avec garde-fous.</div>";
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
