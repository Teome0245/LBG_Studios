/**
 * Desktop pet VRM — three + @pixiv/three-vrm (bundlé).
 * Idle (respiration / bras) + poses guide (pointer / saluer).
 */
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { VRMLoaderPlugin, VRMUtils } from "@pixiv/three-vrm";

/** Guard: three-vrm parfois assigne colorSpace sur texture undefined. */
function installColorSpaceGuard(THREE) {
  try {
    const desc = Object.getOwnPropertyDescriptor(THREE.Texture.prototype, "colorSpace");
    if (!desc || !desc.set) return;
    Object.defineProperty(THREE.Texture.prototype, "colorSpace", {
      configurable: true,
      enumerable: desc.enumerable,
      get: desc.get,
      set(v) {
        if (this == null || typeof this !== "object") return;
        try {
          desc.set.call(this, v);
        } catch (_) {}
      },
    });
  } catch (_) {}
}

const MOOD_EXPR = {
  serene: { relaxed: 0.4 },
  curious: { happy: 0.15, surprised: 0.2 },
  tense: { angry: 0.4, surprised: 0.15 },
  alert: { surprised: 0.55 },
  happy: { happy: 0.65 },
  sad: { sad: 0.5 },
};

/** Euler locaux (rad) relatifs au T-pose — clés = bones humanoid normalisés.
 * Pour un bras normalisé horizontal en T-pose :
 * - rotation Z négative pour leftUpperArm = bras descend le long du corps
 * - rotation Z positive pour rightUpperArm = bras descend le long du corps
 */
