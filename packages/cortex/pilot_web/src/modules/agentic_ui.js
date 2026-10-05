/** Phase C — bannière job agentique (lien Pilot Jobs) sans régénérer les chunks legacy. */

function esc(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function agenticBannerHtml(out) {
  if (!out || !out.agentic || !out.job_id) return "";
  const jid = String(out.job_id);
  const href = out.pilot_jobs_href || "#/jobs?job=" + encodeURIComponent(jid);
  return (
    '<div style="margin:0.5rem 0;padding:0.75rem;border:1px solid #9ec9b0;border-radius:6px;background:#f0faf4;">' +
    '<div style="font-weight:600;">Mode agentique — job de fond</div>' +
    '<div class="muted" style="margin-top:0.25rem;">' +
    esc(out.reply || "") +
    "</div>" +
    '<div style="margin-top:0.45rem;"><a href="' +
    esc(href) +
    '">Ouvrir le job #' +
    esc(jid.slice(0, 8)) +
    "</a> · statut <code>" +
    esc(out.status || "?") +
    "</code></div></div>"
  );
}

export function installAgenticUi() {
  const App = globalThis.PilotApp || (globalThis.PilotApp = {});
  if (App.__agenticPrettyPatched) return;

  function patch() {
    const orig = App.renderPretty;
    if (typeof orig !== "function") return false;
    App.__agenticPrettyPatched = true;
    App.renderPretty = function patchedRenderPretty(root) {
      let html = "";
      try {
        html = orig(root) || "";
      } catch (_) {
        html = "";
      }
      const out = root && root.result && root.result.output;
      const banner = agenticBannerHtml(out);
      return banner ? banner + html : html;
    };
    return true;
  }

  if (!patch()) {
    // Chunks enregistrés juste avant ; un tick suffit en général.
    setTimeout(function () {
      patch();
    }, 0);
  }
}
