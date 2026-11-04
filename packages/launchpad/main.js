const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn, execSync } = require('child_process');
const fs = require('fs');
const http = require('http');
const https = require('https');
const crypto = require('crypto');

const LAUNCHPAD_VERSION = '2.1.5';
const STATUS_API_TIMEOUT_MS = 12000;
const STATUS_API_FAIL_THRESHOLD = 2;
const PRECU_HOST_LAN = '192.168.0.245';
const PRIME_HOST_LAN = '192.168.0.246';

/** Chemins Windows candidats pour Godot 4.6 + prime-client (J: syncé = runtime dev ; C: = runtime 2nd PC ; WSL = source). */
const CANDIDATE_GODOT_EXES = [
  'J:\\mmmorpg\\Godot_v4.6.1-stable_win64\\Godot_v4.6.1-stable_win64.exe',
  'C:\\LBG_MMO\\mmmorpg\\Godot_v4.6.1-stable_win64\\Godot_v4.6.1-stable_win64.exe',
];

function resolveDefaultGodotExe() {
  if (process.platform === 'win32') {
    for (const exe of CANDIDATE_GODOT_EXES) {
      if (fs.existsSync(exe)) return exe;
    }
  }
  return CANDIDATE_GODOT_EXES[0];
}

const DEFAULT_GODOT_EXE = resolveDefaultGodotExe();
const J_PRIME_CLIENT_DIR = 'J:\\swgemu\\clients\\prime-client';
const C_PRIME_CLIENT_DIR = 'C:\\LBG_MMO\\clients\\prime-client';
const WSL_LBG_STUDIOS_PRIME =
  '\\\\wsl.localhost\\Ubuntu\\home\\sdesh\\projects\\LBG_Studios\\packages\\prime-client';
const WSL_NEW_MMO_PRIME =
  '\\\\wsl.localhost\\Ubuntu\\home\\sdesh\\projects\\new_mmo\\prime-client';

/** Affiche un tampon ISO UTC (…Z) en heure locale (Europe/Paris ≈ +1/+2). */
function formatStampLocal(stamp) {
  const s = String(stamp || '').trim();
  if (!s || s.startsWith('(')) return s;
  const d = new Date(s.endsWith('Z') || /[+-]\d{2}:\d{2}$/.test(s) ? s : `${s}Z`);
  if (Number.isNaN(d.getTime())) return s;
  try {
    return (
      new Intl.DateTimeFormat('fr-FR', {
        timeZone: 'Europe/Paris',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,
      }).format(d) + ' (Paris)'
    );
  } catch (_) {
    return d.toLocaleString('fr-FR');
  }
}

function resolvePrimeClientDir() {
  const fromEnv = (process.env.LBG_PRIME_CLIENT_DIR || '').trim();
  if (fromEnv && fs.existsSync(fromEnv)) {
    // Interdire le legacy new_mmo même via env
    if (/new_mmo/i.test(fromEnv)) {
      console.warn('[Launchpad] LBG_PRIME_CLIENT_DIR pointe new_mmo — ignore, utilise J:');
    } else {
      return fromEnv;
    }
  }
  if (process.platform === 'win32') {
    // Préférer le client syncé J: (dev principal)
    if (fs.existsSync(path.join(J_PRIME_CLIENT_DIR, 'project.godot'))) {
      return J_PRIME_CLIENT_DIR;
    }
    // Client standard C: (ex: second PC)
    if (fs.existsSync(path.join(C_PRIME_CLIENT_DIR, 'project.godot'))) {
      return C_PRIME_CLIENT_DIR;
    }
    if (fs.existsSync(path.join(WSL_LBG_STUDIOS_PRIME, 'project.godot'))) {
      return WSL_LBG_STUDIOS_PRIME;
    }
    // new_mmo = legacy cassé (class_name) — ne plus l’utiliser
  }
  return J_PRIME_CLIENT_DIR;
}

const DEFAULT_PRIME_CLIENT_DIR = resolvePrimeClientDir();

/** Dossier de l’exe (config.json à côté du .exe). */
function appRoot() {
  return app.isPackaged ? path.dirname(process.execPath) : __dirname;
}

/** Racine de l’app (index.html dans app.asar quand packagé). */
function appDir() {
  return __dirname;
}

function configPath() {
  return path.join(appRoot(), 'launchpad.config.json');
}

function defaultProfiles() {
  return [
    {
      id: 'prime',
      label: 'LBG Prime (Godot)',
      clientKind: 'godot',
      gameDir: DEFAULT_PRIME_CLIENT_DIR,
      gameExe: DEFAULT_GODOT_EXE,
      configFile: '',
      patchChannel: 'prime',
      skipPatch: true,
      godotPatchEnabled: true,
      // Fenêtré = même mode que l’éditeur Godot (fullscreen masquait les timeouts WS).
      godotFullscreen: false,
      launchArgs: ['--path', DEFAULT_PRIME_CLIENT_DIR],
      servers: [
        { id: 'prime', label: 'LBG MMO Serveur', ip: PRIME_HOST_LAN, loginPort: 44553 },
      ],
    },
    {
      id: 'swg-3d',
      label: 'SWG Pre-CU 3D (Godot)',
      clientKind: 'godot',
      gameDir: 'J:\\swgemu\\clients\\swg-client',
      gameExe: DEFAULT_GODOT_EXE,
      configFile: '',
      patchChannel: 'swg-3d',
      skipPatch: true,
      godotPatchEnabled: false,
      godotFullscreen: false,
      launchArgs: ['--path', 'J:\\swgemu\\clients\\swg-client'],
      servers: [
        { id: 'swg-3d', label: 'SWG 3D Hub (Lost Heaven)', ip: PRIME_HOST_LAN, loginPort: 8787 },
      ],
    },
  ];
}

function defaultConfig() {
  return {
    launchpadVersion: LAUNCHPAD_VERSION,
    statusApiUrl: 'http://192.168.0.246:8792/api/servers',
    statusApiUrls: ['http://192.168.0.246:8792/api/servers'],
    primeGatewayHealthUrl: `http://${PRIME_HOST_LAN}:8787/healthz`,
    patchServerUrl: 'http://192.168.0.246:8080',
    patchServerUrlNas: 'http://192.168.0.245:8080',
    diskSpaceWarningGb: 40,
    defaultProfileId: 'prime',
    profiles: defaultProfiles(),
  };
}

