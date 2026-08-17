/**
 * Face Rig 2D — calques yeux/bouche pour Pilot (#/assistant).
 * API : init, setMood, setExpression, setTalking, say, destroy.
 * Sans PNG : fallback CSS. Avec manifest + sheets : background-position.
 */
(function (global) {
  "use strict";

  const MOOD_TO_EXPRESSION = {
    serene: "neutral",
    curious: "surprised",
    vigilant: "neutral",
    tense: "angry",
    waiting: "sad",
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

  let hostEl = null;
  let stageEl = null;
  let layerEls = {};
  let manifest = null;
  let assetBase = "";
  let currentExpression = "neutral";
  let talkTimer = null;
  let talkCycleTimer = null;
  let blinkTimer = null;
  let ready = false;
  let useSheets = false;

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
  }

  function scheduleBlink() {
    if (blinkTimer) global.clearTimeout(blinkTimer);
    const delay = 2200 + Math.floor(Math.random() * 2800);
    blinkTimer = global.setTimeout(function () {
      applyEyes("blink");
      global.setTimeout(function () {
        const emo = (manifest && manifest.emotions) || DEFAULT_EMOTIONS;
        const conf = emo[currentExpression] || emo.neutral || DEFAULT_EMOTIONS.neutral;
        applyEyes((conf && conf.eyes) || "idle");
        scheduleBlink();
      }, 120);
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
    // Une seule cellule visible : sheet agrandie × cols/rows, positionnée sur (col,row)
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
    if (conf && Array.isArray(conf.mouth_cycle) && conf.mouth_cycle.length) {
      // leave mouth to talk cycle
    } else {
      applyMouth((conf && conf.mouth) || "closed");
    }
  }

  function buildDom(host) {
    host.innerHTML = "";
    host.classList.add("face-rig-host");
    stageEl = global.document.createElement("div");
    stageEl.className = "face-rig-stage face-rig-stage--fallback";
    stageEl.setAttribute("role", "img");
    stageEl.setAttribute("aria-label", "Visage expressif Lyra");
    stageEl.innerHTML =
      '<div class="face-rig-base"></div>' +
      '<div class="face-rig-layer face-rig-eyes" data-layer="eyes">' +
      '<span class="face-rig-eye face-rig-eye--l"></span>' +
      '<span class="face-rig-eye face-rig-eye--r"></span>' +
      "</div>" +
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
    // Layout bandes optionnel (sinon ancrage dans le PNG, plein stage)
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
    if (!hostEl) return;
    clearTimers();
    buildDom(hostEl);
    await loadManifest(characterId);
    applyEmotion("neutral");
    scheduleBlink();
    ready = true;
  }

  function setExpression(expression) {
    if (!ready) return;
    const key = String(expression || "neutral");
    if (talkCycleTimer) {
      global.clearInterval(talkCycleTimer);
      talkCycleTimer = null;
    }
    applyEmotion(key);
  }

  function setMood(mood) {
    const expr = MOOD_TO_EXPRESSION[String(mood || "off")] || "neutral";
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
      applyEmotion(currentExpression === "talking" ? "neutral" : currentExpression);
      return;
    }
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

  function destroy() {
    clearTimers();
    ready = false;
    useSheets = false;
    if (hostEl) hostEl.innerHTML = "";
    hostEl = null;
    stageEl = null;
    layerEls = {};
    manifest = null;
  }

  global.FaceRig = {
    get ready() {
      return ready;
    },
    init: init,
    setMood: setMood,
    setExpression: setExpression,
    setTalking: setTalking,
    say: say,
    destroy: destroy,
    MOOD_TO_EXPRESSION: MOOD_TO_EXPRESSION,
  };
})(typeof window !== "undefined" ? window : globalThis);