const POSE_EULERS = {
  idle: {
    leftUpperArm: [0, 0, -1.28],
    rightUpperArm: [0, 0, 1.28],
    leftLowerArm: [0, 0, 0],
    rightLowerArm: [0, 0, 0],
    leftHand: [0, 0, 0],
    rightHand: [0, 0, 0],
    spine: [0.02, 0, 0],
    chest: [0.03, 0, 0],
    neck: [0, 0, 0],
    head: [0, 0, 0],
    leftUpperLeg: [0, 0, -0.02],
    rightUpperLeg: [0, 0, 0.02],
  },
  /** Bras croisés confiants (posture robotique fière, coudes et avant-bras croisés devant la poitrine). */
  crossArms: {
    leftUpperArm: [0.45, -0.22, -0.82],
    rightUpperArm: [0.38, 0.22, 0.82],
    leftLowerArm: [0.15, 0.10, -1.55],
    rightLowerArm: [-0.15, -0.10, -1.55],
    leftHand: [0, 0, 0.12],
    rightHand: [0, 0, -0.12],
    spine: [0.03, 0, 0],
    chest: [0.06, 0, 0],
    neck: [-0.02, 0.03, 0],
    head: [-0.03, 0.04, 0.01],
    leftUpperLeg: [0, 0, -0.02],
    rightUpperLeg: [0, 0, 0.02],
  },
  /** Pointer vers la gauche (bras contenu, dirigé vers l'avant-gauche sans sortir du cadre). */
  pointLeft: {
    leftUpperArm: [0, 0, -1.28],
    rightUpperArm: [0.40, 0.35, 0.65],
    leftLowerArm: [0, 0, 0],
    rightLowerArm: [0, 0.20, -0.65],
    leftHand: [0, 0, 0],
    rightHand: [0, 0, 0],
    spine: [0.02, 0.08, 0],
    chest: [0.03, 0.08, 0],
    neck: [0, 0.12, 0],
    head: [0, 0.14, 0],
    leftUpperLeg: [0, 0, -0.02],
    rightUpperLeg: [0, 0, 0.02],
  },
  /** Pointer vers la droite (bras contenu, dirigé vers l'avant-droite sans sortir du cadre). */
  pointRight: {
    leftUpperArm: [0.40, -0.35, -0.65],
    rightUpperArm: [0, 0, 1.28],
    leftLowerArm: [0, -0.20, 0.65],
    rightLowerArm: [0, 0, 0],
    leftHand: [0, 0, 0],
    rightHand: [0, 0, 0],
    spine: [0.02, -0.08, 0],
    chest: [0.03, -0.08, 0],
    neck: [0, -0.12, 0],
    head: [0, -0.14, 0],
    leftUpperLeg: [0, 0, -0.02],
    rightUpperLeg: [0, 0, 0.02],
  },
  /** Pointer l'écran : bras droit dirigé vers l'écran en profondeur Z. */
  pointScreen: {
    leftUpperArm: [0, 0, -1.28],
    rightUpperArm: [0.35, 0.35, 0.30],
    leftLowerArm: [0, 0, 0],
    rightLowerArm: [0, 0.15, -0.55],
    leftHand: [0, 0, 0],
    rightHand: [0, 0, 0],
    spine: [0.02, 0.10, 0],
    chest: [0.03, 0.10, 0],
    neck: [0, 0.15, 0],
    head: [0, 0.16, 0],
    leftUpperLeg: [0, 0, -0.02],
    rightUpperLeg: [0, 0, 0.02],
  },
  /** Saluer : coude près des côtes, main droite oscillant près de l'épaule (ne sort jamais du cadre). */
  wave: {
    leftUpperArm: [0, 0, -1.28],
    rightUpperArm: [0.30, -0.05, 0.95],
    leftLowerArm: [0, 0, 0],
    rightLowerArm: [0.10, 0.20, -1.55],
    leftHand: [0, 0, 0.15],
    rightHand: [0, 0, 0.15],
    spine: [0.02, -0.03, 0],
    chest: [0.03, -0.03, 0],
    neck: [0, -0.03, 0],
    head: [0, -0.05, -0.03],
    leftUpperLeg: [0, 0, -0.02],
    rightUpperLeg: [0, 0, 0.02],
  },
  /** Réflexion : main droite sous le menton, coude en avant du torse. */
  think: {
    leftUpperArm: [0, 0, -1.25],
    rightUpperArm: [0.28, 0.25, 0.88],
    leftLowerArm: [0, 0, 0],
    rightLowerArm: [0.05, 0.10, -1.65],
    leftHand: [0, 0, 0],
    rightHand: [0.15, 0, 0.20],
    spine: [0.04, 0.04, 0],
    chest: [0.04, 0.03, 0],
    neck: [0.05, 0.06, 0.04],
    head: [0.07, 0.08, 0.06],
    leftUpperLeg: [0, 0, -0.02],
    rightUpperLeg: [0, 0, 0.02],
  },
  /** Approbation / hochement : geste affirmatif, tête qui acquiesce. */
  approve: {
    leftUpperArm: [0, 0, -1.25],
    rightUpperArm: [0.22, 0.20, 1.05],
    leftLowerArm: [0, 0, 0],
    rightLowerArm: [0, 0, -1.25],
    leftHand: [0, 0, 0],
    rightHand: [0, 0, 0],
    spine: [0.05, 0, 0],
    chest: [0.06, 0, 0],
    neck: [-0.08, 0, 0],
    head: [-0.14, 0, 0],
    leftUpperLeg: [0, 0, -0.02],
    rightUpperLeg: [0, 0, 0.02],
  },
  /** Célébration / joie : deux poings levés près des épaules, coudes contre les côtes (contenu). */
  cheer: {
    leftUpperArm: [0.30, 0.10, -1.05],
    rightUpperArm: [0.30, -0.10, 1.05],
    leftLowerArm: [0, 0, -1.35],
    rightLowerArm: [0, 0, 1.35],
    leftHand: [0, 0, 0],
    rightHand: [0, 0, 0],
    spine: [0.03, 0, 0],
    chest: [0.05, 0, 0],
    neck: [-0.05, 0, 0],
    head: [-0.08, 0, 0],
    leftUpperLeg: [0, 0, -0.02],
    rightUpperLeg: [0, 0, 0.02],
  },
  /** Révérence / salutation polie. */
  bow: {
    leftUpperArm: [0, 0, -1.15],
    rightUpperArm: [0, 0, 1.15],
    leftLowerArm: [0, 0, -0.15],
    rightLowerArm: [0, 0, 0.15],
    leftHand: [0, 0, 0],
    rightHand: [0, 0, 0],
    spine: [0.22, 0, 0],
    chest: [0.15, 0, 0],
    neck: [0.12, 0, 0],
    head: [0.12, 0, 0],
    leftUpperLeg: [0, 0, -0.02],
    rightUpperLeg: [0, 0, 0.02],
  },
  /** Danse rythmée / groove avec balancement et déhanché. */
  dance: {
    leftUpperArm: [0.25, 0.2, -0.65],
    rightUpperArm: [0.25, -0.2, 0.65],
    leftLowerArm: [0, 0, -1.15],
    rightLowerArm: [0, 0, 1.15],
    leftHand: [0, 0, 0],
    rightHand: [0, 0, 0],
    hips: [0, 0, 0],
    spine: [0.03, 0, 0],
    chest: [0.04, 0, 0],
    neck: [0, 0, 0],
    head: [0, 0, 0],
    leftUpperLeg: [0, 0, -0.05],
    rightUpperLeg: [0, 0, 0.05],
    leftLowerLeg: [0.1, 0, 0],
    rightLowerLeg: [0.1, 0, 0],
  },
  /** Colère / bouderie expressive : poings sur les hanches, torse gonflé. */
  angry: {
    leftUpperArm: [0.18, 0.4, -0.75],
    rightUpperArm: [0.18, -0.4, 0.75],
    leftLowerArm: [0, 0, -1.55],
    rightLowerArm: [0, 0, 1.55],
    leftHand: [-0.25, 0, 0],
    rightHand: [-0.25, 0, 0],
    hips: [0, 0, 0],
    spine: [0.06, 0, 0],
    chest: [0.08, 0, 0],
    neck: [-0.04, 0, 0],
    head: [-0.06, 0, 0],
    leftUpperLeg: [0, 0, -0.08],
    rightUpperLeg: [0, 0, 0.08],
  },
  /** Cycle de marche naturel et souple. */
  walk: {
    leftUpperArm: [0, 0, -1.25],
    rightUpperArm: [0, 0, 1.25],
    leftLowerArm: [0, 0, -0.20],
    rightLowerArm: [0, 0, 0.20],
    leftHand: [0, 0, 0],
    rightHand: [0, 0, 0],
    hips: [0.02, 0, 0],
    spine: [0.03, 0, 0],
    chest: [0.03, 0, 0],
    neck: [0, 0, 0],
    head: [0.01, 0, 0],
    leftUpperLeg: [0, 0, -0.02],
    rightUpperLeg: [0, 0, 0.02],
    leftLowerLeg: [0.02, 0, 0],
    rightLowerLeg: [0.02, 0, 0],
    leftFoot: [0, 0, 0],
    rightFoot: [0, 0, 0],
  },
};

