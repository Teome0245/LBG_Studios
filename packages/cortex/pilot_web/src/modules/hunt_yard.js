/** Cour de chasse — Lia / Nix / Mira. Branche le hash #/hunt sur l'API Pilot. */

const TICK_MS = 140;

let _timer = null;
let _running = false;
let _bound = false;
let _last = null;

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

async function postHunt(path, body) {
  const r = await fetch(getBase() + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
  const j = await r.json();
  if (!r.ok || !j || j.ok === false) {
    throw new Error((j && (j.detail || j.error)) || ("HTTP " + r.status));
  }
  return j;
}

async function getHunt() {
  const r = await fetch(getBase() + "/v1/pilot/hunt-yard");
  return r.json();
}

function setHint(msg, isError) {
  const el = document.getElementById("hunt-hint");
  if (!el) return;
  el.textContent = msg || "—";
  el.style.color = isError ? "#a30" : "";
}

function drawYard(snap) {
  const canvas = document.getElementById("hunt-canvas");
  if (!canvas || !snap) return;
  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;
  const pad = 18;
  const sx = (w - pad * 2) / (snap.width || 28);
  const sy = (h - pad * 2) / (snap.height || 18);
  const px = (x) => pad + x * sx;
  const py = (y) => pad + y * sy;

  ctx.fillStyle = "#c4a574";
  ctx.fillRect(0, 0, w, h);
  ctx.fillStyle = "#d7be91";
  for (let i = 0; i < 18; i += 1) {
    ctx.fillRect(0, i * 22, w, 8);
  }
  ctx.strokeStyle = "#6b5344";
  ctx.lineWidth = 4;
  ctx.strokeRect(6, 6, w - 12, h - 12);

  ctx.fillStyle = "#8a6a4b";
  ctx.font = "12px ui-sans-serif, system-ui, sans-serif";
  ctx.fillText("porte Lost Heaven", 16, h - 14);

  (snap.loot || []).forEach((drop) => {
    ctx.fillStyle = "#e8d5a3";
    ctx.fillRect(px(drop.x) - 4, py(drop.y) - 4, 8, 8);
  });

  (snap.beasts || []).forEach((b) => {
    ctx.beginPath();
    ctx.fillStyle = b.alive ? "#4a3224" : "#9a8670";
    ctx.arc(px(b.x), py(b.y), b.alive ? 7 : 4, 0, Math.PI * 2);
    ctx.fill();
    if (b.alive) {
      ctx.fillStyle = "#3a2418";
      ctx.fillRect(px(b.x) - 10, py(b.y) - 14, 20 * (b.hp / b.hp_max), 3);
    }
  });

  (snap.players || []).forEach((p) => {
    ctx.beginPath();
    ctx.fillStyle = p.alive ? p.color : "#888";
    ctx.arc(px(p.x), py(p.y), 10, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = "#1b120c";
    ctx.lineWidth = 1.5;
    ctx.stroke();
    ctx.fillStyle = "#1b120c";
    ctx.font = "600 12px ui-sans-serif, system-ui, sans-serif";
    ctx.fillText(p.name, px(p.x) - 12, py(p.y) - 14);
    ctx.fillStyle = "#2f6b3a";
    ctx.fillRect(px(p.x) - 12, py(p.y) + 12, 24 * (p.hp / p.hp_max), 4);
  });
}

function renderHud(snap) {
  const hud = document.getElementById("hunt-hud");
  const logEl = document.getElementById("hunt-log");
  if (!snap) return;
  const statusFr = { ongoing: "en cours", victory: "victoire", defeat: "défaite" };
  const lines = (snap.players || []).map((p) => {
    const act = p.last_action || "idle";
    return `${p.name}  ${p.hp}/${p.hp_max} PV  ${act}  loot ${p.loot_count}`;
  });
  if (hud) {
    hud.innerHTML =
      `<strong>${statusFr[snap.status] || snap.status}</strong>` +
      ` · tick ${snap.tick} · kills ${snap.kills} · soins ${snap.heals}` +
      `<br>${lines.join("<br>")}`;
  }
  if (logEl) {
    const log = Array.isArray(snap.log) ? snap.log.slice().reverse() : [];
    logEl.textContent = log.join("\n") || "—";
  }
  const play = document.getElementById("btn-hunt-play");
  if (play) play.textContent = _running ? "Pause" : "Lancer";
}

function applySnap(snap) {
  _last = snap;
  drawYard(snap);
  renderHud(snap);
  if (snap.status && snap.status !== "ongoing") {
    stopLoop();
    setHint(snap.status === "victory" ? "Meute dispersée." : "Le chœur est à terre.", false);
  }
}

async function stepOnce(n) {
  const snap = await postHunt("/v1/pilot/hunt-yard/tick", { n: n || 1 });
  applySnap(snap);
}

function stopLoop() {
  _running = false;
  if (_timer !== null) {
    window.clearInterval(_timer);
    _timer = null;
  }
  const play = document.getElementById("btn-hunt-play");
  if (play) play.textContent = "Lancer";
}

function startLoop() {
  if (_running) return;
  _running = true;
  const play = document.getElementById("btn-hunt-play");
  if (play) play.textContent = "Pause";
  _timer = window.setInterval(() => {
    stepOnce(1).catch((e) => {
      stopLoop();
      setHint(String(e), true);
    });
  }, TICK_MS);
}

async function resetYard() {
  stopLoop();
  setHint("Nouvelle meute…", false);
  const snap = await postHunt("/v1/pilot/hunt-yard/reset", { seed: 1 + Math.floor(Math.random() * 99) });
  applySnap(snap);
  setHint("Prêt.", false);
}

function bindButtons() {
  if (_bound) return;
  _bound = true;
  const play = document.getElementById("btn-hunt-play");
  const step = document.getElementById("btn-hunt-step");
  const reset = document.getElementById("btn-hunt-reset");
  if (play) {
    play.addEventListener("click", () => {
      if (_running) stopLoop();
      else startLoop();
    });
  }
  if (step) {
    step.addEventListener("click", () => {
      stopLoop();
      stepOnce(1).catch((e) => setHint(String(e), true));
    });
  }
  if (reset) {
    reset.addEventListener("click", () => {
      resetYard().catch((e) => setHint(String(e), true));
    });
  }
}

export function huntYardBindPage() {
  bindButtons();
  getHunt()
    .then((snap) => {
      applySnap(snap);
      if (snap && snap.status === "ongoing" && snap.tick === 0) startLoop();
    })
    .catch((e) => setHint(String(e), true));
}

export function huntYardStop() {
  stopLoop();
}

export function installHuntYard() {
  const App = globalThis.PilotApp || (globalThis.PilotApp = {});
  App.huntYardBindPage = huntYardBindPage;
  App.huntYardStop = huntYardStop;

  const origParse = App.pilotParseRoute;
  App.pilotParseRoute = function huntParseRoute() {
    const raw = (location.hash || "").replace(/^#/, "").replace(/^\//, "");
    const pathOnly = raw.split("?")[0];
    const parts = pathOnly.split("/").filter(Boolean);
    if (parts[0] === "hunt" || parts[0] === "chasse") return "hunt";
    return typeof origParse === "function" ? origParse() : "home";
  };

  const origApply = App.pilotApplyRoute;
  App.pilotApplyRoute = function huntApplyRoute() {
    if (typeof origApply === "function") origApply();
    const r = App.pilotParseRoute();
    const page = document.getElementById("pilot-page-hunt");
    if (page) page.hidden = r !== "hunt";
    const jeu = document.querySelector('#pilot-nav .pilot-nav-group[data-nav-group="jeu"]');
    if (jeu && r === "hunt") jeu.classList.add("pilot-nav-active");
    if (r === "hunt") huntYardBindPage();
    else huntYardStop();
  };
}