/** Retire PreCU / SWGEmu du Launchpad (Godot-only). */
function stripPrecuProfiles(cfg) {
  let changed = false;
  const beforeIds = (cfg.profiles || []).map((p) => p.id).join(',');
  cfg.profiles = (cfg.profiles || []).filter((p) => p && p.id !== 'precu' && p.id !== 'swgemu');
  for (const profile of cfg.profiles) {
    const n0 = (profile.servers || []).length;
    profile.servers = (profile.servers || []).filter(
      (s) => s && s.id !== 'precu' && s.id !== 'swgemu'
    );
    if (profile.servers.length !== n0) changed = true;
    if (profile.id === 'prime' && (profile.servers || []).length === 0) {
      profile.servers = [
        { id: 'prime', label: 'LBG MMO Serveur', ip: PRIME_HOST_LAN, loginPort: 44553 },
      ];
      changed = true;
    }
  }
  if (!cfg.profiles.some((p) => p.id === 'prime')) {
    cfg.profiles = defaultProfiles();
    changed = true;
  }
  if (cfg.defaultProfileId !== 'prime' && cfg.defaultProfileId !== 'swg-3d') {
    cfg.defaultProfileId = 'prime';
    changed = true;
  }
  if (Array.isArray(cfg.statusApiUrls)) {
    const filtered = cfg.statusApiUrls.filter((u) => !String(u).includes('.245:'));
    if (filtered.length !== cfg.statusApiUrls.length) {
      cfg.statusApiUrls = filtered;
      changed = true;
    }
  }
  if (!cfg.statusApiUrls || cfg.statusApiUrls.length === 0) {
    cfg.statusApiUrls = [`http://${PRIME_HOST_LAN}:8792/api/servers`];
    changed = true;
  }
  if (cfg.statusApiUrl !== cfg.statusApiUrls[0]) {
    cfg.statusApiUrl = cfg.statusApiUrls[0];
    changed = true;
  }
  if (beforeIds !== cfg.profiles.map((p) => p.id).join(',')) changed = true;
  return changed;
}

/** Ancien format (gameDir unique + servers[]) → profil Prime Godot only. */
function migrateLegacyConfig(legacy) {
  const legacyServers = Array.isArray(legacy.servers) ? legacy.servers : [];
  const primeServer = legacyServers.find((s) => s.id === 'prime') || {
    id: 'prime',
    label: 'LBG MMO Serveur',
    ip: PRIME_HOST_LAN,
    loginPort: 44553,
  };

  return {
    launchpadVersion: LAUNCHPAD_VERSION,
    statusApiUrl: legacy.statusApiUrl || defaultConfig().statusApiUrl,
    statusApiUrls: legacy.statusApiUrls || defaultConfig().statusApiUrls,
    primeGatewayHealthUrl:
      legacy.primeGatewayHealthUrl || defaultConfig().primeGatewayHealthUrl,
    patchServerUrl: legacy.patchServerUrl || defaultConfig().patchServerUrl,
    patchServerUrlNas: legacy.patchServerUrlNas || '',
    diskSpaceWarningGb: legacy.diskSpaceWarningGb ?? 40,
    defaultProfileId: 'prime',
    profiles: [
      {
        id: 'prime',
        label: 'LBG Prime (Godot)',
        clientKind: 'godot',
        gameDir: DEFAULT_PRIME_CLIENT_DIR,
        gameExe: DEFAULT_GODOT_EXE,
        configFile: '',
        patchChannel: 'prime',
        skipPatch: true,
        godotPatchEnabled: true,
        godotFullscreen: false,
        launchArgs: ['--path', DEFAULT_PRIME_CLIENT_DIR],
        servers: [primeServer],
      },
    ],
  };
}

function isGodotProfile(profile) {
  if (!profile) return false;
  if (String(profile.clientKind || '').toLowerCase() === 'godot') return true;
  const exe = String(profile.gameExe || '').toLowerCase();
  return exe.includes('godot') || exe.endsWith('primeclient.exe') || exe.endsWith('prime-client.exe');
}

/** Initialise les chemins du profil Prime Godot s'ils sont vides, sans écraser les choix de l'utilisateur. */
function migratePrimeClientPath(cfg) {
  let changed = false;
  for (const profile of cfg.profiles || []) {
    if (profile.id !== 'prime') continue;
    if (!profile.gameDir || typeof profile.gameDir !== 'string' || !profile.gameDir.trim()) {
      profile.gameDir = resolvePrimeClientDir();
      changed = true;
    }
    if (!profile.gameExe || typeof profile.gameExe !== 'string' || !profile.gameExe.trim()) {
      profile.gameExe = resolveDefaultGodotExe();
      changed = true;
    }
    const expectedArgs = ['--path', profile.gameDir];
    const args = Array.isArray(profile.launchArgs) ? profile.launchArgs : [];
    const argsOk =
      args.length === expectedArgs.length &&
      args.every((a, i) => String(a) === expectedArgs[i]);
    if (!argsOk) {
      profile.launchArgs = expectedArgs.slice();
      changed = true;
    }
    if (profile.clientKind !== 'godot') {
      profile.clientKind = 'godot';
      changed = true;
    }
  }
  return changed;
}

function migratePrimeToGodot(cfg) {
  let changed = false;
  for (const profile of cfg.profiles || []) {
    if (profile.id !== 'prime') continue;
    const exe = String(profile.gameExe || '').toLowerCase();
    const stillRetail =
      exe.includes('lbgemu') ||
      String(profile.gameDir || '').toLowerCase().includes('prime-lbg');
    if (!stillRetail && isGodotProfile(profile)) continue;
    profile.label = 'LBG Prime (Godot)';
    profile.clientKind = 'godot';
    profile.gameDir = DEFAULT_PRIME_CLIENT_DIR;
    profile.gameExe = DEFAULT_GODOT_EXE;
    profile.configFile = '';
    profile.patchChannel = '';
    profile.skipPatch = true;
    if (profile.godotFullscreen == null) {
      profile.godotFullscreen = false;
    }
    changed = true;
  }
  return changed;
}

function ensureGodotPatchDefaults(cfg) {
  let changed = false;
  for (const profile of cfg.profiles || []) {
    if (profile.id !== 'prime' || !isGodotProfile(profile)) continue;
    if (!profile.patchChannel) {
      profile.patchChannel = 'prime';
      changed = true;
    }
    if (profile.godotPatchEnabled == null) {
      profile.godotPatchEnabled = true;
      changed = true;
    }
  }
  return changed;
}

function ensureGodotFullscreenDefault(cfg) {
  let changed = false;
  for (const profile of cfg.profiles || []) {
    if (profile.id !== 'prime' || !isGodotProfile(profile)) continue;
    if (profile.godotFullscreen != null) continue;
    const args = Array.isArray(profile.launchArgs) ? profile.launchArgs : [];
    // Défaut fenêtré (aligné éditeur) — l’utilisateur peut forcer fullscreen dans la config.
    profile.godotFullscreen = args.some((a) => String(a).trim() === '--fullscreen');
    changed = true;
  }
  return changed;
}

/** Si un vieux Launchpad / config pointe encore new_mmo → forcer J: à chaque load. */
function banLegacyNewMmoPrimePath(cfg) {
  const dir = resolvePrimeClientDir();
  let changed = false;
  for (const profile of cfg.profiles || []) {
    if (profile.id !== 'prime') continue;
    const gd = String(profile.gameDir || '');
    if (/new_mmo/i.test(gd) || /\\new_mmo\\/i.test(gd)) {
      console.warn('[Launchpad] gameDir legacy new_mmo détecté →', dir);
      profile.gameDir = dir;
      profile.launchArgs = ['--path', dir];
      profile.clientKind = 'godot';
      changed = true;
    }
  }
  return changed;
}

function migratePrecuHost246(cfg) {
  let changed = false;
  for (const profile of cfg.profiles || []) {
    for (const server of profile.servers || []) {
      if (server.id === 'precu' && server.ip === PRIME_HOST_LAN) {
        server.ip = PRECU_HOST_LAN;
        changed = true;
      }
    }
  }
  return changed;
}

