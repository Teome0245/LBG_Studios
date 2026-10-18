"use strict";

const {
  app,
  BrowserWindow,
  Tray,
  Menu,
  nativeImage,
  ipcMain,
  shell,
  screen,
  Notification,
} = require("electron");
const path = require("path");
const fs = require("fs");
const http = require("http");
const https = require("https");
const { createAvatarBridge } = require("./avatar_bridge");
const {
  listWindows,
  findWindowByTitle,
  desktopIconsZone,
  taskbarZone,
} = require("./desktop_targets");

const DEFAULT_CONFIG = {
  compagnonUrl: "http://192.168.0.100:5174/",
  window: { width: 1180, height: 780, minWidth: 720, minHeight: 520 },
  overlay: {
    enabled: true,
    /** face = FaceRig 2D (Lyra) · vrm = perso 3D */
    mode: "vrm",
    width: 270,
    height: 420,
    marginRight: 16,
    marginBottom: 0,
    alwaysOnTop: true,
    vrmModel: "./vrm/Compagnon.vrm",
    /** bust = visage · full = corps entier */
    vrmFraming: "full",
    /** Deplacement autonome sur le bureau */
    wander: true,
    wanderSpeed: 48,
    wanderPauseMs: 15000,
    /** Guide vers fenêtre / icônes (px/s) */
    guideSpeed: 220,
  },
  tray: { tooltip: "LBG Compagnon" },
  /** D3 — initiatives (quota strict, jamais d'auto-exec) */
  initiative: {
    enabled: true,
    pollIntervalMs: 60_000,
    maxPerHour: 3,
    minIntervalSec: 600,
    minSilenceSec: 90,
    proactiveUrl: "http://192.168.0.100:5174/api/pilot/orchestrator/proactive/status",
  },
  /** D7 — Présence Agents (SSE via main process) */
  sessionIsland: {
    enabled: false,
    streamUrl: "http://192.168.0.143:5005/session/stream",
    decisionUrl: "http://192.168.0.143:5005/session/decision",
  },
  /** Avatar bridge — SSE loopback pour FaceRig + adaptateurs VRM (Mate Engine / liqu) */
  avatarBridge: {
    enabled: true,
    host: "127.0.0.1",
    port: 8765,
    heartbeatMs: 30_000,
  },
};

let mainWindow = null;
let overlayWindow = null;
let tray = null;
let config = { ...DEFAULT_CONFIG };
let quitting = false;
let initiativeTimer = null;
/** @type {{ ts: number, id: string }[]} */
let initiativeShown = [];
let lastNotifiedId = "";
/** @type {import("http").IncomingMessage | null} */
let sessionStreamReq = null;
let sessionStreamRetry = null;
/** @type {ReturnType<typeof createAvatarBridge> | null} */
let avatarBridge = null;
/** @type {ReturnType<typeof setInterval> | null} */
let motionTimer = null;
/**
 * @type {{
 *   x: number, y: number, tx: number, ty: number,
 *   speed: number, mode: 'wander'|'guide',
 *   pauseUntil: number,
 *   onArrive: null | (() => void),
 * } | null}
 */
let motionState = null;
/** Alias compat wander (pause drag) */
let wanderState = null;

function appRoot() {
  return app.isPackaged ? path.dirname(process.execPath) : __dirname;
}

function loadConfig() {
  const candidates = [
    path.join(appRoot(), "config.json"),
    path.join(__dirname, "config.json"),
  ];
  for (const p of candidates) {
    try {
      if (!fs.existsSync(p)) continue;
      // PowerShell Set-Content -Encoding UTF8 ajoute souvent un BOM (ï»¿)
      const text = fs.readFileSync(p, "utf8").replace(/^\uFEFF/, "");
      const raw = JSON.parse(text);
      config = {
        ...DEFAULT_CONFIG,
        ...raw,
        window: { ...DEFAULT_CONFIG.window, ...(raw.window || {}) },
        overlay: { ...DEFAULT_CONFIG.overlay, ...(raw.overlay || {}) },
        tray: { ...DEFAULT_CONFIG.tray, ...(raw.tray || {}) },
        initiative: { ...DEFAULT_CONFIG.initiative, ...(raw.initiative || {}) },
        sessionIsland: {
          ...DEFAULT_CONFIG.sessionIsland,
          ...(raw.sessionIsland || {}),
        },
        avatarBridge: {
          ...DEFAULT_CONFIG.avatarBridge,
          ...(raw.avatarBridge || {}),
        },
      };
      return;
    } catch (e) {
      console.warn("[compagnon] config", p, e.message);
    }
  }
  config = { ...DEFAULT_CONFIG };
}

function iconPath() {
  const p = path.join(__dirname, "assets", "icon.png");
  return fs.existsSync(p) ? p : null;
}

function trayImage() {
  const p = iconPath();
  if (!p) return nativeImage.createEmpty();
  let img = nativeImage.createFromPath(p);
  if (!img.isEmpty()) {
    img = img.resize({ width: 32, height: 32, quality: "best" });
  }
  return img;
}

function compagnonUrl() {
  const fromEnv = (process.env.LBG_COMPAGNON_URL || "").trim();
  if (fromEnv) return fromEnv.replace(/\/?$/, "/");
  return String(config.compagnonUrl || DEFAULT_CONFIG.compagnonUrl).replace(/\/?$/, "/");
}

