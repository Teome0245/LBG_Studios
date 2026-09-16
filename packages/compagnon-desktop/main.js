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

const DEFAULT_CONFIG = {
  compagnonUrl: "http://192.168.0.100:5174/",
  window: { width: 1180, height: 780, minWidth: 720, minHeight: 520 },
  overlay: {
    enabled: true,
    width: 168,
    height: 200,
    marginRight: 16,
    marginBottom: 72,
    alwaysOnTop: true,
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
      const raw = JSON.parse(fs.readFileSync(p, "utf8"));
      config = {
        ...DEFAULT_CONFIG,
        ...raw,
        window: { ...DEFAULT_CONFIG.window, ...(raw.window || {}) },
        overlay: { ...DEFAULT_CONFIG.overlay, ...(raw.overlay || {}) },
        tray: { ...DEFAULT_CONFIG.tray, ...(raw.tray || {}) },
        initiative: { ...DEFAULT_CONFIG.initiative, ...(raw.initiative || {}) },
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
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
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

  mainWindow.loadURL(compagnonUrl()).catch((err) => {
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

  return mainWindow;
}

function overlayBounds() {
  const o = config.overlay || DEFAULT_CONFIG.overlay;
  const display = screen.getPrimaryDisplay();
  const wa = display.workArea;
  const width = o.width || 168;
  const height = o.height || 200;
  const x = wa.x + wa.width - width - (o.marginRight || 16);
  const y = wa.y + wa.height - height - (o.marginBottom || 72);
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
      sandbox: true,
    },
  });

  overlayWindow.setAlwaysOnTop(o.alwaysOnTop !== false, "floating");
  overlayWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: false });

  overlayWindow.once("ready-to-show", () => {
    if (overlayWindow && !overlayWindow.isDestroyed()) overlayWindow.showInactive();
  });

  overlayWindow.on("closed", () => {
    overlayWindow = null;
  });

  overlayWindow.loadFile(path.join(__dirname, "overlay", "index.html"));
  return overlayWindow;
}

function showChat() {
  createMainWindow();
  if (mainWindow && !mainWindow.isDestroyed()) {
    if (mainWindow.isMinimized()) mainWindow.restore();
    mainWindow.show();
    mainWindow.focus();
  }
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

function buildTray() {
  if (tray) return tray;
  tray = new Tray(trayImage());
  tray.setToolTip((config.tray && config.tray.tooltip) || "LBG Compagnon");
  const menu = Menu.buildFromTemplate([
    { label: "Ouvrir Compagnon", click: () => showChat() },
    { label: "Afficher / masquer chat", click: () => toggleChat() },
    { type: "separator" },
    { label: "Avatar (overlay)", click: () => toggleOverlay() },
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
  if (status.infra_signals && status.infra_signals.ad_agent_down) return "infra:ad_agent_down";
  return "";
}

function initiativeMessage(status) {
  const act = status.last_action;
  if (act && act.message) return String(act.message);
  if (status.infra_signals && status.infra_signals.ad_agent_down) {
    return "Agent AD injoignable — ouvrir Compagnon pour en parler.";
  }
  return "Initiative Compagnon disponible.";
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

  const body = initiativeMessage(status);
  initiativeShown.push({ ts: Date.now(), id });
  lastNotifiedId = id;

  setOverlayMood({ tone: "alert", label: "Initiative" });
  setTimeout(() => setOverlayMood({ tone: "serene", label: "Serein" }), 8000);

  if (Notification.isSupported()) {
    const n = new Notification({
      title: "Compagnon · initiative",
      body: body.slice(0, 180),
      silent: false,
    });
    n.on("click", () => showChat());
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
}));

ipcMain.on("compagnon:open-chat", () => showChat());

ipcMain.on("compagnon:overlay-mood", (_e, mood) => {
  setOverlayMood(mood);
});

const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
  app.quit();
} else {
  app.on("second-instance", () => showChat());

  app.whenReady().then(() => {
    loadConfig();
    if (process.platform === "win32") {
      app.setAppUserModelId("lbg.compagnon.desktop");
    }
    buildTray();
    createOverlayWindow();
    showChat();
    startInitiativePolling();
  });

  app.on("before-quit", () => {
    quitting = true;
    if (initiativeTimer) clearInterval(initiativeTimer);
  });

  app.on("window-all-closed", () => {
    // Keep process for tray (Windows / Linux)
  });

  app.on("activate", () => showChat());
}