/** statusApiUrl ne doit plus dépendre uniquement de PreCU (.245) — sinon UI « tous hors ligne ». */
function migrateStatusApiPrimeFirst(cfg) {
  let changed = false;
  const primeUrl = `http://${PRIME_HOST_LAN}:8792/api/servers`;
  const precuUrl = `http://${PRECU_HOST_LAN}:8792/api/servers`;
  const current = String(cfg.statusApiUrl || '').trim();
  if (!current || current.includes(`${PRECU_HOST_LAN}:8792`)) {
    if (current !== primeUrl) {
      cfg.statusApiUrl = primeUrl;
      changed = true;
    }
  }
  const desired = [primeUrl, precuUrl];
  const existing = Array.isArray(cfg.statusApiUrls) ? cfg.statusApiUrls.map(String) : [];
  const merged = [];
  for (const u of [...desired, ...existing]) {
    const s = String(u || '').trim();
    if (s && !merged.includes(s)) merged.push(s);
  }
  if (JSON.stringify(existing) !== JSON.stringify(merged)) {
    cfg.statusApiUrls = merged;
    changed = true;
  }
  return changed;
}

function resolveApiClientHost(row, serverId) {
  if (row.client_ip) {
    return row.client_ip;
  }
  if (row.host && row.host !== '127.0.0.1' && row.host !== 'localhost') {
    return row.host;
  }
  return serverId === 'precu' ? PRECU_HOST_LAN : PRIME_HOST_LAN;
}

function applyStatusApiHosts(rows) {
  if (!Array.isArray(rows) || rows.length === 0) return false;
  const idMap = { swgemu: 'precu', prime: 'prime' };
  let changed = false;
  for (const row of rows) {
    const serverId = idMap[row.id] || row.id;
    const host = resolveApiClientHost(row, serverId);
    for (const profile of config.profiles) {
      for (const server of profile.servers || []) {
        if (server.id === serverId && server.ip !== host) {
          server.ip = host;
          changed = true;
        }
      }
    }
  }
  if (changed) saveConfig(config);
  return changed;
}

function normalizeConfig(raw) {
  const base = defaultConfig();
  if (!raw || typeof raw !== 'object') {
    return base;
  }
  if (Array.isArray(raw.profiles) && raw.profiles.length > 0) {
    const normalized = {
      ...base,
      ...raw,
      profiles: raw.profiles.map((p) => ({
        ...p,
        servers: Array.isArray(p.servers) ? p.servers : [],
      })),
    };
    migratePrecuHost246(normalized);
    migrateStatusApiPrimeFirst(normalized);
    migratePrimeToGodot(normalized);
    migratePrimeClientPath(normalized);
    banLegacyNewMmoPrimePath(normalized);
    ensureGodotFullscreenDefault(normalized);
    ensureGodotPatchDefaults(normalized);
    return normalized;
  }
  if (raw.gameDir || (Array.isArray(raw.servers) && raw.servers.length > 0)) {
    return migrateLegacyConfig(raw);
  }
  return base;
}

function flattenServers(profiles) {
  const rows = [];
  for (const profile of profiles) {
    for (const server of profile.servers || []) {
      rows.push({
        ...server,
        profileId: profile.id,
        profileLabel: profile.label,
      });
    }
  }
  return rows;
}

function loadConfig() {
  const cfgPath = configPath();
  try {
    if (fs.existsSync(cfgPath)) {
      const raw = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));
      const normalized = normalizeConfig(raw);
      const strippedPrecu = stripPrecuProfiles(normalized);
      const migratedHost = migratePrecuHost246(normalized);
      const migratedStatusApi = migrateStatusApiPrimeFirst(normalized);
      const migratedGodot = migratePrimeToGodot(normalized);
      const migratedPath = migratePrimeClientPath(normalized);
      const bannedLegacy = banLegacyNewMmoPrimePath(normalized);
      const migratedFs = ensureGodotFullscreenDefault(normalized);
      const migratedPatch = ensureGodotPatchDefaults(normalized);
      if (
        !raw.profiles ||
        raw.launchpadVersion !== LAUNCHPAD_VERSION ||
        strippedPrecu ||
        migratedHost ||
        migratedStatusApi ||
        migratedGodot ||
        migratedPath ||
        bannedLegacy ||
        migratedFs ||
        migratedPatch
      ) {
        saveConfig(normalized);
      }
      return normalized;
    }
  } catch (err) {
    console.error('launchpad.config.json:', err.message);
  }
  const fresh = defaultConfig();
  try {
    saveConfig(fresh);
  } catch (e) {
    console.warn('save default config:', e.message);
  }
  return fresh;
}

function saveConfig(next) {
  const cfgPath = configPath();
  const out = { ...next, launchpadVersion: LAUNCHPAD_VERSION };
  fs.writeFileSync(cfgPath, `${JSON.stringify(out, null, 2)}\n`, 'utf8');
}

function getProfileById(profileId) {
  return config.profiles.find((p) => p.id === profileId) || config.profiles[0];
}

function getProfileForServer(serverId) {
  for (const profile of config.profiles) {
    if ((profile.servers || []).some((s) => s.id === serverId)) {
      return profile;
    }
  }
  return getProfileById(config.defaultProfileId);
}

function getServer(serverId) {
  for (const profile of config.profiles) {
    const hit = (profile.servers || []).find((s) => s.id === serverId);
    if (hit) return hit;
  }
  return flattenServers(config.profiles)[0];
}

function resolveGameExe(profile) {
  const raw = (profile.gameExe || '').trim();
  if (!raw) {
    return path.join(profile.gameDir, 'SWGEmu.exe');
  }
  if (path.isAbsolute(raw)) {
    return raw;
  }
  return path.join(profile.gameDir, raw);
}

function resolveLaunchArgs(profile) {
  if (isGodotProfile(profile)) {
    const args = ['--path', profile.gameDir];
    if (profile.godotFullscreen) {
      args.push('--fullscreen');
    }
    if (Array.isArray(profile.launchArgsExtra)) {
      for (const a of profile.launchArgsExtra) {
        const s = String(a).trim();
        if (s) args.push(s);
      }
    }
    return args;
  }
  if (Array.isArray(profile.launchArgs) && profile.launchArgs.length > 0) {
    return profile.launchArgs.map(String);
  }
  const cfgName = profile.configFile || 'swgemu.cfg';
  return ['-s', cfgName];
}

function profilePathPayload(profile) {
  const gameExe = resolveGameExe(profile);
  const godot = isGodotProfile(profile);
  return {
    profileId: profile.id,
    profileLabel: profile.label,
    clientKind: godot ? 'godot' : 'swgemu',
    gameDir: profile.gameDir,
    gameExe,
    gameExeRelative: profile.gameExe || path.basename(gameExe),
    gameExeConfigured: Boolean((profile.gameExe || '').trim()),
    configFile: godot ? '' : profile.configFile || 'swgemu.cfg',
    patchChannel: profile.patchChannel || (godot ? 'prime' : profile.id),
    skipPatch: Boolean(profile.skipPatch),
    godotPatchEnabled: profile.godotPatchEnabled !== false,
    godotFullscreen: Boolean(profile.godotFullscreen),
    launchArgs: resolveLaunchArgs(profile),
  };
}