function createMainWindow() {
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.show();
    mainWindow.focus();
    return mainWindow;
  }

  const wcfg = config.window || DEFAULT_CONFIG.window;
  mainWindow = new BrowserWindow({
    width: wcfg.width || 1180,
    height: wcfg.height || 780,
    minWidth: wcfg.minWidth || 720,
    minHeight: wcfg.minHeight || 520,
    title: "LBG Compagnon",
    backgroundColor: "#020617",
    show: false,
    autoHideMenuBar: true,
    icon: iconPath() || undefined,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
      // Nouvelle partition = cache Chromium neuf (évite Selfcheck/Team fantômes)
      partition: "persist:compagnon-chat-v2",
    },
  });

  mainWindow.once("ready-to-show", () => {
    if (mainWindow && !mainWindow.isDestroyed()) mainWindow.show();
  });

  mainWindow.on("close", (e) => {
    if (quitting) return;
    e.preventDefault();
    mainWindow.hide();
  });

  mainWindow.on("closed", () => {
    mainWindow = null;
  });

  const ses = mainWindow.webContents.session;
  Promise.resolve()
    .then(() =>
      ses.clearCache().catch(() => {})
    )
    .then(() =>
      ses
        .clearStorageData({
          storages: [
            "serviceworkers",
            "cachestorage",
            "shadercache",
            "websql",
          ],
        })
        .catch(() => {})
    )
    .finally(() => {
      if (!mainWindow || mainWindow.isDestroyed()) return;
      const base = compagnonUrl();
      const bust = `desktop=1&_=${Date.now()}`;
      const url = base.includes("?") ? `${base}&${bust}` : `${base}?${bust}`;
      mainWindow.loadURL(url).catch((err) => {
        console.error("[compagnon] loadURL", err);
        const fallback = `data:text/html;charset=utf-8,${encodeURIComponent(
          `<!doctype html><html><body style="font-family:sans-serif;background:#020617;color:#e2e8f0;padding:2rem">
      <h1>Compagnon injoignable</h1>
      <p>URL : ${compagnonUrl()}</p>
      <p>Verifier le CT .100:5174 puis Relancer.</p>
      </body></html>`
        )}`;
        mainWindow.loadURL(fallback);
      });
    });

  return mainWindow;
}

function overlayBounds() {
  const o = config.overlay || DEFAULT_CONFIG.overlay;
  const display = screen.getPrimaryDisplay();
  const wa = display.workArea;
  const width = o.width || 270;
  const height = o.height || 420;
  const marginRight = Number.isFinite(o.marginRight) ? o.marginRight : 16;
  const marginBottom = Number.isFinite(o.marginBottom) ? o.marginBottom : 0;
  const x = wa.x + wa.width - width - marginRight;
  const y = wa.y + wa.height - height - marginBottom;
  return { x, y, width, height };
}

function createOverlayWindow() {
  const o = config.overlay || DEFAULT_CONFIG.overlay;
  if (o.enabled === false) return null;
  if (overlayWindow && !overlayWindow.isDestroyed()) return overlayWindow;

  const b = overlayBounds();
  overlayWindow = new BrowserWindow({
    ...b,
    frame: false,
    transparent: true,
    resizable: false,
    movable: true,
    skipTaskbar: true,
    hasShadow: false,
    alwaysOnTop: o.alwaysOnTop !== false,
    focusable: true,
    show: false,
    backgroundColor: "#00000000",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      nodeIntegration: false,
      contextIsolation: true,
      // sandbox off: bundle three-vrm local
      sandbox: false,
    },
  });

  overlayWindow.setAlwaysOnTop(o.alwaysOnTop !== false, "floating");
  overlayWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: false });

  overlayWindow.once("ready-to-show", () => {
    if (overlayWindow && !overlayWindow.isDestroyed()) overlayWindow.showInactive();
    if ((config.overlay || {}).wander) startWander();
  });

  overlayWindow.on("closed", () => {
    stopMotion();
    overlayWindow = null;
  });

  overlayWindow.loadFile(path.join(__dirname, "overlay", "index.html"));
  return overlayWindow;
}

function clampOverlayPos(x, y) {
  const o = config.overlay || DEFAULT_CONFIG.overlay;
  const w = o.width || 270;
  const h = o.height || 420;
  const display = screen.getDisplayNearestPoint({ x, y });
  const wa = display.workArea;
  return {
    x: Math.max(wa.x, Math.min(wa.x + wa.width - w, Math.round(x))),
    y: Math.max(wa.y, Math.min(wa.y + wa.height - h, Math.round(y))),
  };
}

function moveOverlayTo(x, y) {
  if (!overlayWindow || overlayWindow.isDestroyed()) return;
  const p = clampOverlayPos(x, y);
  overlayWindow.setPosition(p.x, p.y);
}

function pickWanderTarget() {
  const o = config.overlay || DEFAULT_CONFIG.overlay;
  const w = o.width || 270;
  const h = o.height || 420;

  // Reste sur l'écran où se trouve actuellement l'avatar
  let d = screen.getPrimaryDisplay();
  let curX = 0;
  if (overlayWindow && !overlayWindow.isDestroyed()) {
    const pos = overlayWindow.getPosition();
    curX = pos[0];
    d = screen.getDisplayNearestPoint({ x: curX + w / 2, y: pos[1] + h / 2 }) || d;
  }
  const wa = d.workArea;

  // STRICTEMENT sur la barre des tâches (100% du temps) :
  const floorY = wa.y + wa.height - h;

  // Petits déplacements vivants et mesurés (80 à 200 px) au lieu de traverser l'écran en automate
  const minX = wa.x + 10;
  const maxX = wa.x + wa.width - w - 10;

  const strollDist = 80 + Math.random() * 120;
  const dir = Math.random() < 0.5 ? -1 : 1;
  let targetX = curX + dir * strollDist;

  // Rebond doux si elle s'approche des bords de l'écran
  if (targetX < minX) {
    targetX = minX + 30 + Math.random() * 80;
  } else if (targetX > maxX) {
    targetX = maxX - 30 - Math.random() * 80;
  }

  return {
    x: Math.round(targetX),
    y: Math.round(floorY),
  };
}

function stopMotion() {
  if (motionTimer) {
    clearInterval(motionTimer);
    motionTimer = null;
  }
  if (motionState && motionState.isWalking) {
    sendVrmPose("idle", 0);
    sendVrmHeading(0);
  }
  motionState = null;
  wanderState = null;
}

function stopWander() {
  if (motionState && motionState.mode === "wander") stopMotion();
}

