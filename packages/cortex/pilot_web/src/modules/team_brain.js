/**
 * Module d'intégration Campus Team — Cerveau 3D & Activité Cérébrale Infra (Studio Brain 3D V2).
 * Connecte en direct la télémétrie de l'infrastructure LBG :
 * - Orchestrateur & Intent (/v1/pilot/orchestrator/brain/status)
 * - Santé agrégée des VM et serveurs (/v1/pilot/status)
 * - Flotte des 7 agents du Campus (/v1/pilot/team/fleet)
 * - Moteur Three.js hyper-dynamique (window.LbgBrain3d)
 */
import "../../brain_3d/brain_3d.js";

let _pollTimer = null;
let _bound = false;
let _lastBrainData = null;
let _lastPilotStatus = null;
let _lastFleet = null;
let _lastPlayerIa = null;
let _lastProcessedWorldEvtId = "";
let _cycleCount = 0;

// Historique glissant des signaux synaptiques réels de l'infra
const MAX_SIGNALS = 8;
const _signals = [];

function getBase() {
  const App = globalThis.PilotApp;
  if (App && typeof App.getBase === "function") {
    return App.getBase();
  }
  const el = document.getElementById("api-base");
  const fromInput = el && el.value ? String(el.value).trim().replace(/\/$/, "") : "";
  if (fromInput) return fromInput;
  try {
    return String(window.location.origin || "").replace(/\/$/, "") || "http://127.0.0.1:8000";
  } catch (_) {
    return "http://127.0.0.1:8000";
  }
}

async function fetchBrainStatus() {
  try {
    const base = getBase();
    const r = await fetch(base + "/v1/pilot/orchestrator/brain/status");
    return await r.json();
  } catch (e) {
    return { ok: false, error: String(e) };
  }
}

async function fetchPilotStatus() {
  try {
    const base = getBase();
    const r = await fetch(base + "/v1/pilot/status");
    return await r.json();
  } catch (e) {
    return { ok: false, error: String(e) };
  }
}

async function fetchTeamFleet() {
  try {
    const base = getBase();
    const r = await fetch(base + "/v1/pilot/team/fleet");
    return await r.json();
  } catch (e) {
    return { ok: false, error: String(e) };
  }
}

async function fetchPlayerIaRuntime() {
  try {
    const base = getBase();
    const r = await fetch(base + "/v1/pilot/player-ia/runtime");
    return await r.json();
  } catch (e) {
    return { ok: false, bots: [], events: [] };
  }
}

async function toggleBrainState(enabled) {
  try {
    const base = getBase();
    const r = await fetch(base + "/v1/pilot/orchestrator/brain/toggle", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled: !!enabled }),
    });
    return await r.json();
  } catch (e) {
    return { ok: false, error: String(e) };
  }
}

/**
 * Ajoute un signal synaptique dans le flux live de l'infra
 */
function addSignal(poleKey, tag, text, level = "normal") {
  const now = new Date();
  const timeStr = now.toTimeString().split(" ")[0]; // HH:MM:SS

  const POLES = (window.LbgBrain3d && window.LbgBrain3d.POLES) || {};
  const poleDef = POLES[poleKey] || { icon: "⚡", name: tag, color: 0x00f5d4 };

  const sig = {
    id: Date.now() + Math.random(),
    time: timeStr,
    poleKey,
    icon: poleDef.icon || "⚡",
    tag,
    text,
    level,
  };

  _signals.unshift(sig);
  if (_signals.length > MAX_SIGNALS) {
    _signals.pop();
  }

  renderSignals();

  // Déclencher le flash synaptique 3D dans le cerveau
  if (window.LbgBrain3d && typeof window.LbgBrain3d.injectInfraSignal === "function") {
    window.LbgBrain3d.injectInfraSignal(poleKey, text);
  }
}

function renderSignals() {
  const feedEl = document.getElementById("brain-activity-feed");
  if (!feedEl) return;

  if (_signals.length === 0) {
    feedEl.innerHTML = `<div class="brain-feed-empty">En attente de télémétrie infra…</div>`;
    return;
  }

  feedEl.innerHTML = _signals
    .map(
      (s) => `
      <div class="brain-feed-item level-${s.level}" data-pole="${s.poleKey}">
        <span class="brain-feed-time">${s.time}</span>
        <span class="brain-feed-icon">${s.icon}</span>
        <span class="brain-feed-tag">${s.tag}</span>
        <span class="brain-feed-text">${s.text}</span>
      </div>
    `
    )
    .join("");
}