function getFreeBytesForPath(targetPath) {
  const resolved = path.resolve(targetPath);
  if (process.platform === 'win32') {
    try {
      const drive = path.parse(resolved).root.replace(/\\$/, '');
      if (!drive) return null;
      const out = execSync(
        `wmic logicaldisk where "DeviceID='${drive}'" get FreeSpace /value`,
        { encoding: 'utf8', timeout: 8000 },
      );
      const m = out.match(/FreeSpace=(\d+)/);
      return m ? parseInt(m[1], 10) : null;
    } catch (err) {
      console.warn('disk space wmic:', err.message);
      return null;
    }
  }
  try {
    const { statfsSync } = fs;
    if (typeof statfsSync === 'function') {
      const st = statfsSync(resolved);
      return st.bsize * st.bavail;
    }
  } catch (_) {
    /* ignore */
  }
  return null;
}

function diskSpaceStatus() {
  const requiredGb = Number(config.diskSpaceWarningGb) || 40;
  // Godot seul : ~1 Go suffit ; PreCu retail : gros install
  const dirs = config.profiles
    .filter((p) => !isGodotProfile(p))
    .map((p) => p.gameDir)
    .filter(Boolean);
  const checkDirs =
    dirs.length > 0
      ? dirs
      : config.profiles.map((p) => p.gameDir).filter(Boolean);
  const effectiveRequired =
    dirs.length === 0 ? Math.min(requiredGb, 5) : requiredGb;
  let minFree = null;
  for (const dir of checkDirs) {
    const free = getFreeBytesForPath(dir);
    if (free != null && (minFree == null || free < minFree)) {
      minFree = free;
    }
  }
  const freeGb = minFree != null ? minFree / (1024 ** 3) : null;
  return {
    requiredGb: effectiveRequired,
    freeGb: freeGb != null ? Math.round(freeGb * 10) / 10 : null,
    ok: freeGb == null ? true : freeGb >= effectiveRequired,
    message:
      freeGb == null
        ? `Prévoir environ ${effectiveRequired} Go libres.`
        : freeGb >= effectiveRequired
          ? `Espace disque OK (${freeGb} Go libres, ${effectiveRequired} Go recommandés).`
          : `Attention : ${freeGb} Go libres — environ ${effectiveRequired} Go recommandés.`,
  };
}

let config = loadConfig();
let mainWindow;
let selectedServerId =
  flattenServers(config.profiles).find((s) => s.id === config.defaultProfileId)?.id
  || flattenServers(config.profiles)[0]?.id
  || 'prime';
/** IP login par galaxie (API :8792 + repli LAN). */
let lastApiHosts = {
  precu: PRECU_HOST_LAN,
  prime: PRIME_HOST_LAN,
};
let lastGoodServerStatus = null;
let statusApiFailStreak = 0;

function getActiveProfile() {
  return getProfileForServer(selectedServerId);
}

function patchManifestUrls(patchChannel) {
  const base = (config.patchServerUrl || '').replace(/\/$/, '');
  const channel = patchChannel || 'precu';
  return [
    `${base}/patches/${channel}/manifest.json`,
    `${base}/manifest.json`,
  ];
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 900,
    height: 720,
    frame: false,
    transparent: false,
    backgroundColor: '#0a0e17',
    show: false,
    center: true,
    resizable: false,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    mainWindow.focus();
  });

  const indexPath = path.join(appDir(), 'index.html');
  mainWindow.loadFile(indexPath).catch((err) => {
    console.error('loadFile failed:', indexPath, err);
    const logPath = path.join(appRoot(), 'launchpad-error.log');
    fs.writeFileSync(
      logPath,
      `index.html introuvable: ${indexPath}\n${err.stack || err}\n`,
      'utf8',
    );
  });

  mainWindow.webContents.once('did-finish-load', () => {
    sendConfigToRenderer();
    setTimeout(checkServerStatus, 500);
  });

  mainWindow.webContents.on('did-fail-load', (_ev, code, desc, url) => {
    console.error('did-fail-load', code, desc, url);
  });
}

function sendConfigToRenderer() {
  if (!mainWindow) return;
  const profile = getActiveProfile();
  const flat = flattenServers(config.profiles);
  mainWindow.webContents.send('config', {
    launchpadVersion: config.launchpadVersion,
    servers: flat,
    defaultServerId: selectedServerId,
    defaultProfileId: config.defaultProfileId,
    profiles: config.profiles.map((p) => profilePathPayload(p)),
    diskSpace: diskSpaceStatus(),
    ...profilePathPayload(profile),
  });
}

function httpGetJson(url, timeoutMs = 4000) {
  return new Promise((resolve, reject) => {
    const lib = url.startsWith('https') ? https : http;
    const req = lib.get(url, (res) => {
      if (res.statusCode !== 200) {
        res.resume();
        return reject(new Error(`HTTP ${res.statusCode}`));
      }
      let raw = '';
      res.on('data', (c) => {
        raw += c;
      });
      res.on('end', () => {
        try {
          resolve(JSON.parse(raw));
        } catch (e) {
          reject(e);
        }
      });
    });
    req.on('error', reject);
    req.setTimeout(timeoutMs, () => {
      req.destroy();
      reject(new Error('timeout'));
    });
  });
}

async function fetchPatchManifest(patchChannel) {
  const urls = patchManifestUrls(patchChannel);
  let lastErr;
  for (const url of urls) {
    try {
      return await httpGetJson(url, 5000);
    } catch (err) {
      lastErr = err;
    }
  }
  throw lastErr || new Error('manifest introuvable');
}

function mapStatusApiRows(rows) {
  applyStatusApiHosts(rows);
  for (const r of Array.isArray(rows) ? rows : []) {
    const id = r.id === 'swgemu' ? 'precu' : r.id === 'prime' ? 'prime' : r.id;
    lastApiHosts[id] = resolveApiClientHost(r, id);
  }
  return (Array.isArray(rows) ? rows : []).map((r) => {
    const id = r.id === 'swgemu' ? 'precu' : r.id === 'prime' ? 'prime' : r.id;
    const server = getServer(id);
    const host = lastApiHosts[id] || server?.ip || PRIME_HOST_LAN;
    return {
      id,
      label: r.label,
      host,
      online: Boolean(r.online),
      ready: Boolean(r.ready),
      status: r.status || (r.online ? 'ready' : 'offline'),
      pid: r.pid,
    };
  });
}

async function fetchPrimeGatewayHealth() {
  // G5 : autorité joueur = prime-hub Godot (:8787), plus le gateway Core3 :8765
  const url =
    (config && config.primeGatewayHealthUrl) ||
    `http://${PRIME_HOST_LAN}:8787/healthz`;
  try {
    const data = await httpGetJson(url, 3500);
    const ok = Boolean(data && data.ok);
    return {
      online: ok,
      ready: ok,
      status: ok ? 'ready' : 'offline',
      source: 'prime_hub',
      url,
    };
  } catch (err) {
    return {
      online: false,
      ready: false,
      status: 'offline',
      source: 'prime_hub',
      url,
      error: err.message,
    };
  }
}

function mergePrimeGatewayRow(rows, gw) {
  const list = Array.isArray(rows) ? [...rows] : [];
  const server = getServer('prime') || {
    id: 'prime',
    label: 'LBG MMO Serveur Prime',
    ip: PRIME_HOST_LAN,
  };
  const row = {
    id: 'prime',
    label: server.label || 'LBG MMO Serveur Prime',
    host: PRIME_HOST_LAN,
    online: Boolean(gw.online),
    ready: Boolean(gw.ready),
    status: gw.status || (gw.online ? 'ready' : 'offline'),
    healthSource: gw.source || 'gateway',
  };
  const idx = list.findIndex((r) => r.id === 'prime');
  if (idx >= 0) {
    list[idx] = { ...list[idx], ...row };
  } else {
    list.push(row);
  }
  return list;
}

