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
  globalShortcut,
  powerMonitor,
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
  getActiveWindow,
  categorizeFocus,
} = require("./desktop_targets");

const DEFAULT_CONFIG = {
  compagnonUrl: "http://192.168.0.100:5174/",
  window: { width: 1180, height: 780, minWidth: 720, minHeight: 520 },
  overlay: {
    enabled: true,
    /** face = FaceRig 2D (Lyra) · vrm = perso 3D */
    mode: "vrm",
    width: 320,
    height: 420,
    marginRight: 16,
    marginBottom: 0,
    alwaysOnTop: true,
    vrmModel: "./vrm/Compagnon.vrm",
    /** bust = visage · full = corps entier */
    vrmFraming: "full",
    /** Deplacement autonome sur le bureau */
    wander: true,
    wanderSpeed: 165,
    wanderPauseMs: 45000,
    /** Guide vers fenêtre / icônes (px/s) */
    guideSpeed: 220,
    /** Mode fantôme : clics traversants (VSeeFace canon) */
    clickThrough: false,
    clickThroughHotkey: "CommandOrControl+Shift+F",
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
  /** Ticket 1.1 — Push-to-Talk / Voice-In */
  stt: {
    enabled: true,
    hotkey: "CommandOrControl+Shift+Space",
  },
  /** Ticket 1.2 — Conscience Contextuelle de l'Espace de Travail (Focus Awareness) */
  focusAwareness: {
    enabled: true,
    intervalMs: 45_000,
    idleThresholdSec: 300,
  },
};

let mainWindow = null;
let overlayWindow = null;
let tray = null;
let config = { ...DEFAULT_CONFIG };
let quitting = false;
let initiativeTimer = null;
let focusTimer = null;
let currentFocusState = { category: "idle", app: "unknown", attitude: "relax", ts: Date.now() };
/** @type {{ ts: number, id: string }[]} */
let initiativeShown = [];
let lastNotifiedId = "";
/** @type {import("http").IncomingMessage | null} */
let sessionStreamReq = null;
let sessionStreamRetry = null;
let clickThrough = false;
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

  mainWindow.webContents.on("before-input-event", (event, input) => {
    if (input.key === "F5" || (input.control && input.key.toLowerCase() === "r")) {
      mainWindow.webContents.reloadIgnoringCache();
      event.preventDefault();
    }
    if (input.control && input.shift && input.key.toLowerCase() === "i") {
      mainWindow.webContents.toggleDevTools();
      event.preventDefault();
    }
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
  const width = o.width || 320;
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
    if ((config.overlay || {}).wander !== false) scheduleNextDesktopInteraction();
  });

  overlayWindow.on("closed", () => {
    stopMotion();
    overlayWindow = null;
  });

  overlayWindow.loadFile(path.join(__dirname, "overlay", "index.html"));
  if (clickThrough) {
    overlayWindow.setIgnoreMouseEvents(true, { forward: true });
  }
  return overlayWindow;
}