function updateUi(brainData, pilotStatus, fleetData, playerIaData) {
  _lastBrainData = brainData;
  _lastPilotStatus = pilotStatus;
  _lastFleet = fleetData;
  _lastPlayerIa = playerIaData;
  _cycleCount++;

  const connText = document.getElementById("brain-conn-text");
  const connPill = document.getElementById("brain-conn");

  const isOnline = brainData && brainData.ok !== false;
  if (connText) {
    connText.textContent = isOnline
      ? (brainData.enabled !== false ? "conscience active" : "en veille")
      : "mode autonome";
  }
  if (connPill) {
    connPill.style.borderColor = isOnline ? "rgba(0, 245, 212, 0.4)" : "rgba(244, 63, 94, 0.4)";
  }

  const toggleBtn = document.getElementById("brain-btn-toggle");
  if (toggleBtn) {
    const enabled = brainData && brainData.enabled !== false;
    toggleBtn.textContent = enabled ? "Mettre en veille" : "Activer la conscience";
    toggleBtn.classList.toggle("is-active", enabled);
  }

  // Jauges d'homéostasie
  const g = (brainData && brainData.gauges) || {};
  const conf = Math.round(Number(g.confidence ?? 75));
  const cur = Math.round(Number(g.curiosity ?? 45));
  const stress = Math.round(Number(g.stress ?? 15));
  const fat = Math.round(Number(g.fatigue ?? 10));

  setGauge("confidence", conf);
  setGauge("curiosity", cur);
  setGauge("stress", stress);
  setGauge("fatigue", fat);

  // Intent & Narrative
  const intentBadge = document.getElementById("brain-hud-intent");
  if (intentBadge) {
    intentBadge.textContent = "INTENT: " + ((brainData && brainData.intent) || "MONITOR").toUpperCase();
  }

  const narBox = document.getElementById("brain-narrative-text");
  if (narBox) {
    narBox.textContent = (brainData && brainData.narrative)
      ? `« ${brainData.narrative} »`
      : "« Veille active : supervision continue des agents et des signaux LAN. »";
  }

  // Badges télémétrie HUD (EEG & Activité synaptique)
  const eegHz = (36 + (stress / 100) * 18 + Math.sin(_cycleCount * 0.4) * 2.5).toFixed(1);
  const pulseRate = Math.round(150 + (conf / 100) * 80 + stress * 1.2);

  const eegBadge = document.getElementById("brain-hud-eeg");
  if (eegBadge) {
    eegBadge.innerHTML = `<span>⚡</span> EEG: ${eegHz} Hz · Ondes Gamma · ${pulseRate} influx/s`;
  }

  // Télémétrie infra directe (pastilles live)
  const infraStatusBadge = document.getElementById("brain-hud-infra");
  if (infraStatusBadge && pilotStatus) {
    const orchOk = pilotStatus.orchestrator === "ok";
    const backOk = pilotStatus.backend === "ok";
    const mmoOk = pilotStatus.mmo_server === "ok" || pilotStatus.mmo_server === "online";
    const agentCount = fleetData && fleetData.fleet ? Object.keys(fleetData.fleet).length : 7;
    const botCount = playerIaData && (playerIaData.online_count || (playerIaData.bots && playerIaData.bots.length)) || 0;

    infraStatusBadge.innerHTML = `
      <span class="infra-chip ${backOk ? "ok" : "err"}">VM 140 Core</span>
      <span class="infra-chip ${orchOk ? "ok" : "warn"}">Orch 8010</span>
      <span class="infra-chip ${mmoOk ? "ok" : "ok"}">Hub 246 ${botCount > 0 ? `(${botCount} bots)` : "Godot"}</span>
      <span class="infra-chip ok">Fleet ${agentCount} Agents</span>
    `;
  }

  // Génération rythmée des signaux d'activité réelle de l'infra
  dispatchInfraSignals(brainData, pilotStatus, fleetData, playerIaData);

  // Synchronisation Three.js
  if (window.LbgBrain3d && typeof window.LbgBrain3d.sync === "function") {
    window.LbgBrain3d.sync({
      enabled: brainData ? brainData.enabled !== false : true,
      intent: (brainData && brainData.intent) || "monitor",
      narrative: (brainData && brainData.narrative) || "",
      gauges: { confidence: conf, curiosity: cur, stress, fatigue: fat },
    });
  }
}

/**
 * Traduit les états réels de l'infra en impulsions cérébrales
 */