function ensureMotionTick() {
  if (motionTimer) return;
  const tickMs = 50;
  motionTimer = setInterval(() => {
    if (!overlayWindow || overlayWindow.isDestroyed() || !motionState) {
      stopMotion();
      return;
    }
    const now = Date.now();
    if (now < motionState.pauseUntil) {
      if (motionState.isWalking) {
        motionState.isWalking = false;
        sendVrmPose("idle", 0);
        sendVrmHeading(0); // Face caméra pendant la pause
      }
      return;
    }
    const dx = motionState.tx - motionState.x;
    const dy = motionState.ty - motionState.y;
    const dist = Math.hypot(dx, dy);

    // Orientation gauche (-1) ou droite (+1) selon dx
    const heading = dx > 8 ? 1 : (dx < -8 ? -1 : 0);

    if (!motionState.isWalking) {
      motionState.isWalking = true;
      sendVrmPose("walk", 0);
      sendVrmHeading(heading);
      motionState.lastHeading = heading;
    } else if (motionState.lastHeading !== heading && Math.abs(dx) > 12) {
      motionState.lastHeading = heading;
      sendVrmHeading(heading);
    }

    if (dist < 6) {
      motionState.x = motionState.tx;
      motionState.y = motionState.ty;
      moveOverlayTo(motionState.x, motionState.y);
      if (motionState.isWalking) {
        motionState.isWalking = false;
        sendVrmPose("idle", 0);
        sendVrmHeading(0); // Face caméra à l'arrêt
      }
      const arrive = motionState.onArrive;
      motionState.onArrive = null;
      if (typeof arrive === "function") {
        try {
          arrive();
        } catch (_) {}
      }
      if (motionState && motionState.mode === "wander") {
        const o = config.overlay || DEFAULT_CONFIG.overlay;
        // Pause plus longue et naturelle sur la barre des tâches (12 à 22s de vie sur place)
        const basePause = Math.max(6000, Number(o.wanderPauseMs) || 15000);
        const pauseMs = Math.round(basePause * (0.8 + Math.random() * 0.5));
        motionState.pauseUntil = now + pauseMs;
        const n = pickWanderTarget();
        motionState.tx = n.x;
        motionState.ty = n.y;
        return;
      }
      // guide : rester sur place
      if (motionTimer) {
        clearInterval(motionTimer);
        motionTimer = null;
      }
      return;
    }
    const step = (Math.max(20, motionState.speed) * tickMs) / 1000;
    const k = Math.min(1, step / dist);
    motionState.x += dx * k;
    motionState.y += dy * k;
    moveOverlayTo(motionState.x, motionState.y);
  }, tickMs);
}

function animateOverlayTo(tx, ty, opts) {
  if (!overlayWindow || overlayWindow.isDestroyed()) return;
  const o = config.overlay || DEFAULT_CONFIG.overlay;
  const options = opts || {};
  const mode = options.mode === "wander" ? "wander" : "guide";
  const speed =
    Number(options.speed) ||
    (mode === "wander"
      ? Math.max(20, Number(o.wanderSpeed) || 45)
      : Math.max(80, Number(o.guideSpeed) || 220));
  const [cx, cy] = overlayWindow.getPosition();
  const p = clampOverlayPos(tx, ty);
  motionState = {
    x: cx,
    y: cy,
    tx: p.x,
    ty: p.y,
    speed,
    mode,
    pauseUntil: 0,
    isWalking: false,
    onArrive: typeof options.onArrive === "function" ? options.onArrive : null,
  };
  wanderState = mode === "wander" ? motionState : null;
  ensureMotionTick();
}

function startWander() {
  stopMotion();
  if (!overlayWindow || overlayWindow.isDestroyed()) return;
  const o = config.overlay || DEFAULT_CONFIG.overlay;
  if (o.wander === false) return;
  const t = pickWanderTarget();
  animateOverlayTo(t.x, t.y, { mode: "wander" });
}

function setWanderEnabled(on) {
  config.overlay = { ...(config.overlay || {}), wander: Boolean(on) };
  try {
    const cfgPath = path.join(appRoot(), "config.json");
    if (fs.existsSync(cfgPath)) {
      const text = fs.readFileSync(cfgPath, "utf8").replace(/^\uFEFF/, "");
      const raw = JSON.parse(text);
      raw.overlay = { ...(raw.overlay || {}), wander: Boolean(on) };
      fs.writeFileSync(cfgPath, JSON.stringify(raw, null, 2) + "\n", "utf8");
    }
  } catch (_) {}
  if (on) startWander();
  else stopWander();
}

/** Place l'avatar à côté d'un rectangle écran (fenêtre / zone icônes). */
function placeBesideRect(rect) {
  const o = config.overlay || DEFAULT_CONFIG.overlay;
  const ow = o.width || 240;
  const oh = o.height || 420;
  const gap = 16;
  const midY = rect.y + Math.max(0, (rect.height - oh) * 0.28);
  let x = rect.x + rect.width + gap;
  let y = midY;
  let pointSide = "left"; // flèche vers la cible (à gauche de l'avatar)
  const display = screen.getDisplayNearestPoint({
    x: rect.x + rect.width / 2,
    y: rect.y + rect.height / 2,
  });
  const wa = display.workArea;
  if (x + ow > wa.x + wa.width - 4) {
    x = rect.x - ow - gap;
    pointSide = "right";
  }
  if (y + oh > wa.y + wa.height) y = wa.y + wa.height - oh;
  if (y < wa.y) y = wa.y;
  const p = clampOverlayPos(x, y);
  return { ...p, pointSide };
}

function sendOverlayGuide(payload) {
  if (!overlayWindow || overlayWindow.isDestroyed()) return;
  try {
    overlayWindow.webContents.send("compagnon:guide", payload || {});
  } catch (_) {}
}

/**
 * Guide l'avatar vers une cible : se déplace seul + bulle « regarde ici ».
 * @param {{ x:number,y:number,width?:number,height?:number,title?:string,message?:string }} target
 */