function statusApiUrlList() {
  const urls = [];
  const fromArr = Array.isArray(config.statusApiUrls) ? config.statusApiUrls : [];
  for (const u of fromArr) {
    const s = String(u || '').trim();
    if (s && !urls.includes(s)) urls.push(s);
  }
  const primary = String(config.statusApiUrl || '').trim();
  if (primary && !urls.includes(primary)) urls.unshift(primary);
  if (!urls.length) {
    urls.push(`http://${PRIME_HOST_LAN}:8792/api/servers`);
  }
  return urls;
}

function filterKnownServerRows(rows) {
  const known = new Set(flattenServers(config.profiles).map((s) => s.id));
  return (rows || []).filter((r) => r && known.has(r.id));
}

function mergeStatusApiRowLists(lists) {
  const byId = new Map();
  for (const rows of lists) {
    for (const row of rows || []) {
      if (!row || !row.id) continue;
      const prev = byId.get(row.id);
      if (!prev) {
        byId.set(row.id, row);
        continue;
      }
      // Préférer une ligne ready/online à une offline du même id.
      const score = (r) => (r.ready ? 2 : 0) + (r.online ? 1 : 0);
      if (score(row) >= score(prev)) byId.set(row.id, { ...prev, ...row });
    }
  }
  return Array.from(byId.values());
}

async function fetchStatusApiRowsMerged() {
  const urls = statusApiUrlList();
  const mappedLists = [];
  const errors = [];
  await Promise.all(
    urls.map(async (url) => {
      try {
        const rows = await httpGetJson(url, STATUS_API_TIMEOUT_MS);
        mappedLists.push(mapStatusApiRows(rows));
      } catch (err) {
        errors.push(`${url}: ${err.message}`);
      }
    }),
  );
  if (!mappedLists.length) {
    const err = new Error(errors.join(' | ') || 'status API KO');
    throw err;
  }
  return {
    mapped: mergeStatusApiRowLists(mappedLists),
    partial: errors.length > 0,
    errors,
  };
}

async function checkServerStatus() {
  if (!mainWindow) return;
  let mapped = null;
  let apiError = null;
  try {
    const out = await fetchStatusApiRowsMerged();
    mapped = out.mapped;
    statusApiFailStreak = 0;
    if (out.partial) {
      apiError = out.errors.join(' | ');
      console.warn('status API partial:', apiError);
    }
  } catch (err) {
    console.warn('status API:', err.message);
    apiError = err.message;
    statusApiFailStreak += 1;
    if (lastGoodServerStatus && statusApiFailStreak < STATUS_API_FAIL_THRESHOLD) {
      mapped = lastGoodServerStatus;
    }
  }
  const gw = await fetchPrimeGatewayHealth();
  if (mapped) {
    mapped = filterKnownServerRows(mergePrimeGatewayRow(mapped, gw));
    lastGoodServerStatus = mapped;
    mainWindow.webContents.send('servers-status', {
      source: apiError ? 'api+gateway' : 'api',
      servers: mapped,
      stale: Boolean(apiError),
      primeGateway: gw,
    });
    return;
  }
  const fallbackServers = filterKnownServerRows(
    mergePrimeGatewayRow(
      lastGoodServerStatus
        ? lastGoodServerStatus
        : flattenServers(config.profiles).map((s) => ({
            ...s,
            host: s.ip,
            online: false,
            ready: false,
            status: 'offline',
          })),
      gw,
    ),
  );
  lastGoodServerStatus = fallbackServers;
  mainWindow.webContents.send('servers-status', {
    source: 'gateway-fallback',
    servers: fallbackServers,
    error: !lastGoodServerStatus,
    stale: Boolean(lastGoodServerStatus),
    primeGateway: gw,
  });
}

setInterval(checkServerStatus, 10000);

function resolveServerLoginEndpoint(server) {
  if (!server) {
    return { ip: PRIME_HOST_LAN, loginPort: 44553 };
  }
  let ip = lastApiHosts[server.id] || server.ip;
  if (server.id === 'precu' && ip === PRIME_HOST_LAN) {
    ip = PRECU_HOST_LAN;
  }
  if (server.id === 'prime' && (!ip || ip === PRECU_HOST_LAN)) {
    ip = PRIME_HOST_LAN;
  }
  const loginPort =
    server.loginPort || (server.id === 'precu' ? 44453 : 44553);
  return { ip, loginPort };
}

