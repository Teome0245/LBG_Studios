/**
 * Campus Team — vue pixel art interactive (Option B — Inspiration Le Bureau des Agents / VibesMoney).
 * Rendu procédural 100% Canvas 2D (aucun asset externe requis).
 * 
 * - Robots cubiques animés (tête cube, visière, yeux orange luminescents, corps teinté par rôle)
 * - Bureaux équipés (laptop, écran avec reflets de code, clavier, mug)
 * - Meubles et props décoratifs (serveurs rack Core/LLM, machine à café, arcade Prime)
 * - Animations en temps réel : frappe clavier en busy, respiration en idle, alerte en review, marche sur chemins
 * - Bulles de statut pixel art
 * 
 * window.LbgOfficeMap = { start, stop, sync, setView }
 */
(function (global) {
  "use strict";

  const PHASER_CDN = "https://cdn.jsdelivr.net/npm/phaser@3.80.1/dist/phaser.min.js";
  const TILE = 16;
  const MAP_W = 42;
  const MAP_H = 30;

  /** Zones : rects en tuiles + waypoints pour déplacements */
  const ZONES = {
    zone_coffee: { x: 16, y: 1, w: 10, h: 5, label: "Café", color: 0x3d5a3a },
    zone_front: { x: 1, y: 8, w: 11, h: 8, label: "Front .100", color: 0x2a4a5a },
    zone_core: { x: 15, y: 8, w: 12, h: 8, label: "Core 140", color: 0x2a5a48 },
    zone_llm: { x: 30, y: 8, w: 11, h: 8, label: "Forge LLM", color: 0x2a5040 },
    zone_mmo_lab: { x: 1, y: 19, w: 12, h: 8, label: "Lab 245", color: 0x5a3e28 },
    zone_prime: { x: 15, y: 19, w: 12, h: 8, label: "Prime 246", color: 0x2a3a58 },
    zone_games: { x: 29, y: 19, w: 12, h: 8, label: "Salle jeux", color: 0x4a2a5a },
  };

  const PATH_HUB = { x: 21, y: 16 };

  const STATUS_COLOR = {
    busy: 0x3ecf8e,
    review: 0xe6b84d,
    failed: 0xe06b6b,
    idle: 0x6b8a94,
    offline: 0x4d646c,
  };

  /** Palette & profils de rôles */
  const ROLE_PROFILES = {
    chef: { key: "chef", label: "Chef", base: "#8b5cf6", body: "#312e81", eyes: "#ffb703", visor: "#0c0a14" },
    admin_infra: { key: "infra", label: "Infra", base: "#2dd4bf", body: "#134e4a", eyes: "#ff9900", visor: "#090e12" },
    dev_frontend: { key: "front", label: "Front", base: "#06b6d4", body: "#164e63", eyes: "#38bdf8", visor: "#080e14" },
    forge_llm: { key: "llm", label: "LLM", base: "#f59e0b", body: "#78350f", eyes: "#fde047", visor: "#120e06" },
    dev_godot: { key: "prime", label: "Prime", base: "#3b82f6", body: "#1e3a8a", eyes: "#60a5fa", visor: "#080e18" },
    player_bridge: { key: "bridge", label: "Pont", base: "#ec4899", body: "#831843", eyes: "#f472b6", visor: "#140810" },
    compagnon: { key: "compagnon", label: "Lyra", base: "#00f5d4", body: "#0f333a", eyes: "#00f5d4", visor: "#041014" },
    default: { key: "default", label: "Agent", base: "#64748b", body: "#1e293b", eyes: "#ff9900", visor: "#0b0f14" },
  };

  function resolveProfile(role, agentId) {
    const r = String(role || agentId || "").toLowerCase();
    if (r.includes("chef") || r.includes("pm") || r.includes("lead")) return ROLE_PROFILES.chef;
    if (r.includes("infra") || r.includes("admin") || r.includes("ops")) return ROLE_PROFILES.admin_infra;
    if (r.includes("front") || r.includes("web") || r.includes("ui")) return ROLE_PROFILES.dev_frontend;
    if (r.includes("llm") || r.includes("forge") || r.includes("model")) return ROLE_PROFILES.forge_llm;
    if (r.includes("godot") || r.includes("prime") || r.includes("mmo")) return ROLE_PROFILES.dev_godot;
    if (r.includes("bridge") || r.includes("player")) return ROLE_PROFILES.player_bridge;
    if (r.includes("compagnon") || r.includes("lyra")) return ROLE_PROFILES.compagnon;
    return ROLE_PROFILES.default;
  }

  // --- Fonctions utilitaires Pixel Art Canvas ---
  function makeCanvas(w, h) {
    const c = document.createElement("canvas");
    c.width = Math.max(1, Math.ceil(w));
    c.height = Math.max(1, Math.ceil(h));
    return c;
  }

  function getCtx(c) {
    const g = c.getContext("2d", { willReadFrequently: false });
    g.imageSmoothingEnabled = false;
    return g;
  }

  function rect(g, x, y, w, h, col) {
    g.fillStyle = col;
    g.fillRect(Math.round(x), Math.round(y), Math.round(w), Math.round(h));
  }

  function px(g, x, y, col) {
    g.fillStyle = col;
    g.fillRect(Math.round(x), Math.round(y), 1, 1);
  }

  function hexToRgb(hex) {
    let c = hex.replace("#", "");
    if (c.length === 3) c = c[0] + c[0] + c[1] + c[1] + c[2] + c[2];
    const num = parseInt(c, 16);
    return [(num >> 16) & 255, (num >> 8) & 255, num & 255];
  }

  function rgbToHex(r, g, b) {
    return "#" + [r, g, b].map(function (x) {
      return Math.max(0, Math.min(255, Math.round(x))).toString(16).padStart(2, "0");
    }).join("");
  }

  function lighten(hex, amount) {
    const rgb = hexToRgb(hex);
    return rgbToHex(rgb[0] + (255 - rgb[0]) * amount, rgb[1] + (255 - rgb[1]) * amount, rgb[2] + (255 - rgb[2]) * amount);
  }

  function darken(hex, amount) {
    const rgb = hexToRgb(hex);
    return rgbToHex(rgb[0] * (1 - amount), rgb[1] * (1 - amount), rgb[2] * (1 - amount));
  }

  // --- Dessin procédural des meubles et props ---

  function createDeskCanvas(active) {
    const c = makeCanvas(32, 24);
    const g = getCtx(c);
    const wood = "#825330";
    const woodHi = "#a87146";
    const woodDark = "#54331b";

    // Ombre sous le bureau
    rect(g, 2, 21, 28, 2, "rgba(0,0,0,0.35)");

    // Pieds
    rect(g, 3, 15, 3, 7, woodDark);
    rect(g, 26, 15, 3, 7, woodDark);
    rect(g, 3, 21, 3, 1, "#2b1a0d");
    rect(g, 26, 21, 3, 1, "#2b1a0d");

    // Façade sous le plateau
    rect(g, 3, 13, 26, 4, wood);
    rect(g, 3, 17, 26, 1, woodDark);

    // Plateau principal
    rect(g, 1, 7, 30, 7, wood);
    rect(g, 1, 7, 30, 1, woodHi);
    rect(g, 1, 8, 1, 6, woodHi);
    rect(g, 30, 8, 1, 6, woodDark);
    rect(g, 1, 13, 30, 1, woodDark);

    // Ordinateur portable
    const lapW = 12;
    const lapX = 10;
    const lapY = 5;
    rect(g, lapX, lapY, lapW, 6, "#222530");
    rect(g, lapX, lapY, lapW, 1, "#3f465c");
    rect(g, lapX + lapW - 1, lapY + 1, 1, 5, "#15171e");

    if (active) {
      // Écran allumé avec reflets de code
      rect(g, lapX + 4, lapY + 2, 4, 2, "#3ecf8e");
      px(g, lapX + 5, lapY + 2, "#e6fffa");
      // Halo lumineux sur le bureau
      rect(g, lapX - 1, lapY + 6, lapW + 2, 2, "rgba(62,207,142,0.45)");
    } else {
      // Logo veille
      rect(g, lapX + 5, lapY + 2, 2, 2, "#50576e");
    }

    // Clavier fin
    rect(g, lapX - 1, lapY + 6, lapW + 2, 1, "#cfd4db");

    // Tasse à café
    rect(g, 4, 8, 4, 4, "#f8fafc");
    rect(g, 4, 9, 4, 1, active ? "#f97316" : "#0284c7");
    rect(g, 7, 9, 1, 2, "#cbd5e1");

    // Feuilles / carnet
    rect(g, 23, 8, 6, 4, "#f1f5f9");
    rect(g, 24, 9, 4, 1, "#94a3b8");
    rect(g, 24, 11, 3, 1, "#94a3b8");

    return c;
  }

  function createServerRackCanvas(theme) {
    const c = makeCanvas(16, 28);
    const g = getCtx(c);
    const isLlm = theme === "llm";

    // Casing
    rect(g, 0, 0, 16, 28, "#111827");
    rect(g, 0, 0, 16, 1, "#374151");
    rect(g, 0, 0, 1, 28, "#374151");
    rect(g, 15, 1, 1, 27, "#030712");

    // Blades
    for (let y = 3; y <= 23; y += 4) {
      rect(g, 2, y, 12, 3, "#1f2937");
      rect(g, 3, y + 1, 6, 1, "#374151");
      // LEDs
      if (isLlm) {
        px(g, 10, y + 1, "#f59e0b");
        px(g, 12, y + 1, (y % 8 === 3) ? "#fbbf24" : "#78350f");
      } else {
        px(g, 10, y + 1, "#10b981");
        px(g, 12, y + 1, (y % 8 === 3) ? "#06b6d4" : "#065f46");
      }
    }
    return c;
  }

  function createCoffeeBarCanvas() {
    const c = makeCanvas(24, 22);
    const g = getCtx(c);

    // Comptoir
    rect(g, 0, 10, 24, 12, "#334155");
    rect(g, 0, 10, 24, 1, "#64748b");

    // Machine espresso
    rect(g, 3, 2, 18, 9, "#cbd5e1");
    rect(g, 4, 3, 16, 1, "#f8fafc");
    rect(g, 5, 5, 8, 4, "#0f172a");
    // Boutons & voyants
    px(g, 15, 4, "#10b981");
    px(g, 17, 4, "#ef4444");
    // Buse & carafe
    rect(g, 6, 7, 6, 4, "rgba(99,102,241,0.2)");
    rect(g, 7, 9, 4, 2, "#451a03");
    return c;
  }

  function createWaterCoolerCanvas() {
    const c = makeCanvas(12, 24);
    const g = getCtx(c);

    // Bouteille transparente
    rect(g, 2, 0, 8, 10, "#38bdf8");
    rect(g, 3, 1, 6, 8, "#7dd3fc");
    px(g, 4, 3, "#ffffff");
    px(g, 5, 6, "#ffffff");

    // Socle distributeur
    rect(g, 1, 10, 10, 14, "#f8fafc");
    rect(g, 1, 10, 10, 1, "#e2e8f0");
    rect(g, 3, 12, 6, 5, "#334155");
    // Robinets rouge et bleu
    px(g, 4, 13, "#ef4444");
    px(g, 7, 13, "#3b82f6");
    return c;
  }

  function createArcadeCanvas() {
    const c = makeCanvas(20, 28);
    const g = getCtx(c);

    // Borne Prime Lost Heaven
    rect(g, 2, 0, 16, 28, "#1e1b4b");
    rect(g, 2, 0, 16, 1, "#4338ca");
    rect(g, 3, 2, 14, 4, "#312e81");
    rect(g, 5, 3, 10, 2, "#818cf8"); // Enseigne PRIME

    // Écran
    rect(g, 3, 8, 14, 10, "#0284c7");
    rect(g, 4, 9, 12, 8, "#38bdf8");
    // Paysage pixel (dune + ciel)
    rect(g, 4, 13, 12, 4, "#f59e0b");
    px(g, 6, 11, "#ffffff"); // Soleil/étoile

    // Pupitre commandes
    rect(g, 2, 19, 16, 3, "#312e81");
    px(g, 5, 20, "#ef4444"); // Joystick
    px(g, 10, 20, "#eab308");
    px(g, 13, 20, "#10b981");

    return c;
  }

  // --- Dessin procédural des Robots Cubiques (Le Bureau des Agents) ---

  function createRobotCanvas(profile, pose) {
    const c = makeCanvas(22, 26);
    const g = getCtx(c);

    const base = profile.base;
    const bodyColor = profile.body;
    const topFacet = lighten(base, 0.28);
    const frontFacet = base;
    const shadeFacet = darken(base, 0.28);
    const visorCol = profile.visor;
    const eyeCol = profile.eyes;
    const eyeHi = lighten(eyeCol, 0.4);

    let bobY = 0;
    let armLeftY = 0;
    let armRightY = 0;
    let legLeftX = 7;
    let legRightX = 13;
    let legY = 19;
    let blink = false;
    let eyesLeft = false;

    if (pose === "type1") {
      bobY = 1;
      armLeftY = 1;
      armRightY = -1;
    } else if (pose === "type2") {
      bobY = 0;
      armLeftY = -1;
      armRightY = 1;
    } else if (pose === "think") {
      bobY = -1;
      armRightY = -4; // Main levée vers la joue
      eyesLeft = true;
    } else if (pose === "walk1") {
      bobY = -1;
      legLeftX = 6;
      legRightX = 14;
    } else if (pose === "walk2") {
      bobY = 0;
      legLeftX = 8;
      legRightX = 12;
    }

    const headX = 5;
    const headY = 3 + bobY;

    // Ombre sous le robot
    rect(g, 6, 23, 10, 2, "rgba(0,0,0,0.3)");

    // Jambes pistons robotiques
    rect(g, legLeftX, legY, 2, 4, "#1e293b");
    rect(g, legRightX, legY, 2, 4, "#1e293b");
    rect(g, legLeftX - 1, legY + 3, 3, 1, "#0f172a");
    rect(g, legRightX, legY + 3, 3, 1, "#0f172a");

    // Torse du robot
    const torsoX = 6;
    const torsoY = 12 + bobY;
    rect(g, torsoX, torsoY, 10, 7, bodyColor);
    rect(g, torsoX, torsoY, 10, 1, lighten(bodyColor, 0.25));
    rect(g, torsoX + 9, torsoY, 1, 7, darken(bodyColor, 0.25));

    // Cœur / réacteur ventral luminescent
    rect(g, torsoX + 3, torsoY + 2, 4, 3, darken(base, 0.15));
    rect(g, torsoX + 4, torsoY + 3, 2, 1, base);

    // Bras articulés
    rect(g, torsoX - 2, torsoY + 1 + armLeftY, 2, 5, darken(base, 0.1));
    rect(g, torsoX - 2, torsoY + 5 + armLeftY, 2, 2, base); // Main gauche

    if (pose === "think") {
      // Main droite au menton
      rect(g, torsoX + 10, torsoY - 1, 2, 4, darken(base, 0.1));
      rect(g, torsoX + 9, torsoY - 2, 2, 2, base);
    } else {
      rect(g, torsoX + 10, torsoY + 1 + armRightY, 2, 5, darken(base, 0.1));
      rect(g, torsoX + 10, torsoY + 5 + armRightY, 2, 2, base); // Main droite
    }

    // Tête cubique (Signature Robot / VibesMoney)
    // Facette supérieure
    rect(g, headX, headY, 12, 2, topFacet);
    rect(g, headX, headY, 12, 1, lighten(topFacet, 0.15));

    // Facette avant
    rect(g, headX, headY + 2, 11, 7, frontFacet);
    rect(g, headX + 11, headY + 2, 1, 7, shadeFacet);
    rect(g, headX, headY + 8, 11, 1, shadeFacet);

    // Visière noire brillante
    rect(g, headX + 2, headY + 3, 8, 4, visorCol);
    rect(g, headX + 2, headY + 3, 3, 1, lighten(visorCol, 0.35));

    // Yeux orange / dorés luminescents
    const eyeY = headY + 4;
    const shiftX = eyesLeft ? -1 : 0;
    if (blink) {
      rect(g, headX + 3 + shiftX, eyeY + 1, 2, 1, darken(eyeCol, 0.2));
      rect(g, headX + 7 + shiftX, eyeY + 1, 2, 1, darken(eyeCol, 0.2));
    } else {
      rect(g, headX + 3 + shiftX, eyeY, 2, 2, eyeCol);
      px(g, headX + 3 + shiftX, eyeY, eyeHi);
      rect(g, headX + 7 + shiftX, eyeY, 2, 2, eyeCol);
      px(g, headX + 7 + shiftX, eyeY, eyeHi);
    }

    // Oreilles / boulons latéraux
    rect(g, headX - 1, headY + 4, 1, 3, darken(base, 0.2));
    rect(g, headX + 12, headY + 4, 1, 3, darken(base, 0.3));

    return c;
  }

  let _phaserPromise = null;
  let _game = null;
  let _scene = null;
  let _host = null;
  let _agents = new Map();
  let _onSelect = null;
  let _running = false;
  let _zoneHostBadges = new Map();
  let _zoneLabelNodes = new Map();

  function zoneDisplayLabel(zid) {
    const z = ZONES[zid];
    if (!z) return zid;
    const badge = _zoneHostBadges.get(zid);
    if (badge) return z.label + " · " + badge;
    return z.label;
  }

  function refreshZoneLabels() {
    _zoneLabelNodes.forEach(function (txt, zid) {
      if (txt && txt.setText) txt.setText(zoneDisplayLabel(zid));
    });
  }

  function setZoneHostStates(zones) {
    _zoneHostBadges = new Map();
    (zones || []).forEach(function (z) {
      if (!z || !z.id) return;
      if (String(z.host_status || "") === "offline") {
        _zoneHostBadges.set(z.id, String(z.host_badge || "Éteinte"));
      }
    });
    refreshZoneLabels();
  }

  function loadPhaser() {
    if (global.Phaser) return Promise.resolve(global.Phaser);
    if (_phaserPromise) return _phaserPromise;
    _phaserPromise = new Promise(function (resolve, reject) {
      const s = document.createElement("script");
      s.src = PHASER_CDN;
      s.async = true;
      s.onload = function () {
        if (global.Phaser) resolve(global.Phaser);
        else reject(new Error("Phaser non chargé"));
      };
      s.onerror = function () {
        reject(new Error("CDN Phaser KO"));
      };
      document.head.appendChild(s);
    });
    return _phaserPromise;
  }

  function zoneCenter(zid) {
    const z = ZONES[zid] || ZONES.zone_core;
    return {
      x: (z.x + z.w / 2) * TILE,
      y: (z.y + z.h / 2) * TILE,
    };
  }

  function slotInZone(zid, index, total) {
    const z = ZONES[zid] || ZONES.zone_core;
    const cols = Math.max(2, Math.min(4, Math.ceil(Math.sqrt(Math.max(total, 1)))));
    const col = index % cols;
    const row = Math.floor(index / cols);
    const padX = 1.6;
    const padY = 2.0;
    const usableW = Math.max(2, z.w - padX * 2);
    const usableH = Math.max(2, z.h - padY * 2);
    const cx = z.x + padX + (col + 0.5) * (usableW / cols);
    const cy = z.y + padY + (row + 0.5) * (usableH / Math.max(1, Math.ceil(total / cols)));
    return { x: cx * TILE, y: cy * TILE };
  }

  function truncate(s, n) {
    const t = String(s || "").trim();
    if (t.length <= n) return t;
    return t.slice(0, n - 1) + "…";
  }

  function initials(name) {
    const parts = String(name || "?").trim().split(/\s+/).filter(Boolean);
    if (!parts.length) return "?";
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }

  function createScene(Phaser) {
    class CampusScene extends Phaser.Scene {
      constructor() {
        super("Campus");
        this.agentNodes = new Map();
        this.floorGfx = null;
        this.hoverLabel = null;
        this.typingTimer = null;
        this.typeToggle = false;
      }

      initTextures() {
        if (this.textures.exists("lbg_desk_normal")) return;

        // Desks
        this.textures.addCanvas("lbg_desk_normal", createDeskCanvas(false));
        this.textures.addCanvas("lbg_desk_active", createDeskCanvas(true));

        // Props de décor
        this.textures.addCanvas("lbg_prop_server_core", createServerRackCanvas("core"));
        this.textures.addCanvas("lbg_prop_server_llm", createServerRackCanvas("llm"));
        this.textures.addCanvas("lbg_prop_coffee_bar", createCoffeeBarCanvas());
        this.textures.addCanvas("lbg_prop_water_cooler", createWaterCoolerCanvas());
        this.textures.addCanvas("lbg_prop_arcade_prime", createArcadeCanvas());

        // Sprites de robots pour chaque profil et pose
        const poses = ["sit", "type1", "type2", "think", "walk1", "walk2"];
        Object.keys(ROLE_PROFILES).forEach((pKey) => {
          const prof = ROLE_PROFILES[pKey];
          poses.forEach((pose) => {
            const key = "robot_" + prof.key + "_" + pose;
            this.textures.addCanvas(key, createRobotCanvas(prof, pose));
          });
        });
      }

      create() {
        _scene = this;
        this.cameras.main.setBackgroundColor("#080c10");
        this.initTextures();
        this.drawWorld();

        this.hoverLabel = this.add
          .text(8, 8, "", {
            fontFamily: "IBM Plex Mono, monospace",
            fontSize: "11px",
            color: "#e2e8f0",
            backgroundColor: "#090d12ee",
            padding: { x: 8, y: 6 },
          })
          .setScrollFactor(0)
          .setDepth(2000)
          .setVisible(false);

        // Timer de frappe au clavier pour les agents busy (6 FPS fluide)
        this.typingTimer = this.time.addEvent({
          delay: 160,
          loop: true,
          callback: () => {
            this.typeToggle = !this.typeToggle;
            this.agentNodes.forEach((node) => {
              if (node.agent && node.agent.status === "busy" && !node.isWalking) {
                const prof = resolveProfile(node.agent.role, node.agent.agent_id);
                const frameKey = "robot_" + prof.key + "_" + (this.typeToggle ? "type1" : "type2");
                if (this.textures.exists(frameKey)) {
                  node.robotSprite.setTexture(frameKey);
                }
              }
            });
          },
        });

        // Sync initial agents
        this.resyncAll();
      }

      drawWorld() {
        const g = this.add.graphics();
        this.floorGfx = g;

        // Pelouse extérieure campus
        g.fillStyle(0x132219, 1);
        g.fillRect(0, 0, MAP_W * TILE, MAP_H * TILE);

        // Trame de pavage
        g.fillStyle(0x1a3024, 0.4);
        for (let y = 0; y < MAP_H; y++) {
          for (let x = 0; x < MAP_W; x++) {
            if ((x + y) % 2 === 0) g.fillRect(x * TILE, y * TILE, TILE, TILE);
          }
        }

        // Chemins en terre battue / pavés dorés
        g.fillStyle(0xb38d4a, 0.65);
        const pathRects = [
          [19, 6, 4, 3], // café → hub
          [12, 11, 18, 2], // front-core-llm
          [19, 13, 4, 7], // hub vertical
          [10, 16, 12, 2], // to lab
          [20, 16, 12, 2], // to prime
        ];
        pathRects.forEach(([x, y, w, h]) => {
          g.fillRect(x * TILE, y * TILE, w * TILE, h * TILE);
        });

        // Bâtiments et zones de travail
        Object.keys(ZONES).forEach((zid) => {
          const z = ZONES[zid];
          // Ombre portée
          g.fillStyle(0x000000, 0.45);
          g.fillRect(z.x * TILE + 4, z.y * TILE + 4, z.w * TILE, z.h * TILE);
          // Sol du bureau
          g.fillStyle(z.color, 1);
          g.fillRect(z.x * TILE, z.y * TILE, z.w * TILE, z.h * TILE);
          // Tapis intérieur
          g.fillStyle(0xffffff, 0.05);
          g.fillRect(z.x * TILE + 6, z.y * TILE + 6, z.w * TILE - 12, z.h * TILE - 12);
          // Murs renforcés avec liseré
          g.lineStyle(2, 0x475569, 0.5);
          g.strokeRect(z.x * TILE + 1, z.y * TILE + 1, z.w * TILE - 2, z.h * TILE - 2);
          // Seuil de porte
          g.fillStyle(0xc9a45a, 0.95);
          const dx = (z.x + z.w / 2) * TILE - 8;
          const dy = (z.y + z.h) * TILE - 2;
          g.fillRect(dx, dy, 16, 4);
        });

        // Intégration des props décoratifs de zone
        // Core 140 : Racks de serveurs
        this.add.image(16 * TILE + 10, 9 * TILE + 14, "lbg_prop_server_core").setDepth(3);
        this.add.image(24 * TILE + 10, 9 * TILE + 14, "lbg_prop_server_core").setDepth(3);

        // Forge LLM (.110 / .111) : Racks serveurs GPU avec LEDs ambre
        this.add.image(31 * TILE + 10, 9 * TILE + 14, "lbg_prop_server_llm").setDepth(3);
        this.add.image(39 * TILE + 6, 9 * TILE + 14, "lbg_prop_server_llm").setDepth(3);

        // Pause Café : Machine à espresso & bonbonne d'eau
        this.add.image(18 * TILE + 8, 3 * TILE + 8, "lbg_prop_coffee_bar").setDepth(3);
        this.add.image(24 * TILE + 6, 3 * TILE + 8, "lbg_prop_water_cooler").setDepth(3);

        // Prime 246 & Salle de jeux : Bornes Arcade Lost Heaven
        this.add.image(16 * TILE + 10, 20 * TILE + 14, "lbg_prop_arcade_prime").setDepth(3);
        this.add.image(30 * TILE + 10, 20 * TILE + 14, "lbg_prop_arcade_prime").setDepth(3);

        // Labels de zones
        _zoneLabelNodes.clear();
        Object.keys(ZONES).forEach((zid) => {
          const z = ZONES[zid];
          const txt = this.add
            .text(z.x * TILE + 8, z.y * TILE + 4, zoneDisplayLabel(zid), {
              fontFamily: "IBM Plex Mono, monospace",
              fontSize: "10px",
              color: "#e2e8f0",
              fontStyle: "bold",
            })
            .setDepth(5);
          _zoneLabelNodes.set(zid, txt);
        });

        // Décoration : Arbres d'extérieur
        this.drawTree(14 * TILE, 3 * TILE);
        this.drawTree(28 * TILE, 3.5 * TILE);
        this.drawTree(2 * TILE, 17 * TILE);
        this.drawTree(39 * TILE, 18 * TILE);

        // Badge titre campus
        this.add
          .text(MAP_W * TILE - 8, 6, "LBG Studios · Campus", {
            fontFamily: "IBM Plex Mono, monospace",
            fontSize: "10px",
            color: "#64748b",
            fontStyle: "bold",
          })
          .setOrigin(1, 0)
          .setDepth(5);
      }

      drawTree(x, y) {
        const g = this.add.graphics();
        g.fillStyle(0x1e3a24, 1);
        g.fillCircle(x, y, 8);
        g.fillStyle(0x2d5a37, 1);
        g.fillCircle(x - 3, y - 2, 6);
        g.fillStyle(0x452b1a, 1);
        g.fillRect(x - 1, y + 5, 3, 5);
        g.setDepth(4);
      }

      resyncAll() {
        const byZone = {};
        _agents.forEach((a) => {
          const loc = a.location && ZONES[a.location] ? a.location : "zone_core";
          if (!byZone[loc]) byZone[loc] = [];
          byZone[loc].push(a);
        });
        Object.keys(byZone).forEach((loc) => {
          byZone[loc].forEach((a, i) => {
            this.upsertAgent(a, slotInZone(loc, i, byZone[loc].length), false);
          });
        });
        // Retrait des agents disparus
        const ids = new Set(_agents.keys());
        this.agentNodes.forEach((node, id) => {
          if (!ids.has(id)) {
            node.container.destroy();
            this.agentNodes.delete(id);
          }
        });
      }

      upsertAgent(agent, target, animate) {
        const id = agent.agent_id;
        let node = this.agentNodes.get(id);
        const prof = resolveProfile(agent.role, id);
        const isBusy = agent.status === "busy";
        const isReview = agent.status === "review";
        const label = truncate(agent.display_name || id, 14);
        const bubble = truncate(agent.current_action || "", 32);

        const deskKey = isBusy ? "lbg_desk_active" : "lbg_desk_normal";
        const robotKey = "robot_" + prof.key + "_" + (isBusy ? "type1" : isReview ? "think" : "sit");

        if (!node) {
          const container = this.add.container(target.x, target.y);

          // 1. Bureau en bois équipé
          const deskSprite = this.add.image(0, 4, deskKey).setOrigin(0.5, 0.5);

          // 2. Petit robot cubique (derrière le bureau)
          const robotSprite = this.add.sprite(0, -6, robotKey).setOrigin(0.5, 0.5);

          // 3. Aura d'activité ou de validation
          const ring = this.add.circle(0, 3, 14);
          ring.setStrokeStyle(2, STATUS_COLOR[agent.status] || STATUS_COLOR.idle, 0.65);
          ring.setVisible(isBusy || isReview);

          // 4. Badge nominatif (sous le bureau)
          const nameBg = this.add.rectangle(0, 16, 48, 12, 0x090d12, 0.85).setOrigin(0.5, 0.5);
          nameBg.setStrokeStyle(1, Phaser.Display.Color.HexStringToColor(prof.base).color, 0.6);
          const nameText = this.add
            .text(0, 16, label, {
              fontFamily: "IBM Plex Mono, monospace",
              fontSize: "9px",
              color: "#f8fafc",
              fontStyle: "bold",
            })
            .setOrigin(0.5, 0.5);

          // 5. Bulle de dialogue pixel art (action courante au-dessus du robot)
          const speechContainer = this.add.container(0, -26);
          const speechBg = this.add.rectangle(0, 0, 70, 14, 0x090d12, 0.92);
          speechBg.setStrokeStyle(1, 0x38bdf8, 0.7);
          const speechText = this.add
            .text(0, 0, bubble || prof.label, {
              fontFamily: "IBM Plex Mono, monospace",
              fontSize: "8px",
              color: "#e2e8f0",
            })
            .setOrigin(0.5, 0.5);
          speechContainer.add([speechBg, speechText]);
          speechContainer.setVisible(!!bubble);

          container.add([ring, robotSprite, deskSprite, nameBg, nameText, speechContainer]);
          container.setSize(34, 38);
          container.setDepth(20);
          container.setInteractive(
            new Phaser.Geom.Rectangle(-16, -14, 32, 34),
            Phaser.Geom.Rectangle.Contains
          );

          container.on("pointerdown", () => {
            if (typeof _onSelect === "function") _onSelect(agent);
          });
          container.on("pointerover", () => {
            container.setScale(1.12);
            this.hoverLabel.setText(
              (agent.display_name || id) + " (" + (agent.role || prof.label) + ") · " + (agent.status || "idle") + "\n" +
              "Action : " + (agent.current_action || "Au repos") + (agent.task_id ? ("\nTâche : #" + String(agent.task_id).slice(0, 8)) : "")
            );
            this.hoverLabel.setVisible(true);
          });
          container.on("pointerout", () => {
            container.setScale(1.0);
            this.hoverLabel.setVisible(false);
          });

          // Animation de pulsation d'aura
          this.tweens.add({
            targets: ring,
            scale: 1.2,
            alpha: 0.25,
            duration: 900,
            yoyo: true,
            repeat: -1,
            ease: "Sine.easeInOut",
          });

          // Respiration douce en idle
          this.tweens.add({
            targets: robotSprite,
            y: -5,
            duration: 1800,
            yoyo: true,
            repeat: -1,
            ease: "Sine.easeInOut",
          });

          node = {
            container: container,
            robotSprite: robotSprite,
            deskSprite: deskSprite,
            ring: ring,
            nameBg: nameBg,
            nameText: nameText,
            speechContainer: speechContainer,
            speechBg: speechBg,
            speechText: speechText,
            agent: agent,
            isWalking: false,
          };
          this.agentNodes.set(id, node);
        } else {
          node.agent = agent;
          node.deskSprite.setTexture(deskKey);
          if (!node.isWalking) {
            node.robotSprite.setTexture(robotKey);
          }
          node.ring.setStrokeStyle(2, STATUS_COLOR[agent.status] || STATUS_COLOR.idle, 0.65);
          node.ring.setVisible(isBusy || isReview);
          node.nameText.setText(label);
          node.speechText.setText(bubble || prof.label);
          node.speechContainer.setVisible(!!bubble);

          node.container.off("pointerdown");
          node.container.on("pointerdown", () => {
            if (typeof _onSelect === "function") _onSelect(agent);
          });
        }

        const dest = target || zoneCenter(agent.location || "zone_core");
        if (animate) {
          node.isWalking = true;
          const walkKey1 = "robot_" + prof.key + "_walk1";
          const walkKey2 = "robot_" + prof.key + "_walk2";
          node.robotSprite.setTexture(walkKey1);

          // Masquer temporairement le bureau pendant le trajet à pied
          node.deskSprite.setVisible(false);

          // Timer d'alternance des pas pendant la marche
          const walkTimer = this.time.addEvent({
            delay: 180,
            repeat: 12,
            callback: () => {
              if (node.isWalking) {
                const cur = node.robotSprite.texture.key;
                node.robotSprite.setTexture(cur === walkKey1 ? walkKey2 : walkKey1);
              }
            },
          });

          const from = { x: node.container.x, y: node.container.y };
          const via = { x: PATH_HUB.x * TILE, y: PATH_HUB.y * TILE };
          const dist = Phaser.Math.Distance.Between(from.x, from.y, dest.x, dest.y);

          const onArrival = () => {
            node.isWalking = false;
            if (walkTimer) walkTimer.remove();
            node.deskSprite.setVisible(true);
            node.robotSprite.setTexture(robotKey);
          };

          if (dist > 80) {
            this.tweens.chain({
              targets: node.container,
              tweens: [
                { x: via.x, y: via.y, duration: Math.min(650, dist * 0.45), ease: "Sine.easeInOut" },
                { x: dest.x, y: dest.y, duration: Math.min(650, dist * 0.45), ease: "Sine.easeInOut", onComplete: onArrival },
              ],
            });
          } else {
            this.tweens.add({
              targets: node.container,
              x: dest.x,
              y: dest.y,
              duration: 420,
              ease: "Sine.easeInOut",
              onComplete: onArrival,
            });
          }

          // Petit saut de démarche
          this.tweens.add({
            targets: node.container,
            y: dest.y - 4,
            duration: 120,
            yoyo: true,
            repeat: 2,
            ease: "Quad.easeOut",
          });
        } else {
          node.container.setPosition(dest.x, dest.y);
          node.deskSprite.setVisible(true);
        }
      }
    }

    return CampusScene;
  }

  function start(opts) {
    opts = opts || {};
    _host = opts.host || document.getElementById("office-map-host");
    _onSelect = opts.onSelect || null;
    if (!_host) return Promise.reject(new Error("host manquant"));
    if (_running && _game) return Promise.resolve();

    return loadPhaser().then(function (Phaser) {
      const CampusScene = createScene(Phaser);
      const w = Math.min(_host.clientWidth || 672, 900);
      const h = Math.round((w / (MAP_W * TILE)) * (MAP_H * TILE));
      _host.innerHTML = "";
      _game = new Phaser.Game({
        type: Phaser.AUTO,
        parent: _host,
        width: MAP_W * TILE,
        height: MAP_H * TILE,
        backgroundColor: "#080c10",
        scene: [CampusScene],
        scale: {
          mode: Phaser.Scale.FIT,
          autoCenter: Phaser.Scale.CENTER_BOTH,
          width: MAP_W * TILE,
          height: MAP_H * TILE,
        },
        banner: false,
      });
      _running = true;
      _host.style.minHeight = Math.max(320, Math.min(h, 520)) + "px";
    });
  }

  function stop() {
    _running = false;
    if (_game) {
      try {
        _game.destroy(true);
      } catch (_) {}
      _game = null;
    }
    _scene = null;
    if (_host) _host.innerHTML = "";
  }

  function sync(agents, opts) {
    opts = opts || {};
    const animate = !!opts.animate;
    const prevLoc = new Map();
    _agents.forEach((a, id) => prevLoc.set(id, a.location));

    _agents = new Map();
    (agents || []).forEach((a) => {
      if (a && a.agent_id) _agents.set(a.agent_id, a);
    });

    if (!_scene) return;

    // Groupement par zone pour les slots
    const byZone = {};
    _agents.forEach((a) => {
      const loc = a.location && ZONES[a.location] ? a.location : "zone_core";
      if (!byZone[loc]) byZone[loc] = [];
      byZone[loc].push(a);
    });

    _agents.forEach((a) => {
      const loc = a.location && ZONES[a.location] ? a.location : "zone_core";
      const list = byZone[loc];
      const idx = list.findIndex((x) => x.agent_id === a.agent_id);
      const target = slotInZone(loc, idx, list.length);
      const moved =
        animate && prevLoc.has(a.agent_id) && prevLoc.get(a.agent_id) !== a.location;
      _scene.upsertAgent(a, target, !!moved);
    });

    // Nettoyage des agents partis
    const ids = new Set(_agents.keys());
    _scene.agentNodes.forEach((node, id) => {
      if (!ids.has(id)) {
        node.container.destroy();
        _scene.agentNodes.delete(id);
      }
    });
  }

  global.LbgOfficeMap = {
    start: start,
    stop: stop,
    sync: sync,
    setZoneHostStates: setZoneHostStates,
    isRunning: function () {
      return _running;
    },
  };
})(typeof window !== "undefined" ? window : globalThis);