function clampOverlayPos(x, y) {
  const o = config.overlay || DEFAULT_CONFIG.overlay;
  const w = o.width || 320;
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
  const w = o.width || 320;
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

  // Déplacements vivants et calibrés (~180 à 400 px) synchronisés avec le cycle de marche mocap
  const minX = wa.x + 10;
  const maxX = wa.x + wa.width - w - 10;

  const strollDist = 180 + Math.random() * 220;
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

let desktopInteractionTimer = null;

function stopWander() {
  if (desktopInteractionTimer) {
    clearTimeout(desktopInteractionTimer);
    desktopInteractionTimer = null;
  }
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
        stopMotion();
        scheduleNextDesktopInteraction();
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

function returnToTaskbar() {
  if (!overlayWindow || overlayWindow.isDestroyed()) return;
  const o = config.overlay || DEFAULT_CONFIG.overlay;
  const w = o.width || 320;
  const h = o.height || 420;
  const d = screen.getPrimaryDisplay();
  const wa = d.workArea;
  const targetX = wa.x + wa.width - w - (Number.isFinite(o.marginRight) ? o.marginRight : 16);
  const targetY = wa.y + wa.height - h;
  animateOverlayTo(targetX, targetY, {
    mode: "guide",
    onArrive: () => {
      sendVrmPose("relax", 5000);
      sendVrmHeading(0);
    },
  });
}

function scheduleNextDesktopInteraction() {
  if (desktopInteractionTimer) {
    clearTimeout(desktopInteractionTimer);
    desktopInteractionTimer = null;
  }
  const o = config.overlay || DEFAULT_CONFIG.overlay;
  if (o.wander === false) return;

  // Pause sereine et vivante sur la barre des tâches (45s à 90s)
  const delayMs = Math.round(45000 + Math.random() * 45000);
  desktopInteractionTimer = setTimeout(async () => {
    desktopInteractionTimer = null;
    if (!overlayWindow || overlayWindow.isDestroyed()) return;
    if (motionState && motionState.isWalking) return;

    // En autonomie : Compagnon vit et reste posée sur la barre des tâches (sa base naturelle).
    // Les déplacements vers les fenêtres ne sont activés qu'à la demande explicite de l'utilisateur (menu Tray ou API).
    const moves = ["lookaround", "relax", "stretch", "think", "spin", "jump", "fingerHeart"];
    const pick = moves[Math.floor(Math.random() * moves.length)];
    const holdMs = (pick === "lookaround" || pick === "relax") ? 6000 : (pick === "fingerHeart" ? 8500 : 4000);
    sendVrmPose(pick, holdMs);

    scheduleNextDesktopInteraction();
  }, delayMs);
}

function startWander() {
  stopMotion();
  if (!overlayWindow || overlayWindow.isDestroyed()) return;
  const o = config.overlay || DEFAULT_CONFIG.overlay;
  if (o.wander === false) return;
  scheduleNextDesktopInteraction();
}

/** Fait marcher physiquement l'avatar sur la barre des tâches lors d'une commande de marche. */
function startWalkingMovement(holdMs = 6000) {
  if (!overlayWindow || overlayWindow.isDestroyed()) return;
  const o = config.overlay || DEFAULT_CONFIG.overlay;
  const w = o.width || 320;
  const h = o.height || 420;

  const [curX, curY] = overlayWindow.getPosition();
  const d = screen.getDisplayNearestPoint({ x: curX + w / 2, y: curY + h / 2 }) || screen.getPrimaryDisplay();
  const wa = d.workArea;

  const floorY = wa.y + wa.height - h;
  const minX = wa.x + 10;
  const maxX = wa.x + wa.width - w - 10;

  const speed = Math.max(80, Number(o.wanderSpeed) || 165);
  const durationSec = Math.max(1, Number(holdMs) || 6000) / 1000;
  const totalDist = durationSec * speed;

  const spaceRight = maxX - curX;
  const spaceLeft = curX - minX;

  let targetX;
  if (spaceRight >= 120 && (spaceRight >= spaceLeft || spaceLeft < 100)) {
    targetX = Math.min(maxX, curX + Math.min(totalDist, spaceRight));
  } else {
    targetX = Math.max(minX, curX - Math.min(totalDist, spaceLeft));
  }

  animateOverlayTo(Math.round(targetX), floorY, {
    speed,
    mode: "wander",
    onArrive: () => {
      sendVrmPose("idle", 0);
      sendVrmHeading(0);
    },
  });
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
      const hold = Number(target.holdMs) || 5000;
      sendOverlayGuide({
        message,
        label,
        pointSide: place.pointSide,
        holdMs: hold,
      });
      setOverlayMood({ tone: "curious", label: "Guide" });
      if (avatarBridge) {
        avatarBridge.publishSay(message.slice(0, 100));
      }
      setTimeout(() => {
        returnToTaskbar();
      }, hold + 1200);
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
    { label: "Repos posé (relax)", click: () => sendVrmPose("relax", 6000) },
    { label: "Observation (lookaround)", click: () => sendVrmPose("lookaround", 5000) },
    { label: "Étirement (stretch)", click: () => sendVrmPose("stretch", 5000) },
    { label: "Saluer (wave)", click: () => sendVrmPose("wave", 3000) },
    { label: "Confiante (crossArms)", click: () => sendVrmPose("crossArms", 5000) },
    { label: "Réflexion (think)", click: () => sendVrmPose("think", 4000) },
    { label: "🔍 Focus & Scan Code (focus)", click: () => sendVrmPose("focus", 6000) },
    { label: "🏆 Victoire & Célébration (victory)", click: () => sendVrmPose("victory", 4500) },
    { label: "Approbation (approve)", click: () => sendVrmPose("approve", 3500) },
    { type: "separator" },
    { label: "💖 Petite Danse Idol (fingerHeart)", click: () => sendVrmPose("fingerHeart", 8500) },
    { label: "🎵 Danse Pop / Groove (dance)", click: () => sendVrmPose("dance", 8000) },
    { label: "💃 Danse Latino / Samba (samba)", click: () => sendVrmPose("samba", 10000) },
    { label: "🧢 Danse Hip-Hop (hiphop)", click: () => sendVrmPose("hiphop", 10000) },
    { label: "🤖 Danse Robot / Popping (robot)", click: () => sendVrmPose("robot", 10000) },
    { label: "🪩 Danse Disco / Funk (disco)", click: () => sendVrmPose("disco", 10000) },
    { label: "💫 Pirouette 360° (spin)", click: () => sendVrmPose("spin", 6000) },
    { label: "🎉 Saut de joie / Victoire (jump)", click: () => sendVrmPose("jump", 4000) },
    { label: "👏 Applaudissements (clapping)", click: () => sendVrmPose("clapping", 4500) },
    { label: "🙇 Révérence (bow)", click: () => sendVrmPose("bow", 3000) },
    { label: "Colère / boudage (angry)", click: () => sendVrmPose("angry", 4000) },
    { type: "separator" },
    { label: "🚶 Marche (walk)", click: () => startWalkingMovement(6000) },
    { label: "Pointer écran (pointScreen)", click: () => sendVrmPose("pointScreen", 4000) },
    { label: "Pointer à gauche (pointLeft)", click: () => sendVrmPose("pointLeft", 4000) },
    { label: "Pointer à droite (pointRight)", click: () => sendVrmPose("pointRight", 4000) },
  ];

  const menu = Menu.buildFromTemplate([
    { label: "Ouvrir Compagnon", click: () => showChat() },
    { label: "Afficher / masquer chat", click: () => toggleChat() },
    {
      label: "🔄 Recharger l'interface Chat (Ctrl+R / F5)",
      click: () => {
        if (mainWindow && !mainWindow.isDestroyed()) {
          mainWindow.webContents.reloadIgnoringCache();
          mainWindow.show();
        }
      },
    },
    {
      label: "🧠 Conscience 3D de Lyra",
      click: () => shell.openExternal(compagnonUrl() + "brain"),
    },
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
      label: "👓 Accessoires 3D Modulaires",
      submenu: [
        { label: "🕶️ Visière HUD Cyber", click: () => sendVrmAccessory("visor") },
        { label: "📱 Datapad Holographique", click: () => sendVrmAccessory("datapad") },
        { label: "🎧 Oreillette Neurale", click: () => sendVrmAccessory("headset") },
      ],
    },
    {
      label: "🎭 Spectacles & Shows (iStripper)",
      submenu: [
        { label: "✨ Show K-Pop Idol (~45s)", click: () => triggerShow("idol") },
        { label: "🪩 Show Club Electro (~40s)", click: () => triggerShow("club") },
        { label: "💃 Show Fiesta Latina (~40s)", click: () => triggerShow("latino") },
        { type: "separator" },
        { label: "⏹ Arrêter le spectacle", click: () => stopOverlayShow() },
      ],
    },
    {
      label: "Modèles VRM (VRoid)",
      submenu: modelsSub,
    },
    { type: "separator" },
    {
      label: clickThrough ? "👻 Désactiver Mode Fantôme (clics actifs)" : "👻 Activer Mode Fantôme (clic traversant) [Ctrl+Shift+F]",
      type: "checkbox",
      checked: clickThrough,
      click: () => setOverlayClickThrough(!clickThrough),
    },
    {
      label: "Interactions bureau autonomes",
      type: "checkbox",
      checked: Boolean((config.overlay || {}).wander),
      click: (item) => setWanderEnabled(Boolean(item.checked)),
    },
    {
      label: "Interagir avec le bureau…",
      submenu: [
        {
          label: "🪟 Inspecter une fenêtre active",
          click: () => guideDemo("window"),
        },
        {
          label: "🖥️ Aller voir les icônes bureau",
          click: () => guideDemo("icons"),
        },
        {
          label: "🕒 Aller voir la barre des tâches",
          click: () => guideDemo("taskbar"),
        },
        {
          label: "🧘 Reprendre position sur barre des tâches",
          click: () => returnToTaskbar(),
        },
      ],
    },
    {
      label: "Ouvrir dans le navigateur",
      click: () => shell.openExternal(compagnonUrl()),
    },
    { type: "separator" },
    {
      label: "🔄 Vérifier les mises à jour (A: -> C:)",
      click: () => checkAndApplySourceUpdate(true),
    },
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
  return full ? { width: 320, height: 420 } : { width: 220, height: 280 };
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
  if (pose) {
    if (pose === "walk") {
      startWalkingMovement(holdMs);
    } else {
      sendVrmPose(pose, holdMs);
    }
  }
});

function sendVrmAccessory(type, equip) {
  if (overlayWindow && !overlayWindow.isDestroyed()) {
    overlayWindow.webContents.send("compagnon:vrm-accessory", { type, equip });
  }
}

ipcMain.on("compagnon:toggle-accessory", (_e, type) => {
  sendVrmAccessory(type);
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

ipcMain.on("compagnon:poke-avatar", () => {
  const pokes = [
    { pose: "wave", holdMs: 3000, msg: "Coucou ! 👋" },
    { pose: "fingerHeart", holdMs: 6500, msg: "Je suis là pour toi ! 💖" },
    { pose: "approve", holdMs: 3500, msg: "Tout roule ! 👍" },
    { pose: "jump", holdMs: 3500, msg: "Toujours prête ! 🎉" },
    { pose: "stretch", holdMs: 4500, msg: "Une pause ferait du bien ? 🙆" },
  ];
  const pick = pokes[Math.floor(Math.random() * pokes.length)];
  sendVrmPose(pick.pose, pick.holdMs);
  if (overlayWindow && !overlayWindow.isDestroyed()) {
    overlayWindow.webContents.send("compagnon:initiative", {
      message: pick.msg,
      body: pick.msg,
      label: "Compagnon",
    });
    setTimeout(() => {
      if (overlayWindow && !overlayWindow.isDestroyed()) {
        overlayWindow.webContents.send("compagnon:initiative", null);
      }
    }, pick.holdMs);
  }
});

ipcMain.on("compagnon:show-overlay-context-menu", () => {
  if (!overlayWindow || overlayWindow.isDestroyed()) return;

  const currentFraming = (config.overlay && config.overlay.vrmFraming) || "full";
  const contextMenu = Menu.buildFromTemplate([
    {
      label: "💬 Ouvrir Compagnon (Chat)",
      click: () => showChat(),
    },
    {
      label: "🔄 Recharger l'interface Chat (Ctrl+R)",
      click: () => {
        if (mainWindow && !mainWindow.isDestroyed()) {
          mainWindow.webContents.reloadIgnoringCache();
          mainWindow.show();
        }
      },
    },
    { type: "separator" },
    {
      label: "👋 Saluer",
      click: () => sendVrmPose("wave", 3000),
    },
    {
      label: "💖 Mini Heart Idol",
      click: () => sendVrmPose("fingerHeart", 8500),
    },
    {
      label: "🦾 Confiante",
      click: () => sendVrmPose("crossArms", 5000),
    },
    {
      label: "🤔 Réfléchir",
      click: () => sendVrmPose("think", 4000),
    },
    {
      label: "🔍 Focus & Scan Code",
      click: () => sendVrmPose("focus", 6000),
    },
    {
      label: "🏆 Victoire & Célébration",
      click: () => sendVrmPose("victory", 4500),
    },
    {
      label: "🧘 Repos posé",
      click: () => sendVrmPose("relax", 6000),
    },
    {
      label: "👓 Accessoires 3D Modulaires",
      submenu: [
        { label: "🕶️ Visière HUD Cyber", click: () => sendVrmAccessory("visor") },
        { label: "📱 Datapad Holographique", click: () => sendVrmAccessory("datapad") },
        { label: "🎧 Oreillette Neurale", click: () => sendVrmAccessory("headset") },
      ],
    },
    {
      label: "💃 Pack Danses",
      submenu: [
        { label: "🎵 Pop / Groove", click: () => sendVrmPose("dance", 8000) },
        { label: "💃 Samba Latino", click: () => sendVrmPose("samba", 10000) },
        { label: "🧢 Hip-Hop Street", click: () => sendVrmPose("hiphop", 10000) },
        { label: "🤖 Robot / Popping", click: () => sendVrmPose("robot", 10000) },
        { label: "🪩 Disco 70s", click: () => sendVrmPose("disco", 10000) },
        { label: "💫 Pirouette 360°", click: () => sendVrmPose("spin", 6000) },
      ],
    },
    {
      label: "🎭 Spectacles & Shows (iStripper)",
      submenu: [
        { label: "✨ Show K-Pop Idol (~45s)", click: () => triggerShow("idol") },
        { label: "🪩 Show Club Electro (~40s)", click: () => triggerShow("club") },
        { label: "💃 Show Fiesta Latina (~40s)", click: () => triggerShow("latino") },
        { type: "separator" },
        { label: "⏹ Arrêter le spectacle", click: () => stopOverlayShow() },
      ],
    },
    { type: "separator" },
    {
      label: "📐 Cadrage : Buste",
      type: "radio",
      checked: currentFraming === "bust",
      click: () => setOverlayFraming("bust"),
    },
    {
      label: "📐 Cadrage : Corps entier",
      type: "radio",
      checked: currentFraming === "full",
      click: () => setOverlayFraming("full"),
    },
    { type: "separator" },
    {
      label: clickThrough ? "👻 Désactiver Mode Fantôme" : "👻 Mode Fantôme (clic traversant) [Ctrl+Shift+F]",
      type: "checkbox",
      checked: clickThrough,
      click: () => setOverlayClickThrough(!clickThrough),
    },
    {
      label: "🚶 Marche sur la barre des tâches",
      click: () => startWalkingMovement(8000),
    },
    {
      label: "👁 Masquer l'avatar",
      click: () => overlayWindow.hide(),
    },
  ]);

  contextMenu.popup({ window: overlayWindow });
});

/** Mode Fantôme / Clic traversant (VSeeFace canon) */
function setOverlayClickThrough(enable) {
  clickThrough = !!enable;
  if (!overlayWindow || overlayWindow.isDestroyed()) return;
  overlayWindow.setIgnoreMouseEvents(clickThrough, { forward: true });
  overlayWindow.webContents.send("compagnon:click-through-changed", clickThrough);
  rebuildTrayMenu().catch(() => {});
  if (clickThrough) {
    if (Notification.isSupported()) {
      new Notification({
        title: "Compagnon — Mode Fantôme",
        body: "Clics traversants activés. Raccourci Ctrl+Shift+F (ou clic Tray) pour réactiver l'interaction.",
        silent: true,
      }).show();
    }
  }
}

function registerGhostShortcuts() {
  const o = config.overlay || DEFAULT_CONFIG.overlay;
  const hotkey = (o && o.clickThroughHotkey) || "CommandOrControl+Shift+F";
  try {
    const ok = globalShortcut.register(hotkey, () => {
      setOverlayClickThrough(!clickThrough);
    });
    if (ok) {
      console.log("[desktop] Hotkey Mode Fantôme (clic traversant) enregistré :", hotkey);
    }
  } catch (err) {
    console.warn("[desktop] Erreur enregistrement hotkey ghost mode :", hotkey, err);
  }
}

ipcMain.on("compagnon:set-click-through", (_e, enable) => setOverlayClickThrough(enable));
ipcMain.handle("compagnon:get-click-through", () => clickThrough);

/** Show Routine Manager (iStripper / vghd canon) */
function triggerShow(routine = "idol") {
  if (!overlayWindow || overlayWindow.isDestroyed()) return;
  overlayWindow.webContents.send("compagnon:show-event", { action: "start", routine });
}

function stopOverlayShow() {
  if (!overlayWindow || overlayWindow.isDestroyed()) return;
  overlayWindow.webContents.send("compagnon:show-event", { action: "stop" });
}

ipcMain.on("compagnon:start-show", (_e, routine) => triggerShow(routine));
ipcMain.on("compagnon:stop-show", () => stopOverlayShow());

/** Ticket 1.1 — Push-to-Talk / Voice-In (IPC & Raccourci Global) */
ipcMain.on("compagnon:voice-trigger", () => {
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send("compagnon:voice-toggle", { source: "ipc_trigger" });
  }
});

function registerVoiceShortcuts() {
  const sttCfg = config.stt || DEFAULT_CONFIG.stt;
  if (!sttCfg || sttCfg.enabled === false) return;
  const hotkey = sttCfg.hotkey || "CommandOrControl+Shift+Space";

  try {
    const ok = globalShortcut.register(hotkey, () => {
      showChat();
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send("compagnon:voice-toggle", { source: "global_hotkey", hotkey });
      }
      setOverlayMood("listening");
    });
    if (ok) {
      console.log("[desktop] Hotkey Push-to-Talk enregistré :", hotkey);
    } else {
      console.warn("[desktop] Échec enregistrement hotkey Push-to-Talk :", hotkey);
    }
  } catch (err) {
    console.warn("[desktop] Erreur enregistrement hotkey STT :", hotkey, err);
  }
}

/** Ticket 1.2 — Conscience Contextuelle de l'Espace de Travail (Focus Awareness) */
ipcMain.handle("compagnon:get-focus-context", () => currentFocusState);

async function pollFocusAwareness() {
  const cfg = config.focusAwareness || DEFAULT_CONFIG.focusAwareness;
  if (!cfg || cfg.enabled === false) return;

  try {
    let isIdle = false;
    let idleSec = 0;
    if (powerMonitor && typeof powerMonitor.getSystemIdleTime === "function") {
      idleSec = powerMonitor.getSystemIdleTime();
      if (idleSec >= (cfg.idleThresholdSec || 300)) {
        isIdle = true;
      }
    }

    if (isIdle) {
      if (currentFocusState.category !== "idle") {
        currentFocusState = {
          category: "idle",
          app: "system",
          attitude: "relax",
          label: "Inactif / Pause",
          idleSec,
          ts: Date.now(),
        };
        sendVrmPose("relax", 8000);
        notifyFocusContext(currentFocusState);
      }
      return;
    }

    const win = await getActiveWindow();
    const focus = categorizeFocus(win);

    if (focus.category !== currentFocusState.category) {
      const prev = currentFocusState.category;
      currentFocusState = {
        ...focus,
        idleSec,
        ts: Date.now(),
      };
      console.log(`[desktop] Focus contextuel changé : ${prev} → ${focus.category} (${focus.attitude})`);

      if (focus.attitude === "think") {
        sendVrmPose("think", 4000);
      } else if (focus.attitude === "curious") {
        sendVrmPose("lookaround", 5000);
      } else if (focus.attitude === "alert") {
        sendVrmPose("crossArms", 4500);
      } else if (focus.attitude === "cheer") {
        sendVrmPose("approve", 3500);
      }

      notifyFocusContext(currentFocusState);
    }
  } catch (err) {
    console.warn("[desktop] Erreur sondage focus awareness :", err);
  }
}

function notifyFocusContext(context) {
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send("compagnon:focus-context", context);
  }
  if (avatarBridge) {
    avatarBridge.publishSay(`[focus:${context.category}]`);
  }
}