function patchLoginConfig(profile, server) {
  const loginCfgPath = path.join(profile.gameDir, 'swgemu_login.cfg');
  if (!fs.existsSync(loginCfgPath)) return;
  const { ip, loginPort } = resolveServerLoginEndpoint(server);
  let text = fs.readFileSync(loginCfgPath, 'utf8');
  text = text.replace(/loginServerAddress\d*=.*/g, `loginServerAddress0=${ip}`);
  text = text.replace(/loginServerPort\d*=.*/g, `loginServerPort0=${loginPort}`);
  fs.writeFileSync(loginCfgPath, text, 'utf8');
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

ipcMain.on('window-control', (event, action) => {
  if (action === 'minimize') mainWindow.minimize();
  if (action === 'close') app.quit();
});

ipcMain.on('select-server', (event, serverId) => {
  const flat = flattenServers(config.profiles);
  if (flat.some((s) => s.id === serverId)) {
    selectedServerId = serverId;
    const profile = getActiveProfile();
    event.reply('active-profile', profilePathPayload(profile));
  }
});

function normalizeGameExeForSave(gameDir, gameExe) {
  const trimmed = (gameExe || '').trim();
  if (!trimmed) return '';
  const absExe = path.isAbsolute(trimmed) ? trimmed : path.join(gameDir, trimmed);
  const rel = path.relative(gameDir, absExe);
  if (rel && !rel.startsWith('..') && !path.isAbsolute(rel)) {
    return rel;
  }
  return absExe;
}

ipcMain.on('save-path-settings', (event, payload) => {
  if (!payload || typeof payload !== 'object') return;
  const profile = getActiveProfile();
  if (!profile) {
    event.reply('path-settings-saved', { ok: false, message: 'Profil introuvable' });
    return;
  }
  if (typeof payload.gameDir === 'string' && payload.gameDir.trim()) {
    profile.gameDir = payload.gameDir.trim();
  }
  if (typeof payload.gameExe === 'string') {
    profile.gameExe = normalizeGameExeForSave(profile.gameDir, payload.gameExe);
  }
  if (isGodotProfile(profile)) {
    profile.clientKind = 'godot';
    profile.skipPatch = true;
    profile.configFile = '';
    profile.launchArgs = ['--path', profile.gameDir];
    if (payload.godotFullscreen != null) {
      profile.godotFullscreen = Boolean(payload.godotFullscreen);
    }
  }
  try {
    saveConfig(config);
    const updated = profilePathPayload(profile);
    event.reply('path-settings-saved', { ok: true, ...updated });
  } catch (err) {
    event.reply('path-settings-saved', { ok: false, message: err.message });
  }
});

ipcMain.on('browse-game-dir', async (event) => {
  const profile = getActiveProfile();
  const result = await dialog.showOpenDialog(mainWindow, {
    title: `Dossier client — ${profile.label}`,
    properties: ['openDirectory'],
    defaultPath: profile.gameDir,
  });
  if (result.canceled || !result.filePaths?.[0]) {
    event.reply('browse-result', { canceled: true });
    return;
  }
  event.reply('browse-result', { canceled: false, gameDir: result.filePaths[0] });
});

ipcMain.on('browse-game-exe', async (event) => {
  const profile = getActiveProfile();
  const godot = isGodotProfile(profile);
  const result = await dialog.showOpenDialog(mainWindow, {
    title: godot
      ? `Godot / Prime Client — ${profile.label}`
      : `Exécutable — ${profile.label}`,
    properties: ['openFile'],
    defaultPath: profile.gameDir,
    filters: godot
      ? [
          { name: 'Godot / Client', extensions: ['exe'] },
          { name: 'Tous', extensions: ['*'] },
        ]
      : [{ name: 'Client SWG', extensions: ['exe'] }],
  });
  if (result.canceled || !result.filePaths?.[0]) {
    event.reply('browse-result', { canceled: true });
    return;
  }
  const picked = result.filePaths[0];
  event.reply('browse-result', {
    canceled: false,
    gameExe: picked,
    gameDir: godot ? profile.gameDir : path.dirname(picked),
  });
});

ipcMain.on('launch-game', (event, keepOpen) => {
  const server = getServer(selectedServerId);
  const profile = getActiveProfile();
  const gamePath = resolveGameExe(profile);
  const godot = isGodotProfile(profile);
  const cfgName = profile.configFile || 'swgemu.cfg';
  const cfgPath = path.join(profile.gameDir, cfgName);
  const disk = diskSpaceStatus();

  if (!disk.ok) {
    event.reply('launch-status', {
      error: true,
      message: disk.message,
    });
    return;
  }

  if (process.platform !== 'win32') {
    event.reply('launch-status', {
      error: true,
      message: 'Environnement non-Windows : lancement simulé uniquement.',
    });
    if (!keepOpen) setTimeout(() => app.quit(), 2000);
    return;
  }

  if (!fs.existsSync(gamePath)) {
    event.reply('launch-status', {
      error: true,
      message: godot
        ? `Godot introuvable : ${gamePath}\nInstallez Godot 4.6 ou réglez le chemin (Emplacement du client).`
        : `${path.basename(gamePath)} introuvable : ${gamePath}`,
    });
    return;
  }
  if (godot) {
    const projectFile = path.join(profile.gameDir, 'project.godot');
    if (!fs.existsSync(projectFile)) {
      event.reply('launch-status', {
        error: true,
        message: `Projet Godot introuvable : ${projectFile}\nCopiez prime-client vers ce dossier ou changez « Dossier jeu ».`,
      });
      return;
    }
    if (/new_mmo/i.test(String(profile.gameDir || ''))) {
      event.reply('launch-status', {
        error: true,
        message:
          `Dossier legacy new_mmo interdit : ${profile.gameDir}\n` +
          `Utilise J:\\swgemu\\clients\\prime-client — mets à jour via « Vérifier Mises à Jour ».`,
      });
      return;
    }
    const classCache = path.join(profile.gameDir, '.godot', 'global_script_class_cache.cfg');
    if (!fs.existsSync(classCache)) {
      event.reply('launch-status', {
        error: true,
        message:
          `Cache Godot manquant (.godot) dans ${profile.gameDir}\n` +
          `Clique « Vérifier Mises à Jour » (import Godot auto), puis relance.`,
      });
      return;
    }
    try {
      const cacheTxt = fs.readFileSync(classCache, 'utf8');
      if (profile.id === 'prime' && (!cacheTxt.includes('EntityManager') || !cacheTxt.includes('LbgWsClient'))) {
        event.reply('launch-status', {
          error: true,
          message:
            `Cache Godot incomplet dans ${profile.gameDir}\n` +
            `Clique « Vérifier Mises à Jour », puis relance.`,
        });
        return;
      }
    } catch (_) {
      /* ignore read errors — Godot tentera quand même */
    }
  } else if (!fs.existsSync(cfgPath)) {
    event.reply('launch-status', {
      error: true,
      message: `Fichier config introuvable : ${cfgPath}`,
    });
    return;
  }

  try {
    if (!godot) {
      patchLoginConfig(profile, server);
    }
    const args = resolveLaunchArgs(profile);
    const cwd = godot ? profile.gameDir : profile.gameDir;
    try {
      fs.writeFileSync(
        path.join(appRoot(), 'last-launch.log'),
        `${new Date().toISOString()}\nexe=${gamePath}\ncwd=${cwd}\nargs=${args.join(' ')}\n`,
        'utf8',
      );
    } catch (_) {
      /* ignore */
    }
    const gameProcess = spawn(gamePath, args, {
      cwd,
      detached: false,
      stdio: 'ignore',
    });
    gameProcess.on('error', (spawnErr) => {
      event.reply('launch-status', {
        error: true,
        message: `Impossible de lancer ${path.basename(gamePath)} : ${spawnErr.message}`,
      });
    });
    gameProcess.on('exit', (code, signal) => {
      if (code !== null && code !== 0) {
        event.reply('launch-status', {
          error: true,
          message: godot
            ? `Godot arrêté immédiatement (code ${code}). Vérifiez Godot 4.6 + project.godot.`
            : `Client arrêté immédiatement (code ${code}). Voir docs/troubleshoot_lbgemu_launch.md — script recover_prime_client.ps1`,
        });
      }
    });
    setTimeout(() => {
      if (gameProcess.exitCode === null && gameProcess.signalCode === null) {
        gameProcess.unref();
        const target = godot
          ? `Godot prime-client → hub ${PRIME_HOST_LAN}:8787 (HTTP+WS)`
          : `${profile.label} → ${server.label} (${server.ip}:${server.loginPort})`;
        event.reply('launch-status', {
          error: false,
          message: target,
        });
        if (!keepOpen) app.quit();
      }
    }, 2500);
  } catch (error) {
    event.reply('launch-status', { error: true, message: error.message });
  }
});

ipcMain.on('manual-update-check', () => {
  checkUpdates();
});

ipcMain.on('apply-launchpad-update', () => {
  applyLaunchpadUpdateAndRestart();
});

function compareVersions(v1, v2) {
  const parts1 = String(v1 || '')
    .replace(/^v/i, '')
    .split('.')
    .map((n) => parseInt(n, 10) || 0);
  const parts2 = String(v2 || '')
    .replace(/^v/i, '')
    .split('.')
    .map((n) => parseInt(n, 10) || 0);
  const len = Math.max(parts1.length, parts2.length);
  for (let i = 0; i < len; i++) {
    const p1 = parts1[i] || 0;
    const p2 = parts2[i] || 0;
    if (p1 > p2) return 1;
    if (p1 < p2) return -1;
  }
  return 0;
}

function getAppAsarPaths() {
  if (!app.isPackaged) return null;
  const execDir = path.dirname(process.execPath);
  const resourcesDir = path.join(execDir, 'resources');
  const asarPath = path.join(resourcesDir, 'app.asar');
  const updatePath = path.join(resourcesDir, 'app.asar.update');
  return { resourcesDir, asarPath, updatePath };
}

async function checkAndUpdateLaunchpad() {
  const patchBase = (config.patchServerUrl || '').replace(/\/$/, '');
  if (!patchBase) return null;
  let remoteVer = null;
  let asarUrl = `${patchBase}/releases/launchpad/app.asar`;

  try {
    try {
      const vInfo = await httpGetJson(`${patchBase}/releases/launchpad/version.json`, 4000);
      remoteVer = vInfo?.version || vInfo?.launchpad_version;
      if (vInfo?.asar_path) asarUrl = `${patchBase}${vInfo.asar_path}`;
    } catch (_) {
      const inst = await httpGetJson(`${patchBase}/releases/installer-manifest.json`, 4000);
      remoteVer = inst?.launchpad_version;
      if (inst?.urls?.launchpad_asar) asarUrl = `${patchBase}${inst.urls.launchpad_asar}`;
    }
  } catch (err) {
    return null;
  }

  if (!remoteVer) return null;

  if (compareVersions(remoteVer, LAUNCHPAD_VERSION) <= 0) {
    return { updated: false, version: LAUNCHPAD_VERSION, remoteVer };
  }

  if (!app.isPackaged) {
    return { updated: false, devMode: true, remoteVer };
  }

  const paths = getAppAsarPaths();
  if (!paths) return null;

  mainWindow?.webContents.send('patch-status', {
    status: 'patching',
    message: `Launchpad : téléchargement mise à jour v${remoteVer}…`,
  });

  try {
    await downloadFile(asarUrl, paths.updatePath, (percent) => {
      mainWindow?.webContents.send('patch-progress', {
        percent,
        file: `Launchpad v${remoteVer}`,
      });
    });

    if (fs.existsSync(paths.updatePath) && fs.statSync(paths.updatePath).size > 10000) {
      return { updated: true, version: remoteVer };
    }
  } catch (err) {
    console.warn('[Launchpad] Erreur téléchargement app.asar:', err.message);
  }
  return null;
}

function applyLaunchpadUpdateAndRestart() {
  const paths = getAppAsarPaths();
  if (!paths || !fs.existsSync(paths.updatePath)) {
    return false;
  }
  if (process.platform === 'win32') {
    const batPath = path.join(app.getPath('temp'), 'lbg_update_launchpad.bat');
    const execPath = process.execPath;
    const batContent = [
      '@echo off',
      'chcp 65001 >nul',
      'timeout /t 1 /nobreak >nul',
      ':retry',
      `move /y "${paths.updatePath}" "${paths.asarPath}" >nul 2>&1`,
      'if errorlevel 1 (',
      '  timeout /t 1 /nobreak >nul',
      '  goto retry',
      ')',
      `start "" "${execPath}"`,
      'exit',
    ].join('\r\n');

    fs.writeFileSync(batPath, batContent, 'utf8');

    const child = spawn('cmd.exe', ['/c', batPath], {
      detached: true,
      stdio: 'ignore',
      windowsHide: true,
    });
    child.unref();
    app.quit();
    return true;
  }

  try {
    fs.copyFileSync(paths.updatePath, paths.asarPath);
    fs.unlinkSync(paths.updatePath);
    app.relaunch();
    app.quit();
    return true;
  } catch (err) {
    console.error('applyLaunchpadUpdate error:', err);
    return false;
  }
}

function getFileHash(filePath) {
  return new Promise((resolve) => {
    const hash = crypto.createHash('md5');
    const stream = fs.createReadStream(filePath);
    stream.on('error', () => resolve(null));
    stream.on('data', (chunk) => hash.update(chunk));
    stream.on('end', () => resolve(hash.digest('hex')));
  });
}

function downloadFile(url, dest, onProgress) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(dest);
    const lib = url.startsWith('https') ? https : http;
    lib
      .get(url, (response) => {
        if (response.statusCode !== 200) {
          return reject(new Error(`Status: ${response.statusCode}`));
        }
        const len = parseInt(response.headers['content-length'], 10);
        let downloaded = 0;
        response.on('data', (chunk) => {
          downloaded += chunk.length;
          if (len) onProgress(Math.round((100.0 * downloaded) / len));
        });
        response.pipe(file);
        file.on('finish', () => {
          file.close();
          resolve();
        });
      })
      .on('error', (err) => {
        fs.unlink(dest, () => {});
        reject(err);
      });
  });
}