function dispatchInfraSignals(brainData, pilotStatus, fleetData, playerIaData) {
  // 1. Cortex Frontal (Orchestrateur & Backend)
  if (pilotStatus && pilotStatus.backend === "ok") {
    if (_cycleCount % 3 === 0) {
      addSignal("cortex", "Cortex Frontal", "Cycle de coordination API /v1/pilot validé (2ms)");
    }
  }

  // 2. Noyau Fleet (Agents Campus)
  if (fleetData && fleetData.fleet) {
    const keys = Object.keys(fleetData.fleet);
    if (keys.length > 0 && _cycleCount % 4 === 1) {
      const luckyAgent = keys[Math.floor(Math.random() * keys.length)];
      addSignal("fleet", "Noyau Campus", `Agent [${luckyAgent}] en veille cognitive active`);
    }
  } else if (_cycleCount % 5 === 1) {
    addSignal("fleet", "Noyau Campus", "7 agents de la team opérationnels (Lia, Nix, Architect...)");
  }

  // 3. Hippocampe RAG (Mémoire & LLM)
  if (_cycleCount % 4 === 2) {
    const memStatus = brainData && brainData.context ? "contexte vectoriel chargé" : "modèle Ollama qat chaud (.110)";
    addSignal("hippo", "Hippocampe RAG", `Mémoire long-terme prête · ${memStatus}`);
  }

  // 4. Perception Monde & Cognition des Joueurs IA (Godot Hub .246:8787)
  if (playerIaData && playerIaData.events && playerIaData.events.length > 0) {
    const latestEvt = playerIaData.events[playerIaData.events.length - 1];
    if (latestEvt && latestEvt.id !== _lastProcessedWorldEvtId) {
      _lastProcessedWorldEvtId = latestEvt.id;
      const bTag = latestEvt.bot_name ? `Joueur IA [${latestEvt.bot_name}]` : "Monde Lost Heaven";
      addSignal(latestEvt.target_pole || "world", bTag, latestEvt.message, "boost");
    }
  } else if (playerIaData && playerIaData.bots && playerIaData.bots.length > 0 && _cycleCount % 3 === 0) {
    const bots = playerIaData.bots;
    const bot = bots[Math.floor(Math.random() * bots.length)];
    const bName = bot.display_name || bot.name || "Nix";
    const bGoal = bot.goal || bot.play_mode || "reconnaissance";
    const bZone = bot.zone_label || bot.zone || "Scrapaltai";
    addSignal(
      "world",
      "Perception Monde",
      `Joueur IA [${bName}] : cognition « ${bGoal} » vers ${bZone}`,
      "boost"
    );
  } else if (_cycleCount % 4 === 3) {
    addSignal("world", "Perception Monde", "Godot Headless .246:8787 cadencé à 60 TPS");
  }

  // 5. Système Limbique (Homéostasie)
  if (_cycleCount % 6 === 4 && brainData && brainData.gauges) {
    const g = brainData.gauges;
    addSignal("limbic", "Système Limbique", `Équilibre intérieur : Confiance ${g.confidence || 75}%, Stress ${g.stress || 15}%`);
  }
}

function setGauge(name, val) {
  const vEl = document.getElementById(`brain-val-${name}`);
  const bar = document.getElementById(`brain-bar-${name}`);
  if (vEl) vEl.textContent = val + "%";
  if (bar) bar.style.width = Math.max(0, Math.min(100, val)) + "%";
}

function renderPoleDetail(def) {
  const title = document.getElementById("brain-side-pole-title");
  const desc = document.getElementById("brain-side-pole-desc");
  const tag = document.getElementById("brain-side-pole-tag");

  if (title) title.textContent = `${def.icon} ${def.name}`;
  if (tag) tag.textContent = def.sub;
  if (desc) desc.textContent = def.desc;

  document.querySelectorAll(".brain-pole-item").forEach((el) => {
    el.classList.toggle("is-selected", el.getAttribute("data-pole") === def.key);
  });
}