function guideToTarget(target) {
  if (!overlayWindow || overlayWindow.isDestroyed()) {
    createOverlayWindow();
  }
  if (!overlayWindow || overlayWindow.isDestroyed() || !target) {
    return { ok: false, error: "overlay ou cible manquant" };
  }
  if (overlayWindow.isVisible && !overlayWindow.isVisible()) {
    overlayWindow.showInactive();
  }
  // Interrompt la promenade aléatoire le temps du guide
  if (motionState && motionState.mode === "wander") stopMotion();

  const rect = {
    x: Number(target.x) || 0,
    y: Number(target.y) || 0,
    width: Math.max(40, Number(target.width) || 80),
    height: Math.max(40, Number(target.height) || 80),
  };
  const place = placeBesideRect(rect);
  const label = String(target.title || target.label || "ici").slice(0, 60);
  const message =
    String(target.message || "").trim() ||
    `Regarde : ${label}`;

  animateOverlayTo(place.x, place.y, {
    mode: "guide",
    onArrive: () => {
      sendOverlayGuide({
        message,
        label,
        pointSide: place.pointSide,
        holdMs: Number(target.holdMs) || 8000,
      });
      setOverlayMood({ tone: "curious", label: "Guide" });
      if (avatarBridge) {
        avatarBridge.publishSay(message.slice(0, 100));
      }
    },
  });
  return { ok: true, target: label, x: place.x, y: place.y };
}

async function guideToWindowTitle(title, message) {
  const windows = await listWindows();
  const hit = findWindowByTitle(windows, title);
  if (!hit) {
    sendOverlayGuide({
      message: `Je ne trouve pas « ${String(title).slice(0, 40)} »…`,
      pointSide: "none",
      holdMs: 4000,
    });
    return { ok: false, error: "fenêtre introuvable", title };
  }
  return guideToTarget({
    ...hit,
    message: message || `Voici « ${hit.title.slice(0, 40)} »`,
  });
}

async function guideDemo(kind) {
  const k = String(kind || "icons").toLowerCase();
  if (k === "icons" || k === "desktop") {
    return guideToTarget({
      ...desktopIconsZone(),
      message: "Ici, tes icônes bureau — je te montre la zone.",
    });
  }
  if (k === "taskbar" || k === "tray") {
    return guideToTarget({
      ...taskbarZone(),
      message: "Barre des tâches, en bas.",
    });
  }
  if (k === "compagnon" || k === "chat") {
    return guideToWindowTitle("LBG Compagnon", "Voici la fenêtre Compagnon.");
  }
  // Première fenêtre utile
  const windows = await listWindows();
  const skip = /compagnon vrm|electron/i;
  const hit = windows.find((w) => !skip.test(w.title)) || windows[0];
  if (!hit) {
    return guideToTarget({
      ...desktopIconsZone(),
      message: "Pas de fenêtre listée — zone icônes.",
    });
  }
  return guideToTarget({
    ...hit,
    message: `Je te montre « ${hit.title.slice(0, 36)} »`,
  });
}

function getVrmDir() {
  return path.join(__dirname, "overlay", "vrm");
}

function getVrmModels() {
  try {
    const dir = getVrmDir();
    if (!fs.existsSync(dir)) return [];
    return fs.readdirSync(dir)
      .filter((f) => f.toLowerCase().endsWith(".vrm"))
      .map((f) => ({
        filename: f,
        relPath: `./vrm/${f}`,
        name: f.replace(/\.vrm$/i, ""),
      }));
  } catch (e) {
    console.warn("[compagnon] getVrmModels", e.message);
    return [];
  }
}

function setVrmModel(modelRelPath) {
  persistOverlayConfig({ vrmModel: modelRelPath });
  if (overlayWindow && !overlayWindow.isDestroyed()) {
    overlayWindow.webContents.send("compagnon:vrm-model", modelRelPath);
  }
  rebuildTrayMenu().catch(() => {});
}

function sendVrmPose(pose, holdMs = 3000) {
  if (overlayWindow && !overlayWindow.isDestroyed()) {
    overlayWindow.webContents.send("compagnon:vrm-pose", { pose, holdMs });
  }
}

function sendVrmHeading(heading = 0) {
  if (overlayWindow && !overlayWindow.isDestroyed()) {
    overlayWindow.webContents.send("compagnon:vrm-heading", heading);
  }
}