function resolveGodotConsoleExe(profile) {
  const exe = resolveGameExe(profile);
  const consoleExe = String(exe).replace(
    /Godot_v4\.6\.1-stable_win64\.exe$/i,
    'Godot_v4.6.1-stable_win64_console.exe'
  );
  if (consoleExe !== exe && fs.existsSync(consoleExe)) return consoleExe;
  return exe;
}

/** Régénère le cache .godot après un patch (même rôle que sync_prime_client_to_j.sh). */
function runGodotImport(profile) {
  return new Promise((resolve) => {
    const exe = resolveGodotConsoleExe(profile);
    if (!exe || !fs.existsSync(exe)) {
      resolve(false);
      return;
    }
    const child = spawn(
      exe,
      ['--headless', '--path', profile.gameDir, '--import', '--quit-after', '40'],
      { cwd: profile.gameDir, stdio: 'ignore', windowsHide: true }
    );
    const timer = setTimeout(() => {
      try {
        child.kill();
      } catch (_) {
        /* ignore */
      }
      resolve(false);
    }, 90000);
    child.on('error', () => {
      clearTimeout(timer);
      resolve(false);
    });
    child.on('exit', (code) => {
      clearTimeout(timer);
      const cache = path.join(profile.gameDir, '.godot', 'global_script_class_cache.cfg');
      resolve(code === 0 || fs.existsSync(cache));
    });
  });
}

function readLocalBuildInfo(gameDir) {
  const p = path.join(gameDir, 'assets', 'build_info.json');
  if (!fs.existsSync(p)) return null;
  try {
    return JSON.parse(fs.readFileSync(p, 'utf8'));
  } catch (err) {
    console.warn('build_info local:', err.message);
    return null;
  }
}

async function fetchRemoteBuildInfo(channel) {
  const base = (config.patchServerUrl || '').replace(/\/$/, '');
  const urls = [
    `${base}/patches/${channel}/build_info.json`,
    `${base}/patches/${channel}/assets/build_info.json`,
  ];
  let lastErr;
  for (const url of urls) {
    try {
      return await httpGetJson(url, 8000);
    } catch (err) {
      lastErr = err;
    }
  }
  throw lastErr || new Error('build_info distant introuvable');
}

