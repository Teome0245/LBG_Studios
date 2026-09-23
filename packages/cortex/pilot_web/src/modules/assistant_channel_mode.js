/** Canal unique — routage Discuter/Piloter automatique (indicateur seulement). */

const STORAGE_FORCE = "lbg_pilot_assistant_channel_force_v1"; // "" | discuter | piloter

function getForceMode() {
  try {
    const v = localStorage.getItem(STORAGE_FORCE);
    if (v === "discuter" || v === "piloter") return v;
  } catch (_) {}
  return "";
}

function setForceMode(mode) {
  const m = mode === "discuter" || mode === "piloter" ? mode : "";
  try {
    if (m) localStorage.setItem(STORAGE_FORCE, m);
    else localStorage.removeItem(STORAGE_FORCE);
  } catch (_) {}
  return m;
}

/**
 * Heuristique locale (rapide) — intention ops vs réflexion.
 * @returns {"discuter"|"piloter"}
 */
export function classifyChannelIntent(text) {
  const t = String(text || "").trim();
  if (!t) return "discuter";

  // Mentions agents / préfixes Orch
  if (/(^|\s)@(iris|themis|lyra|forge|devops|team)\b/i.test(t)) return "piloter";
  if (/^(team|cursor|diagnostic)\s*:/i.test(t)) return "piloter";

  // Actions / ops LAN
  if (
    /\b(ouvre|ouvrir|lance|lancer|ex[eé]cute|ex[eé]cuter|kill|red[eé]marre|red[eé]marrer|d[eé]ploie|d[eé]ployer|installe|installer)\b/i.test(
      t
    )
  ) {
    return "piloter";
  }
  if (
    /\b(diagnostic|selfcheck?|sant[eé]|status|statut|probe|notepad|mail|imap|desktop|godot|launchpad|forge|dry-?run|capability|approbation)\b/i.test(
      t
    )
  ) {
    return "piloter";
  }
  if (/\b(v[eé]rifie|v[eé]rifier|check|teste|tester)\b.+\b(service|backend|orchestrateur|ollama|agent|lan)\b/i.test(t)) {
    return "piloter";
  }

  // Réflexion / produit / idées
  if (
    /\b(id[eé]e|am[eé]lior|[eé]volut|refacto|architecture|comment\s+(pourrait|on\s+pourrait)|et\s+si|r[eé]fl[eé]chis|brainstorm|spec|cahier\s+des\s+charges|roadmap|pourquoi|explique)\b/i.test(
      t
    )
  ) {
    return "discuter";
  }

  // Questions ouvertes → discussion
  if (/\?$/.test(t) && !/\b(status|statut|diagnostic|sant[eé])\b/i.test(t)) {
    return "discuter";
  }

  // Par défaut : discussion (safe — pas d’action)
  return "discuter";
}

function resolveModeForText(text) {
  const force = getForceMode();
  if (force) return force;
  return classifyChannelIntent(text);
}

function applyModeChrome(mode, meta) {
  const m = mode === "piloter" ? "piloter" : "discuter";
  const page = document.getElementById("pilot-page-assistant");
  if (page) page.dataset.assistantMode = m;
  document.body.dataset.assistantMode = m;

  const badge = document.getElementById("assistant-mode-badge");
  if (badge) {
    badge.textContent = m === "discuter" ? "Canal · réflexion" : "Canal · ops";
  }

  const ind = document.getElementById("assistant-mode-indicator");
  if (ind) {
    const forced = !!getForceMode();
    ind.textContent =
      (forced ? "forcé · " : "auto · ") + (m === "discuter" ? "réflexion" : "ops");
    ind.classList.toggle("assistant-mode-indicator--ops", m === "piloter");
    ind.title = forced
      ? "Forçage manuel (Options). Effacer pour revenir à l’auto."
      : "Routage automatique selon le message (comme Cursor).";
  }

  const lead = document.getElementById("assistant-mode-lead");
  if (lead) {
    lead.textContent =
      m === "discuter"
        ? "Réflexion — pas d’actions LAN sur ce tour."
        : "Ops détecté — proposer / exécuter disponibles.";
  }

  if (meta && meta.source === "preview") {
    /* avant envoi : pas de toast */
  }
}

export function previewChannelModeFromDraft() {
  const ta = document.getElementById("assistant-text");
  const text = ta && ta.value ? ta.value : "";
  if (getForceMode()) {
    applyModeChrome(getForceMode(), { source: "preview" });
    return getForceMode();
  }
  if (!String(text).trim()) {
    applyModeChrome("discuter", { source: "preview" });
    return "discuter";
  }
  const m = classifyChannelIntent(text);
  applyModeChrome(m, { source: "preview" });
  return m;
}

export function applyChannelModeForMessage(text) {
  const m = resolveModeForText(text);
  applyModeChrome(m, { source: "send" });
  return m;
}

function bindForceControls() {
  const sel = document.getElementById("assistant-channel-force");
  if (!sel || sel.dataset.bound) return;
  sel.dataset.bound = "1";
  sel.value = getForceMode() || "auto";
  sel.addEventListener("change", function () {
    const raw = sel.value;
    const v = raw === "discuter" || raw === "piloter" ? raw : "";
    setForceMode(v);
    previewChannelModeFromDraft();
  });
}

function bindDraftPreview() {
  const ta = document.getElementById("assistant-text");
  if (!ta || ta.dataset.channelPreviewBound) return;
  ta.dataset.channelPreviewBound = "1";
  let timer = null;
  function schedule() {
    if (timer) clearTimeout(timer);
    timer = setTimeout(function () {
      previewChannelModeFromDraft();
    }, 220);
  }
  ta.addEventListener("input", schedule);
  ta.addEventListener("change", schedule);
}

export function installAssistantChannelMode() {
  const App = globalThis.PilotApp || (globalThis.PilotApp = {});
  bindForceControls();
  bindDraftPreview();
  previewChannelModeFromDraft();

  const origPropose = App.assistantPropose;
  App.assistantPropose = async function gatedPropose() {
    const ta = document.getElementById("assistant-text");
    const mode = applyChannelModeForMessage(ta && ta.value ? ta.value : "");
    if (mode !== "piloter") {
      if (App.assistantUiHint) {
        App.assistantUiHint(
          "Intention « réflexion » — reformule en action, ou force « Piloter » dans Options.",
          true
        );
      }
      return;
    }
    if (typeof origPropose === "function") return origPropose();
  };

  const origExecute = App.assistantExecute;
  App.assistantExecute = async function gatedExecute(execMode) {
    if ((document.body.dataset.assistantMode || "") !== "piloter") {
      if (App.assistantUiHint) {
        App.assistantUiHint("Exécution réservée au mode ops (auto ou forcé).", true);
      }
      return;
    }
    if (typeof origExecute === "function") return origExecute(execMode);
  };

  const origApply = App.pilotApplyRoute;
  App.pilotApplyRoute = function channelModeApplyRoute() {
    if (typeof origApply === "function") origApply();
    const r = App.pilotParseRoute ? App.pilotParseRoute() : "";
    if (r === "assistant") previewChannelModeFromDraft();
  };

  App.assistantClassifyChannelIntent = classifyChannelIntent;
  App.assistantApplyChannelModeForMessage = applyChannelModeForMessage;
  App.assistantPreviewChannelMode = previewChannelModeFromDraft;
  App.assistantGetChannelMode = function () {
    return document.body.dataset.assistantMode === "piloter" ? "piloter" : "discuter";
  };
}