async function rebuildTrayMenu() {
  if (!tray) return;
  const windows = await listWindows();
  const top = windows.slice(0, 12).map((w) => ({
    label: w.title.length > 48 ? `${w.title.slice(0, 46)}…` : w.title,
    click: () =>
      guideToTarget({
        ...w,
        message: `Regarde cette fenêtre : ${w.title.slice(0, 40)}`,
      }),
  }));
  const guideSub = [
    {
      label: "Démo : zone icônes bureau",
      click: () => guideDemo("icons"),
    },
    {
      label: "Démo : barre des tâches",
      click: () => guideDemo("taskbar"),
    },
    {
      label: "Démo : fenêtre Compagnon",
      click: () => guideDemo("compagnon"),
    },
    { type: "separator" },
    ...(top.length
      ? top
      : [{ label: "(aucune fenêtre listée)", enabled: false }]),
    { type: "separator" },
    {
      label: "Rafraîchir la liste…",
      click: () => {
        rebuildTrayMenu();
      },
    },
  ];

  const currentModel = String((config.overlay || {}).vrmModel || "./vrm/default.vrm");
  const models = getVrmModels();
  const modelsSub = [
    ...(models.length
      ? models.map((m) => ({
          label: m.name + (m.filename === "default.vrm" ? " (défaut)" : ""),
          type: "radio",
          checked: currentModel === m.relPath || currentModel === m.filename,
          click: () => setVrmModel(m.relPath),
        }))
      : [{ label: "(aucun .vrm trouvé)", enabled: false }]),
    { type: "separator" },
    {
      label: "Ouvrir dossier VRM (déposer un .vrm)...",
      click: () => shell.openPath(getVrmDir()),
    },
  ];

  const posesSub = [
    { label: "Repos (idle)", click: () => sendVrmPose("idle", 0) },
    { label: "Saluer (wave)", click: () => sendVrmPose("wave", 2500) },
    { label: "Danse (dance)", click: () => sendVrmPose("dance", 8000) },
    { label: "Colère / boudage (angry)", click: () => sendVrmPose("angry", 4000) },
    { label: "Marche (walk)", click: () => sendVrmPose("walk", 6000) },
    { label: "Réflexion (think)", click: () => sendVrmPose("think", 4000) },
    { label: "Approbation (approve)", click: () => sendVrmPose("approve", 3500) },
    { label: "Pointer écran (pointScreen)", click: () => sendVrmPose("pointScreen", 4000) },
    { label: "Pointer à gauche (pointLeft)", click: () => sendVrmPose("pointLeft", 4000) },
    { label: "Pointer à droite (pointRight)", click: () => sendVrmPose("pointRight", 4000) },
    { label: "Célébrer (cheer)", click: () => sendVrmPose("cheer", 3500) },
    { label: "Révérence (bow)", click: () => sendVrmPose("bow", 3000) },
  ];

  const menu = Menu.buildFromTemplate([
    { label: "Ouvrir Compagnon", click: () => showChat() },
    { label: "Afficher / masquer chat", click: () => toggleChat() },
    { type: "separator" },
    { label: "Avatar (overlay)", click: () => toggleOverlay() },
    {
      label: "Avatar mode: VRM 3D",
      click: () => setOverlayMode("vrm"),
    },
    {
      label: "Avatar mode: FaceRig 2D",
      click: () => setOverlayMode("face"),
    },
    {
      label: "Retourner avatar (face/dos)",
      click: () => {
        if (overlayWindow && !overlayWindow.isDestroyed()) {
          overlayWindow.webContents.send("compagnon:vrm-flip");
        }
      },
    },
    {
      label: "VRM : corps entier",
      type: "radio",
      checked: String((config.overlay || {}).vrmFraming || "full") !== "bust",
      click: () => setVrmFraming("full"),
    },
    {
      label: "VRM : gros plan visage",
      type: "radio",
      checked: String((config.overlay || {}).vrmFraming || "full") === "bust",
      click: () => setVrmFraming("bust"),
    },
    { type: "separator" },
    {
      label: "Poses VRM",
      submenu: posesSub,
    },
    {
      label: "Modèles VRM (VRoid)",
      submenu: modelsSub,
    },
    { type: "separator" },
    {
      label: "Se promener (aléatoire)",
      type: "checkbox",
      checked: Boolean((config.overlay || {}).wander),
      click: (item) => setWanderEnabled(Boolean(item.checked)),
    },
    {
      label: "Guider vers…",
      submenu: guideSub,
    },
    {
      label: "Ouvrir dans le navigateur",
      click: () => shell.openExternal(compagnonUrl()),
    },
    { type: "separator" },
    {
      label: "Quitter",
      click: () => {
        quitting = true;
        app.quit();
      },
    },
  ]);
  tray.setContextMenu(menu);
}

function showChat() {
  createMainWindow();
  if (mainWindow && !mainWindow.isDestroyed()) {
    if (mainWindow.isMinimized()) mainWindow.restore();
    mainWindow.show();
    mainWindow.focus();
  }
}

/** Ouvre le chat avec une carte Agir préremplie (deep-link ?agir=). */
function showChatWithAgir(payload) {
  const text = String((payload && payload.sourceText) || "").trim();
  const label = String((payload && payload.label) || "Initiative").trim();
  createMainWindow();
  if (!mainWindow || mainWindow.isDestroyed()) return;
  if (text) {
    try {
      const u = new URL(compagnonUrl());
      u.searchParams.set("stay", "1");
      u.searchParams.set("agir", text);
      u.searchParams.set("agir_label", label);
      mainWindow.loadURL(u.toString()).catch(() => {});
    } catch (_) {
      /* ignore */
    }
  }
  if (mainWindow.isMinimized()) mainWindow.restore();
  mainWindow.show();
  mainWindow.focus();
}

function toggleChat() {
  if (mainWindow && !mainWindow.isDestroyed() && mainWindow.isVisible()) {
    mainWindow.hide();
    return;
  }
  showChat();
}

function toggleOverlay() {
  if (!overlayWindow || overlayWindow.isDestroyed()) {
    createOverlayWindow();
    return;
  }
  if (overlayWindow.isVisible()) overlayWindow.hide();
  else overlayWindow.showInactive();
}

function vrmOverlaySize(framing) {
  const full = String(framing || "").toLowerCase() !== "bust";
  return full ? { width: 270, height: 420 } : { width: 200, height: 280 };
}

function persistOverlayConfig(patch) {
  config.overlay = {
    ...(config.overlay || DEFAULT_CONFIG.overlay),
    ...(patch || {}),
  };
  try {
    const cfgPath = path.join(appRoot(), "config.json");
    if (fs.existsSync(cfgPath)) {
      const text = fs.readFileSync(cfgPath, "utf8").replace(/^\uFEFF/, "");
      const raw = JSON.parse(text);
      raw.overlay = { ...(raw.overlay || {}), ...config.overlay };
      fs.writeFileSync(cfgPath, JSON.stringify(raw, null, 2) + "\n", "utf8");
    }
  } catch (e) {
    console.warn("[compagnon] persistOverlayConfig", e.message);
  }
}

function recreateOverlay() {
  if (overlayWindow && !overlayWindow.isDestroyed()) {
    try {
      overlayWindow.close();
    } catch (_) {}
    overlayWindow = null;
  }
  createOverlayWindow();
}

function setOverlayMode(mode) {
  const next = mode === "vrm" ? "vrm" : "face";
  const framing = (config.overlay && config.overlay.vrmFraming) || "full";
  const size =
    next === "vrm" ? vrmOverlaySize(framing) : { width: 188, height: 280 };
  persistOverlayConfig({ mode: next, ...size });
  recreateOverlay();
}

function setVrmFraming(framing) {
  const next = String(framing || "").toLowerCase() === "bust" ? "bust" : "full";
  const mode = (config.overlay && config.overlay.mode) || "vrm";
  const size = mode === "vrm" ? vrmOverlaySize(next) : {};
  persistOverlayConfig({ vrmFraming: next, ...size });
  if (mode === "vrm" && overlayWindow && !overlayWindow.isDestroyed()) {
    overlayWindow.webContents.send("compagnon:vrm-framing", next);
    try {
      const [x, y] = overlayWindow.getPosition();
      overlayWindow.setSize(size.width, size.height);
      moveOverlayTo(x, y);
    } catch (_) {}
  } else {
    recreateOverlay();
  }
  rebuildTrayMenu().catch(() => {});
}