const BONE_NAMES = [
  "hips",
  "spine",
  "chest",
  "upperChest",
  "neck",
  "head",
  "leftUpperArm",
  "leftLowerArm",
  "leftHand",
  "rightUpperArm",
  "rightLowerArm",
  "rightHand",
  "leftUpperLeg",
  "rightUpperLeg",
  "leftLowerLeg",
  "rightLowerLeg",
  "leftFoot",
  "rightFoot",
];

function lerpEulerMap(a, b, t) {
  const out = {};
  const keys = new Set([...Object.keys(a || {}), ...Object.keys(b || {})]);
  for (const k of keys) {
    const ea = a[k] || [0, 0, 0];
    const eb = b[k] || [0, 0, 0];
    out[k] = [
      ea[0] + (eb[0] - ea[0]) * t,
      ea[1] + (eb[1] - ea[1]) * t,
      ea[2] + (eb[2] - ea[2]) * t,
    ];
  }
  return out;
}

export function createVrmPet(hostEl, opts = {}) {
  installColorSpaceGuard(THREE);
  const modelUrl = opts.modelUrl || "./vrm/default.vrm";
  /** bust = gros plan visage · full = corps entier */
  let framing = String(opts.framing || opts.vrmFraming || "full").toLowerCase() === "bust"
    ? "bust"
    : "full";
  const clock = new THREE.Clock();
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(framing === "full" ? 30 : 25, 1, 0.05, 40);

  const renderer = new THREE.WebGLRenderer({
    alpha: true,
    antialias: true,
    premultipliedAlpha: false,
  });
  renderer.setClearColor(0x000000, 0);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  hostEl.appendChild(renderer.domElement);

  scene.add(new THREE.HemisphereLight(0xffffff, 0x444466, 1.0));
  const key = new THREE.DirectionalLight(0xffffff, 1.4);
  key.position.set(1.0, 1.8, 2.2);
  scene.add(key);
  scene.add(new THREE.DirectionalLight(0x99e9f2, 0.45).translateX(-2).translateY(1));

  /** @type {import('@pixiv/three-vrm').VRM | null} */
  let vrm = null;
  let talkingUntil = 0;
  let mouthAmp = 0;
  let ready = false;
  let disposed = false;
  let loadError = null;
  let targetHeadingY = 0;
  let currentHeadingY = 0;
  let nextBlinkTime = 2.0;
  let blinkProgress = 0;
  let nextIdleFidgetTime = 6.0;

  /** Pose courante / cible pour blend */
  let poseFrom = "idle";
  let poseTo = "idle";
  let poseBlend = 1; // 0..1 vers poseTo
  let poseHoldUntil = 0;
  let poseReturnTo = "idle";

  const _euler = new THREE.Euler();
  const _quat = new THREE.Quaternion();

  function setHeading(dir) {
    if (typeof dir === "number") {
      if (dir > 0.05) targetHeadingY = 1.30; // profil 3/4 droit (~75°)
      else if (dir < -0.05) targetHeadingY = -1.30; // profil 3/4 gauche (~-75°)
      else targetHeadingY = 0; // face caméra
    } else if (typeof dir === "string") {
      const s = dir.toLowerCase();
      if (s === "right" || s === "droite") targetHeadingY = 1.30;
      else if (s === "left" || s === "gauche") targetHeadingY = -1.30;
      else targetHeadingY = 0;
    }
  }

  function resize() {
    const w = Math.max(64, hostEl.clientWidth || 220);
    const h = Math.max(64, hostEl.clientHeight || 360);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h, false);
    if (vrm) frameVrm(vrm);
  }

  function setExpressionWeights(weights) {
    if (!vrm?.expressionManager) return;
    const em = vrm.expressionManager;
    for (const n of ["happy", "angry", "sad", "surprised", "relaxed", "neutral", "aa"]) {
      try {
        em.setValue(n, 0);
      } catch (_) {}
    }
    for (const [k, v] of Object.entries(weights || {})) {
      try {
        em.setValue(k, Math.max(0, Math.min(1, Number(v) || 0)));
      } catch (_) {}
    }
  }

  function setMood(mood) {
    let tone = "serene";
    if (mood && typeof mood === "object") tone = String(mood.tone || mood.mood || "serene");
    else if (mood != null) tone = String(mood);
    setExpressionWeights(MOOD_EXPR[tone.toLowerCase()] || MOOD_EXPR.serene);
  }

  function setTalking(msOrBool) {
    if (msOrBool === false || msOrBool === 0) {
      talkingUntil = 0;
      mouthAmp = 0;
      return;
    }
    const ms = typeof msOrBool === "number" && Number.isFinite(msOrBool) ? msOrBool : 2500;
    talkingUntil = performance.now() + Math.max(400, Math.min(20000, ms));
  }

  function say(text) {
    setTalking(Math.min(12000, Math.max(900, 55 * String(text || "").length)));
  }

  function pulse() {
    setMood("alert");
    setPose("wave", 1800);
    setTimeout(() => setMood("tense"), 900);
  }

  /**
   * @param {string} name idle | pointLeft | pointRight | pointScreen | wave | think | approve | cheer | bow
   * @param {number} [holdMs] durée avant retour idle (0 = tenir)
   */
  function setPose(name, holdMs, heading) {
    const raw = String(name || "idle");
    const n = raw.toLowerCase().replace(/[-_\s]/g, "");
    let key = "idle";
    if (n === "point" || n === "pointleft") key = "pointLeft";
    else if (n === "pointright") key = "pointRight";
    else if (n === "pointscreen" || n === "screen" || n === "desktop") key = "pointScreen";
    else if (n === "think" || n === "reflect" || n === "ponder") key = "think";
    else if (n === "approve" || n === "nod" || n === "ok" || n === "yes") key = "approve";
    else if (n === "cheer" || n === "happy" || n === "joy") key = "cheer";
    else if (n === "crossarms" || n === "cross" || n === "arms") key = "crossArms";
    else if (n === "bow" || n === "greet" || n === "welcome") key = "bow";
    else if (n === "wave" || n === "hello" || n === "salute") key = "wave";
    else if (n === "dance" || n === "danse" || n === "groove") key = "dance";
    else if (n === "angry" || n === "colere" || n === "mad" || n === "pout") key = "angry";
    else if (n === "walk" || n === "marche" || n === "step") key = "walk";
    else if (POSE_EULERS[raw]) key = raw;
    else if (POSE_EULERS[n]) key = n;

    if (heading !== undefined) {
      setHeading(heading);
    } else if (key === "idle") {
      setHeading(0);
    }

    if (key === "angry") setMood("tense");
    else if (key === "dance" || key === "cheer") setMood("happy");
    else if (key === "think") setMood("curious");

    poseFrom = poseTo;
    poseTo = key;
    poseBlend = 0;
    const hold = Number(holdMs);
    if (Number.isFinite(hold) && hold > 0) {
      poseHoldUntil = performance.now() + hold;
      poseReturnTo = "idle";
    } else {
      poseHoldUntil = 0;
    }
  }

  function bone(name) {
    try {
      return vrm?.humanoid?.getNormalizedBoneNode?.(name) || null;
    } catch (_) {
      return null;
    }
  }

  function applyBoneEulers(map, t) {
    if (!vrm?.humanoid) return;
    // Respiration / sway sur la pose idle (toujours, même en point)
    const breath = Math.sin(t * 1.55) * 0.018;
    const sway = Math.sin(t * 0.65) * 0.025;
    const armBob = Math.sin(t * 1.2) * 0.03;

    const animated = { ...map };
    if (animated.spine) {
      animated.spine = [
        animated.spine[0] + breath,
        animated.spine[1] + sway * 0.4,
        animated.spine[2],
      ];
    }
    if (animated.chest) {
      animated.chest = [
        animated.chest[0] + breath * 1.2,
        animated.chest[1] + sway * 0.5,
        animated.chest[2],
      ];
    }
    if (animated.head && poseTo === "idle") {
      // Regard curieux et observateur : hochements subtils et observation des fenêtres de l'écran
      const headNod = Math.sin(t * 0.55) * 0.04 + Math.sin(t * 1.4) * 0.02;
      const headTurn = Math.sin(t * 0.25) * 0.09 + Math.cos(t * 0.11) * 0.06;
      const headTilt = Math.sin(t * 0.18) * 0.035;
      animated.head = [
        animated.head[0] + headNod,
        animated.head[1] + headTurn,
        animated.head[2] + headTilt,
      ];
    }
    if (poseTo === "idle") {
      // Transfert naturel du poids du corps (déhanché de repos vivant)
      const weightShift = Math.sin(t * 0.32) * 0.025;
      if (animated.hips) {
        animated.hips = [animated.hips[0], animated.hips[1], weightShift];
      }
      if (animated.spine) {
        animated.spine = [animated.spine[0], animated.spine[1], -weightShift * 0.5];
      }
      if (animated.leftUpperArm) {
        animated.leftUpperArm = [
          animated.leftUpperArm[0],
          animated.leftUpperArm[1],
          animated.leftUpperArm[2] + armBob * 0.6,
        ];
      }
      if (animated.rightUpperArm) {
        animated.rightUpperArm = [
          animated.rightUpperArm[0],
          animated.rightUpperArm[1],
          animated.rightUpperArm[2] - armBob * 0.6,
        ];
      }
    }
    if (poseTo === "wave") {
      // Oscillation douce et contenue de la main droite près de l'épaule
      const flap = Math.sin(t * 7.5) * 0.18;
      if (animated.rightHand) {
        animated.rightHand = [
          animated.rightHand[0],
          animated.rightHand[1],
          animated.rightHand[2] + flap,
        ];
      }
    }
    if (poseTo === "crossArms") {
      // Respiration fière et légère oscillation vivante en pose bras croisés
      const chestPulse = Math.sin(t * 1.6) * 0.02;
      const headSway = Math.sin(t * 0.4) * 0.02;
      if (animated.chest) animated.chest = [animated.chest[0] + chestPulse, animated.chest[1], animated.chest[2]];
      if (animated.head) animated.head = [animated.head[0], animated.head[1] + headSway, animated.head[2]];
    }
    if (poseTo === "approve") {
      const nod = Math.sin(t * 5.5) * 0.05;
      if (animated.head) animated.head = [animated.head[0] + nod, animated.head[1], animated.head[2]];
      if (animated.neck) animated.neck = [animated.neck[0] + nod * 0.5, animated.neck[1], animated.neck[2]];
    }
    if (poseTo === "think") {
      const swayThink = Math.sin(t * 0.8) * 0.03;
      if (animated.head) animated.head = [animated.head[0], animated.head[1] + swayThink, animated.head[2] + swayThink * 0.5];
    }
    if (poseTo === "dance") {
      const beat = t * 4.8;
      const sway = Math.sin(beat) * 0.14;
      const bounce = Math.abs(Math.sin(beat * 2)) * 0.04;
      if (animated.hips) animated.hips = [animated.hips[0], sway * 0.6, sway];
      if (animated.leftUpperArm) {
        animated.leftUpperArm = [
          animated.leftUpperArm[0] + Math.sin(beat) * 0.22,
          animated.leftUpperArm[1],
          animated.leftUpperArm[2] + Math.cos(beat) * 0.18,
        ];
      }
      if (animated.rightUpperArm) {
        animated.rightUpperArm = [
          animated.rightUpperArm[0] - Math.sin(beat) * 0.22,
          animated.rightUpperArm[1],
          animated.rightUpperArm[2] + Math.cos(beat) * 0.18,
        ];
      }
      if (animated.head) {
        animated.head = [
          animated.head[0] + bounce,
          animated.head[1] + Math.sin(beat) * 0.1,
          animated.head[2] - Math.sin(beat) * 0.08,
        ];
      }
    }
    if (poseTo === "angry") {
      const pout = Math.sin(t * 6.2) * 0.08;
      const puff = Math.sin(t * 4.5) * 0.035;
      if (animated.head) animated.head = [animated.head[0] + puff * 0.5, animated.head[1] + pout, animated.head[2]];
      if (animated.chest) animated.chest = [animated.chest[0] + puff, animated.chest[1], animated.chest[2]];
    }
    if (poseTo === "walk") {
      // Cadence et phase de marche lissée (2.7 rad/s)
      const stepFreq = t * 2.7;
      const phaseL = stepFreq;
      const phaseR = stepFreq + Math.PI;

      // Foulée souple sinusoïdale
      const stride = Math.sin(stepFreq) * 0.10;
      // Balancement des bras en opposition rigoureuse (jambe gauche avance -> bras droit avance)
      const armSwing = Math.sin(stepFreq) * 0.14;

      // Rebond vertical naturel (bobbing à double fréquence, 2 montées/descentes par cycle de marche)
      const walkBounce = Math.sin(stepFreq * 2) * 0.012;
      const hipsYaw = -Math.sin(stepFreq) * 0.035;
      const hipsRoll = Math.sin(stepFreq) * 0.030;
      const chestYaw = Math.sin(stepFreq) * 0.025;

      // Flexion des genoux continue et lissée (courbe d'ordre supérieur évitant les à-coups du Math.max brutal)
      // Le genou fléchit pendant la phase de suspension (swing) et se détend doucement à la pose
      const leftKnee = 0.05 + Math.pow(Math.max(0, -Math.cos(phaseL)), 1.6) * 0.35;
      const rightKnee = 0.05 + Math.pow(Math.max(0, -Math.cos(phaseR)), 1.6) * 0.35;

      if (animated.leftUpperLeg) animated.leftUpperLeg = [stride, 0, animated.leftUpperLeg[2]];
      if (animated.rightUpperLeg) animated.rightUpperLeg = [-stride, 0, animated.rightUpperLeg[2]];
      if (animated.leftLowerLeg) animated.leftLowerLeg = [leftKnee, 0, 0];
      if (animated.rightLowerLeg) animated.rightLowerLeg = [rightKnee, 0, 0];

      // Déroulé souple des chevilles (talon au contact, propulsion à l'arrière)
      if (animated.leftFoot) animated.leftFoot = [-stride * 0.35, 0, 0];
      if (animated.rightFoot) animated.rightFoot = [stride * 0.35, 0, 0];

      // Bassin et torse : déhanchement organique et micro-rebond
      if (animated.hips) animated.hips = [0.02 + walkBounce, hipsYaw, hipsRoll];
      if (animated.spine) animated.spine = [animated.spine[0], -hipsYaw * 0.4, 0];
      if (animated.chest) animated.chest = [animated.chest[0], chestYaw, -hipsRoll * 0.4];

      // Balancement souple des bras le long du corps avec légère flexion d'amorti des coudes
      if (animated.leftUpperArm) {
        animated.leftUpperArm = [0, -armSwing, -1.25];
      }
      if (animated.rightUpperArm) {
        animated.rightUpperArm = [0, armSwing, 1.25];
      }
      if (animated.leftLowerArm) {
        // Coude gauche fléchit légèrement quand le bras avance
        animated.leftLowerArm = [0, 0, -0.18 - Math.max(0, armSwing) * 0.15];
      }
      if (animated.rightLowerArm) {
        // Coude droit fléchit légèrement quand le bras avance
        animated.rightLowerArm = [0, 0, -0.18 - Math.max(0, -armSwing) * 0.15];
      }

      // Tête stable compensant le roulis des hanches
      if (animated.head) animated.head = [animated.head[0], 0, -hipsRoll * 0.25];
    }

    // Important three-vrm 3.x :
    // setPose() → raw, puis vrm.update() écrase raw avec normalized (T-pose).
    // Il faut setNormalizedPose() (autoUpdateHumanBones=true).
    const poseObj = {};
    for (const name of BONE_NAMES) {
      const e = animated[name];
      if (!e) continue;
      _euler.set(e[0], e[1], e[2], "XYZ");
      _quat.setFromEuler(_euler);
      poseObj[name] = { rotation: [_quat.x, _quat.y, _quat.z, _quat.w] };
    }
    const h = vrm.humanoid;
    try {
      if (typeof h.setNormalizedPose === "function") {
        h.setNormalizedPose(poseObj);
      } else if (typeof h.setPose === "function") {
        h.setPose(poseObj);
      }
    } catch (_) {
      for (const name of Object.keys(poseObj)) {
        const node = bone(name);
        if (!node) continue;
        const r = poseObj[name].rotation;
        node.quaternion.set(r[0], r[1], r[2], r[3]);
      }
    }
  }

  function updatePoseSystem(t, dt) {
    if (!vrm?.humanoid) return;
    const now = performance.now();
    if (poseHoldUntil > 0 && now >= poseHoldUntil && poseTo !== poseReturnTo) {
      poseFrom = poseTo;
      poseTo = poseReturnTo || "idle";
      poseBlend = 0;
      poseHoldUntil = 0;
      setMood("serene");
    }
    // Blend ~0.35s
    if (poseBlend < 1) {
      poseBlend = Math.min(1, poseBlend + dt / 0.35);
    }
    const a = POSE_EULERS[poseFrom] || POSE_EULERS.idle;
    const b = POSE_EULERS[poseTo] || POSE_EULERS.idle;
    const smooth = poseBlend * poseBlend * (3 - 2 * poseBlend);
    applyBoneEulers(lerpEulerMap(a, b, smooth), t);
  }

  function frameVrm(v) {
    v.scene.updateMatrixWorld(true);

    if (framing === "bust") {
      camera.fov = 25;
      camera.updateProjectionMatrix();
      let focus = new THREE.Vector3(0, 1.4, 0);
      try {
        const head = v.humanoid?.getNormalizedBoneNode?.("head");
        const hips = v.humanoid?.getNormalizedBoneNode?.("hips");
        if (head) {
          focus = new THREE.Vector3();
          head.getWorldPosition(focus);
        } else if (hips) {
          hips.getWorldPosition(focus);
          focus.y += 0.5;
        }
      } catch (_) {}
      const dist = 1.15;
      camera.position.set(focus.x, focus.y + 0.02, focus.z + dist);
      camera.lookAt(focus.x, focus.y, focus.z);
      return;
    }

    camera.fov = 28;
    camera.updateProjectionMatrix();
    const box = new THREE.Box3().setFromObject(v.scene);
    const size = new THREE.Vector3();
    const center = new THREE.Vector3();
    box.getSize(size);
    box.getCenter(center);
    if (!Number.isFinite(size.y) || size.y < 0.2) {
      center.set(0, 0.9, 0);
      size.set(0.45, 1.45, 0.4);
    }
    const fovRad = (camera.fov * Math.PI) / 180;
    // Cadrage compact sans vide inutile : l'avatar remplit 95% de la hauteur du cadre
    const neededH = size.y * 1.05;
    const dist = neededH / (2 * Math.tan(fovRad / 2));
    const visibleH = 2.0 * dist * Math.tan(fovRad / 2);
    // Alignement parfait au sol : les pieds reposent sur le bord inférieur (barre des tâches)
    const lookY = box.min.y - 0.005 + (visibleH / 2);
    camera.position.set(center.x, lookY, center.z + dist);
    camera.lookAt(center.x, lookY, center.z);
  }

  function faceTheCamera(v) {
    targetHeadingY = 0;
    currentHeadingY = 0;
    v.scene.rotation.y = 0;
    v.scene.position.set(0, 0, 0);
    v.scene.updateMatrixWorld(true);
  }

  function setFraming(next) {
    framing = String(next || "").toLowerCase() === "bust" ? "bust" : "full";
    if (vrm) frameVrm(vrm);
  }

  function makeSolidColorTexture(hexColor) {
    const canvas = document.createElement("canvas");
    canvas.width = 4;
    canvas.height = 4;
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = hexColor;
    ctx.fillRect(0, 0, 4, 4);
    const tex = new THREE.CanvasTexture(canvas);
    tex.colorSpace = THREE.SRGBColorSpace;
    tex.needsUpdate = true;
    return tex;
  }

  function applyAndroidTheme(v) {
    if (!v?.scene) return;

    const cyanTexture = makeSolidColorTexture("#00f5d4");
    const cyanBrightTexture = makeSolidColorTexture("#80ffff");
    const darkSocketTexture = makeSolidColorTexture("#061320");

    v.scene.traverse((child) => {
      if (!child.isMesh) return;
      const materials = Array.isArray(child.material) ? child.material : [child.material];

      for (const m of materials) {
        const name = (m.name || "").toLowerCase();

        // 1. Optiques cybernétiques : Yeux néon cyan lumineux (comme l'illustration mascotte)
        if (name.includes("iris") || name.includes("eyeiris")) {
          if (m.color) m.color.setHex(0x00f5d4);
          if (m.shadeColor) m.shadeColor.setHex(0x00d4aa);
          m.map = cyanTexture;
          m.shadeMultiplyTexture = cyanTexture;
          if (m.emissive) {
            m.emissive.setHex(0x00f5d4);
            m.emissiveIntensity = 2.5;
          }
          m.needsUpdate = true;
        } else if (name.includes("eyehighlight")) {
          if (m.color) m.color.setHex(0xa0ffff);
          if (m.shadeColor) m.shadeColor.setHex(0x80ffff);
          m.map = cyanBrightTexture;
          m.shadeMultiplyTexture = cyanBrightTexture;
          m.needsUpdate = true;
        } else if (name.includes("eyewhite")) {
          // Fond d'optique sombre cybernétique
          if (m.color) m.color.setHex(0x061320);
          if (m.shadeColor) m.shadeColor.setHex(0x030a10);
          m.map = darkSocketTexture;
          m.shadeMultiplyTexture = darkSocketTexture;
          m.needsUpdate = true;
        } else if (name.includes("eyeline") || name.includes("eyelash")) {
          // Contour des yeux cyber bleu marine très sombre
          if (m.color) m.color.setHex(0x081220);
          if (m.shadeColor) m.shadeColor.setHex(0x040910);
          m.needsUpdate = true;
        } else if (name.includes("brow")) {
          if (m.color) m.color.setHex(0x182c48);
          m.needsUpdate = true;
        } else if (name.includes("mouth")) {
          if (m.color) m.color.setHex(0x121e30);
          m.needsUpdate = true;
        }
        // 2. Châssis métallique androïde : Corps et visage bleu nuit métallique avec halo néon cyan
        else if (name.includes("skin") || name.includes("body") || name.includes("face")) {
          if (m.color) m.color.setHex(0x28426b);
          if (m.shadeColor) m.shadeColor.setHex(0x121e33);
          // Bordure lumineuse néon cyan le long de la silhouette (rim lighting)
          if (m.parametricRimColor) m.parametricRimColor.setHex(0x00f0ff);
          if (m.rimLightingMix !== undefined) m.rimLightingMix = 0.70;
          if (m.parametricRimFresnelPower !== undefined) m.parametricRimFresnelPower = 2.0;
          m.needsUpdate = true;
        }
        // 3. Chevelure métallique : Bleu nuit profond / indigo avec reflets cyan
        else if (name.includes("hair")) {
          if (m.color) m.color.setHex(0x182846);
          if (m.shadeColor) m.shadeColor.setHex(0x0c1626);
          if (m.parametricRimColor) m.parametricRimColor.setHex(0x00e5ff);
          if (m.rimLightingMix !== undefined) m.rimLightingMix = 0.65;
          m.needsUpdate = true;
        }
      }
    });

    // 4. Proportions Chibi mignonnes : tête légèrement agrandie (+14%)
    try {
      const headBone = v.humanoid?.getNormalizedBoneNode?.("head");
      if (headBone) {
        headBone.scale.set(1.14, 1.14, 1.14);
      }
    } catch (_) {}
  }

  const loader = new GLTFLoader();
  loader.register((parser) => new VRMLoaderPlugin(parser));

  loader.load(
    modelUrl,
    (gltf) => {
      if (disposed) return;
      try {
        vrm = gltf.userData.vrm;
        if (!vrm) throw new Error("pas de VRM dans le fichier");

        VRMUtils.removeUnnecessaryVertices(gltf.scene);
        VRMUtils.combineSkeletons?.(gltf.scene);

        scene.add(vrm.scene);
        faceTheCamera(vrm);
        // Métamorphose Chibi Android Cyber Blue (Option 1)
        applyAndroidTheme(vrm);
        // Pose idle dès le chargement (sortir du T-pose)
        poseFrom = "idle";
        poseTo = "idle";
        poseBlend = 1;
        applyBoneEulers(POSE_EULERS.idle, 0);
        vrm.scene.updateMatrixWorld(true);
        frameVrm(vrm);
        setMood("serene");
        ready = true;
        resize();
        console.info("[vrm_pet] VRM ready", modelUrl, "pose idle, android theme applied");
      } catch (e) {
        loadError = String(e?.message || e);
        console.warn("[vrm_pet] setup", e);
      }
    },
    undefined,
    (err) => {
      loadError = String(err?.message || err);
      console.warn("[vrm_pet] load", err);
    }
  );

  function animate() {
    if (disposed) return;
    requestAnimationFrame(animate);
    const dt = Math.min(0.05, clock.getDelta());
    const t = clock.elapsedTime;
    if (vrm) {
      updatePoseSystem(t, dt);
      // Rotation fluide vers targetHeadingY
      const turnSpeed = 6.0;
      const diff = targetHeadingY - currentHeadingY;
      currentHeadingY += diff * Math.min(1, dt * turnSpeed);
      vrm.scene.rotation.y = currentHeadingY;

      // 1. Clignements naturels des yeux cyber
      if (t > nextBlinkTime) {
        blinkProgress += dt * 10.0;
        const blinkVal = Math.sin(Math.min(Math.PI, blinkProgress));
        try {
          vrm.expressionManager?.setValue("blink", blinkVal);
        } catch (_) {}
        if (blinkProgress >= Math.PI) {
          blinkProgress = 0;
          nextBlinkTime = t + 2.5 + Math.random() * 3.5;
        }
      }

      // 2. Micro-gestes autonomes vivants pendant les pauses sur la barre des tâches
      // Uniquement des postures calmes et contenues qui ne sortent jamais du cadre (bras croisés, réflexion, acquiescement)
      if (poseTo === "idle" && poseHoldUntil === 0) {
        if (t > nextIdleFidgetTime) {
          nextIdleFidgetTime = t + 9.0 + Math.random() * 9.0;
          const gestures = ["crossArms", "think", "approve"];
          const pick = gestures[Math.floor(Math.random() * gestures.length)];
          const holdMs = pick === "crossArms" ? 4000 : (pick === "think" ? 2800 : 2000);
          setPose(pick, holdMs);
        }
      }

      // Micro bob très subtil
      vrm.scene.position.y = -Math.abs(Math.sin(t * 1.25)) * (framing === "full" ? 0.002 : 0.005);
      if (vrm.lookAt) {
        try {
          vrm.lookAt.lookAt(camera.position);
        } catch (_) {}
      }
      if (performance.now() < talkingUntil) {
        mouthAmp = 0.3 + 0.5 * Math.abs(Math.sin(t * 13));
      } else {
        mouthAmp *= 0.85;
        if (mouthAmp < 0.02) mouthAmp = 0;
      }
      try {
        vrm.expressionManager?.setValue("aa", mouthAmp);
      } catch (_) {}
      try {
        vrm.update(dt);
      } catch (_) {}
    }
    renderer.render(scene, camera);
  }

  resize();
  window.addEventListener("resize", resize);
  animate();

  function flip() {
    if (!vrm) return;
    targetHeadingY = (targetHeadingY + Math.PI) % (Math.PI * 2);
    currentHeadingY = targetHeadingY;
    vrm.scene.rotation.y = currentHeadingY;
    vrm.scene.updateMatrixWorld(true);
    frameVrm(vrm);
  }

  return {
    get ready() {
      return ready;
    },
    get error() {
      return loadError;
    },
    setMood,
    setTalking,
    say,
    pulse,
    flip,
    setFraming,
    setPose,
    setHeading,
    get pose() {
      return poseTo;
    },
    get framing() {
      return framing;
    },
    destroy() {
      disposed = true;
      window.removeEventListener("resize", resize);
      try {
        renderer.dispose();
      } catch (_) {}
      if (renderer.domElement?.parentNode) {
        renderer.domElement.parentNode.removeChild(renderer.domElement);
      }
      vrm = null;
    },
  };
}

if (typeof window !== "undefined") {
  window.__createVrmPet = createVrmPet;
}
