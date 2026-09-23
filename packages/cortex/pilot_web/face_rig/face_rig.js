/**
 * Face Rig 2D — multi-instances + idle look + API mood string|{tone}.
 * API instance : init, setMood, setExpression, setTalking, say, pulse, destroy.
 * Singleton : FaceRig.init / setMood / … (rétrocompat).
 */
(function (global) {
  "use strict";

  const MOOD_TO_EXPRESSION = {
    serene: "neutral",
    curious: "surprised",
    vigilant: "neutral",
    tense: "angry",
    waiting: "sad",
    alert: "angry",
    happy: "happy",
    off: "neutral",
  };

  const DEFAULT_EMOTIONS = {
    neutral: { eyes: "idle", mouth: "closed" },
    happy: { eyes: "happy", mouth: "smile" },
    sad: { eyes: "sad", mouth: "frown" },
    angry: { eyes: "angry", mouth: "frown" },
    surprised: { eyes: "surprised", mouth: "open_wide" },
    determined: { eyes: "idle", mouth: "closed" },
    talking: { eyes: "idle", mouth_cycle: ["talk_1", "talk_2", "talk_3"] },
  };

  function normalizeMood(mood) {
    if (mood && typeof mood === "object") {
      return String(mood.tone || mood.mood || mood.expression || "serene");
    }
    return String(mood || "serene");
  }

  function createInstance() {
    let hostEl = null;
    let stageEl = null;
    let layerEls = {};
    let manifest = null;
    let assetBase = "";
    let currentExpression = "neutral";
    let talkTimer = null;
    let talkCycleTimer = null;
    let blinkTimer = null;
    let idleTimer = null;
    let pulseTimer = null;
    let ready = false;
    let useSheets = false;
    let idlePaused = false;

    function assetUrl(file) {
      try {
        return new URL(file, assetBase).href;
      } catch (_) {
        return assetBase + file;
      }
    }

    function resolveAssetBase(characterId) {
      try {
        const scripts = global.document && global.document.getElementsByTagName("script");
        if (scripts) {
          for (let i = scripts.length - 1; i >= 0; i--) {
            const src = scripts[i].src || "";
            if (src.indexOf("face_rig.js") >= 0) {
              return new URL("assets/" + characterId + "/", src).href;
            }
          }
        }
      } catch (_) {}
      try {
        return new URL("face_rig/assets/" + characterId + "/", global.location.href).href;
      } catch (_) {
        return "face_rig/assets/" + characterId + "/";
      }
    }

    function clearTimers() {
      if (talkTimer) {
        global.clearTimeout(talkTimer);
        talkTimer = null;
      }
      if (talkCycleTimer) {
        global.clearInterval(talkCycleTimer);
        talkCycleTimer = null;
      }
      if (blinkTimer) {
        global.clearTimeout(blinkTimer);
        blinkTimer = null;
      }
      if (idleTimer) {
        global.clearTimeout(idleTimer);
        idleTimer = null;
      }
      if (pulseTimer) {
        global.clearTimeout(pulseTimer);
        pulseTimer = null;
      }
    }

    function scheduleBlink() {
      if (blinkTimer) global.clearTimeout(blinkTimer);
      // Fallback CSS : blink + look-around gérés par keyframes (style chat)
      if (!useSheets) return;
      if (!ready || idlePaused) return;
      const delay = 1800 + Math.floor(Math.random() * 2600);
      blinkTimer = global.setTimeout(function () {
        if (idlePaused) {
          scheduleBlink();
          return;
        }
        applyEyes("blink");
        global.setTimeout(function () {
          const emo = (manifest && manifest.emotions) || DEFAULT_EMOTIONS;
          const conf = emo[currentExpression] || emo.neutral || DEFAULT_EMOTIONS.neutral;
          applyEyes((conf && conf.eyes) || "idle");
          scheduleBlink();
        }, 130);
      }, delay);
    }

    function scheduleIdleLook() {
      if (idleTimer) global.clearTimeout(idleTimer);
      // Fallback CSS : regard géré par face-cat-look
      if (!useSheets) return;
      if (!ready) return;
      const delay = 5000 + Math.floor(Math.random() * 5000);
      idleTimer = global.setTimeout(function () {
        if (!ready || idlePaused || talkCycleTimer) {
          scheduleIdleLook();
          return;
        }
        if (Math.random() < 0.22) {
          applyEyes("surprised");
          global.setTimeout(function () {
            if (idlePaused || talkCycleTimer) return;
            const emo = (manifest && manifest.emotions) || DEFAULT_EMOTIONS;
            const conf = emo[currentExpression] || emo.neutral || DEFAULT_EMOTIONS.neutral;
            applyEyes((conf && conf.eyes) || "idle");
            scheduleIdleLook();
          }, 420);
        } else {
          scheduleIdleLook();
        }
      }, delay);
    }

    function setLayerFrame(layerName, frameKey) {
      const layer = manifest && manifest.layers && manifest.layers[layerName];
      const el = layerEls[layerName];
      if (!el || !layer || !useSheets) return;
      const frames = layer.frames || {};
      const xy = frames[frameKey];
      if (!xy || !Array.isArray(xy) || xy.length < 2) return;
      const cols = Number(layer.cols) || 1;
      const rows = Number(layer.rows) || 1;
      const col = Number(xy[0]) || 0;
      const row = Number(xy[1]) || 0;
      el.style.backgroundImage = "url(" + assetUrl(layer.file) + ")";
      el.style.backgroundRepeat = "no-repeat";
      el.style.backgroundSize = cols * 100 + "% " + rows * 100 + "%";
      const xPct = cols <= 1 ? 0 : (col / (cols - 1)) * 100;
      const yPct = rows <= 1 ? 0 : (row / (rows - 1)) * 100;
      el.style.backgroundPosition = xPct + "% " + yPct + "%";
      el.dataset.frame = frameKey;
    }

    function applyEyes(frameKey) {
      if (useSheets) {
        setLayerFrame("eyes", frameKey);
        return;
      }
      if (!stageEl) return;
      stageEl.setAttribute("data-eyes", frameKey || "idle");
    }

    function applyMouth(frameKey) {
      if (useSheets) {
        setLayerFrame("mouth", frameKey);
        return;
      }
      if (!stageEl) return;
      stageEl.setAttribute("data-mouth", frameKey || "closed");
    }

    function applyEmotion(expression) {
      const emo = (manifest && manifest.emotions) || DEFAULT_EMOTIONS;
      const conf = emo[expression] || emo.neutral || DEFAULT_EMOTIONS.neutral;
      currentExpression = expression;
      if (stageEl) stageEl.setAttribute("data-expression", expression);
      applyEyes((conf && conf.eyes) || "idle");
      if (!(conf && Array.isArray(conf.mouth_cycle) && conf.mouth_cycle.length)) {
        applyMouth((conf && conf.mouth) || "closed");
      }
    }

    function buildDom(host) {
      host.innerHTML = "";
      host.classList.add("face-rig-host");
      stageEl = global.document.createElement("div");
      stageEl.className = "face-rig-stage face-rig-stage--fallback face-rig-stage--alive";
      stageEl.setAttribute("role", "img");
      stageEl.setAttribute("aria-label", "Visage expressif Lyra");
      stageEl.innerHTML =
        '<div class="face-rig-ear face-rig-ear--l" aria-hidden="true"></div>' +
        '<div class="face-rig-ear face-rig-ear--r" aria-hidden="true"></div>' +
        '<div class="face-rig-base" aria-hidden="true"></div>' +
        '<div class="face-rig-layer face-rig-eyes" data-layer="eyes">' +
        '<span class="face-rig-eye face-rig-eye--l">' +
        '<span class="face-rig-pupil"></span>' +
        "</span>" +
        '<span class="face-rig-eye face-rig-eye--r">' +
        '<span class="face-rig-pupil"></span>' +
        "</span>" +
        "</div>" +
        '<div class="face-rig-muzzle" aria-hidden="true"></div>' +
        '<div class="face-rig-layer face-rig-mouth" data-layer="mouth"></div>';
      host.appendChild(stageEl);
      layerEls = {
        eyes: stageEl.querySelector('[data-layer="eyes"]'),
        mouth: stageEl.querySelector('[data-layer="mouth"]'),
        base: stageEl.querySelector(".face-rig-base"),
      };
    }

    function enableSheetsIfPossible() {
      if (!manifest || !manifest.layers) return;
      const eyes = manifest.layers.eyes;
      const mouth = manifest.layers.mouth;
      if (!eyes || !eyes.file || !mouth || !mouth.file) return;
      useSheets = true;
      if (stageEl) {
        stageEl.classList.remove("face-rig-stage--fallback");
        stageEl.classList.add("face-rig-stage--sheets");
      }
      ["base", "eyes", "mouth"].forEach(function (name) {
        const layer = manifest.layers[name];
        const el = layerEls[name];
        if (!layer || !el || !layer.file) return;
        if (layer.hidden || (manifest.layout && manifest.layout.hide_base && name === "base")) {
          el.style.display = "none";
          return;
        }
        el.classList.add("face-rig-sheet");
        el.style.backgroundImage = "url(" + assetUrl(layer.file) + ")";
        el.style.backgroundRepeat = "no-repeat";
      });
      const layout = manifest.layout || {};
      const useBands = !!(layout && layout.use_bands);
      ["eyes", "mouth"].forEach(function (name) {
        const el = layerEls[name];
        const conf = layout[name];
        if (!el) return;
        if (useBands && conf) {
          el.style.inset = "auto";
          if (conf.top) el.style.top = conf.top;
          if (conf.left) el.style.left = conf.left;
          if (conf.right) el.style.right = conf.right;
          if (conf.height) el.style.height = conf.height;
        } else {
          el.style.inset = "0";
          el.style.top = "";
          el.style.height = "";
          el.style.left = "";
          el.style.right = "";
        }
      });
      if (layerEls.eyes) {
        const eyesInner = layerEls.eyes.querySelectorAll(".face-rig-eye");
        eyesInner.forEach(function (n) {
          n.style.display = "none";
        });
      }
    }

    async function loadManifest(characterId) {
      assetBase = resolveAssetBase(characterId);
      try {
        const res = await fetch(assetUrl("manifest.json"), { cache: "no-cache" });
        if (!res.ok) throw new Error("HTTP " + res.status);
        manifest = await res.json();
      } catch (_) {
        manifest = {
          character_id: characterId,
          fallback: true,
          emotions: DEFAULT_EMOTIONS,
          layers: {},
        };
      }
      if (manifest.fallback || !manifest.layers || !Object.keys(manifest.layers).length) {
        useSheets = false;
      } else {
        enableSheetsIfPossible();
      }
    }

    async function init(hostId, opts) {
      opts = opts || {};
      const characterId = opts.characterId || "lyra_assistant";
      hostEl = typeof hostId === "string" ? global.document.getElementById(hostId) : hostId;
      if (!hostEl) return api;
      clearTimers();
      idlePaused = false;
      buildDom(hostEl);
      await loadManifest(characterId);
      applyEmotion("neutral");
      ready = true;
      scheduleBlink();
      scheduleIdleLook();
      return api;
    }

    function setExpression(expression) {
      if (!ready) return;
      if (talkCycleTimer) {
        global.clearInterval(talkCycleTimer);
        talkCycleTimer = null;
      }
      applyEmotion(String(expression || "neutral"));
    }

    function setMood(mood) {
      const key = normalizeMood(mood);
      const expr = MOOD_TO_EXPRESSION[key] || (DEFAULT_EMOTIONS[key] ? key : "neutral");
      setExpression(expr);
    }

    function setTalking(onOrMs) {
      if (!ready) return;
      if (talkTimer) {
        global.clearTimeout(talkTimer);
        talkTimer = null;
      }
      if (talkCycleTimer) {
        global.clearInterval(talkCycleTimer);
        talkCycleTimer = null;
      }
      const emo = (manifest && manifest.emotions) || DEFAULT_EMOTIONS;
      const talkConf = emo.talking || DEFAULT_EMOTIONS.talking;
      const cycle = (talkConf && talkConf.mouth_cycle) || ["talk_1", "talk_2"];
      if (onOrMs === false || onOrMs === 0) {
        idlePaused = false;
        applyEmotion(currentExpression === "talking" ? "neutral" : currentExpression);
        scheduleBlink();
        scheduleIdleLook();
        return;
      }
      idlePaused = true;
      applyEyes((talkConf && talkConf.eyes) || "idle");
      let i = 0;
      applyMouth(cycle[0]);
      talkCycleTimer = global.setInterval(function () {
        i = (i + 1) % cycle.length;
        applyMouth(cycle[i]);
      }, 140);
      if (typeof onOrMs === "number" && onOrMs > 0) {
        talkTimer = global.setTimeout(function () {
          setTalking(false);
        }, onOrMs);
      }
    }

    function say(text) {
      const n = String(text || "").trim().length;
      const ms = Math.min(8000, Math.max(900, 80 * Math.max(8, n)));
      setTalking(ms);
    }

    function pulse(kind) {
      if (!stageEl) return;
      stageEl.classList.remove("face-pulse-ok", "face-pulse-warn", "face-pulse-alert");
      const cls =
        kind === "warn"
          ? "face-pulse-warn"
          : kind === "alert"
            ? "face-pulse-alert"
            : "face-pulse-ok";
      // reflow
      void stageEl.offsetWidth;
      stageEl.classList.add(cls);
      if (pulseTimer) global.clearTimeout(pulseTimer);
      pulseTimer = global.setTimeout(function () {
        if (stageEl) stageEl.classList.remove(cls);
      }, 1200);
    }

    function destroy() {
      clearTimers();
      ready = false;
      useSheets = false;
      idlePaused = false;
      if (hostEl) hostEl.innerHTML = "";
      hostEl = null;
      stageEl = null;
      layerEls = {};
      manifest = null;
    }

    const api = {
      get ready() {
        return ready;
      },
      init: init,
      setMood: setMood,
      setExpression: setExpression,
      setTalking: setTalking,
      say: say,
      pulse: pulse,
      destroy: destroy,
    };
    return api;
  }

  const defaultInst = createInstance();
  const instances = [];

  function broadcast(method, args) {
    try {
      if (defaultInst.ready && typeof defaultInst[method] === "function") {
        defaultInst[method].apply(defaultInst, args);
      }
    } catch (_) {}
    instances.forEach(function (inst) {
      try {
        if (inst && inst.ready && typeof inst[method] === "function") {
          inst[method].apply(inst, args);
        }
      } catch (_) {}
    });
  }

  global.FaceRig = {
    MOOD_TO_EXPRESSION: MOOD_TO_EXPRESSION,
    create: function () {
      const inst = createInstance();
      instances.push(inst);
      return inst;
    },
    get ready() {
      return defaultInst.ready;
    },
    init: function (hostId, opts) {
      return defaultInst.init(hostId, opts);
    },
    setMood: function (mood) {
      broadcast("setMood", [mood]);
    },
    setExpression: function (expr) {
      broadcast("setExpression", [expr]);
    },
    setTalking: function (v) {
      broadcast("setTalking", [v]);
    },
    say: function (text) {
      broadcast("say", [text]);
    },
    pulse: function (kind) {
      broadcast("pulse", [kind]);
    },
    destroy: function () {
      defaultInst.destroy();
    },
  };
})(typeof window !== "undefined" ? window : globalThis);