function buildTray() {
  if (tray) return tray;
  tray = new Tray(trayImage());
  tray.setToolTip((config.tray && config.tray.tooltip) || "LBG Compagnon");
  rebuildTrayMenu().catch(() => {});
  tray.on("double-click", () => showChat());
  tray.on("click", () => {
    if (process.platform === "win32") toggleChat();
  });
  return tray;
}

function setOverlayMood(mood) {
  if (overlayWindow && !overlayWindow.isDestroyed()) {
    overlayWindow.webContents.send("compagnon:mood", mood);
  }
  if (avatarBridge) avatarBridge.publishMood(mood);
}

function publishAvatarPresence(payload) {
  if (!avatarBridge || !payload) return;
  const kind = String(payload.kind || payload.event || "").toLowerCase();
  if (kind === "talking" || kind === "avatar.talking") {
    avatarBridge.publishTalking({
      text: payload.text,
      ms: payload.ms,
      talking: payload.talking !== false,
    });
    if (overlayWindow && !overlayWindow.isDestroyed()) {
      overlayWindow.webContents.send("compagnon:talking", payload);
    }
    return;
  }
  if (kind === "say" || kind === "avatar.say") {
    avatarBridge.publishSay(payload.text || "");
    return;
  }
  if (kind === "idle" || kind === "avatar.idle" || payload.talking === false) {
    avatarBridge.publishTalking({ talking: false });
    return;
  }
  if (kind === "mood" || kind === "avatar.mood") {
    setOverlayMood(payload.mood || payload.tone || "serene");
  }
}

function fetchJson(url) {
  return new Promise((resolve, reject) => {
    const lib = url.startsWith("https") ? https : http;
    const req = lib.get(url, { timeout: 8000 }, (res) => {
      let data = "";
      res.on("data", (c) => {
        data += c;
      });
      res.on("end", () => {
        try {
          resolve(JSON.parse(data));
        } catch (e) {
          reject(e);
        }
      });
    });
    req.on("error", reject);
    req.on("timeout", () => {
      req.destroy();
      reject(new Error("timeout"));
    });
  });
}

function pruneInitiativeShown(now = Date.now()) {
  const hourAgo = now - 60 * 60 * 1000;
  initiativeShown = initiativeShown.filter((x) => x.ts >= hourAgo);
}

function initiativeFingerprint(status) {
  const job = typeof status.last_job_id === "string" ? status.last_job_id.trim() : "";
  if (job) return `job:${job}`;
  const act = status.last_action && typeof status.last_action === "object" ? status.last_action : null;
  if (act) {
    const kind = String(act.kind || "");
    const msg = String(act.message || "").slice(0, 120);
    if (kind || msg) return `act:${kind}|${msg}`;
  }
  const infra = status.infra_signals && typeof status.infra_signals === "object" ? status.infra_signals : null;
  if (infra && infra.desktop_agent_down) return "infra:desktop_agent_down";
  if (infra && infra.ad_agent_down) return "infra:ad_agent_down";
  if (infra && infra.orchestrator_reachable === false) return "infra:orch_down";
  return "";
}

/** Miroir UI `agirIntentsFromStatus` — toast/pet = Agir-ready, pas du vague. */
function agirIntentsFromStatus(status) {
  const out = [];
  const infra =
    status && status.infra_signals && typeof status.infra_signals === "object"
      ? status.infra_signals
      : {};
  const tension = Number(status && status.tension);
  const job = typeof (status && status.last_job_id) === "string" ? status.last_job_id : "";

  if (infra.desktop_agent_down || infra.ad_agent_down) {
    out.push({
      id: "probe_ad",
      label: "Sonde agent desktop (dry-run)",
      sourceText: "fais un diagnostic infra selfcheck de l agent desktop sur le LAN",
      hint: "devops_probe · lecture seule",
    });
  }
  if (infra.orchestrator_reachable === false) {
    out.push({
      id: "probe_orch",
      label: "Sonde orchestrateur",
      sourceText: "fais un diagnostic HTTP health de l orchestrateur Cortex",
      hint: "devops_probe",
    });
  }
  if (Number.isFinite(tension) && tension >= 0.85) {
    out.push({
      id: "open_jobs",
      label: "Ouvrir Pilot Jobs",
      sourceText: "ouvre http://192.168.0.140:8080/#/jobs dans le navigateur",
      hint: "navigateur par défaut · .10",
    });
  }
  if (job && !out.some((x) => x.id === "open_jobs")) {
    out.push({
      id: "open_jobs_job",
      label: "Revue job L2",
      sourceText: "ouvre http://192.168.0.140:8080/#/jobs dans le navigateur",
      hint: `job ${String(job).slice(0, 8)}…`,
    });
  }
  if (infra.mmo_sidecar_reachable === false) {
    out.push({
      id: "note_mmo",
      label: "Ouvrir notes sidecar",
      sourceText: "ouvre notepadpp sur mon pc",
      hint: "desktop · noter l alerte MMO",
    });
  }
  if (!out.length) {
    out.push({
      id: "status_check",
      label: "État Studio (dry-run)",
      sourceText: "fais un diagnostic infra selfcheck LAN",
      hint: "lecture seule",
    });
  }
  return out.slice(0, 3);
}

function initiativeMessage(status) {
  const infra = status && status.infra_signals;
  if (infra && (infra.desktop_agent_down || infra.ad_agent_down)) {
    return "Je vois l’agent desktop injoignable — je peux lancer une sonde (dry-run).";
  }
  if (infra && infra.orchestrator_reachable === false) {
    return "Orchestrateur injoignable — je propose une sonde health.";
  }
  if (typeof (status && status.tension) === "number" && status.tension >= 0.85) {
    return "Tension orch élevée — j’ouvre Pilot Jobs pour revue L2 ?";
  }
  const act = status && status.last_action;
  if (act && typeof act === "object" && act.message) {
    return `Signal : ${String(act.message)} — action concrète ci-dessous.`;
  }
  return "Petite initiative — une action possible ci-dessous.";
}