async function checkGodotClientUpdates(profile) {
  const channel = profile.patchChannel || 'prime';
  if (profile.godotPatchEnabled === false) {
    mainWindow.webContents.send('patch-status', {
      status: 'ready',
      message: 'Mises à jour Prime désactivées (godotPatchEnabled=false).',
    });
    return;
  }

  mainWindow.webContents.send('patch-status', {
    status: 'checking',
    message: `Vérification des mises à jour (Prime & Launchpad)…`,
  });

  let lpUpdateResult = null;
  try {
    lpUpdateResult = await checkAndUpdateLaunchpad();
  } catch (err) {
    console.warn('[Launchpad] checkAndUpdateLaunchpad:', err.message);
  }
  if (lpUpdateResult?.updated) {
    mainWindow.webContents.send('launchpad-update-ready', { version: lpUpdateResult.version });
  }

  const lpNotice = lpUpdateResult?.updated
    ? `\n★ Mise à jour Launchpad v${lpUpdateResult.version} prête — clique sur « Redémarrer Launchpad ».`
    : '';

  const targetDir = profile.gameDir;
  const localBuild = readLocalBuildInfo(targetDir);
  const localStamp = localBuild?.synced_at || '(aucun build_info.json local)';

  let remoteBuild = null;
  let manifest = null;
  let remoteErr = '';

  try {
    remoteBuild = await fetchRemoteBuildInfo(channel);
  } catch (err) {
    remoteErr = err.message;
  }

  try {
    manifest = await fetchPatchManifest(channel);
  } catch (err) {
    mainWindow.webContents.send('patch-status', {
      status: 'error',
      message:
        `Manifeste Prime indisponible (${err.message}).\n` +
        `Local : ${localStamp}\n` +
        `Publiez : python3 tools/generate_prime_patch_manifest.py puis déployez sur ${config.patchServerUrl}/patches/${channel}/` +
        lpNotice,
    });
    return;
  }

  const remoteStamp =
    remoteBuild?.synced_at || manifest.version || manifest.synced_at || '(manifeste sans date)';
  const sameStamp = localStamp !== '(aucun build_info.json local)' && localStamp === remoteStamp;
  const remoteIsOlder =
    localStamp !== '(aucun build_info.json local)' &&
    remoteStamp !== '(manifeste sans date)' &&
    localStamp > remoteStamp;

  const filesToUpdate = [];
  for (const file of manifest.files || []) {
    const filePath = path.join(targetDir, file.name);
    const localHash = await getFileHash(filePath);
    if (localHash !== file.hash) filesToUpdate.push(file);
  }

  const patchBase = (config.patchServerUrl || '').replace(/\/$/, '');

  if (filesToUpdate.length === 0) {
    mainWindow.webContents.send('patch-status', {
      status: 'ready',
      message:
        `Prime à jour (${filesToUpdate.length} diff). Local ${formatStampLocal(localStamp)} · référence ${formatStampLocal(remoteStamp)}` +
        (sameStamp ? ' ✓' : ' (fichiers OK, tampon différent)') +
        lpNotice,
    });
    return;
  }

  if (remoteIsOlder) {
    mainWindow.webContents.send('patch-status', {
      status: 'ready',
      message:
        `Patch ignoré — référence ${remoteStamp} plus ancienne que le client local ${localStamp}. ` +
        `${filesToUpdate.length} fichier(s) diffèrent. Publiez un manifeste à jour sur le serveur patch ` +
        `(generate_prime_patch_manifest.py + deploy_prime_client_patch_246.sh) ou resynchronisez depuis WSL.` +
        lpNotice,
    });
    return;
  }

  mainWindow.webContents.send('patch-status', {
    status: 'patching',
    message: `Prime — ${filesToUpdate.length} fichier(s) à mettre à jour (local ${localStamp} → ref ${remoteStamp})…`,
  });

  try {
    for (const file of filesToUpdate) {
      const filePath = path.join(targetDir, file.name);
      const dir = path.dirname(filePath);
      if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
      const urls = [
        `${patchBase}/patches/${channel}/${file.name}`,
        `${patchBase}/${file.name}`,
      ];
      let ok = false;
      let lastDlErr;
      for (const url of urls) {
        try {
          await downloadFile(url, filePath, (percent) => {
            mainWindow.webContents.send('patch-progress', {
              percent,
              file: file.name,
            });
          });
          ok = true;
          break;
        } catch (err) {
          lastDlErr = err;
        }
      }
      if (!ok) throw lastDlErr || new Error(`Échec ${file.name}`);
    }

    if (remoteBuild) {
      const biPath = path.join(targetDir, 'assets', 'build_info.json');
      const biDir = path.dirname(biPath);
      if (!fs.existsSync(biDir)) fs.mkdirSync(biDir, { recursive: true });
      fs.writeFileSync(biPath, `${JSON.stringify(remoteBuild, null, 2)}\n`, 'utf8');
    }

    mainWindow.webContents.send('patch-status', {
      status: 'patching',
      message: `Prime — import Godot (.godot) après ${filesToUpdate.length} fichier(s)…`,
    });
    const imported = await runGodotImport(profile);
    mainWindow.webContents.send('patch-status', {
      status: 'ready',
      message:
        (imported
          ? `Prime mis à jour — ${filesToUpdate.length} fichier(s). Référence ${remoteStamp}. Relance Godot.`
          : `Prime fichiers OK (${filesToUpdate.length}) mais import Godot incomplet — ouvre une fois l’éditeur puis relance.`) +
        lpNotice,
    });
  } catch (error) {
    mainWindow.webContents.send('patch-status', {
      status: 'error',
      message:
        `Échec patch Prime : ${error.message}\nLocal ${localStamp} · ref ${remoteStamp}${remoteErr ? `\n(${remoteErr})` : ''}` +
        lpNotice,
    });
  }
}

async function checkUpdates() {
  const profile = getActiveProfile();
  const channel = profile.patchChannel || profile.id;

  if (isGodotProfile(profile)) {
    await checkGodotClientUpdates(profile);
    return;
  }

  if (profile.skipPatch) {
    mainWindow.webContents.send('patch-status', {
      status: 'ready',
      message: 'Patches désactivés pour ce profil.',
    });
    return;
  }

  mainWindow.webContents.send('patch-status', {
    status: 'checking',
    message: `Vérification des mises à jour (${profile.label})…`,
  });

  try {
    const manifest = await fetchPatchManifest(channel);
    const filesToUpdate = [];
    let targetDir = profile.gameDir;
    if (process.platform !== 'win32') {
      targetDir = path.join(appRoot(), 'test_game_dir', channel);
      if (!fs.existsSync(targetDir)) fs.mkdirSync(targetDir, { recursive: true });
    }

    for (const file of manifest.files || []) {
      const filePath = path.join(targetDir, file.name);
      const localHash = await getFileHash(filePath);
      if (localHash !== file.hash) filesToUpdate.push(file);
    }

    const patchBase = (config.patchServerUrl || '').replace(/\/$/, '');

    if (filesToUpdate.length > 0) {
      mainWindow.webContents.send('patch-status', {
        status: 'patching',
        message: `[${channel}] Téléchargement de ${filesToUpdate.length} fichier(s)…`,
      });
      for (const file of filesToUpdate) {
        const filePath = path.join(targetDir, file.name);
        const dir = path.dirname(filePath);
        if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
        const urls = [
          `${patchBase}/patches/${channel}/${file.name}`,
          `${patchBase}/${file.name}`,
        ];
        let ok = false;
        let lastErr;
        for (const url of urls) {
          try {
            await downloadFile(url, filePath, (percent) => {
              mainWindow.webContents.send('patch-progress', {
                percent,
                file: file.name,
              });
            });
            ok = true;
            break;
          } catch (err) {
            lastErr = err;
          }
        }
        if (!ok) throw lastErr || new Error(`Échec téléchargement ${file.name}`);
      }
    }

    // swgemu_login.cfg vient du patch serveur — réappliquer IP/port selon la galaxie choisie.
    const server = getServer(selectedServerId);
    patchLoginConfig(profile, server);

    mainWindow.webContents.send('patch-status', {
      status: 'ready',
      message: `[${channel}] Client à jour.`,
    });
  } catch (error) {
    console.error('Patch error:', error);
    mainWindow.webContents.send('patch-status', {
      status: 'error',
      message: `Mise à jour indisponible (${channel}) : ${error.message}`,
    });
  }
}