function startFocusAwareness() {
  if (focusTimer) clearInterval(focusTimer);
  const cfg = config.focusAwareness || DEFAULT_CONFIG.focusAwareness;
  if (!cfg || cfg.enabled === false) return;
  const interval = Math.max(15_000, Number(cfg.intervalMs) || 45_000);
  focusTimer = setInterval(pollFocusAwareness, interval);
  setTimeout(pollFocusAwareness, 8_000);
}

function stopFocusAwareness() {
  if (focusTimer) {
    clearInterval(focusTimer);
    focusTimer = null;
  }
}

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

function checkAndApplySourceUpdate(manual = false) {
  if (process.platform !== "win32") return false;

  const candidateRoots = [
    "A:\\LBG_Studios\\packages\\compagnon-desktop",
    "\\\\192.168.0.143\\projects\\LBG_Studios\\packages\\compagnon-desktop",
  ];

  let sourceRoot = null;
  for (const c of candidateRoots) {
    try {
      if (fs.existsSync(path.join(c, "main.js"))) {
        sourceRoot = c;
        break;
      }
    } catch (_) {}
  }

  if (!sourceRoot) {
    if (manual) {
      new Notification({
        title: "LBG Compagnon",
        body: "Dépôt source non détecté (A: ou réseau déconnecté).",
      }).show();
    }
    return false;
  }

  const localRoot = __dirname;
  if (sourceRoot.toLowerCase() === localRoot.toLowerCase()) return false;

  const { spawnSync } = require("child_process");

  function runRobocopy(src, dst, args = []) {
    // Robocopy codes 0..7 sont des succès (0=identique, 1=fichiers copiés, etc.)
    const res = spawnSync("robocopy", [src, dst, ...args, "/NFL", "/NDL", "/NJH", "/NJS", "/nc", "/ns", "/np"], {
      windowsHide: true,
      encoding: "utf8",
    });
    return res.status != null && res.status < 8;
  }

  console.info(`[AutoUpdate] Vérification depuis ${sourceRoot}...`);

  // 1. Synchronisation du dossier overlay (VRM, animations, bundle, shaders)
  const srcOverlay = path.join(sourceRoot, "overlay");
  const dstOverlay = path.join(localRoot, "overlay");
  if (fs.existsSync(srcOverlay)) {
    runRobocopy(srcOverlay, dstOverlay, ["/MIR"]);
  }

  // 2. Synchronisation de main.js et preload.js
  let codeUpdated = false;
  for (const file of ["main.js", "preload.js"]) {
    const srcFile = path.join(sourceRoot, file);
    const dstFile = path.join(localRoot, file);
    if (fs.existsSync(srcFile) && fs.existsSync(dstFile)) {
      try {
        const srcStat = fs.statSync(srcFile);
        const dstStat = fs.statSync(dstFile);
        if (srcStat.mtimeMs > dstStat.mtimeMs + 500) {
          fs.copyFileSync(srcFile, dstFile);
          codeUpdated = true;
          console.info(`[AutoUpdate] Fichier ${file} synchronisé depuis le repo.`);
        }
      } catch (err) {
        console.warn(`[AutoUpdate] Erreur copie ${file}:`, err);
      }
    }
  }

  if (codeUpdated) {
    console.info("[AutoUpdate] Code principal mis à jour. Relaunch de l'application...");
    if (manual) {
      new Notification({
        title: "LBG Compagnon",
        body: "Mise à jour appliquée ! Relance en cours...",
      }).show();
    }
    app.relaunch();
    app.exit(0);
    return true;
  }

  if (manual) {
    new Notification({
      title: "LBG Compagnon",
      body: "Compagnon synchronisé et à jour !",
    }).show();
    if (overlayWindow && !overlayWindow.isDestroyed()) {
      overlayWindow.webContents.reload();
    }
  }

  return false;
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
      // Synchronisation automatique transparente au démarrage
      const didRelaunch = checkAndApplySourceUpdate(false);
      if (didRelaunch) return;
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
            if (pose === "walk") {
              startWalkingMovement(holdMs);
            } else {
              sendVrmPose(pose, holdMs);
            }
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
    registerVoiceShortcuts();
    registerGhostShortcuts();
    startInitiativePolling();
    startSessionIslandStream();
    startFocusAwareness();
  });

  app.on("before-quit", () => {
    quitting = true;
    try {
      globalShortcut.unregisterAll();
    } catch (_) {}
    if (initiativeTimer) clearInterval(initiativeTimer);
    stopFocusAwareness();
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