function buildInitiativePayload(status, id) {
  const intents = agirIntentsFromStatus(status);
  const primary = intents[0] || null;
  return {
    id,
    message: initiativeMessage(status),
    kind: (status.last_action && status.last_action.kind) || "initiative",
    intents,
    primary,
    sourceText: primary ? primary.sourceText : "",
    label: primary ? primary.label : "Initiative",
  };
}

function sendOverlayInitiative(payload) {
  if (overlayWindow && !overlayWindow.isDestroyed()) {
    overlayWindow.webContents.send("compagnon:initiative", payload);
  }
  if (avatarBridge) avatarBridge.publishInitiative(payload);
}

function canNotifyInitiative(id, cfg) {
  if (!id) return false;
  const now = Date.now();
  pruneInitiativeShown(now);
  if (initiativeShown.some((x) => x.id === id)) return false;
  if (initiativeShown.length >= (cfg.maxPerHour || 3)) return false;
  const last = initiativeShown.reduce((a, b) => (a.ts > b.ts ? a : b), { ts: 0 });
  if (last.ts && now - last.ts < (cfg.minIntervalSec || 600) * 1000) return false;
  return true;
}

function notifyInitiative(status) {
  const cfg = config.initiative || DEFAULT_CONFIG.initiative;
  if (cfg.enabled === false) return;
  if (status.enabled === false || status.ok === false) return;
  const silence = Number(status.silence_seconds_est);
  if (Number.isFinite(silence) && silence < (cfg.minSilenceSec || 90)) return;
  const id = initiativeFingerprint(status);
  if (!canNotifyInitiative(id, cfg)) return;
  if (id === lastNotifiedId) return;

  const payload = buildInitiativePayload(status, id);
  const body = `${payload.message}${
    payload.primary ? ` → ${payload.primary.label}` : ""
  }`;
  initiativeShown.push({ ts: Date.now(), id });
  lastNotifiedId = id;

  setOverlayMood({ tone: "tense", label: "Initiative" });
  sendOverlayInitiative(payload);
  setTimeout(() => setOverlayMood({ tone: "serene", label: "Serein" }), 12_000);

  if (Notification.isSupported()) {
    const n = new Notification({
      title: "Compagnon · initiative",
      body: body.slice(0, 180),
      silent: false,
    });
    n.on("click", () => showChatWithAgir(payload));
    n.show();
  } else if (tray) {
    tray.displayBalloon({
      title: "Compagnon · initiative",
      content: body.slice(0, 180),
    });
  }
}

async function pollInitiative() {
  const cfg = config.initiative || DEFAULT_CONFIG.initiative;
  if (cfg.enabled === false) return;
  const url =
    (cfg.proactiveUrl || "").trim() ||
    `${compagnonUrl().replace(/\/?$/, "")}/api/pilot/orchestrator/proactive/status`;
  try {
    const status = await fetchJson(url);
    notifyInitiative(status);
  } catch (e) {
    // silencieux — réseau lab
  }
}

function startInitiativePolling() {
  const cfg = config.initiative || DEFAULT_CONFIG.initiative;
  if (cfg.enabled === false) return;
  if (initiativeTimer) clearInterval(initiativeTimer);
  setTimeout(() => {
    pollInitiative();
  }, 12_000);
  initiativeTimer = setInterval(
    () => pollInitiative(),
    cfg.pollIntervalMs || 60_000
  );
}

ipcMain.handle("compagnon:get-config", () => ({
  compagnonUrl: compagnonUrl(),
  overlay: config.overlay,
  initiative: config.initiative,
  sessionIsland: config.sessionIsland,
  avatarBridge: config.avatarBridge,
}));

ipcMain.on("compagnon:open-chat", () => showChat());

ipcMain.on("compagnon:open-chat-agir", (_e, payload) => {
  const p = payload || {};
  const primary = p.primary || null;
  showChatWithAgir({
    sourceText: p.sourceText || (primary && primary.sourceText) || "",
    label: p.label || (primary && primary.label) || "Initiative",
  });
});

ipcMain.on("compagnon:overlay-mood", (_e, mood) => {
  setOverlayMood(mood);
});

ipcMain.on("compagnon:set-pose", (_e, payload) => {
  const pose = payload && payload.pose;
  const holdMs = payload && payload.holdMs;
  if (pose) sendVrmPose(pose, holdMs);
});

ipcMain.on("compagnon:avatar-presence", (_e, payload) => {
  publishAvatarPresence(payload || {});
});

ipcMain.on("compagnon:overlay-move", (_e, payload) => {
  const x = Number(payload && payload.x);
  const y = Number(payload && payload.y);
  if (!Number.isFinite(x) || !Number.isFinite(y)) return;
  // Pause motion pendant un drag manuel
  if (motionState) {
    motionState.pauseUntil = Date.now() + 8000;
    motionState.x = x;
    motionState.y = y;
  }
  moveOverlayTo(x, y);
});

ipcMain.handle("compagnon:overlay-get-bounds", () => {
  if (!overlayWindow || overlayWindow.isDestroyed()) return null;
  const [x, y] = overlayWindow.getPosition();
  const [width, height] = overlayWindow.getSize();
  return { x, y, width, height };
});

ipcMain.handle("compagnon:session-decision", async (_e, body) => {
  const cfg = config.sessionIsland || DEFAULT_CONFIG.sessionIsland;
  const url = String((cfg && cfg.decisionUrl) || "").trim();
  if (!url) return { ok: false, error: "decisionUrl manquant" };
  try {
    const u = new URL(url);
    const lib = u.protocol === "https:" ? https : http;
    const payload = JSON.stringify(body || {});
    return await new Promise((resolve) => {
      const req = lib.request(
        {
          hostname: u.hostname,
          port: u.port || (u.protocol === "https:" ? 443 : 80),
          path: u.pathname + u.search,
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Content-Length": Buffer.byteLength(payload),
          },
          timeout: 8000,
        },
        (res) => {
          let data = "";
          res.on("data", (c) => {
            data += c;
          });
          res.on("end", () => {
            try {
              resolve(JSON.parse(data));
            } catch (_) {
              resolve({ ok: res.statusCode >= 200 && res.statusCode < 300, raw: data.slice(0, 200) });
            }
          });
        }
      );
      req.on("error", (err) => resolve({ ok: false, error: String(err.message || err) }));
      req.write(payload);
      req.end();
    });
  } catch (e) {
    return { ok: false, error: String((e && e.message) || e) };
  }
});

