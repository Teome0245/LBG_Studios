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

/** Euler locaux (rad) relatifs au T-pose — clés = bones humanoid normalisés. */
const POSE_EULERS = {
  idle: {
    leftUpperArm: [0.12, 0.05, 1.15],
    rightUpperArm: [0.12, -0.05, -1.15],
    leftLowerArm: [0.15, 0, 0.08],
    rightLowerArm: [0.15, 0, -0.08],
    leftHand: [0.1, 0, 0],
    rightHand: [0.1, 0, 0],
    spine: [0.02, 0, 0],
    chest: [0.03, 0, 0],
    neck: [0, 0, 0],
    head: [0, 0, 0],
    leftUpperLeg: [0, 0, 0.02],
    rightUpperLeg: [0, 0, -0.02],
  },
  /** Pointer vers la gauche de l'écran (bras droit du perso → côté +X world souvent). */
  pointLeft: {
    leftUpperArm: [0.1, 0.05, 1.1],
    rightUpperArm: [-0.85, -0.35, -0.25],
    leftLowerArm: [0.15, 0, 0.08],
    rightLowerArm: [-0.35, 0.1, -0.15],
    leftHand: [0.1, 0, 0],
    rightHand: [0.2, 0.3, 0],
    spine: [0.04, 0.12, 0],
    chest: [0.05, 0.1, 0],
    neck: [0, 0.15, 0],
    head: [0, 0.2, 0],
    leftUpperLeg: [0, 0, 0.02],
    rightUpperLeg: [0, 0, -0.02],
  },
  pointRight: {
    leftUpperArm: [-0.85, 0.35, 0.25],
    rightUpperArm: [0.1, -0.05, -1.1],
    leftLowerArm: [-0.35, -0.1, 0.15],
    rightLowerArm: [0.15, 0, -0.08],
    leftHand: [0.2, -0.3, 0],
    rightHand: [0.1, 0, 0],
    spine: [0.04, -0.12, 0],
    chest: [0.05, -0.1, 0],
    neck: [0, -0.15, 0],
    head: [0, -0.2, 0],
    leftUpperLeg: [0, 0, 0.02],
    rightUpperLeg: [0, 0, -0.02],
  },
  wave: {
    leftUpperArm: [0.12, 0.05, 1.15],
    rightUpperArm: [-1.1, -0.2, -0.15],
    leftLowerArm: [0.15, 0, 0.08],
    rightLowerArm: [-0.9, 0.2, 0],
    leftHand: [0.1, 0, 0],
    rightHand: [0, 0, 0.4],
    spine: [0.03, -0.08, 0],
    chest: [0.04, -0.06, 0],
    neck: [0, -0.08, 0],
    head: [0, -0.1, 0],
    leftUpperLeg: [0, 0, 0.02],
    rightUpperLeg: [0, 0, -0.02],
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

  /** Pose courante / cible pour blend */
  let poseFrom = "idle";
  let poseTo = "idle";
  let poseBlend = 1; // 0..1 vers poseTo
  let poseHoldUntil = 0;
  let poseReturnTo = "idle";

  const _euler = new THREE.Euler();
  const _quat = new THREE.Quaternion();

  function resize() {
    const w = Math.max(64, hostEl.clientWidth || 220);
    const h = Math.max(64, hostEl.clientHeight || 360);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h, false);
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
   * @param {string} name idle | pointLeft | pointRight | wave
   * @param {number} [holdMs] durée avant retour idle (0 = tenir)
   */
  function setPose(name, holdMs) {
    const n = String(name || "idle");
    const key =
      n === "point" || n === "point_left" || n === "pointLeft"
        ? "pointLeft"
        : n === "point_right" || n === "pointRight"
          ? "pointRight"
          : n === "wave" || n === "hello"
            ? "wave"
            : n === "idle"
              ? "idle"
              : POSE_EULERS[n]
                ? n
                : "idle";
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
      animated.head = [
        animated.head[0] + Math.sin(t * 0.45) * 0.03,
        animated.head[1] + Math.sin(t * 0.35) * 0.06,
        animated.head[2],
      ];
    }
    if (poseTo === "idle") {
      if (animated.leftUpperArm) {
        animated.leftUpperArm = [
          animated.leftUpperArm[0],
          animated.leftUpperArm[1],
          animated.leftUpperArm[2] + armBob,
        ];
      }
      if (animated.rightUpperArm) {
        animated.rightUpperArm = [
          animated.rightUpperArm[0],
          animated.rightUpperArm[1],
          animated.rightUpperArm[2] - armBob * 0.9,
        ];
      }
    }
    if (poseTo === "wave") {
      const flap = Math.sin(t * 9) * 0.35;
      if (animated.rightLowerArm) {
        animated.rightLowerArm = [
          animated.rightLowerArm[0] + flap,
          animated.rightLowerArm[1],
          animated.rightLowerArm[2],
        ];
      }
    }

    const poseObj = {};
    for (const name of BONE_NAMES) {
      const e = animated[name];
      if (!e) continue;
      _euler.set(e[0], e[1], e[2], "XYZ");
      _quat.setFromEuler(_euler);
      poseObj[name] = { rotation: [_quat.x, _quat.y, _quat.z, _quat.w] };
    }
    try {
      vrm.humanoid.setPose(poseObj);
    } catch (_) {
      // Fallback : écrire sur les bones normalisés
      try {
        vrm.humanoid.resetPose();
      } catch (_) {}
      for (const name of Object.keys(poseObj)) {
        const node = bone(name);
        if (!node) continue;
        node.quaternion.set(
          poseObj[name].rotation[0],
          poseObj[name].rotation[1],
          poseObj[name].rotation[2],
          poseObj[name].rotation[3]
        );
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

    camera.fov = 30;
    camera.updateProjectionMatrix();
    const box = new THREE.Box3().setFromObject(v.scene);
    const size = new THREE.Vector3();
    const center = new THREE.Vector3();
    box.getSize(size);
    box.getCenter(center);
    if (!Number.isFinite(size.y) || size.y < 0.2) {
      center.set(0, 0.9, 0);
      size.set(0.5, 1.7, 0.4);
    }
    const lookY = box.min.y + size.y * 0.52;
    const fovRad = (camera.fov * Math.PI) / 180;
    const fitH = (size.y * 0.58) / Math.tan(fovRad / 2);
    const fitW = ((size.x * 0.55) / Math.tan(fovRad / 2)) / Math.max(0.2, camera.aspect);
    const dist = Math.max(2.0, fitH, fitW) * 1.08;
    camera.position.set(center.x, lookY, center.z + dist);
    camera.lookAt(center.x, lookY, center.z);
  }

  function faceTheCamera(v) {
    VRMUtils.rotateVRM0?.(v);
    v.scene.rotation.y = 0;
    v.scene.position.set(0, 0, 0);
    v.scene.updateMatrixWorld(true);
  }

  function setFraming(next) {
    framing = String(next || "").toLowerCase() === "bust" ? "bust" : "full";
    if (vrm) frameVrm(vrm);
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
        console.info("[vrm_pet] VRM ready", modelUrl, "pose idle");
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
      // Micro bob global
      vrm.scene.position.y = Math.sin(t * 1.25) * (framing === "full" ? 0.003 : 0.006);
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
    vrm.scene.rotation.y += Math.PI;
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
