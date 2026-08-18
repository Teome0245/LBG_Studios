    /**
     * Texte brut → HTML sûr : échappement + liens http(s) + pastilles « copier » pour chemins docs/ / infra/.
     */
    function pmRichFormat(raw) {
      const s = String(raw || "");
      const re = /(https?:\/\/[^\s<]+)|(\b(?:docs|infra)\/[A-Za-z0-9_.\/-]+(?:\.md|\.sh)?\b)/g;
      const chunks = [];
      let idx = 0;
      let m;
      while ((m = re.exec(s)) !== null) {
        if (m.index > idx) chunks.push({ type: "t", v: s.slice(idx, m.index) });
        if (m[1]) chunks.push({ type: "url", v: m[1] });
        else if (m[2]) chunks.push({ type: "path", v: m[2] });
        idx = m.index + m[0].length;
      }
      if (idx < s.length) chunks.push({ type: "t", v: s.slice(idx) });
      return chunks
        .map(function (c) {
          if (c.type === "t") return escapeHtmlPm(c.v).replace(/\n/g, "<br>");
          if (c.type === "url") {
            const u = c.v;
            const href = u.replace(/"/g, "%22");
            return (
              '<a href="' +
              href +
              '" target="_blank" rel="noopener noreferrer">' +
              escapeHtmlPm(u) +
              "</a>"
            );
          }
          const p = c.v;
          return (
            '<button type="button" class="pm-path-chip" data-copy="' +
            escapeHtmlPm(p) +
            '" title="Copier le chemin (repo LBG_Studios)">' +
            escapeHtmlPm(p) +
            "</button>"
          );
        })
        .join("");
    }

    function renderPmEncarts(brief) {
      const wrap = document.getElementById("pm-encarts");
      const wStep = document.getElementById("pm-encart-step-wrap");
      const wFa = document.getElementById("pm-encart-fa-wrap");
      const elStep = document.getElementById("pm-encart-step");
      const elFa = document.getElementById("pm-encart-fa");
      if (!wrap || !wStep || !wFa || !elStep || !elFa) return;
      if (!brief || typeof brief !== "object") {
        wrap.style.display = "none";
        wStep.hidden = true;
        wFa.hidden = true;
        return;
      }
      const step = typeof brief.current_step === "string" ? brief.current_step.trim() : "";
      const fa = typeof brief.file_attente === "string" ? brief.file_attente.trim() : "";
      let any = false;
      if (step) {
        wStep.hidden = false;
        elStep.innerHTML = pmRichFormat(step);
        any = true;
      } else {
        wStep.hidden = true;
        elStep.innerHTML = "";
      }
      if (fa) {
        wFa.hidden = false;
        elFa.innerHTML = pmRichFormat(fa);
        any = true;
      } else {
        wFa.hidden = true;
        elFa.innerHTML = "";
      }
      wrap.style.display = any ? "grid" : "none";
    }

    function buildPmMarkdownFromBrief(brief) {
      if (!brief || typeof brief !== "object") return "# Brief chef de projet\n\n_(vide)_\n";
      let md = "# Brief chef de projet\n\n";
      md += "_Généré depuis le stub PM (pilot)._\n\n";
      if (brief.current_step) md += "## Étape actuelle\n\n" + String(brief.current_step).trim() + "\n\n";
      if (brief.file_attente) md += "## File d'attente\n\n" + String(brief.file_attente).trim() + "\n\n";
      const ms = brief.milestones;
      if (Array.isArray(ms) && ms.length) {
        md += "## Jalons\n\n";
        ms.forEach(function (m) {
          md += "- **" + (m.date || "") + "** — " + (m.summary || "").replace(/\n/g, " ") + "\n";
        });
        md += "\n";
      }
      const ts = brief.tasks;
      if (Array.isArray(ts) && ts.length) {
        md += "## Tâches\n\n";
        ts.forEach(function (t) {
          md += "- [ ] " + (t.title || "") + " _" + (t.source || "") + "_\n";
        });
        md += "\n";
      }
      return md;
    }

    function pmExtractBrief(resp) {
      if (!resp || typeof resp !== "object") return null;
      if (resp.brief && typeof resp.brief === "object") return resp.brief;
      if (resp.output && typeof resp.output === "object" && resp.output.brief && typeof resp.output.brief === "object")
        return resp.output.brief;
      const r = resp.result;
      if (
        r &&
        typeof r === "object" &&
        r.output &&
        typeof r.output === "object" &&
        r.output.brief &&
        typeof r.output.brief === "object"
      )
        return r.output.brief;
      return null;
    }

