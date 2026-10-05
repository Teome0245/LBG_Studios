/**
 * Campus Team — vue pixel Phaser (Option A).
 * Lazy-load Phaser CDN ; positions = zones team.presence.v1.
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
    zone_mmo_lab: { x: 4, y: 19, w: 14, h: 8, label: "Lab 245", color: 0x5a3e28 },
    zone_prime: { x: 24, y: 19, w: 14, h: 8, label: "Prime 246", color: 0x2a3a58 },
  };

  const PATH_HUB = { x: 21, y: 16 };

  const STATUS_COLOR = {
    busy: 0x3ecf8e,
    review: 0xe6b84d,
    failed: 0xe06b6b,
    idle: 0x6b8a94,
    offline: 0x4d646c,
  };

  let _phaserPromise = null;
  let _game = null;
  let _scene = null;
  let _host = null;
  let _agents = new Map();
  let _onSelect = null;
  let _running = false;
  /** @type {Map<string, string|null>} zone_id → badge (ex. Éteinte) */
  let _zoneHostBadges = new Map();
  /** @type {Map<string, object>} Phaser text labels for zones */
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
    const padX = 1.2;
    const padY = 1.6;
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
      }

      create() {
        _scene = this;
        this.cameras.main.setBackgroundColor("#0c1216");
        this.drawWorld();
        this.hoverLabel = this.add
          .text(8, 8, "", {
            fontFamily: "IBM Plex Mono, monospace",
            fontSize: "11px",
            color: "#d7e6ea",
            backgroundColor: "#10181ccc",
            padding: { x: 6, y: 4 },
          })
          .setScrollFactor(0)
          .setDepth(1000)
          .setVisible(false);

        this.input.on("pointermove", (p) => {
          // no-op; agents handle pointer
        });

        // Sync initial agents
        this.resyncAll();
      }

      drawWorld() {
        const g = this.add.graphics();
        this.floorGfx = g;

        // Outdoor grass
        g.fillStyle(0x1a2a22, 1);
        g.fillRect(0, 0, MAP_W * TILE, MAP_H * TILE);

        // Grid dots
        g.fillStyle(0x243830, 0.35);
        for (let y = 0; y < MAP_H; y++) {
          for (let x = 0; x < MAP_W; x++) {
            if ((x + y) % 2 === 0) g.fillRect(x * TILE, y * TILE, TILE, TILE);
          }
        }

        // Paths (sand)
        g.fillStyle(0xc9a45a, 0.55);
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

        // Buildings
        Object.keys(ZONES).forEach((zid) => {
          const z = ZONES[zid];
          // shadow
          g.fillStyle(0x000000, 0.25);
          g.fillRect(z.x * TILE + 3, z.y * TILE + 3, z.w * TILE, z.h * TILE);
          // floor
          g.fillStyle(z.color, 1);
          g.fillRect(z.x * TILE, z.y * TILE, z.w * TILE, z.h * TILE);
          // carpet
          g.fillStyle(0xffffff, 0.06);
          g.fillRect(z.x * TILE + 8, z.y * TILE + 8, z.w * TILE - 16, z.h * TILE - 16);
          // walls
          g.lineStyle(2, 0xd7e6ea, 0.35);
          g.strokeRect(z.x * TILE + 1, z.y * TILE + 1, z.w * TILE - 2, z.h * TILE - 2);
          // door notch
          g.fillStyle(0xc9a45a, 0.9);
          const dx = (z.x + z.w / 2) * TILE - 6;
          const dy = (z.y + z.h) * TILE - 2;
          g.fillRect(dx, dy, 12, 4);
        });

        // Labels
        _zoneLabelNodes.clear();
        Object.keys(ZONES).forEach((zid) => {
          const z = ZONES[zid];
          const txt = this.add
            .text(z.x * TILE + 6, z.y * TILE + 4, zoneDisplayLabel(zid), {
              fontFamily: "IBM Plex Mono, monospace",
              fontSize: "10px",
              color: "#e8f2f4",
              fontStyle: "bold",
            })
            .setDepth(5);
          _zoneLabelNodes.set(zid, txt);
        });

        // Decor: trees near café
        this.drawTree(14 * TILE, 3 * TILE);
        this.drawTree(28 * TILE, 3.5 * TILE);
        this.drawTree(2 * TILE, 17 * TILE);
        this.drawTree(39 * TILE, 18 * TILE);

        // Title badge
        this.add
          .text(MAP_W * TILE - 8, 6, "LBG campus", {
            fontFamily: "IBM Plex Mono, monospace",
            fontSize: "10px",
            color: "#7f98a1",
          })
          .setOrigin(1, 0)
          .setDepth(5);
      }

      drawTree(x, y) {
        const g = this.add.graphics();
        g.fillStyle(0x2d4a32, 1);
        g.fillCircle(x, y, 7);
        g.fillStyle(0x3d6a42, 1);
        g.fillCircle(x - 3, y - 2, 5);
        g.fillStyle(0x5a3a22, 1);
        g.fillRect(x - 1, y + 4, 2, 5);
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
        // Remove gone
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
        const color = STATUS_COLOR[agent.status] || STATUS_COLOR.idle;
        const label = truncate(agent.display_name || id, 12);
        const bubble = truncate(agent.current_action || "", 28);

        if (!node) {
          const container = this.add.container(target.x, target.y);
          const body = this.add.circle(0, 0, 7, color);
          body.setStrokeStyle(2, 0x0e1518, 0.8);
          const ring = this.add.circle(0, 0, 10);
          ring.setStrokeStyle(2, color, 0.55);
          ring.setVisible(agent.status === "busy");
          const ini = this.add
            .text(0, 0, initials(agent.display_name || id), {
              fontFamily: "IBM Plex Mono, monospace",
              fontSize: "8px",
              color: "#0e1518",
              fontStyle: "bold",
            })
            .setOrigin(0.5);
          const name = this.add
            .text(0, 12, label, {
              fontFamily: "IBM Plex Mono, monospace",
              fontSize: "9px",
              color: "#eef6f8",
              backgroundColor: "#0e1518aa",
              padding: { x: 3, y: 1 },
            })
            .setOrigin(0.5, 0);
          const speech = this.add
            .text(0, -18, bubble, {
              fontFamily: "IBM Plex Mono, monospace",
              fontSize: "8px",
              color: "#0e1518",
              backgroundColor: "#d7e6eadd",
              padding: { x: 4, y: 2 },
            })
            .setOrigin(0.5, 1)
            .setVisible(!!bubble);

          container.add([ring, body, ini, name, speech]);
          container.setSize(24, 28);
          container.setDepth(20);
          container.setInteractive(
            new Phaser.Geom.Circle(0, 0, 12),
            Phaser.Geom.Circle.Contains
          );
          container.on("pointerdown", () => {
            if (typeof _onSelect === "function") _onSelect(agent);
          });
          container.on("pointerover", () => {
            container.setScale(1.12);
            this.hoverLabel.setText(
              (agent.display_name || id) + " · " + (agent.status || "?") + "\n" + truncate(agent.current_action || "", 48)
            );
            this.hoverLabel.setVisible(true);
          });
          container.on("pointerout", () => {
            container.setScale(1);
            this.hoverLabel.setVisible(false);
          });

          // Busy pulse
          this.tweens.add({
            targets: ring,
            scale: 1.25,
            alpha: 0.2,
            duration: 900,
            yoyo: true,
            repeat: -1,
            ease: "Sine.easeInOut",
          });

          node = { container, body, ring, ini, name, speech, agent };
          this.agentNodes.set(id, node);
        } else {
          node.agent = agent;
          node.body.setFillStyle(color);
          node.ring.setStrokeStyle(2, color, 0.55);
          node.ring.setVisible(agent.status === "busy");
          node.ini.setText(initials(agent.display_name || id));
          node.name.setText(label);
          node.speech.setText(bubble);
          node.speech.setVisible(!!bubble);
          node.container.off("pointerdown");
          node.container.on("pointerdown", () => {
            if (typeof _onSelect === "function") _onSelect(agent);
          });
        }

        const dest = target || zoneCenter(agent.location || "zone_core");
        if (animate) {
          // Via hub if far
          const from = { x: node.container.x, y: node.container.y };
          const via = { x: PATH_HUB.x * TILE, y: PATH_HUB.y * TILE };
          const dist = Phaser.Math.Distance.Between(from.x, from.y, dest.x, dest.y);
          if (dist > 80) {
            this.tweens.chain({
              targets: node.container,
              tweens: [
                { x: via.x, y: via.y, duration: Math.min(700, dist * 0.45), ease: "Sine.easeInOut" },
                { x: dest.x, y: dest.y, duration: Math.min(700, dist * 0.45), ease: "Sine.easeInOut" },
              ],
            });
          } else {
            this.tweens.add({
              targets: node.container,
              x: dest.x,
              y: dest.y,
              duration: 450,
              ease: "Sine.easeInOut",
            });
          }
          // hop
          this.tweens.add({
            targets: node.container,
            y: dest.y - 4,
            duration: 120,
            yoyo: true,
            ease: "Quad.easeOut",
          });
        } else {
          node.container.setPosition(dest.x, dest.y);
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
        backgroundColor: "#0c1216",
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
      // apply size on host
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

    // Group by zone for slots
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

    // prune
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