function forwardSessionEvent(ev) {
  if (!overlayWindow || overlayWindow.isDestroyed()) return;
  try {
    overlayWindow.webContents.send("compagnon:session-event", ev);
  } catch (_) {}
}

function stopSessionIslandStream() {
  if (sessionStreamRetry) {
    clearTimeout(sessionStreamRetry);
    sessionStreamRetry = null;
  }
  if (sessionStreamReq) {
    try {
      sessionStreamReq.destroy();
    } catch (_) {}
    sessionStreamReq = null;
  }
}

function startSessionIslandStream() {
  const cfg = config.sessionIsland || DEFAULT_CONFIG.sessionIsland;
  if (!cfg || cfg.enabled === false) return;
  const url = String(cfg.streamUrl || "").trim();
  if (!url) return;
  stopSessionIslandStream();
  let u;
  try {
    u = new URL(url);
  } catch (_) {
    return;
  }
  const lib = u.protocol === "https:" ? https : http;
  const req = lib.get(
    {
      hostname: u.hostname,
      port: u.port || (u.protocol === "https:" ? 443 : 80),
      path: u.pathname + u.search,
      headers: { Accept: "text/event-stream" },
      timeout: 0,
    },
    (res) => {
      sessionStreamReq = res;
      let buf = "";
      res.setEncoding("utf8");
      res.on("data", (chunk) => {
        buf += chunk;
        const parts = buf.split("\n\n");
        buf = parts.pop() || "";
        for (const block of parts) {
          const line = block
            .split("\n")
            .find((l) => l.startsWith("data: "));
          if (!line) continue;
          try {
            forwardSessionEvent(JSON.parse(line.slice(6)));
          } catch (_) {}
        }
      });
      res.on("end", () => {
        sessionStreamReq = null;
        sessionStreamRetry = setTimeout(startSessionIslandStream, 5000);
      });
      res.on("error", () => {
        sessionStreamReq = null;
        sessionStreamRetry = setTimeout(startSessionIslandStream, 8000);
      });
    }
  );
  req.on("error", () => {
    sessionStreamRetry = setTimeout(startSessionIslandStream, 8000);
  });
}

const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
  app.quit();
} else {
  app.on("second-instance", () => showChat());

  app.whenReady().then(async () => {
    loadConfig();
    if (process.platform === "win32") {
      app.setAppUserModelId("lbg.compagnon.desktop");
    }
    // Purge partitions Chromium (ancienne + courante) — plus de chips fantômes
    try {
      const { session } = require("electron");
      for (const name of ["persist:compagnon-chat", "persist:compagnon-chat-v2"]) {
        const s = session.fromPartition(name);
        await s.clearCache().catch(() => {});
        await s
          .clearStorageData({
            storages: ["serviceworkers", "cachestorage", "shadercache"],
          })
          .catch(() => {});
      }
    } catch (_) {
      /* ignore */
    }
    buildTray();
    createOverlayWindow();
    avatarBridge = createAvatarBridge(config.avatarBridge || DEFAULT_CONFIG.avatarBridge, {
      onCommand: async (body) => {
        const cmd = String((body && body.cmd) || "").trim();
        const d = (body && body.detail) || body || {};
        if (cmd === "open_chat") {
          showChat();
          return { ok: true };
        }
        if (cmd === "open_agir") {
          showChatWithAgir({
            sourceText: d.sourceText || "",
            label: d.label || "Initiative",
          });
          return { ok: true };
        }
        if (cmd === "set_mood") {
          setOverlayMood(d.mood || d.tone || "serene");
          return { ok: true };
        }
        if (cmd === "guide" || cmd === "guide_to") {
          if (d.title || d.window) {
            return guideToWindowTitle(d.title || d.window, d.message);
          }
          if (d.demo) return guideDemo(d.demo);
          if (Number.isFinite(Number(d.x)) && Number.isFinite(Number(d.y))) {
            return guideToTarget({
              x: Number(d.x),
              y: Number(d.y),
              width: Number(d.width) || 80,
              height: Number(d.height) || 80,
              title: d.label || "cible",
              message: d.message,
            });
          }
          return guideDemo("icons");
        }
        if (cmd === "guide_demo") {
          return guideDemo(d.kind || d.demo || "icons");
        }
        if (cmd === "set_pose" || cmd === "pose") {
          const pose = d.pose || d.name || "wave";
          const holdMs = Number(d.holdMs) || 2500;
          if (overlayWindow && !overlayWindow.isDestroyed()) {
            overlayWindow.webContents.send("compagnon:vrm-pose", { pose, holdMs });
            return { ok: true, pose, holdMs };
          }
          return { ok: false, error: "overlay absent" };
        }
        if (cmd === "set_model" || cmd === "vrm_model" || cmd === "model") {
          const model = d.model || d.path || "./vrm/default.vrm";
          setVrmModel(model);
          return { ok: true, model };
        }
        if (cmd === "wander" || cmd === "set_wander") {
          const on = d.enabled !== undefined ? Boolean(d.enabled) : true;
          setWanderEnabled(on);
          return { ok: true, wander: on };
        }
        return { ok: false, error: `cmd inconnu: ${cmd}` };
      },
    });
    avatarBridge.start();
    showChat();
    startInitiativePolling();
    startSessionIslandStream();
  });

  app.on("before-quit", () => {
    quitting = true;
    if (initiativeTimer) clearInterval(initiativeTimer);
    stopSessionIslandStream();
    if (avatarBridge) {
      avatarBridge.stop();
      avatarBridge = null;
    }
  });

  app.on("window-all-closed", () => {
    // Keep process for tray (Windows / Linux)
  });

  app.on("activate", () => showChat());
}