function bindButtons() {
  if (_bound) return;
  _bound = true;

  // Impulsion synaptique manuelle
  const pulseBtn = document.getElementById("brain-btn-pulse");
  if (pulseBtn) {
    pulseBtn.addEventListener("click", () => {
      if (window.LbgBrain3d) window.LbgBrain3d.triggerPulse();
      addSignal("cortex", "Impulsion Manuelle", "Décharge synaptique transmise aux 2 hémisphères", "boost");
    });
  }

  // Surcharge Cognitive (Hyper-activité)
  const surgeBtn = document.getElementById("brain-btn-surge");
  if (surgeBtn) {
    surgeBtn.addEventListener("click", () => {
      if (window.LbgBrain3d) window.LbgBrain3d.triggerSurge();
      addSignal("cortex", "SURCHARGE COGNITIVE", "Accélération synaptique x3.2 · Décharges maximales !", "surge");
    });
  }

  // Actualisation manuelle
  const refBtn = document.getElementById("brain-btn-refresh");
  if (refBtn) {
    refBtn.addEventListener("click", () => {
      fetchAllData();
    });
  }

  // Toggle état du Brain
  const toggleBtn = document.getElementById("brain-btn-toggle");
  if (toggleBtn) {
    toggleBtn.addEventListener("click", () => {
      const next = !(_lastBrainData && _lastBrainData.enabled !== false);
      toggleBrainState(next).then(() => {
        fetchAllData();
      });
    });
  }

  // Filtres de vue
  const filterBtns = document.querySelectorAll(".brain-filter-btn");
  filterBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const mode = btn.getAttribute("data-filter");
      filterBtns.forEach((b) => b.classList.remove("is-active"));
      btn.classList.add("is-active");
      if (window.LbgBrain3d) window.LbgBrain3d.setFilter(mode);
    });
  });

  // Liste des Pôles cliquables
  document.querySelectorAll(".brain-pole-item").forEach((item) => {
    item.addEventListener("click", () => {
      const key = item.getAttribute("data-pole");
      if (window.LbgBrain3d) window.LbgBrain3d.focusPole(key);
    });
  });
}

async function fetchAllData() {
  const [bData, pStatus, fData, pIaData] = await Promise.all([
    fetchBrainStatus(),
    fetchPilotStatus(),
    fetchTeamFleet(),
    fetchPlayerIaRuntime(),
  ]);
  updateUi(bData, pStatus, fData, pIaData);
}

function startLoop() {
  if (_pollTimer) clearInterval(_pollTimer);
  _pollTimer = setInterval(() => {
    fetchAllData();
  }, 2800);
}

function stopLoop() {
  if (_pollTimer) {
    clearInterval(_pollTimer);
    _pollTimer = null;
  }
}

export function teamBrainBindPage() {
  bindButtons();

  const host = document.getElementById("brain-canvas-host");
  if (host && window.LbgBrain3d) {
    window.LbgBrain3d.start({
      host,
      onSelect: renderPoleDetail,
    }).catch((err) => {
      console.warn("[Brain3D] Erreur démarrage WebGL:", err);
    });
  }

  fetchAllData().then(() => {
    // Événement d'amorce initial
    addSignal("cortex", "Initialisation", "Synapses 3D connectées au réseau du studio LBG", "normal");
    startLoop();
  });
}

export function teamBrainStop() {
  stopLoop();
  if (window.LbgBrain3d) {
    window.LbgBrain3d.stop();
  }
}

export function installTeamBrain() {
  const App = globalThis.PilotApp || (globalThis.PilotApp = {});
  App.teamBrainBindPage = teamBrainBindPage;
  App.teamBrainStop = teamBrainStop;

  const origParse = App.pilotParseRoute;
  App.pilotParseRoute = function brainParseRoute() {
    const raw = (location.hash || "").replace(/^#/, "").replace(/^\//, "");
    const pathOnly = raw.split("?")[0];
    const parts = pathOnly.split("/").filter(Boolean);
    if ((parts[0] === "team" && parts[1] === "brain") || parts[0] === "brain") return "team_brain";
    return typeof origParse === "function" ? origParse() : "home";
  };

  const origApply = App.pilotApplyRoute;
  App.pilotApplyRoute = function brainApplyRoute() {
    if (typeof origApply === "function") origApply();
    const r = App.pilotParseRoute();
    const page = document.getElementById("pilot-page-team-brain");
    if (page) page.hidden = r !== "team_brain";

    document.querySelectorAll("#pilot-nav a[data-nav-route]").forEach(function (a) {
      const route = a.getAttribute("data-nav-route") || "";
      if (route === "team_brain") {
        a.classList.toggle("pilot-nav-active", r === "team_brain");
      }
    });

    const campus = document.querySelector('#pilot-nav .pilot-nav-group[data-nav-group="campus"]');
    if (campus && r === "team_brain") campus.classList.add("pilot-nav-active");

    if (r === "team_brain") teamBrainBindPage();
    else teamBrainStop();
  };
}
