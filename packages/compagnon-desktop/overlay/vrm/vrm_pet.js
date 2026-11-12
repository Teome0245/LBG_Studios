/**
 * Desktop pet VRM — three + @pixiv/three-vrm (bundlé).
 * Idle (respiration / bras) + poses guide (pointer / saluer).
 */
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { VRMLoaderPlugin, VRMUtils } from "@pixiv/three-vrm";
import { VRMAnimationLoaderPlugin, createVRMAnimationClip } from "@pixiv/three-vrm-animation";

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
        } catch (_) { }
      },
    });
  } catch (_) { }
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
  /** Focus / Scan de code : corps légèrement penché en avant, main gauche relevée près du buste (tenant un datapad), tête attentive qui scrute l'écran. */
  focus: {
    leftUpperArm: [0.35, 0.25, -1.05],
    leftLowerArm: [0.10, 0.20, -1.45],
    leftHand: [0.15, -0.10, 0.30],
    rightUpperArm: [0.15, 0, 1.25],
    rightLowerArm: [0, 0, 0.15],
    rightHand: [0, 0, 0],
    spine: [0.08, 0.02, 0],
    chest: [0.10, 0.02, 0],
    neck: [-0.05, 0.04, 0.02],
    head: [-0.08, 0.05, 0.03],
    leftUpperLeg: [0, 0, -0.02],
    rightUpperLeg: [0, 0, 0.02],
  },
  /** Victoire / Célébration : deux bras levés en V triomphal, buste relevé et tête fière. */
  victory: {
    leftUpperArm: [0.10, 0.10, -2.55],
    rightUpperArm: [0.10, -0.10, 2.55],
    leftLowerArm: [0, 0, -0.35],
    rightLowerArm: [0, 0, -0.35],
    leftHand: [0.20, 0, 0],
    rightHand: [0.20, 0, 0],
    spine: [-0.04, 0, 0],
    chest: [-0.06, 0, 0],
    neck: [0.06, 0, 0],
    head: [0.08, 0, 0],
    leftUpperLeg: [0, 0, -0.04],
    rightUpperLeg: [0, 0, 0.04],
  },
  /** Finger Heart (geste coréen K-Pop / anime idol : pouce et index croisés en mini cœur au niveau du haut du torse/menton, tête penchée espiègle, main gauche sur la hanche, grands yeux vifs et sourire pétillant). */
  fingerHeart: {
    // Épaule et bras droit : coude maintenu près du flanc/torse, avant-bras levé vers le haut du buste/menton
    rightShoulder: [0.02, 0, 0.04],
    rightUpperArm: [0.38, 0.18, 1.05],
    rightLowerArm: [0.10, 0.25, -1.80],
    rightHand: [0.18, -0.15, 0.22],
    // Doigts articulés de la main droite : pouce et index croisés en mini cœur 🫰 vers la caméra
    rightThumbMetacarpal: [0.12, 0.15, -0.08],
    rightThumbProximal: [0.28, 0.28, -0.18],
    rightThumbDistal: [0.10, 0.12, 0.05],
    rightIndexProximal: [0.45, 0.05, 0.05],
    rightIndexIntermediate: [0.55, 0.02, 0.02],
    rightIndexDistal: [0.25, 0, 0],
    // Autres doigts repliés dans la paume
    rightMiddleProximal: [1.35, 0, -0.05],
    rightMiddleIntermediate: [1.40, 0, 0],
    rightMiddleDistal: [0.60, 0, 0],
    rightRingProximal: [1.35, 0, -0.05],
    rightRingIntermediate: [1.40, 0, 0],
    rightRingDistal: [0.60, 0, 0],
    rightLittleProximal: [1.35, 0, -0.05],
    rightLittleIntermediate: [1.40, 0, 0],
    rightLittleDistal: [0.60, 0, 0],
    // Bras gauche : main posée avec style sur la hanche (silhouette idol)
    leftUpperArm: [0.18, -0.15, -0.92],
    leftLowerArm: [0.08, 0.15, -1.05],
    leftHand: [0.10, 0, -0.18],
    leftThumbProximal: [0.35, 0, 0],
    leftIndexProximal: [0.45, 0, 0],
    leftMiddleProximal: [0.55, 0, 0],
    leftRingProximal: [0.55, 0, 0],
    leftLittleProximal: [0.55, 0, 0],
    // Hanches en appui déhanché (contrapposto pop), buste cambré et tête inclinée vers la main
    hips: [0, 0.07, -0.05],
    spine: [0.02, -0.03, 0.03],
    chest: [0.04, -0.02, 0.02],
    neck: [-0.03, -0.04, 0.12],
    head: [-0.05, -0.06, 0.18],
    leftUpperLeg: [0, 0, -0.02],
    rightUpperLeg: [0, 0, 0.04],
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
  /** Cyber Groove 128 BPM : posture live scénique avec micro en main et déhanché fluide */
  cyberGroove: {
    rightShoulder: [0.06, 0.04, -0.06],
    rightUpperArm: [0.32, 0.35, 0.85],
    rightLowerArm: [-0.22, -0.16, -2.10],
    rightHand: [0.18, -0.15, 0.32],
    // Doigts fermés sur le manche du micro
    rightThumbProximal: [0.55, 0.30, 0],
    rightThumbDistal: [0.45, 0, 0],
    rightIndexProximal: [1.40, 0, 0],
    rightIndexIntermediate: [1.30, 0, 0],
    rightMiddleProximal: [1.45, 0, 0],
    rightMiddleIntermediate: [1.35, 0, 0],
    rightRingProximal: [1.45, 0, 0],
    rightRingIntermediate: [1.35, 0, 0],
    rightLittleProximal: [1.40, 0, 0],
    rightLittleIntermediate: [1.25, 0, 0],
    // Bras gauche diva sur la hanche avec grâce
    leftShoulder: [0.02, -0.02, 0.02],
    leftUpperArm: [0.12, 0.10, -1.15],
    leftLowerArm: [0.18, 0.12, -1.25],
    leftHand: [-0.10, 0.08, -0.15],
    leftThumbProximal: [0.25, 0.10, 0],
    leftIndexProximal: [0.30, 0, 0],
    leftMiddleProximal: [0.35, 0, 0],
    leftRingProximal: [0.35, 0, 0],
    leftLittleProximal: [0.30, 0, 0],
    // Dos cambré féminin et poitrine projetée fière
    hips: [-0.10, 0.14, -0.10],
    spine: [0.06, -0.08, 0.08],
    chest: [0.14, -0.06, 0.06],
    neck: [-0.08, 0.04, 0.04],
    head: [-0.22, -0.06, 0.08],
    // Stance de concert ouverte en éventail (pieds écartés et genoux fléchis)
    leftUpperLeg: [-0.24, -0.15, -0.26],
    rightUpperLeg: [0.06, 0.15, 0.26],
    leftLowerLeg: [0.55, 0, 0],
    rightLowerLeg: [0.25, 0, 0],
    leftFoot: [-0.12, -0.25, 0],
    rightFoot: [0.04, 0.25, 0],
  },
  /** Aeysa Singing : Performance subtile & intimiste de chanteuse virtuelle cyber (@aeysamusic) */
  aeysaSinging: {
    rightShoulder: [0.05, 0.03, -0.05],
    rightUpperArm: [0.32, 0.35, 0.85],
    rightLowerArm: [-0.22, -0.16, -2.12],
    rightHand: [0.18, -0.14, 0.32],
    rightThumbProximal: [0.55, 0.30, 0],
    rightThumbDistal: [0.45, 0, 0],
    rightIndexProximal: [1.40, 0, 0],
    rightIndexIntermediate: [1.30, 0, 0],
    rightMiddleProximal: [1.45, 0, 0],
    rightMiddleIntermediate: [1.35, 0, 0],
    rightRingProximal: [1.45, 0, 0],
    rightRingIntermediate: [1.35, 0, 0],
    rightLittleProximal: [1.40, 0, 0],
    rightLittleIntermediate: [1.25, 0, 0],
    leftShoulder: [0.03, 0.01, 0.02],
    leftUpperArm: [0.24, 0.12, -0.85],
    leftLowerArm: [0.18, 0.15, -1.05],
    leftHand: [0.12, 0.08, 0.04],
    leftThumbProximal: [0.25, 0.10, 0],
    leftIndexProximal: [0.22, 0, 0],
    leftMiddleProximal: [0.25, 0, 0],
    leftRingProximal: [0.25, 0, 0],
    leftLittleProximal: [0.20, 0, 0],
    hips: [-0.06, 0.08, -0.05],
    spine: [0.04, -0.05, 0.04],
    chest: [0.08, -0.03, 0.03],
    neck: [-0.04, 0.02, 0.02],
    head: [-0.08, -0.02, 0.03],
    leftUpperLeg: [-0.12, -0.08, -0.18],
    rightUpperLeg: [0.04, 0.08, 0.18],
    leftLowerLeg: [0.25, 0, 0],
    rightLowerLeg: [0.20, 0, 0],
    leftFoot: [0.02, -0.18, 0],
    rightFoot: [0.02, 0.18, 0],
  },
  /** Pointer vers la gauche (geste doux et courtois de la main, coude souple vers l'avant). */
  pointLeft: {
    leftUpperArm: [0, 0, -1.28],
    rightUpperArm: [0.25, 0.20, 0.95],
    leftLowerArm: [0, 0, 0],
    rightLowerArm: [0.10, 0.15, -1.25],
    leftHand: [0, 0, 0],
    rightHand: [0, 0, 0.12],
    spine: [0.02, 0.08, 0],
    chest: [0.03, 0.08, 0],
    neck: [0, 0.12, 0],
    head: [0, 0.14, 0],
    leftUpperLeg: [0, 0, -0.02],
    rightUpperLeg: [0, 0, 0.02],
  },
  /** Pointer vers la droite (geste doux et courtois de la main, coude souple vers l'avant). */
  pointRight: {
    leftUpperArm: [0.25, -0.20, -0.95],
    rightUpperArm: [0, 0, 1.28],
    leftLowerArm: [0.10, -0.15, -1.25],
    rightLowerArm: [0, 0, 0],
    leftHand: [0, 0, -0.12],
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
    rightLowerArm: [0, 0, -1.35],
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
    rightLowerArm: [0, 0, -0.15],
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
    leftUpperArm: [0.20, 0.15, -1.05],
    rightUpperArm: [0.20, -0.15, 1.05],
    leftLowerArm: [0, 0, -1.15],
    rightLowerArm: [0, 0, -1.15],
    leftHand: [0, 0, 0],
    rightHand: [0, 0, 0],
    hips: [0, 0, 0],
    spine: [0.02, 0, 0],
    chest: [0.03, 0, 0],
    neck: [0, 0, 0],
    head: [0, 0, 0],
    leftUpperLeg: [0, 0, -0.03],
    rightUpperLeg: [0, 0, 0.03],
    leftLowerLeg: [0.05, 0, 0],
    rightLowerLeg: [0.05, 0, 0],
  },
  /** Danse Samba / Salsa latino énergique avec déhanché en huit. */
  samba: {
    leftUpperArm: [0.35, 0.20, -1.35],
    rightUpperArm: [0.15, -0.20, 0.85],
    leftLowerArm: [0, 0, -1.40],
    rightLowerArm: [0, 0, -0.80],
    leftHand: [0, 0, 0.2],
    rightHand: [0, 0, -0.2],
    hips: [0, 0.08, 0.05],
    spine: [0.04, -0.04, -0.03],
    chest: [0.05, -0.03, -0.02],
    neck: [0, 0, 0],
    head: [0.04, 0.05, -0.04],
    leftUpperLeg: [0, 0, -0.06],
    rightUpperLeg: [0, 0, 0.06],
    leftLowerLeg: [0.08, 0, 0],
    rightLowerLeg: [0.08, 0, 0],
  },
  /** Danse Hip-Hop / B-Boy street bounce avec attitude penchée et coudes ouverts. */
  hiphop: {
    leftUpperArm: [0.45, 0.30, -1.25],
    rightUpperArm: [0.45, -0.30, 1.25],
    leftLowerArm: [0, 0, -1.50],
    rightLowerArm: [0, 0, -1.50],
    leftHand: [0.1, 0, 0.2],
    rightHand: [0.1, 0, -0.2],
    hips: [0.06, 0, 0],
    spine: [0.14, 0, 0],
    chest: [0.10, 0, 0],
    neck: [0.08, 0, 0],
    head: [0.12, 0, 0],
    leftUpperLeg: [-0.08, 0.1, -0.10],
    rightUpperLeg: [-0.08, -0.1, 0.10],
    leftLowerLeg: [0.16, 0, 0],
    rightLowerLeg: [0.16, 0, 0],
  },
  /** Danse Wave / Robot avec ondulation fluide et arrêts robotiques. */
  robot: {
    leftUpperArm: [0.10, 0, -1.50],
    rightUpperArm: [0.10, 0, 0.60],
    leftLowerArm: [0, 0, -0.20],
    rightLowerArm: [0, 0, -1.30],
    leftHand: [0, 0, 0.3],
    rightHand: [0, 0, 0],
    hips: [0, 0, 0],
    spine: [0.02, 0, 0],
    chest: [0.04, 0, 0],
    neck: [0, 0, 0],
    head: [0, 0.08, 0],
    leftUpperLeg: [0, 0, -0.02],
    rightUpperLeg: [0, 0, 0.02],
    leftLowerLeg: [0.02, 0, 0],
    rightLowerLeg: [0.02, 0, 0],
  },
  /** Danse Disco / Twist Fever avec pose iconique bras vers le ciel. */
  disco: {
    leftUpperArm: [0.15, 0.25, -0.85],
    rightUpperArm: [-0.55, -0.20, 2.45],
    leftLowerArm: [0, 0, -1.65],
    rightLowerArm: [0, 0, -0.25],
    leftHand: [0, 0, 0],
    rightHand: [0, 0, -0.2],
    hips: [0, 0.12, 0.06],
    spine: [0.04, -0.10, -0.04],
    chest: [0.06, -0.08, -0.03],
    neck: [-0.04, 0.06, 0],
    head: [-0.06, 0.10, 0.04],
    leftUpperLeg: [0, 0.05, -0.04],
    rightUpperLeg: [0, -0.05, 0.04],
    leftLowerLeg: [0.06, 0, 0],
    rightLowerLeg: [0.06, 0, 0],
  },
  /** Pirouette 360° gracieuse (rotation complète avec bras déployés). */
  spin: {
    leftUpperArm: [0.10, 0, -0.85],
    rightUpperArm: [0.10, 0, 0.85],
    leftLowerArm: [0, 0, -0.45],
    rightLowerArm: [0, 0, -0.45],
    leftHand: [0, 0, 0.1],
    rightHand: [0, 0, -0.1],
    hips: [0, 0, 0],
    spine: [0.04, 0, 0],
    chest: [0.06, 0, 0],
    neck: [0, 0, 0],
    head: [0.02, 0, 0],
    leftUpperLeg: [0, 0, -0.02],
    rightUpperLeg: [0, 0, 0.02],
    leftLowerLeg: [0.04, 0, 0],
    rightLowerLeg: [0.04, 0, 0],
  },
  /** Saut de joie / célébration chibi avec bras levés en V triomphal. */
  jump: {
    leftUpperArm: [0.20, 0.10, -2.35],
    rightUpperArm: [0.20, -0.10, 2.35],
    leftLowerArm: [0, 0, -0.55],
    rightLowerArm: [0, 0, -0.55],
    leftHand: [0, 0, 0.15],
    rightHand: [0, 0, -0.15],
    hips: [0, 0, 0],
    spine: [0.03, 0, 0],
    chest: [0.06, 0, 0],
    neck: [0.04, 0, 0],
    head: [0.06, 0, 0],
    leftUpperLeg: [0, 0, -0.04],
    rightUpperLeg: [0, 0, 0.04],
    leftLowerLeg: [0.08, 0, 0],
    rightLowerLeg: [0.08, 0, 0],
  },
  /** Étirement relaxant vers le haut. */
  stretch: {
    leftUpperArm: [0.05, 0, -2.60],
    rightUpperArm: [0.05, 0, 2.60],
    leftLowerArm: [0, 0, -0.15],
    rightLowerArm: [0, 0, -0.15],
    leftHand: [0, 0, 0],
    rightHand: [0, 0, 0],
    hips: [0, 0, 0],
    spine: [0.08, 0, 0],
    chest: [0.12, 0, 0],
    neck: [0.08, 0, 0],
    head: [0.10, 0, 0],
    leftUpperLeg: [0, 0, -0.02],
    rightUpperLeg: [0, 0, 0.02],
  },
  /** Colère / bouderie expressive : poings sur les hanches, torse gonflé. */
  angry: {
    leftUpperArm: [0.18, 0.4, -0.75],
    rightUpperArm: [0.18, -0.4, 0.75],
    leftLowerArm: [0, 0, -1.55],
    rightLowerArm: [0, 0, -1.55],
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
    rightLowerArm: [0, 0, -0.20],
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
  // Doigts articulés & épaules pour gestuelle expressive
  "rightShoulder",
  "leftShoulder",
  "rightThumbMetacarpal",
  "rightThumbProximal",
  "rightThumbDistal",
  "rightIndexProximal",
  "rightIndexIntermediate",
  "rightIndexDistal",
  "rightMiddleProximal",
  "rightMiddleIntermediate",
  "rightMiddleDistal",
  "rightRingProximal",
  "rightRingIntermediate",
  "rightRingDistal",
  "rightLittleProximal",
  "rightLittleIntermediate",
  "rightLittleDistal",
  "leftThumbMetacarpal",
  "leftThumbProximal",
  "leftThumbDistal",
  "leftIndexProximal",
  "leftIndexIntermediate",
  "leftIndexDistal",
  "leftMiddleProximal",
  "leftMiddleIntermediate",
  "leftMiddleDistal",
  "leftRingProximal",
  "leftRingIntermediate",
  "leftRingDistal",
  "leftLittleProximal",
  "leftLittleIntermediate",
  "leftLittleDistal",
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
  /** bust = gros plan buste & tête · full = corps entier */
  let framing = String(opts.framing || opts.vrmFraming || "bust").toLowerCase() === "bust"
    ? "bust"
    : "full";
  let baseFraming = framing;
  let isDanceFraming = false;
  const clock = new THREE.Clock();
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(framing === "full" ? 28 : 24, 1, 0.05, 40);

  const targetCamPos = new THREE.Vector3(0, 0.9, 2.0);
  const currentCamPos = new THREE.Vector3(0, 0.9, 2.0);
  const targetLookAt = new THREE.Vector3(0, 0.9, 0);
  const currentLookAt = new THREE.Vector3(0, 0.9, 0);
  let targetFov = framing === "full" ? 28 : 24;
  let currentFov = targetFov;
  let cameraInitialized = false;

  // Mouse tracking interactif (suivi du regard vers la souris)
  const mouseNdc = new THREE.Vector2(0, 0);
  const targetMouseNdc = new THREE.Vector2(0, 0);
  let mouseActive = false;
  let mouseActiveTimer = null;
  window.addEventListener("mousemove", (e) => {
    targetMouseNdc.x = (e.clientX / Math.max(1, window.innerWidth)) * 2 - 1;
    targetMouseNdc.y = -(e.clientY / Math.max(1, window.innerHeight)) * 2 + 1;
    mouseActive = true;
    if (mouseActiveTimer) clearTimeout(mouseActiveTimer);
    mouseActiveTimer = setTimeout(() => {
      mouseActive = false;
    }, 3500);
  });
  window.addEventListener("mouseleave", () => {
    mouseActive = false;
  });

  const renderer = new THREE.WebGLRenderer({
    alpha: true,
    antialias: true,
    premultipliedAlpha: false,
  });
  renderer.setClearColor(0x000000, 0);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  hostEl.appendChild(renderer.domElement);

  scene.add(new THREE.HemisphereLight(0xffffff, 0x223355, 0.85));
  const key = new THREE.DirectionalLight(0xe0f7fa, 1.3);
  key.position.set(0.8, 1.8, 2.2);
  scene.add(key);
  scene.add(new THREE.DirectionalLight(0x99e9f2, 0.4).translateX(-2).translateY(1));

  // Éclairage de concert Cyberpunk à contre-jour (Rim Lights Cyan & Magenta)
  const metallicRimLight = new THREE.DirectionalLight(0x00f5d4, 1.35);
  metallicRimLight.position.set(-1.5, 1.8, -1.8);
  scene.add(metallicRimLight);

  const magentaRimLight = new THREE.DirectionalLight(0xd946ef, 1.15);
  magentaRimLight.position.set(1.5, 1.8, -1.8);
  scene.add(magentaRimLight);

  // Halo cybernétique doux (sublime le détachement de l'avatar du fond d'écran)
  const cyberHaloLight = new THREE.DirectionalLight(0x00f5d4, 0.65);
  cyberHaloLight.position.set(0, -1.0, -1.8);
  scene.add(cyberHaloLight);

  // Projecteurs de scène dynamiques pour le ShowRoutineManager (ambiance spectacle / iStripper)
  const stageLightCyan = new THREE.PointLight(0x00f5d4, 0.8, 4.0);
  stageLightCyan.position.set(-1.2, 1.2, 1.2);
  scene.add(stageLightCyan);

  const stageLightMagenta = new THREE.PointLight(0xff007f, 0.8, 4.0);
  stageLightMagenta.position.set(1.2, 1.2, 1.2);
  scene.add(stageLightMagenta);

  /** @type {import('@pixiv/three-vrm').VRM | null} */
  let vrm = null;
  let talkingUntil = 0;
  let mouthAmp = 0;
  let activeVisemes = [];
  let visemesStartTime = 0;
  const VISEME_KEYS = ["aa", "ih", "ou", "ee", "oh"];
  const currentVisemeWeights = { aa: 0, ih: 0, ou: 0, ee: 0, oh: 0 };
  let ready = false;
  let disposed = false;
  let animId = null;
  const createdTextures = [];
  let loadError = null;
  let targetHeadingY = 0;
  let currentHeadingY = 0;
  let nextBlinkTime = 2.0;
  let blinkProgress = 0;
  let nextIdleFidgetTime = 6.0;
  // Déclenchement autonome de la petite danse fingerHeart 1 à 2 fois par heure (toutes les 25 à 35 min)
  // 1er déclenchement test à 25s pour vérification immédiate après le démarrage
  let nextHeartPoseTime = 25.0;
  let wasInHeartPose = false;
  let wasInCyberGroove = false;
  let walkYOffset = 0;
  let spinAngle = 0;

  // Particules néon cyber-cœurs roses émis lors du fingerHeart
  function createHeartTexture() {
    const canvas = document.createElement("canvas");
    canvas.width = 64;
    canvas.height = 64;
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, 64, 64);
    ctx.fillStyle = "#ff2a8d";
    ctx.shadowColor = "#ff2a8d";
    ctx.shadowBlur = 10;
    ctx.beginPath();
    ctx.moveTo(32, 22);
    ctx.bezierCurveTo(32, 16, 22, 10, 14, 18);
    ctx.bezierCurveTo(4, 28, 12, 42, 32, 54);
    ctx.bezierCurveTo(52, 42, 60, 28, 50, 18);
    ctx.bezierCurveTo(42, 10, 32, 16, 32, 22);
    ctx.fill();
    const tex = new THREE.CanvasTexture(canvas);
    tex.colorSpace = THREE.SRGBColorSpace;
    createdTextures.push(tex);
    return tex;
  }

  const heartMat = new THREE.SpriteMaterial({
    map: createHeartTexture(),
    transparent: true,
    opacity: 0,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });
  const heartSprites = [
    new THREE.Sprite(heartMat),
    new THREE.Sprite(heartMat),
    new THREE.Sprite(heartMat),
  ];
  for (const s of heartSprites) {
    s.scale.set(0.065, 0.065, 1);
    s.visible = false;
    scene.add(s);
  }

  // --- Micro 3D de scène pour Cyber Groove ---
  const cyberMicGroup = new THREE.Group();
  cyberMicGroup.name = "cyberMicGroup";
  cyberMicGroup.visible = false;

  // Manche cylindrique noir graphite avec grip
  const micHandleGeo = new THREE.CylinderGeometry(0.016, 0.012, 0.20, 16);
  const micHandleMat = new THREE.MeshStandardMaterial({
    color: 0x11161d,
    metalness: 0.85,
    roughness: 0.30,
  });
  const micHandle = new THREE.Mesh(micHandleGeo, micHandleMat);
  cyberMicGroup.add(micHandle);

  // Tête sphérique chrome métallisée avec grille
  const micHeadGeo = new THREE.SphereGeometry(0.028, 16, 16);
  micHeadGeo.scale(1.0, 1.25, 1.0);
  const micHeadMat = new THREE.MeshStandardMaterial({
    color: 0x4a5568,
    metalness: 0.95,
    roughness: 0.15,
  });
  const micHead = new THREE.Mesh(micHeadGeo, micHeadMat);
  micHead.position.y = 0.11;
  cyberMicGroup.add(micHead);

  // Double anneau néon emissive cyan / magenta éclatant
  const ringGeo = new THREE.TorusGeometry(0.020, 0.004, 12, 24);
  const ringMat = new THREE.MeshBasicMaterial({
    color: 0x00ffff,
  });
  const ringMesh = new THREE.Mesh(ringGeo, ringMat);
  ringMesh.rotation.x = Math.PI / 2;
  ringMesh.position.y = 0.088;
  cyberMicGroup.add(ringMesh);

  const ringGeo2 = new THREE.TorusGeometry(0.016, 0.003, 12, 24);
  const ringMat2 = new THREE.MeshBasicMaterial({
    color: 0xff0088,
  });
  const ringMesh2 = new THREE.Mesh(ringGeo2, ringMat2);
  ringMesh2.rotation.x = Math.PI / 2;
  ringMesh2.position.y = -0.075;
  cyberMicGroup.add(ringMesh2);

  function ensureMicAttached(v) {
    if (!v?.humanoid) return;
    try {
      const rhNode = v.humanoid.getNormalizedBoneNode?.("rightHand") || v.humanoid.getRawBoneNode?.("rightHand");
      if (rhNode && cyberMicGroup.parent !== rhNode) {
        if (cyberMicGroup.parent) cyberMicGroup.parent.remove(cyberMicGroup);
        rhNode.add(cyberMicGroup);
        // Position locale dans la main droite :
        // La sphère du micro se dresse vers le haut et l'arrière pour arriver pile devant les lèvres
        cyberMicGroup.position.set(0.018, 0.045, 0.025);
        cyberMicGroup.rotation.set(0.25, 0.15, 0.60);
        cyberMicGroup.scale.set(1.35, 1.35, 1.35);
      }
    } catch (_) { }
  }

  /** Pose courante / cible pour blend */
  let poseFrom = "idle";
  let poseTo = "idle";
  let poseBlend = 1; // 0..1 vers poseTo
  let poseHoldUntil = 0;
  let poseReturnTo = "idle";

  /** Système d'animation VRMA officiel (@pixiv/three-vrm-animation) */
  let mixer = null;
  let activeVrmaAction = null;
  let activeVrmaName = null;
  const vrmaClips = new Map();
  const vrmaLoading = new Map();

  const VRMA_CATALOG = {
  "180turnwbriefcase": "180 Turn W_ Briefcase.vrma",
  "180 turn w_ briefcase": "180 Turn W_ Briefcase.vrma",
  "airsquatbentarms": "Air Squat Bent Arms.vrma",
  "air squat bent arms": "Air Squat Bent Arms.vrma",
  "armshiphopdance": "Arms Hip Hop Dance.vrma",
  "arms hip hop dance": "Arms Hip Hop Dance.vrma",
  "backsquat": "Back Squat.vrma",
  "back squat": "Back Squat.vrma",
  "backsquat2": "Back Squat2.vrma",
  "back squat2": "Back Squat2.vrma",
  "backflip": "Backflip.vrma",
  "bashful": "Bashful.vrma",
  "batterondeck": "Batter On Deck.vrma",
  "batter on deck": "Batter On Deck.vrma",
  "bellydancing": "Bellydancing.vrma",
  "breakdanceready": "Breakdance Ready.vrma",
  "breakdance ready": "Breakdance Ready.vrma",
  "calling": "Calling.vrma",
  "cancan": "Can Can.vrma",
  "can can": "Can Can.vrma",
  "capoeirapackpiratebyp.konstantinov": "Capoeira_Pack_Pirate By P. Konstantinov.vrma",
  "capoeira_pack_pirate by p. konstantinov": "Capoeira_Pack_Pirate By P. Konstantinov.vrma",
  "capoeirapackarmadatoesquiva": "Capoeira_Pack_armada to esquiva.vrma",
  "capoeira_pack_armada to esquiva": "Capoeira_Pack_armada to esquiva.vrma",
  "capoeirapackarmada": "Capoeira_Pack_armada.vrma",
  "capoeira_pack_armada": "Capoeira_Pack_armada.vrma",
  "capoeirapackautorole": "Capoeira_Pack_au to role.vrma",
  "capoeira_pack_au to role": "Capoeira_Pack_au to role.vrma",
  "capoeirapackau": "Capoeira_Pack_au.vrma",
  "capoeira_pack_au": "Capoeira_Pack_au.vrma",
  "capoeirapackbencao": "Capoeira_Pack_bencao.vrma",
  "capoeira_pack_bencao": "Capoeira_Pack_bencao.vrma",
  "capoeirapackcapoeira(2)": "Capoeira_Pack_capoeira (2).vrma",
  "capoeira_pack_capoeira (2)": "Capoeira_Pack_capoeira (2).vrma",
  "capoeirapackcapoeira(3)": "Capoeira_Pack_capoeira (3).vrma",
  "capoeira_pack_capoeira (3)": "Capoeira_Pack_capoeira (3).vrma",
  "capoeirapackcapoeira": "Capoeira_Pack_capoeira.vrma",
  "capoeira_pack_capoeira": "Capoeira_Pack_capoeira.vrma",
  "capoeirapackchapa2": "Capoeira_Pack_chapa 2.vrma",
  "capoeira_pack_chapa 2": "Capoeira_Pack_chapa 2.vrma",
  "capoeirapackchapagiratoria2": "Capoeira_Pack_chapa giratoria 2.vrma",
  "capoeira_pack_chapa giratoria 2": "Capoeira_Pack_chapa giratoria 2.vrma",
  "capoeirapackchapagiratoria": "Capoeira_Pack_chapa-giratoria.vrma",
  "capoeira_pack_chapa-giratoria": "Capoeira_Pack_chapa-giratoria.vrma",
  "capoeirapackchapaeudecouro": "Capoeira_Pack_chapaeu de couro.vrma",
  "capoeira_pack_chapaeu de couro": "Capoeira_Pack_chapaeu de couro.vrma",
  "capoeirapackesquiva1": "Capoeira_Pack_esquiva 1.vrma",
  "capoeira_pack_esquiva 1": "Capoeira_Pack_esquiva 1.vrma",
  "capoeirapackesquiva2": "Capoeira_Pack_esquiva 2.vrma",
  "capoeira_pack_esquiva 2": "Capoeira_Pack_esquiva 2.vrma",
  "capoeirapackesquiva3": "Capoeira_Pack_esquiva 3.vrma",
  "capoeira_pack_esquiva 3": "Capoeira_Pack_esquiva 3.vrma",
  "capoeirapackesquiva4": "Capoeira_Pack_esquiva 4.vrma",
  "capoeira_pack_esquiva 4": "Capoeira_Pack_esquiva 4.vrma",
  "capoeirapackesquiva5": "Capoeira_Pack_esquiva 5.vrma",
  "capoeira_pack_esquiva 5": "Capoeira_Pack_esquiva 5.vrma",
  "capoeirapackgingabackward": "Capoeira_Pack_ginga backward.vrma",
  "capoeira_pack_ginga backward": "Capoeira_Pack_ginga backward.vrma",
  "capoeirapackgingaforward": "Capoeira_Pack_ginga forward.vrma",
  "capoeira_pack_ginga forward": "Capoeira_Pack_ginga forward.vrma",
  "capoeirapackgingasideways1": "Capoeira_Pack_ginga sideways 1.vrma",
  "capoeira_pack_ginga sideways 1": "Capoeira_Pack_ginga sideways 1.vrma",
  "capoeirapackgingasideways2": "Capoeira_Pack_ginga sideways 2.vrma",
  "capoeira_pack_ginga sideways 2": "Capoeira_Pack_ginga sideways 2.vrma",
  "capoeirapackgingasidewaystoau": "Capoeira_Pack_ginga sideways to au.vrma",
  "capoeira_pack_ginga sideways to au": "Capoeira_Pack_ginga sideways to au.vrma",
  "capoeirapackgingavariation1": "Capoeira_Pack_ginga variation 1.vrma",
  "capoeira_pack_ginga variation 1": "Capoeira_Pack_ginga variation 1.vrma",
  "capoeirapackgingavariation2": "Capoeira_Pack_ginga variation 2.vrma",
  "capoeira_pack_ginga variation 2": "Capoeira_Pack_ginga variation 2.vrma",
  "capoeirapackgingavariation3": "Capoeira_Pack_ginga variation 3.vrma",
  "capoeira_pack_ginga variation 3": "Capoeira_Pack_ginga variation 3.vrma",
  "capoeirapackmacacoside": "Capoeira_Pack_macaco side.vrma",
  "capoeira_pack_macaco side": "Capoeira_Pack_macaco side.vrma",
  "capoeirapackmartelo2": "Capoeira_Pack_martelo 2.vrma",
  "capoeira_pack_martelo 2": "Capoeira_Pack_martelo 2.vrma",
  "capoeirapackmartelo3": "Capoeira_Pack_martelo 3.vrma",
  "capoeira_pack_martelo 3": "Capoeira_Pack_martelo 3.vrma",
  "capoeirapackmartelodochausemmao": "Capoeira_Pack_martelo do chau sem mao.vrma",
  "capoeira_pack_martelo do chau sem mao": "Capoeira_Pack_martelo do chau sem mao.vrma",
  "capoeirapackmartelodochau": "Capoeira_Pack_martelo do chau.vrma",
  "capoeira_pack_martelo do chau": "Capoeira_Pack_martelo do chau.vrma",
  "capoeirapackmeialuadecompassoback": "Capoeira_Pack_meia lua de compasso back.vrma",
  "capoeira_pack_meia lua de compasso back": "Capoeira_Pack_meia lua de compasso back.vrma",
  "capoeirapackmeialuadecompasso": "Capoeira_Pack_meia lua de compasso.vrma",
  "capoeira_pack_meia lua de compasso": "Capoeira_Pack_meia lua de compasso.vrma",
  "capoeirapackmeialuadefrente": "Capoeira_Pack_meia lua de frente.vrma",
  "capoeira_pack_meia lua de frente": "Capoeira_Pack_meia lua de frente.vrma",
  "capoeirapackpontera": "Capoeira_Pack_pontera.vrma",
  "capoeira_pack_pontera": "Capoeira_Pack_pontera.vrma",
  "capoeirapackqueshada1": "Capoeira_Pack_queshada 1.vrma",
  "capoeira_pack_queshada 1": "Capoeira_Pack_queshada 1.vrma",
  "capoeirapackqueshada2": "Capoeira_Pack_queshada 2.vrma",
  "capoeira_pack_queshada 2": "Capoeira_Pack_queshada 2.vrma",
  "capoeirapackrasteira1": "Capoeira_Pack_rasteira 1.vrma",
  "capoeira_pack_rasteira 1": "Capoeira_Pack_rasteira 1.vrma",
  "capoeirapackrasteira2": "Capoeira_Pack_rasteira 2.vrma",
  "capoeira_pack_rasteira 2": "Capoeira_Pack_rasteira 2.vrma",
  "capoeirapacktroca1": "Capoeira_Pack_troca 1.vrma",
  "capoeira_pack_troca 1": "Capoeira_Pack_troca 1.vrma",
  "catwalkwalking": "Catwalk Walking.vrma",
  "catwalk walking": "Catwalk Walking.vrma",
  "cheering": "Cheering.vrma",
  "chickendance": "Chicken Dance.vrma",
  "chicken dance": "Chicken Dance.vrma",
  "crazygesture": "Crazy Gesture.vrma",
  "crazy gesture": "Crazy Gesture.vrma",
  "dancingmaraschinostep": "Dancing Maraschino Step.vrma",
  "dancing maraschino step": "Dancing Maraschino Step.vrma",
  "dancingtwerk": "Dancing Twerk.vrma",
  "dancing twerk": "Dancing Twerk.vrma",
  "dancing": "Dancing.vrma",
  "defeated": "Defeated.vrma",
  "dwarfidle": "Dwarf Idle.vrma",
  "dwarf idle": "Dwarf Idle.vrma",
  "femalecrouchpose": "Female Crouch Pose.vrma",
  "female crouch pose": "Female Crouch Pose.vrma",
  "femaledancepose": "Female Dance Pose.vrma",
  "female dance pose": "Female Dance Pose.vrma",
  "femaledancepose1": "Female Dance Pose1.vrma",
  "female dance pose1": "Female Dance Pose1.vrma",
  "femaledynamicpose": "Female Dynamic Pose.vrma",
  "female dynamic pose": "Female Dynamic Pose.vrma",
  "femalelayingpose": "Female Laying Pose.vrma",
  "female laying pose": "Female Laying Pose.vrma",
  "femalelayingpose1": "Female Laying Pose1.vrma",
  "female laying pose1": "Female Laying Pose1.vrma",
  "femalestandingpose": "Female Standing Pose.vrma",
  "female standing pose": "Female Standing Pose.vrma",
  "femalestandingpose2": "Female Standing Pose2.vrma",
  "female standing pose2": "Female Standing Pose2.vrma",
  "femalestopandstartwalking": "Female Stop And Start Walking.vrma",
  "female stop and start walking": "Female Stop And Start Walking.vrma",
  "femalelocomotionpackpiratebyp.konstantinov": "Female_Locomotion_Pack_Pirate By P. Konstantinov.vrma",
  "female_locomotion_pack_pirate by p. konstantinov": "Female_Locomotion_Pack_Pirate By P. Konstantinov.vrma",
  "femalelocomotionpackidle": "Female_Locomotion_Pack_idle.vrma",
  "female_locomotion_pack_idle": "Female_Locomotion_Pack_idle.vrma",
  "femalelocomotionpackjump": "Female_Locomotion_Pack_jump.vrma",
  "female_locomotion_pack_jump": "Female_Locomotion_Pack_jump.vrma",
  "femalelocomotionpackleftstrafewalk": "Female_Locomotion_Pack_left strafe walk.vrma",
  "female_locomotion_pack_left strafe walk": "Female_Locomotion_Pack_left strafe walk.vrma",
  "femalelocomotionpackleftstrafe": "Female_Locomotion_Pack_left strafe.vrma",
  "female_locomotion_pack_left strafe": "Female_Locomotion_Pack_left strafe.vrma",
  "femalelocomotionpackleftturn": "Female_Locomotion_Pack_left turn.vrma",
  "female_locomotion_pack_left turn": "Female_Locomotion_Pack_left turn.vrma",
  "femalelocomotionpackrightstrafewalk": "Female_Locomotion_Pack_right strafe walk.vrma",
  "female_locomotion_pack_right strafe walk": "Female_Locomotion_Pack_right strafe walk.vrma",
  "femalelocomotionpackrightstrafe": "Female_Locomotion_Pack_right strafe.vrma",
  "female_locomotion_pack_right strafe": "Female_Locomotion_Pack_right strafe.vrma",
  "femalelocomotionpackrightturn": "Female_Locomotion_Pack_right turn.vrma",
  "female_locomotion_pack_right turn": "Female_Locomotion_Pack_right turn.vrma",
  "femalelocomotionpackrunning": "Female_Locomotion_Pack_running.vrma",
  "female_locomotion_pack_running": "Female_Locomotion_Pack_running.vrma",
  "femalelocomotionpackwalking": "Female_Locomotion_Pack_walking.vrma",
  "female_locomotion_pack_walking": "Female_Locomotion_Pack_walking.vrma",
  "flair": "Flair.vrma",
  "freetestpackpiratebyp.konstantinov": "Free_Test_Pack_Pirate By P. Konstantinov.vrma",
  "free_test_pack_pirate by p. konstantinov": "Free_Test_Pack_Pirate By P. Konstantinov.vrma",
  "freetestpackbackfliptouppercut": "Free_Test_Pack_back flip to uppercut.vrma",
  "free_test_pack_back flip to uppercut": "Free_Test_Pack_back flip to uppercut.vrma",
  "freetestpackgangnamstyle": "Free_Test_Pack_gangnam style.vrma",
  "free_test_pack_gangnam style": "Free_Test_Pack_gangnam style.vrma",
  "freetestpackidle": "Free_Test_Pack_idle.vrma",
  "free_test_pack_idle": "Free_Test_Pack_idle.vrma",
  "freetestpackjump": "Free_Test_Pack_jump.vrma",
  "free_test_pack_jump": "Free_Test_Pack_jump.vrma",
  "freetestpackleftstrafewalking": "Free_Test_Pack_left strafe walking.vrma",
  "free_test_pack_left strafe walking": "Free_Test_Pack_left strafe walking.vrma",
  "freetestpackleftturn90": "Free_Test_Pack_left turn 90.vrma",
  "free_test_pack_left turn 90": "Free_Test_Pack_left turn 90.vrma",
  "freetestpackrightstrafewalking": "Free_Test_Pack_right strafe walking.vrma",
  "free_test_pack_right strafe walking": "Free_Test_Pack_right strafe walking.vrma",
  "freetestpackrightturn90": "Free_Test_Pack_right turn 90.vrma",
  "free_test_pack_right turn 90": "Free_Test_Pack_right turn 90.vrma",
  "freetestpacksambadancing": "Free_Test_Pack_samba dancing.vrma",
  "free_test_pack_samba dancing": "Free_Test_Pack_samba dancing.vrma",
  "freetestpackskinningtest": "Free_Test_Pack_skinning test.vrma",
  "free_test_pack_skinning test": "Free_Test_Pack_skinning test.vrma",
  "freetestpackwalking": "Free_Test_Pack_walking.vrma",
  "free_test_pack_walking": "Free_Test_Pack_walking.vrma",
  "golfputtfailure": "Golf Putt Failure.vrma",
  "golf putt failure": "Golf Putt Failure.vrma",
  "happywalk": "Happy Walk.vrma",
  "happy walk": "Happy Walk.vrma",
  "havingameeting,female": "Having A Meeting, Female.vrma",
  "having a meeting, female": "Having A Meeting, Female.vrma",
  "hiphopdancing": "Hip Hop Dancing.vrma",
  "hip hop dancing": "Hip Hop Dancing.vrma",
  "hiphopdancing1": "Hip Hop Dancing1.vrma",
  "hip hop dancing1": "Hip Hop Dancing1.vrma",
  "hiphopdancing2": "Hip Hop Dancing2.vrma",
  "hip hop dancing2": "Hip Hop Dancing2.vrma",
  "hiphopdancing3": "Hip Hop Dancing3.vrma",
  "hip hop dancing3": "Hip Hop Dancing3.vrma",
  "hokeypokey": "Hokey Pokey.vrma",
  "hokey pokey": "Hokey Pokey.vrma",
  "idletositup": "Idle To Situp.vrma",
  "idle to situp": "Idle To Situp.vrma",
  "idle": "Idle.vrma",
  "jazzdancing": "Jazz Dancing.vrma",
  "jazz dancing": "Jazz Dancing.vrma",
  "jazzdancing2": "Jazz Dancing2.vrma",
  "jazz dancing2": "Jazz Dancing2.vrma",
  "jazzdancing3": "Jazz Dancing3.vrma",
  "jazz dancing3": "Jazz Dancing3.vrma",
  "kettlebellswing": "Kettlebell Swing.vrma",
  "kettlebell swing": "Kettlebell Swing.vrma",
  "kipup": "Kip Up.vrma",
  "kip up": "Kip Up.vrma",
  "kneelingidle": "Kneeling Idle.vrma",
  "kneeling idle": "Kneeling Idle.vrma",
  "layingvomiting": "Laying Vomiting.vrma",
  "laying vomiting": "Laying Vomiting.vrma",
  "lookaround": "lookaround.vrma",
  "look around": "Look Around.vrma",
  "loser": "Loser.vrma",
  "lowcrawl": "Low Crawl.vrma",
  "low crawl": "Low Crawl.vrma",
  "macarenadance": "Macarena Dance.vrma",
  "macarena dance": "Macarena Dance.vrma",
  "ninjaidle": "Ninja Idle.vrma",
  "ninja idle": "Ninja Idle.vrma",
  "pikewalk": "Pike Walk.vrma",
  "pike walk": "Pike Walk.vrma",
  "plotting": "Plotting.vrma",
  "praying": "Praying.vrma",
  "promagicpackcrouchidle": "Pro_Magic_Pack_Crouch Idle.vrma",
  "pro_magic_pack_crouch idle": "Pro_Magic_Pack_Crouch Idle.vrma",
  "promagicpackcrouchtostandingidle": "Pro_Magic_Pack_Crouch To Standing Idle.vrma",
  "pro_magic_pack_crouch to standing idle": "Pro_Magic_Pack_Crouch To Standing Idle.vrma",
  "promagicpackcrouchturnleft90": "Pro_Magic_Pack_Crouch Turn Left 90.vrma",
  "pro_magic_pack_crouch turn left 90": "Pro_Magic_Pack_Crouch Turn Left 90.vrma",
  "promagicpackcrouchturnright90": "Pro_Magic_Pack_Crouch Turn Right 90.vrma",
  "pro_magic_pack_crouch turn right 90": "Pro_Magic_Pack_Crouch Turn Right 90.vrma",
  "promagicpackcrouchwalkback": "Pro_Magic_Pack_Crouch Walk Back.vrma",
  "pro_magic_pack_crouch walk back": "Pro_Magic_Pack_Crouch Walk Back.vrma",
  "promagicpackcrouchwalkforward": "Pro_Magic_Pack_Crouch Walk Forward.vrma",
  "pro_magic_pack_crouch walk forward": "Pro_Magic_Pack_Crouch Walk Forward.vrma",
  "promagicpackcrouchwalkleft": "Pro_Magic_Pack_Crouch Walk Left.vrma",
  "pro_magic_pack_crouch walk left": "Pro_Magic_Pack_Crouch Walk Left.vrma",
  "promagicpackcrouchwalkright": "Pro_Magic_Pack_Crouch Walk Right.vrma",
  "pro_magic_pack_crouch walk right": "Pro_Magic_Pack_Crouch Walk Right.vrma",
  "promagicpackstanding1hmagicattack01": "Pro_Magic_Pack_Standing 1H Magic Attack 01.vrma",
  "pro_magic_pack_standing 1h magic attack 01": "Pro_Magic_Pack_Standing 1H Magic Attack 01.vrma",
  "promagicpackstanding1hmagicattack02": "Pro_Magic_Pack_Standing 1H Magic Attack 02.vrma",
  "pro_magic_pack_standing 1h magic attack 02": "Pro_Magic_Pack_Standing 1H Magic Attack 02.vrma",
  "promagicpackstanding1hmagicattack03": "Pro_Magic_Pack_Standing 1H Magic Attack 03.vrma",
  "pro_magic_pack_standing 1h magic attack 03": "Pro_Magic_Pack_Standing 1H Magic Attack 03.vrma",
  "promagicpackstanding2hcastspell01": "Pro_Magic_Pack_Standing 2H Cast Spell 01.vrma",
  "pro_magic_pack_standing 2h cast spell 01": "Pro_Magic_Pack_Standing 2H Cast Spell 01.vrma",
  "promagicpackstanding2hmagicareaattack01": "Pro_Magic_Pack_Standing 2H Magic Area Attack 01.vrma",
  "pro_magic_pack_standing 2h magic area attack 01": "Pro_Magic_Pack_Standing 2H Magic Area Attack 01.vrma",
  "promagicpackstanding2hmagicareaattack02": "Pro_Magic_Pack_Standing 2H Magic Area Attack 02.vrma",
  "pro_magic_pack_standing 2h magic area attack 02": "Pro_Magic_Pack_Standing 2H Magic Area Attack 02.vrma",
  "promagicpackstanding2hmagicattack01": "Pro_Magic_Pack_Standing 2H Magic Attack 01.vrma",
  "pro_magic_pack_standing 2h magic attack 01": "Pro_Magic_Pack_Standing 2H Magic Attack 01.vrma",
  "promagicpackstanding2hmagicattack02": "Pro_Magic_Pack_Standing 2H Magic Attack 02.vrma",
  "pro_magic_pack_standing 2h magic attack 02": "Pro_Magic_Pack_Standing 2H Magic Attack 02.vrma",
  "promagicpackstanding2hmagicattack03": "Pro_Magic_Pack_Standing 2H Magic Attack 03.vrma",
  "pro_magic_pack_standing 2h magic attack 03": "Pro_Magic_Pack_Standing 2H Magic Attack 03.vrma",
  "promagicpackstanding2hmagicattack04": "Pro_Magic_Pack_Standing 2H Magic Attack 04.vrma",
  "pro_magic_pack_standing 2h magic attack 04": "Pro_Magic_Pack_Standing 2H Magic Attack 04.vrma",
  "promagicpackstanding2hmagicattack05": "Pro_Magic_Pack_Standing 2H Magic Attack 05.vrma",
  "pro_magic_pack_standing 2h magic attack 05": "Pro_Magic_Pack_Standing 2H Magic Attack 05.vrma",
  "promagicpackstandingblockend": "Pro_Magic_Pack_Standing Block End.vrma",
  "pro_magic_pack_standing block end": "Pro_Magic_Pack_Standing Block End.vrma",
  "promagicpackstandingblockidle": "Pro_Magic_Pack_Standing Block Idle.vrma",
  "pro_magic_pack_standing block idle": "Pro_Magic_Pack_Standing Block Idle.vrma",
  "promagicpackstandingblockreactlarge": "Pro_Magic_Pack_Standing Block React Large.vrma",
  "pro_magic_pack_standing block react large": "Pro_Magic_Pack_Standing Block React Large.vrma",
  "promagicpackstandingblockstart": "Pro_Magic_Pack_Standing Block Start.vrma",
  "pro_magic_pack_standing block start": "Pro_Magic_Pack_Standing Block Start.vrma",
  "promagicpackstandingidle03": "Pro_Magic_Pack_Standing Idle 03.vrma",
  "pro_magic_pack_standing idle 03": "Pro_Magic_Pack_Standing Idle 03.vrma",
  "promagicpackstandingidle04": "Pro_Magic_Pack_Standing Idle 04.vrma",
  "pro_magic_pack_standing idle 04": "Pro_Magic_Pack_Standing Idle 04.vrma",
  "promagicpackstandingidletocrouch": "Pro_Magic_Pack_Standing Idle To Crouch.vrma",
  "pro_magic_pack_standing idle to crouch": "Pro_Magic_Pack_Standing Idle To Crouch.vrma",
  "promagicpackstandingjumprunninglanding": "Pro_Magic_Pack_Standing Jump Running Landing.vrma",
  "pro_magic_pack_standing jump running landing": "Pro_Magic_Pack_Standing Jump Running Landing.vrma",
  "promagicpackstandingjumprunning": "Pro_Magic_Pack_Standing Jump Running.vrma",
  "pro_magic_pack_standing jump running": "Pro_Magic_Pack_Standing Jump Running.vrma",
  "promagicpackstandingjump": "Pro_Magic_Pack_Standing Jump.vrma",
  "pro_magic_pack_standing jump": "Pro_Magic_Pack_Standing Jump.vrma",
  "promagicpackstandinglandtostandingidle": "Pro_Magic_Pack_Standing Land To Standing Idle.vrma",
  "pro_magic_pack_standing land to standing idle": "Pro_Magic_Pack_Standing Land To Standing Idle.vrma",
  "promagicpackstandingreactdeathbackward": "Pro_Magic_Pack_Standing React Death Backward.vrma",
  "pro_magic_pack_standing react death backward": "Pro_Magic_Pack_Standing React Death Backward.vrma",
  "promagicpackstandingreactdeathforward": "Pro_Magic_Pack_Standing React Death Forward.vrma",
  "pro_magic_pack_standing react death forward": "Pro_Magic_Pack_Standing React Death Forward.vrma",
  "promagicpackstandingreactdeathleft": "Pro_Magic_Pack_Standing React Death Left.vrma",
  "pro_magic_pack_standing react death left": "Pro_Magic_Pack_Standing React Death Left.vrma",
  "promagicpackstandingreactdeathright": "Pro_Magic_Pack_Standing React Death Right.vrma",
  "pro_magic_pack_standing react death right": "Pro_Magic_Pack_Standing React Death Right.vrma",
  "promagicpackstandingreactlargefromback": "Pro_Magic_Pack_Standing React Large From Back.vrma",
  "pro_magic_pack_standing react large from back": "Pro_Magic_Pack_Standing React Large From Back.vrma",
  "promagicpackstandingreactlargefromfront": "Pro_Magic_Pack_Standing React Large From Front.vrma",
  "pro_magic_pack_standing react large from front": "Pro_Magic_Pack_Standing React Large From Front.vrma",
  "promagicpackstandingreactlargefromleft": "Pro_Magic_Pack_Standing React Large From Left.vrma",
  "pro_magic_pack_standing react large from left": "Pro_Magic_Pack_Standing React Large From Left.vrma",
  "promagicpackstandingreactlargefromright": "Pro_Magic_Pack_Standing React Large From Right.vrma",
  "pro_magic_pack_standing react large from right": "Pro_Magic_Pack_Standing React Large From Right.vrma",
  "promagicpackstandingreactsmallfromback": "Pro_Magic_Pack_Standing React Small From Back.vrma",
  "pro_magic_pack_standing react small from back": "Pro_Magic_Pack_Standing React Small From Back.vrma",
  "promagicpackstandingreactsmallfromfront": "Pro_Magic_Pack_Standing React Small From Front.vrma",
  "pro_magic_pack_standing react small from front": "Pro_Magic_Pack_Standing React Small From Front.vrma",
  "promagicpackstandingreactsmallfromleft": "Pro_Magic_Pack_Standing React Small From Left.vrma",
  "pro_magic_pack_standing react small from left": "Pro_Magic_Pack_Standing React Small From Left.vrma",
  "promagicpackstandingreactsmallfromright": "Pro_Magic_Pack_Standing React Small From Right.vrma",
  "pro_magic_pack_standing react small from right": "Pro_Magic_Pack_Standing React Small From Right.vrma",
  "promagicpackstandingrunback": "Pro_Magic_Pack_Standing Run Back.vrma",
  "pro_magic_pack_standing run back": "Pro_Magic_Pack_Standing Run Back.vrma",
  "promagicpackstandingrunforward": "Pro_Magic_Pack_Standing Run Forward.vrma",
  "pro_magic_pack_standing run forward": "Pro_Magic_Pack_Standing Run Forward.vrma",
  "promagicpackstandingrunleft": "Pro_Magic_Pack_Standing Run Left.vrma",
  "pro_magic_pack_standing run left": "Pro_Magic_Pack_Standing Run Left.vrma",
  "promagicpackstandingrunright": "Pro_Magic_Pack_Standing Run Right.vrma",
  "pro_magic_pack_standing run right": "Pro_Magic_Pack_Standing Run Right.vrma",
  "promagicpackstandingsprintforward": "Pro_Magic_Pack_Standing Sprint Forward.vrma",
  "pro_magic_pack_standing sprint forward": "Pro_Magic_Pack_Standing Sprint Forward.vrma",
  "promagicpackstandingturnleft90": "Pro_Magic_Pack_Standing Turn Left 90.vrma",
  "pro_magic_pack_standing turn left 90": "Pro_Magic_Pack_Standing Turn Left 90.vrma",
  "promagicpackstandingturnright90": "Pro_Magic_Pack_Standing Turn Right 90.vrma",
  "pro_magic_pack_standing turn right 90": "Pro_Magic_Pack_Standing Turn Right 90.vrma",
  "promagicpackstandingwalkback": "Pro_Magic_Pack_Standing Walk Back.vrma",
  "pro_magic_pack_standing walk back": "Pro_Magic_Pack_Standing Walk Back.vrma",
  "promagicpackstandingwalkforward": "Pro_Magic_Pack_Standing Walk Forward.vrma",
  "pro_magic_pack_standing walk forward": "Pro_Magic_Pack_Standing Walk Forward.vrma",
  "promagicpackstandingwalkleft": "Pro_Magic_Pack_Standing Walk Left.vrma",
  "pro_magic_pack_standing walk left": "Pro_Magic_Pack_Standing Walk Left.vrma",
  "promagicpackstandingwalkright": "Pro_Magic_Pack_Standing Walk Right.vrma",
  "pro_magic_pack_standing walk right": "Pro_Magic_Pack_Standing Walk Right.vrma",
  "promagicpackxbot": "Pro_Magic_Pack_X Bot.vrma",
  "pro_magic_pack_x bot": "Pro_Magic_Pack_X Bot.vrma",
  "promagicpackstanding1hcastspell01": "Pro_Magic_Pack_standing 1H cast spell 01.vrma",
  "pro_magic_pack_standing 1h cast spell 01": "Pro_Magic_Pack_standing 1H cast spell 01.vrma",
  "promagicpackstandingidle02": "Pro_Magic_Pack_standing idle 02.vrma",
  "pro_magic_pack_standing idle 02": "Pro_Magic_Pack_standing idle 02.vrma",
  "promagicpackstandingidle": "Pro_Magic_Pack_standing idle.vrma",
  "pro_magic_pack_standing idle": "Pro_Magic_Pack_standing idle.vrma",
  "pullplant": "Pull Plant.vrma",
  "pull plant": "Pull Plant.vrma",
  "pushup": "Push Up.vrma",
  "push up": "Push Up.vrma",
  "rejected": "Rejected.vrma",
  "rejected1": "Rejected1.vrma",
  "sambadancing": "Samba Dancing.vrma",
  "samba dancing": "Samba Dancing.vrma",
  "sambadancing1": "Samba Dancing1.vrma",
  "samba dancing1": "Samba Dancing1.vrma",
  "speedbag": "Speedbag.vrma",
  "standingusingtouchscreentablet": "Standing Using Touchscreen Tablet.vrma",
  "standing using touchscreen tablet": "Standing Using Touchscreen Tablet.vrma",
  "stealthassassination": "Stealth Assassination.vrma",
  "stealth assassination": "Stealth Assassination.vrma",
  "sumohighpull": "Sumo High Pull.vrma",
  "sumo high pull": "Sumo High Pull.vrma",
  "sumohighpull1": "Sumo High Pull1.vrma",
  "sumo high pull1": "Sumo High Pull1.vrma",
  "talkingonphone": "Talking On Phone.vrma",
  "talking on phone": "Talking On Phone.vrma",
  "talkingphonepacing": "Talking Phone Pacing.vrma",
  "talking phone pacing": "Talking Phone Pacing.vrma",
  "taunt": "Taunt.vrma",
  "textingandwalking": "Texting And Walking.vrma",
  "texting and walking": "Texting And Walking.vrma",
  "thinking": "thinking.vrma",
  "victory": "Victory.vrma",
  "yawn": "Yawn.vrma",
  "yellingout": "Yelling Out.vrma",
  "yelling out": "Yelling Out.vrma",
  "angry": "angry.vrma",
  "blush": "blush.vrma",
  "clapping": "clapping.vrma",
  "dance": "dance.vrma",
  "disco": "disco.vrma",
  "goodbye": "goodbye.vrma",
  "hiphop": "hiphop.vrma",
  "idleloop": "idle_loop.vrma",
  "idle_loop": "idle_loop.vrma",
  "idlestretch": "idle_stretch.vrma",
  "idle_stretch": "idle_stretch.vrma",
  "jump": "jump.vrma",
  "look_around": "look_around.vrma",
  "relax": "relax.vrma",
  "robot": "robot.vrma",
  "sad": "sad.vrma",
  "salsa": "salsa.vrma",
  "samba": "samba.vrma",
  "sit": "sit.vrma",
  "sitwave": "sitWave.vrma",
  "sleepy": "sleepy.vrma",
  "spin": "spin.vrma",
  "surprised": "surprised.vrma",
  "walk": "walk.vrma",
  "waveright": "wave_right.vrma",
  "wave_right": "wave_right.vrma"
};

  const VRMA_MAP = {
    walk: "walk.vrma",
    marche: "walk.vrma",
    step: "walk.vrma",
    run: "walk.vrma",
    dance: "dance.vrma",
    danse: "dance.vrma",
    groove: "dance.vrma",
    samba: "samba.vrma",
    salsa: "salsa.vrma",
    latina: "samba.vrma",
    hiphop: "hiphop.vrma",
    bboy: "hiphop.vrma",
    street: "hiphop.vrma",
    bounce: "hiphop.vrma",
    robot: "robot.vrma",
    popping: "robot.vrma",
    wavedance: "robot.vrma",
    disco: "disco.vrma",
    twist: "disco.vrma",
    fever: "disco.vrma",
    spin: "spin.vrma",
    tourner: "spin.vrma",
    pirouette: "spin.vrma",
    jump: "jump.vrma",
    saut: "jump.vrma",
    victory: "jump.vrma",
    victoire: "jump.vrma",
    relax: "relax.vrma",
    repos: "relax.vrma",
    pose: "relax.vrma",
    sit: "sit.vrma",
    sitwave: "sitWave.vrma",
    lookaround: "lookaround.vrma",
    look: "lookaround.vrma",
    observe: "lookaround.vrma",
    idleloop: "idle_loop.vrma",
    stretch: "idle_stretch.vrma",
    etirement: "idle_stretch.vrma",
    thinking: "thinking.vrma",
    think: "thinking.vrma",
    goodbye: "goodbye.vrma",
    wave: "wave_right.vrma",
    waveright: "wave_right.vrma",
    clapping: "clapping.vrma",
    clap: "clapping.vrma",
    cheer: "clapping.vrma",
    blush: "blush.vrma",
    sleepy: "sleepy.vrma",
    surprised: "surprised.vrma",
    sad: "sad.vrma",
    angry: "angry.vrma",
    bellydance: "Bellydancing.vrma",
    bellydancing: "Bellydancing.vrma",
    popdance: "Dancing Maraschino Step.vrma",
    maraschino: "Dancing Maraschino Step.vrma",
    femaledance: "Female Dance Pose.vrma",
    dancepose: "Female Dance Pose.vrma",
    dancing: "Dancing.vrma",
    twerk: "Dancing Twerk.vrma",
    gangnam: "Free_Test_Pack_gangnam style.vrma",
    gangnamstyle: "Free_Test_Pack_gangnam style.vrma",
    cancan: "Can Can.vrma",
    macarena: "Macarena Dance.vrma",
    chickendance: "Chicken Dance.vrma",
    hokeypokey: "Hokey Pokey.vrma",
    backflip: "Backflip.vrma",
    pushup: "Push Up.vrma",
    taunt: "Taunt.vrma",
    catwalk: "Catwalk Walking.vrma",
    happywalk: "Happy Walk.vrma",
    capoeira: "Capoeira_Pack_capoeira.vrma",
    ginga: "Capoeira_Pack_ginga forward.vrma",
    castspell: "Pro_Magic_Pack_standing 1H cast spell 01.vrma",
    magicattack: "Pro_Magic_Pack_Standing 2H Magic Area Attack 01.vrma",
    shieldblock: "Pro_Magic_Pack_Standing Block Idle.vrma",
    hello: "wave_right.vrma",
    salute: "wave_right.vrma",
  };

  function resolveVrmaFile(name) {
    if (!name) return null;
    if (typeof name !== "string") return null;
    if (name.endsWith(".vrma")) return name;
    const clean = name.toLowerCase().replace(/[-_\s]/g, "");
    const raw = name.toLowerCase();
    return VRMA_MAP[clean] || VRMA_MAP[raw] || VRMA_CATALOG[clean] || VRMA_CATALOG[raw] || null;
  }

  function getVrmaUrl(filename) {
    const base = modelUrl.substring(0, modelUrl.lastIndexOf("/"));
    return (base ? base + "/animations/" : "animations/") + filename;
  }

  async function loadVRMA(name, filename) {
    if (vrmaClips.has(name)) return vrmaClips.get(name);
    if (vrmaLoading.has(name)) return vrmaLoading.get(name);
    const targetFile = filename || (name.endsWith(".vrma") ? name : `${name}.vrma`);
    const primaryUrl = getVrmaUrl(targetFile);

    const promise = (async () => {
      let gltf = null;
      try {
        gltf = await loader.loadAsync(primaryUrl);
      } catch (err) {
        console.warn(`[vrm_pet] Local VRMA load failed "${name}" (${primaryUrl}), trying LAN CT100 fallback...`, err);
        try {
          const remoteUrl = `http://192.168.0.100:5174/vrm/animations/${targetFile}`;
          gltf = await loader.loadAsync(remoteUrl);
        } catch (err2) {
          console.warn(`[vrm_pet] VRMA LAN fallback failed "${name}":`, err2);
          return null;
        }
      }

      try {
        const vrmAnimations = gltf.userData.vrmAnimations || (gltf.userData.vrmAnimation ? [gltf.userData.vrmAnimation] : []);
        const animData = vrmAnimations[0];
        if (!animData) throw new Error("No vrmAnimation in file");
        if (!vrm) throw new Error("VRM model not ready yet for animation");
        const clip = createVRMAnimationClip(animData, vrm);
        clip.name = name;

        // In-Place Lock : Neutralise la dérive de translation (root motion X et Z)
        // pour que l'avatar reste TOUJOURS centré au milieu du cadre sans jamais déborder ou disparaître
        const restHipsY = vrm?.humanoid?.getNormalizedBoneNode?.("hips")?.position?.y || 0.824;
        for (const track of clip.tracks) {
          if (track.name.endsWith(".position")) {
            const vals = track.values;
            const y0 = vals.length >= 3 ? vals[1] : restHipsY;
            for (let i = 0; i < vals.length; i += 3) {
              vals[i] = 0;     // Lock horizontal X (zéro dérive gauche/droite hors champ)
              vals[i + 2] = 0; // Lock profondeur Z (zéro dérive avant/arrière)
              // Harmonisation verticale Y : rebond de danse maîtrisé ancré sur restHipsY (évite de flotter)
              const deltaY = (vals[i + 1] - y0) * 0.45;
              vals[i + 1] = restHipsY + deltaY;
            }
          }
        }

        vrmaClips.set(name, clip);
        console.info(`[vrm_pet] VRMA "${name}" loaded (${clip.duration.toFixed(2)}s)`);
        return clip;
      } catch (err) {
        console.warn(`[vrm_pet] VRMA clip creation failed "${name}":`, err);
        return null;
      } finally {
        vrmaLoading.delete(name);
      }
    })();
    vrmaLoading.set(name, promise);
    return promise;
  }

  async function playVRMA(name, opts = {}) {
    if (!vrm || !mixer) return false;
    const key = name.toLowerCase().replace(/[-_\s]/g, "");
    const filename = resolveVrmaFile(name) || (name.endsWith(".vrma") ? name : `${name}.vrma`);
    const clip = await loadVRMA(key, filename);
    if (!clip || disposed) return false;

    const loop = opts.loop !== false;
    const fadeSec = Number(opts.fadeSec ?? 0.35);
    const action = mixer.clipAction(clip);
    if (!loop) {
      action.setLoop(THREE.LoopOnce, 1);
      action.clampWhenFinished = false; // Ne jamais figer le modèle sur la dernière frame
    } else {
      action.setLoop(THREE.LoopRepeat, Infinity);
    }
    // Cadence d'animation adaptée : la marche mocap est calée à 0.55x
    // pour un pas posé et majestueux, parfaitement synchronisé avec les 165 px/s de translation fenêtre
    if (key === "walk" || key === "marche" || key === "step" || key === "run") {
      action.timeScale = Number(opts.timeScale ?? 0.55);
    } else {
      action.timeScale = Number(opts.timeScale ?? 1.0);
    }
    action.reset();
    action.fadeIn(fadeSec);
    action.play();

    if (activeVrmaAction && activeVrmaAction !== action) {
      activeVrmaAction.fadeOut(fadeSec);
    }
    activeVrmaAction = action;
    activeVrmaName = name;
    return true;
  }

  function stopVRMA(fadeSec = 0.25) {
    if (activeVrmaAction) {
      try { activeVrmaAction.fadeOut(fadeSec); } catch (_) { }
      activeVrmaAction = null;
    }
    if (mixer) {
      try { mixer.stopAllAction(); } catch (_) { }
    }
    activeVrmaName = null;
    poseBlend = 0;
    if (vrm?.humanoid) {
      try {
        vrm.humanoid.resetNormalizedPose();
      } catch (_) { }
    }
  }

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
    for (const n of ["happy", "angry", "sad", "surprised", "relaxed", "neutral", "aa", "blinkRight", "blinkLeft"]) {
      try {
        em.setValue(n, 0);
      } catch (_) { }
    }
    for (const [k, v] of Object.entries(weights || {})) {
      try {
        em.setValue(k, Math.max(0, Math.min(1, Number(v) || 0)));
      } catch (_) { }
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
      activeVisemes = [];
      for (const vk of VISEME_KEYS) {
        currentVisemeWeights[vk] = 0;
      }
      return;
    }
    const ms = typeof msOrBool === "number" && Number.isFinite(msOrBool) ? msOrBool : 2500;
    talkingUntil = performance.now() + Math.max(400, Math.min(20000, ms));
  }

  function playVisemes(visemeList, durationMs) {
    if (Array.isArray(visemeList) && visemeList.length > 0) {
      activeVisemes = visemeList;
      visemesStartTime = performance.now();
      const last = visemeList[visemeList.length - 1];
      const calcDurMs = last ? (last.time_offset + last.duration) * 1000 : 3000;
      setTalking(durationMs || calcDurMs);
    } else {
      activeVisemes = [];
      setTalking(durationMs || 2500);
    }
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
    else if (n === "wave" || n === "hello" || n === "salute" || n === "coucou") key = "wave";
    else if (n === "dance" || n === "danse") key = "dance";
    else if (n === "cybergroove" || n === "groove" || n === "concert" || n === "darksynth") key = "cyberGroove";
    else if (n === "aeysasinging" || n === "aeysa" || n === "aeysamusic" || n === "singer" || n === "chanteuse" || n === "livesinger") key = "aeysaSinging";
    else if (n === "samba" || n === "salsa" || n === "latina") key = "samba";
    else if (n === "hiphop" || n === "bboy" || n === "street" || n === "bounce") key = "hiphop";
    else if (n === "robot" || n === "popping" || n === "wavedance") key = "robot";
    else if (n === "disco" || n === "twist" || n === "fever") key = "disco";
    else if (n === "spin" || n === "tourner" || n === "pirouette") key = "spin";
    else if (n === "focus" || n === "scan" || n === "code" || n === "debug") key = "focus";
    else if (n === "victory" || n === "victoire" || n === "win" || n === "success") key = "victory";
    else if (n === "jump" || n === "saut") key = "jump";
    else if (n === "stretch" || n === "etirement") key = "stretch";
    else if (n === "clap" || n === "clapping") key = "clapping";
    else if (n === "angry" || n === "colere" || n === "mad" || n === "pout") key = "angry";
    else if (n === "walk" || n === "marche" || n === "step") key = "walk";
    else if (n === "bellydance" || n === "bellydancing" || n === "belly" || n === "orientale") key = "bellydance";
    else if (n === "popdance" || n === "maraschino" || n === "popstep") key = "popdance";
    else if (n === "femaledance" || n === "dancepose" || n === "chanteuse") key = "femaledance";
    else if (n === "dancing") key = "dancing";
    else if (
      n === "fingerheart" ||
      n === "heart" ||
      n === "kpopheart" ||
      n === "love" ||
      n === "miniheart" ||
      n === "coeur"
    ) key = "fingerHeart";
    else if (POSE_EULERS[raw]) key = raw;
    else if (POSE_EULERS[n]) key = n;

    if (heading !== undefined) {
      setHeading(heading);
    } else if (key === "walk") {
      setHeading(1); // Profil 3/4 droit gracieux lors de la marche
    } else if (key === "idle") {
      setHeading(0);
    }

    if (key === "angry") setMood("tense");
    else if (
      key === "dance" ||
      key === "samba" ||
      key === "hiphop" ||
      key === "robot" ||
      key === "disco" ||
      key === "spin" ||
      key === "cheer" ||
      key === "fingerHeart"
    ) setMood("happy");
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

    // Dézoom dynamique vers le corps entier lors d'une danse/mouvement global si en mode buste
    const fullBodyDances = [
      "dance", "danse", "groove", "samba", "salsa", "latina", "hiphop", "bboy", "street", "bounce",
      "robot", "popping", "wavedance", "disco", "twist", "fever", "spin", "tourner", "pirouette", "jump", "saut", "victory", "walk", "marche",
      "fingerheart", "heart", "kpopheart", "miniheart", "bellydance", "bellydancing", "popdance", "maraschino", "femaledance", "dancepose", "dancing",
      "twerk", "gangnam", "macarena", "cancan", "capoeira", "backflip", "fitness"
    ];
    const isFullBodyAction = fullBodyDances.includes(key) ||
      key.includes("dance") || key.includes("capoeira") || key.includes("magic") ||
      key.includes("squat") || key.includes("jump") || key.includes("flip") ||
      key.includes("walk") || key.includes("run") || key.includes("strafe") ||
      key.includes("twerk") || key.includes("gangnam") || key.includes("macarena") ||
      key.includes("cancan") || key.includes("fitness") || key.includes("sport");
    if (isFullBodyAction && baseFraming === "bust") {
      framing = "full";
      isDanceFraming = true;
      if (vrm) frameVrm(vrm);
    }

    // Déclenchement clip VRMA officiel si disponible (ex: dance, samba, hiphop, walk, lookaround)
    // Sinon repli procédural immédiat (ex: robot, disco, spin, crossArms, bow)
    const vrmaFile = resolveVrmaFile(key) || resolveVrmaFile(n);
    if (vrmaFile) {
      playVRMA(vrmaFile, { loop: !(hold > 0) })
        .then((ok) => {
          if (!ok) stopVRMA(0);
        })
        .catch((err) => {
          console.warn(`[vrm_pet] playVRMA failed for "${key}":`, err);
          stopVRMA(0);
        });
    } else {
      stopVRMA(0);
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
    if (poseTo === "focus") {
      const scanHead = Math.sin(t * 1.8) * 0.04;
      const dataGlow = Math.sin(t * 3.5) * 0.02;
      if (animated.head) animated.head = [animated.head[0] + dataGlow, animated.head[1] + scanHead, animated.head[2]];
      if (animated.leftHand) animated.leftHand = [animated.leftHand[0] + dataGlow, animated.leftHand[1], animated.leftHand[2]];
    }
    if (poseTo === "victory") {
      const cheerArm = Math.sin(t * 5.0) * 0.06;
      if (animated.leftUpperArm) animated.leftUpperArm = [animated.leftUpperArm[0], animated.leftUpperArm[1], animated.leftUpperArm[2] - cheerArm];
      if (animated.rightUpperArm) animated.rightUpperArm = [animated.rightUpperArm[0], animated.rightUpperArm[1], animated.rightUpperArm[2] + cheerArm];
      if (animated.chest) animated.chest = [animated.chest[0] + cheerArm * 0.3, animated.chest[1], animated.chest[2]];
    }
    if (poseTo === "dance") {
      // Tempo groove doux et posé à ~1.05 Hz (63 BPM, détendu et gracieux)
      const tempo = t * 6.5;
      const tempoHalf = tempo * 0.5;
      const swayHips = Math.sin(tempoHalf) * 0.07;
      const rollHips = Math.cos(tempoHalf) * 0.05;
      const armWave = Math.sin(tempoHalf) * 0.14;
      const elbowBounce = Math.sin(tempo) * 0.10;

      // Bassin : ondulation douce et déhanché fluide (zéro secousse axiale X)
      if (animated.hips) animated.hips = [0, swayHips, rollHips];
      if (animated.spine) animated.spine = [animated.spine[0], -swayHips * 0.4, -rollHips * 0.3];
      if (animated.chest) animated.chest = [animated.chest[0], -swayHips * 0.3, -rollHips * 0.2];

      // Genoux : flexion souple en absorption naturelle
      const kneeBounce = 0.04 + Math.abs(Math.sin(tempo)) * 0.05;
      if (animated.leftLowerLeg) animated.leftLowerLeg = [kneeBounce, 0, 0];
      if (animated.rightLowerLeg) animated.rightLowerLeg = [kneeBounce, 0, 0];

      // Bras : balancement gracieux avec coudes pliés naturellement vers l'avant (Z négatif)
      if (animated.leftUpperArm) {
        animated.leftUpperArm = [0.18 + armWave, 0.12, -1.05 + Math.cos(tempoHalf) * 0.10];
      }
      if (animated.rightUpperArm) {
        animated.rightUpperArm = [0.18 - armWave, -0.12, 1.05 - Math.cos(tempoHalf) * 0.10];
      }
      if (animated.leftLowerArm) {
        animated.leftLowerArm = [0, 0, -1.15 - elbowBounce];
      }
      if (animated.rightLowerArm) {
        animated.rightLowerArm = [0, 0, -1.15 + elbowBounce];
      }
      if (animated.head) {
        animated.head = [
          animated.head[0] + Math.sin(tempo) * 0.035,
          swayHips * 0.5,
          -rollHips * 0.4,
        ];
      }
    }
    if (poseTo === "samba") {
      // Cadence festive latino à ~1.75 Hz (105 BPM, vivante et entraînante)
      const tempo = t * 11.0;
      const swayHips = Math.sin(tempo) * 0.12;
      const rollHips = Math.sin(tempo * 2.0) * 0.08;
      const yawHips = Math.cos(tempo) * 0.06;

      // Bassin en figure-8 fluide
      if (animated.hips) animated.hips = [0, yawHips, swayHips];
      if (animated.spine) animated.spine = [0.04, -yawHips * 0.5, -swayHips * 0.4];
      if (animated.chest) animated.chest = [0.05, -yawHips * 0.3, -swayHips * 0.3];

      // Genoux : flexion alternée marquée synchronisée sur le déhanché
      const kneeL = 0.08 + Math.max(0, Math.sin(tempo)) * 0.15;
      const kneeR = 0.08 + Math.max(0, -Math.sin(tempo)) * 0.15;
      if (animated.leftLowerLeg) animated.leftLowerLeg = [kneeL, 0, 0];
      if (animated.rightLowerLeg) animated.rightLowerLeg = [kneeR, 0, 0];

      // Bras aériens asymétriques en mouvement gracieux
      if (animated.leftUpperArm) {
        animated.leftUpperArm = [0.35 + Math.sin(tempo) * 0.15, 0.20, -1.35 + Math.cos(tempo) * 0.12];
      }
      if (animated.rightUpperArm) {
        animated.rightUpperArm = [0.15 - Math.sin(tempo) * 0.15, -0.20, 0.85 - Math.cos(tempo) * 0.12];
      }
      if (animated.leftLowerArm) {
        animated.leftLowerArm = [0, 0, -1.40 + Math.sin(tempo) * 0.18];
      }
      if (animated.rightLowerArm) {
        animated.rightLowerArm = [0, 0, -0.80 - Math.sin(tempo) * 0.18];
      }
      if (animated.head) {
        animated.head = [0.04, yawHips * 0.6, -swayHips * 0.4];
      }
    }
    if (poseTo === "hiphop") {
      // Cadence street bounce à ~1.43 Hz (86 BPM, attitude posée)
      const tempo = t * 9.0;
      const bounce = Math.abs(Math.sin(tempo));
      const nod = Math.sin(tempo) * 0.12;

      // Hanches et torse penchés vers l'avant avec bounce
      if (animated.hips) animated.hips = [0.08 + bounce * 0.03, 0, Math.sin(tempo * 0.5) * 0.04];
      if (animated.spine) animated.spine = [0.14, 0, 0];
      if (animated.chest) animated.chest = [0.10, 0, 0];
      if (animated.head) animated.head = [0.12 + nod, 0, 0];

      // Genoux fléchis en absorption street
      const kneeBend = 0.18 + bounce * 0.12;
      if (animated.leftLowerLeg) animated.leftLowerLeg = [kneeBend, 0, 0];
      if (animated.rightLowerLeg) animated.rightLowerLeg = [kneeBend, 0, 0];

      // Coudes ouverts, bras qui pulsent avec le beat
      if (animated.leftUpperArm) {
        animated.leftUpperArm = [0.45 + nod * 0.4, 0.30, -1.25];
      }
      if (animated.rightUpperArm) {
        animated.rightUpperArm = [0.45 + nod * 0.4, -0.30, 1.25];
      }
      if (animated.leftLowerArm) {
        animated.leftLowerArm = [0, 0, -1.50 - bounce * 0.18];
      }
      if (animated.rightLowerArm) {
        animated.rightLowerArm = [0, 0, -1.50 - bounce * 0.18];
      }
    }
    if (poseTo === "robot") {
      // Onde de wave / popping robotique à ~0.72 Hz
      const tempo = t * 4.5;
      const phaseLeftHand = Math.sin(tempo);
      const phaseLeftElbow = Math.sin(tempo - 0.4);
      const phaseLeftArm = Math.sin(tempo - 0.8);
      const phaseChest = Math.sin(tempo - 1.2);
      const phaseRightArm = Math.sin(tempo - 1.6);
      const phaseRightElbow = Math.sin(tempo - 2.0);
      const phaseRightHand = Math.sin(tempo - 2.4);

      // Micro-pulsation / stop robotique sec
      const stepPop = (Math.floor(tempo * 2.0) % 2 === 0 ? 0.04 : -0.04) * Math.exp(-((tempo * 2) % 1) * 3);

      if (animated.leftUpperArm) {
        animated.leftUpperArm = [0.10, 0, -1.45 + phaseLeftArm * 0.25 + stepPop];
      }
      if (animated.leftLowerArm) {
        animated.leftLowerArm = [0, 0, -0.40 + phaseLeftElbow * 0.35];
      }
      if (animated.leftHand) {
        animated.leftHand = [0, 0, 0.20 + phaseLeftHand * 0.30];
      }
      if (animated.chest) {
        animated.chest = [0.04, phaseChest * 0.08, 0];
      }
      if (animated.rightUpperArm) {
        animated.rightUpperArm = [0.10, 0, 1.45 - phaseRightArm * 0.25 - stepPop];
      }
      if (animated.rightLowerArm) {
        animated.rightLowerArm = [0, 0, -0.40 + phaseRightElbow * 0.35];
      }
      if (animated.rightHand) {
        animated.rightHand = [0, 0, -0.20 - phaseRightHand * 0.30];
      }
      if (animated.head) {
        animated.head = [0, phaseChest * 0.10, 0];
      }
    }
    if (poseTo === "disco") {
      // Cadence disco rythmée à ~1.27 Hz (76 BPM / demi-temps 152)
      const tempo = t * 8.0;
      const phase = tempo % (Math.PI * 4);
      const isUp = phase < Math.PI * 2;
      const reach = isUp ? 1 : 0;
      const twist = Math.sin(tempo) * 0.14;

      // Bras droit iconique disco pointé vers le ciel / redescendant vers la hanche
      if (animated.rightUpperArm) {
        animated.rightUpperArm = [
          -0.55 * reach + 0.30 * (1 - reach),
          -0.20,
          2.45 * reach + 0.90 * (1 - reach),
        ];
      }
      if (animated.rightLowerArm) {
        animated.rightLowerArm = [0, 0, -0.25 * reach - 1.45 * (1 - reach)];
      }
      // Bras gauche posé sur la hanche
      if (animated.leftUpperArm) {
        animated.leftUpperArm = [0.15, 0.25, -0.85];
      }
      if (animated.leftLowerArm) {
        animated.leftLowerArm = [0, 0, -1.65];
      }

      // Twist hanches et buste en opposition
      if (animated.hips) animated.hips = [0, twist, Math.cos(tempo) * 0.07];
      if (animated.spine) animated.spine = [0.04, -twist * 0.6, -Math.cos(tempo) * 0.04];
      if (animated.chest) animated.chest = [0.06, -twist * 0.4, 0];
      if (animated.head) animated.head = [-0.05, twist * 0.4, 0];
      if (animated.leftLowerLeg) animated.leftLowerLeg = [0.06 + Math.abs(Math.sin(tempo)) * 0.06, 0, 0];
      if (animated.rightLowerLeg) animated.rightLowerLeg = [0.06 + Math.abs(Math.sin(tempo + Math.PI)) * 0.06, 0, 0];
    }
    if (poseTo === "spin") {
      const spinFlutter = Math.sin(t * 4.0) * 0.04;
      if (animated.leftUpperArm) animated.leftUpperArm[2] = -0.85 + spinFlutter;
      if (animated.rightUpperArm) animated.rightUpperArm[2] = 0.85 - spinFlutter;
      if (animated.leftLowerArm) animated.leftLowerArm = [0, 0, -0.45];
      if (animated.rightLowerArm) animated.rightLowerArm = [0, 0, -0.45];
    }
    if (poseTo === "jump") {
      // Célébration / Victoire : saut joyeux harmonieux avec élan des bras et amorti
      const jumpPhase = t * 4.0;
      const jumpWave = Math.sin(jumpPhase);
      const isAscending = jumpWave > 0;
      const armPulse = jumpWave * 0.08;

      if (animated.leftUpperArm) animated.leftUpperArm[2] = -2.35 - armPulse;
      if (animated.rightUpperArm) animated.rightUpperArm[2] = 2.35 + armPulse;
      if (animated.leftLowerArm) animated.leftLowerArm = [0, 0, -0.55 + armPulse * 0.3];
      if (animated.rightLowerArm) animated.rightLowerArm = [0, 0, -0.55 + armPulse * 0.3];

      const landingCushion = Math.max(0, -jumpWave) * 0.10;
      if (animated.leftLowerLeg) animated.leftLowerLeg = [0.06 + landingCushion, 0, 0];
      if (animated.rightLowerLeg) animated.rightLowerLeg = [0.06 + landingCushion, 0, 0];

      if (animated.head) {
        animated.head = [animated.head[0] + (isAscending ? 0.05 : -0.02), animated.head[1], animated.head[2]];
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
    if (poseTo === "fingerHeart") {
      // Cadence entraînante K-Pop Idol à ~105 BPM (~1.75 Hz)
      const tempo = t * 6.5;
      const tempoHalf = tempo * 0.5;
      const swayHips = Math.sin(tempoHalf) * 0.08;
      const rollHips = Math.cos(tempoHalf) * 0.05;
      const heartPulse = Math.sin(tempo) * 0.035;
      const kneeBounce = 0.02 + Math.abs(Math.sin(tempo)) * 0.035;

      // 1. Déhanché et rebond pop fluide du bassin et du torse
      if (animated.hips) animated.hips = [0, 0.07 + swayHips * 0.6, -0.05 + rollHips * 0.5];
      if (animated.spine) animated.spine = [0.02, -0.03 - swayHips * 0.3, 0.03 - rollHips * 0.3];
      if (animated.chest) animated.chest = [0.04, -0.02 - swayHips * 0.2, 0.02 - rollHips * 0.2];

      // 2. Genoux souples absorbant le tempo pop
      if (animated.leftLowerLeg) animated.leftLowerLeg = [kneeBounce, 0, 0];
      if (animated.rightLowerLeg) animated.rightLowerLeg = [kneeBounce * 0.7, 0, 0];

      // 3. Bras droit : geste Mini Heart K-Pop au buste/menton vers la caméra avec pulsation
      if (animated.rightUpperArm) {
        animated.rightUpperArm = [0.38 + swayHips * 0.12, 0.18, 1.05];
      }
      if (animated.rightLowerArm) {
        animated.rightLowerArm = [0.10, 0.25, -1.80 - heartPulse * 0.35];
      }
      if (animated.rightHand) {
        animated.rightHand = [
          0.18 + heartPulse * 0.6,
          -0.15,
          0.22 + heartPulse * 0.4,
        ];
      }

      // 4. Bras gauche : main sur la hanche qui ondule avec le déhanché
      if (animated.leftUpperArm) {
        animated.leftUpperArm = [0.18 + Math.cos(tempoHalf) * 0.05, -0.15, -0.92];
      }
      if (animated.leftLowerArm) {
        animated.leftLowerArm = [0.08, 0.15, -1.05 - Math.sin(tempoHalf) * 0.08];
      }

      // 5. Tête penchée espiègle vers la main qui dodeline au rythme du tempo
      const headNod = Math.sin(tempo) * 0.03;
      if (animated.head) {
        animated.head = [
          -0.05 + headNod,
          -0.06 + swayHips * 0.3,
          0.18 + Math.cos(tempoHalf) * 0.05,
        ];
      }
    }
    if (poseTo === "cyberGroove") {
      // Cadence 128 BPM (pulsation de base 13.404 rad/s)
      const tempo = t * 13.404;
      const tempoHalf = tempo * 0.5; // demi-temps (64 BPM)
      const tempoQuarter = tempo * 0.25; // 4 temps (32 BPM)

      // 1. Déphasages cinématiques organiques (Follow-Through / Inertie humaine vivante)
      // Le bassin initie le groove, la colonne transmet avec retard, puis la cage thoracique, les épaules et la tête
      const phaseHips = tempoHalf;
      const phaseSpine = tempoHalf - 0.28;
      const phaseChest = tempoHalf - 0.48;
      const phaseHead = tempo - 0.60;
      const phaseArm = tempoHalf - 0.35;

      // 2. Alternance fluide : Déhanché Diva Cambrée <-> Power Drop Jambes Fléchies (~7,5s par phase)
      const cycleTime = (t * 0.42) % (Math.PI * 2.0);
      const rawDrop = Math.max(0, Math.sin(cycleTime));
      const dropFactor = rawDrop * rawDrop * (3 - 2 * rawDrop); // 0 = debout diva, 1 = drop genoux fléchis
      const divaFactor = 1.0 - dropFactor * 0.75;

      // 3. Déhanché en Huit (Lemniscate / Courbe de Lissajous naturelle)
      const hipSway = Math.sin(phaseHips) * 0.24 * divaFactor; // rotation Y (~14°)
      const hipRoll = Math.cos(phaseHips) * 0.16 * divaFactor; // bascule latérale Z (~9°)
      const hipTwist = Math.sin(tempo) * 0.05 * divaFactor;   // micro-twist au kick
      const hipPitch = -0.12 - dropFactor * 0.14 + Math.abs(Math.sin(tempo)) * 0.03; // cambrure lombaire féminine

      // 4. Rebond élastique et absorption des genoux au kick de batterie (128 BPM)
      const kickCurve = Math.pow(Math.max(0, Math.sin(tempo)), 2.2);
      const kneeBounce = kickCurve * 0.18;
      const footTap = kickCurve * 0.22;

      // Hanches
      if (animated.hips) {
        animated.hips = [hipPitch, hipSway, hipRoll + hipTwist];
      }

      // Colonne & Buste : courbure en S compensatoire avec retard d'inertie
      if (animated.spine) {
        animated.spine = [
          0.06 + dropFactor * 0.16 - hipPitch * 0.20,
          -Math.sin(phaseSpine) * 0.18 * divaFactor,
          -Math.cos(phaseSpine) * 0.15 * divaFactor,
        ];
      }
      if (animated.chest) {
        animated.chest = [
          0.12 + dropFactor * 0.12,
          -Math.sin(phaseChest) * 0.14 * divaFactor,
          -Math.cos(phaseChest) * 0.12 * divaFactor,
        ];
      }

      // Tête & Cou : posture de chant habitée (tête inclinée en arrière vers le micro avec émotion)
      const headRock = Math.sin(phaseHead) * 0.08;
      if (animated.head) {
        animated.head = [
          -0.18 - dropFactor * 0.08 + headRock, // tête renversée en arrière vers le micro
          -Math.sin(phaseChest) * 0.10 * divaFactor + 0.05, // léger 3/4 profil captivant
          0.10 + Math.cos(tempoHalf) * 0.05, // inclinaison gracieuse vers l'épaule
        ];
      }
      if (animated.neck) {
        animated.neck = [-0.08 - dropFactor * 0.04, 0.03, 0.03];
      }

      // 5. JAMBES & PIEDS : Stance large, pieds ouverts en éventail et genoux fléchis
      if (dropFactor > 0.15) {
        // --- PHASE JAMBES FLÉCHIES (Drop Power Stance de concert) ---
        // Stance très dynamique, cuisses bien écartées, genoux fléchis à ~50°
        const squatKnee = 0.85 * dropFactor + kneeBounce;
        if (animated.leftUpperLeg) {
          animated.leftUpperLeg = [
            -0.42 * dropFactor, // cuisse avancée
            -0.25 * dropFactor, // hanche ouverte vers l'extérieur
            -0.34 * dropFactor, // écartement large et stable
          ];
        }
        if (animated.leftLowerLeg) {
          animated.leftLowerLeg = [squatKnee, 0, 0];
        }
        if (animated.leftFoot) {
          animated.leftFoot = [-0.22 * dropFactor, -0.28, 0]; // pied ouvert en éventail
        }

        if (animated.rightUpperLeg) {
          animated.rightUpperLeg = [
            -0.42 * dropFactor,
            0.25 * dropFactor,
            0.34 * dropFactor,
          ];
        }
        if (animated.rightLowerLeg) {
          animated.rightLowerLeg = [squatKnee, 0, 0];
        }
        if (animated.rightFoot) {
          animated.rightFoot = [-0.22 * dropFactor, 0.28, 0];
        }
      } else {
        // --- PHASE DÉHANCHÉ DIVA (Contrapposto : Jambe d'appui vs Jambe libre) ---
        // Stance ouverte garantie : les cuisses ne sont JAMAIS collées ni croisées
        const isLeftBearing = hipSway < 0;
        if (animated.leftUpperLeg) {
          animated.leftUpperLeg = [
            isLeftBearing ? 0.06 : -0.26, // jambe libre avancée ou jambe d'appui en retrait
            -0.18, // hanche ouverte
            -0.26 - (isLeftBearing ? 0.04 : -0.04), // écartement constant vers la gauche
          ];
        }
        if (animated.leftLowerLeg) {
          // Genou toujours fléchi (jambe d'appui déverrouillée à 0.25 rad, jambe libre fléchie à 0.55 rad)
          animated.leftLowerLeg = [isLeftBearing ? 0.25 + kneeBounce * 0.4 : 0.55 + kneeBounce, 0, 0];
        }
        if (animated.leftFoot) {
          animated.leftFoot = [isLeftBearing ? 0.02 : footTap * 0.7, -0.25, 0];
        }

        if (animated.rightUpperLeg) {
          animated.rightUpperLeg = [
            !isLeftBearing ? 0.06 : -0.26,
            0.18,
            0.26 + (!isLeftBearing ? 0.04 : -0.04), // écartement constant vers la droite
          ];
        }
        if (animated.rightLowerLeg) {
          animated.rightLowerLeg = [!isLeftBearing ? 0.25 + kneeBounce * 0.4 : 0.55 + kneeBounce, 0, 0];
        }
        if (animated.rightFoot) {
          animated.rightFoot = [!isLeftBearing ? 0.02 : footTap * 0.7, 0.25, 0];
        }
      }

      // 6. BRAS DROIT : Micro tenu directement devant la bouche (Posture vocale authentique)
      const micBob = Math.sin(tempo) * 0.012;
      if (animated.rightShoulder) {
        animated.rightShoulder = [0.06, 0.04, -0.06];
      }
      if (animated.rightUpperArm) {
        // Bras descendant le long du flanc droit et orienté vers l'avant-buste
        animated.rightUpperArm = [0.32 + micBob * 0.15 + dropFactor * 0.06, 0.35, 0.85];
      }
      if (animated.rightLowerArm) {
        // Coude replié fermement vers le menton et l'intérieur du visage
        animated.rightLowerArm = [-0.22, -0.16, -2.10 + micBob * 0.2];
      }
      if (animated.rightHand) {
        // Poignet dressant le micro directement sous les lèvres
        animated.rightHand = [0.18, -0.15, 0.32];
      }

      // Doigts main droite (fermeture ferme sur le manche du micro)
      animated.rightThumbProximal = [0.55, 0.30, 0];
      animated.rightThumbDistal = [0.45, 0, 0];
      animated.rightIndexProximal = [1.40, 0, 0];
      animated.rightIndexIntermediate = [1.30, 0, 0];
      animated.rightMiddleProximal = [1.45, 0, 0];
      animated.rightMiddleIntermediate = [1.35, 0, 0];
      animated.rightRingProximal = [1.45, 0, 0];
      animated.rightRingIntermediate = [1.35, 0, 0];
      animated.rightLittleProximal = [1.40, 0, 0];
      animated.rightLittleIntermediate = [1.25, 0, 0];

      // 7. BRAS GAUCHE : ÉLÉGANCE ET NATUREL (JAMAIS RAIDE NI EN L-SHAPE)
      if (dropFactor > 0.30) {
        // Au Drop : Geste vocal ample et expressif vers le public / la foule
        const reach = Math.sin(tempoHalf) * 0.08;
        if (animated.leftShoulder) animated.leftShoulder = [0.04, 0, 0.02];
        if (animated.leftUpperArm) {
          animated.leftUpperArm = [0.45 + reach, 0.12, -0.95];
        }
        if (animated.leftLowerArm) {
          animated.leftLowerArm = [0.20, 0.15, -0.90];
        }
        if (animated.leftHand) {
          animated.leftHand = [0.22, 0.10, 0.12]; // paume ouverte vers le ciel
        }
        animated.leftThumbProximal = [0.15, 0, 0];
        animated.leftIndexProximal = [0.18, 0, 0];
        animated.leftMiddleProximal = [0.22, 0, 0];
        animated.leftRingProximal = [0.22, 0, 0];
        animated.leftLittleProximal = [0.18, 0, 0];
      } else {
        // En Déhanché Diva : Main délicatement posée sur la hanche gauche
        const hipBob = Math.sin(phaseArm) * 0.04;
        if (animated.leftShoulder) animated.leftShoulder = [0.02, -0.02, 0.02];
        if (animated.leftUpperArm) {
          // Bras le long du flanc, coude souple vers l'extérieur
          animated.leftUpperArm = [0.12 + hipBob, 0.10, -1.15];
        }
        if (animated.leftLowerArm) {
          // Avant-bras replié ramenant la main sur la crête iliaque
          animated.leftLowerArm = [0.18, 0.12, -1.25 + hipBob * 0.5];
        }
        if (animated.leftHand) {
          animated.leftHand = [-0.10, 0.08, -0.15];
        }
        // Doigts détendus épousant la hanche
        animated.leftThumbProximal = [0.25, 0.10, 0];
        animated.leftIndexProximal = [0.30, 0, 0];
        animated.leftMiddleProximal = [0.35, 0, 0];
        animated.leftRingProximal = [0.35, 0, 0];
        animated.leftLittleProximal = [0.30, 0, 0];
      }
    }
    if (poseTo === "aeysaSinging") {
      // Cadence 128 BPM (pulsation de base 13.404 rad/s)
      const tempo = t * 13.404;
      const tempoHalf = tempo * 0.5;
      const breathe = Math.sin(t * 1.8);

      // 1. Déphasages cinématiques doux et naturels
      const phaseHips = tempoHalf;
      const phaseSpine = tempoHalf - 0.25;
      const phaseChest = tempoHalf - 0.45;
      const phaseHead = tempo - 0.50;

      // 2. Déhanché Lemniscate subtil & fluide (aucun squat, cambrure naturelle)
      const hipSway = Math.sin(phaseHips) * 0.14; // rotation Y (~8°)
      const hipRoll = Math.cos(phaseHips) * 0.08; // bascule Z (~4.5°)
      const hipPitch = -0.06 + Math.sin(tempo) * 0.015; // cambrure lombaire douce

      if (animated.hips) {
        animated.hips = [hipPitch, hipSway, hipRoll];
      }

      // 3. Colonne & Cage thoracique (ondulation de chanteuse en S + respiration vivante)
      if (animated.spine) {
        animated.spine = [
          0.04 + breathe * 0.015,
          -Math.sin(phaseSpine) * 0.09,
          -Math.cos(phaseSpine) * 0.07,
        ];
      }
      if (animated.chest) {
        animated.chest = [
          0.07 + breathe * 0.025,
          -Math.sin(phaseChest) * 0.07,
          -Math.cos(phaseChest) * 0.06,
        ];
      }

      // 4. Tête & Regard : maintien vers la caméra avec contact visuel direct et micro-tilts musicaux
      const headNod = Math.sin(phaseHead) * 0.038;
      const headTilt = Math.cos(tempoHalf) * 0.045;
      if (animated.head) {
        animated.head = [
          -0.10 + headNod,
          -Math.sin(phaseChest) * 0.05,
          headTilt,
        ];
      }
      if (animated.neck) {
        animated.neck = [-0.04, 0.01, 0.01];
      }

      // 5. Jambes : stance stable, déhanché contrapposto léger et genoux souples (sans accroupissement)
      const isLeftBearing = hipSway < 0;
      const kneeSoft = Math.pow(Math.max(0, Math.sin(tempo)), 2.0) * 0.05;
      if (animated.leftUpperLeg) {
        animated.leftUpperLeg = [
          isLeftBearing ? 0.02 : -0.12,
          -0.08,
          -0.16,
        ];
      }
      if (animated.leftLowerLeg) {
        animated.leftLowerLeg = [isLeftBearing ? 0.15 + kneeSoft : 0.28 + kneeSoft, 0, 0];
      }
      if (animated.leftFoot) {
        animated.leftFoot = [0.02, -0.12, 0];
      }

      if (animated.rightUpperLeg) {
        animated.rightUpperLeg = [
          !isLeftBearing ? 0.02 : -0.12,
          0.08,
          0.16,
        ];
      }
      if (animated.rightLowerLeg) {
        animated.rightLowerLeg = [!isLeftBearing ? 0.15 + kneeSoft : 0.28 + kneeSoft, 0, 0];
      }
      if (animated.rightFoot) {
        animated.rightFoot = [0.02, 0.12, 0];
      }

      // 6. Bras droit : Micro tenu délicatement juste devant les lèvres
      const micBob = Math.sin(tempo) * 0.008;
      if (animated.rightShoulder) {
        animated.rightShoulder = [0.04, 0.02, -0.04];
      }
      if (animated.rightUpperArm) {
        animated.rightUpperArm = [0.32 + micBob * 0.1, 0.35, 0.85];
      }
      if (animated.rightLowerArm) {
        animated.rightLowerArm = [-0.21, -0.15, -2.12 + micBob * 0.15];
      }
      if (animated.rightHand) {
        animated.rightHand = [0.18, -0.14, 0.32];
      }
      animated.rightThumbProximal = [0.55, 0.30, 0];
      animated.rightThumbDistal = [0.45, 0, 0];
      animated.rightIndexProximal = [1.40, 0, 0];
      animated.rightIndexIntermediate = [1.30, 0, 0];
      animated.rightMiddleProximal = [1.45, 0, 0];
      animated.rightMiddleIntermediate = [1.35, 0, 0];
      animated.rightRingProximal = [1.45, 0, 0];
      animated.rightRingIntermediate = [1.35, 0, 0];
      animated.rightLittleProximal = [1.40, 0, 0];
      animated.rightLittleIntermediate = [1.25, 0, 0];

      // 7. Bras gauche : gestuelle expressive de chanteuse (alternance subtile entre plexus et geste d'accueil)
      const gestureCycle = Math.sin(t * 0.35); // cycle lent de ~18s
      const isChestHand = gestureCycle > 0;
      if (isChestHand) {
        const handBreath = breathe * 0.03;
        if (animated.leftShoulder) animated.leftShoulder = [0.02, 0.01, 0.02];
        if (animated.leftUpperArm) {
          animated.leftUpperArm = [0.26 + handBreath, 0.18, -0.85];
        }
        if (animated.leftLowerArm) {
          animated.leftLowerArm = [0.22, 0.16, -1.35];
        }
        if (animated.leftHand) {
          animated.leftHand = [0.15, 0.12, 0.10];
        }
        animated.leftThumbProximal = [0.20, 0.08, 0];
        animated.leftIndexProximal = [0.22, 0, 0];
        animated.leftMiddleProximal = [0.25, 0, 0];
        animated.leftRingProximal = [0.26, 0, 0];
        animated.leftLittleProximal = [0.22, 0, 0];
      } else {
        const openReach = Math.sin(tempoHalf) * 0.04;
        if (animated.leftShoulder) animated.leftShoulder = [0.03, 0.01, 0.02];
        if (animated.leftUpperArm) {
          animated.leftUpperArm = [0.32 + openReach, 0.12, -0.90];
        }
        if (animated.leftLowerArm) {
          animated.leftLowerArm = [0.18, 0.14, -0.95];
        }
        if (animated.leftHand) {
          animated.leftHand = [0.20, 0.08, 0.10];
        }
        animated.leftThumbProximal = [0.15, 0, 0];
        animated.leftIndexProximal = [0.18, 0, 0];
        animated.leftMiddleProximal = [0.20, 0, 0];
        animated.leftRingProximal = [0.20, 0, 0];
        animated.leftLittleProximal = [0.18, 0, 0];
      }
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
      if (activeVrmaAction) stopVRMA(0.35);
      poseFrom = poseTo;
      poseTo = poseReturnTo || "idle";
      poseBlend = 0;
      poseHoldUntil = 0;
      try {
        vrm?.expressionManager?.setValue("blinkRight", 0);
        vrm?.expressionManager?.setValue("blinkLeft", 0);
      } catch (_) { }
      setMood("serene");
      // Retour automatique fluide en vue buste après la fin d'une danse
      if (isDanceFraming && baseFraming === "bust") {
        framing = "bust";
        isDanceFraming = false;
        if (vrm) frameVrm(vrm);
      }
    }
    // Si une animation VRMA est active, l'AnimationMixer contrôle les bones en mocap native
    if (activeVrmaAction) return;

    // Blend ~0.35s
    if (poseBlend < 1) {
      poseBlend = Math.min(1, poseBlend + dt / 0.35);
    }
    const a = POSE_EULERS[poseFrom] || POSE_EULERS.idle;
    const b = POSE_EULERS[poseTo] || POSE_EULERS.idle;
    const smooth = poseBlend * poseBlend * (3 - 2 * poseBlend);
    applyBoneEulers(lerpEulerMap(a, b, smooth), t);
  }

  function updateHeadScale(v) {
    if (!v?.humanoid) return;
    try {
      // Étape B : Morphologie adulte élancée de scène (gynoïde chanteuse)
      // 1. Tête légèrement affinée (ratio adulte élancé ~7.5 têtes)
      const headBone = v.humanoid.getNormalizedBoneNode?.("head");
      if (headBone) {
        headBone.scale.set(0.92, 0.92, 0.92);
      }
      // 2. Cou affiné et élancé (port altier)
      const neckBone = v.humanoid.getNormalizedBoneNode?.("neck");
      if (neckBone) {
        neckBone.scale.set(0.92, 1.06, 0.92);
      }
      // 3. Hanches plus marquées et féminines
      const hipsBone = v.humanoid.getNormalizedBoneNode?.("hips");
      if (hipsBone) {
        hipsBone.scale.set(1.09, 1.0, 1.08);
      }
      // 4. Jambes galbées et élancées (gain de stature)
      const leftUpperLeg = v.humanoid.getNormalizedBoneNode?.("leftUpperLeg");
      const rightUpperLeg = v.humanoid.getNormalizedBoneNode?.("rightUpperLeg");
      if (leftUpperLeg) leftUpperLeg.scale.set(0.98, 1.07, 0.98);
      if (rightUpperLeg) rightUpperLeg.scale.set(0.98, 1.07, 0.98);

      const leftLowerLeg = v.humanoid.getNormalizedBoneNode?.("leftLowerLeg");
      const rightLowerLeg = v.humanoid.getNormalizedBoneNode?.("rightLowerLeg");
      if (leftLowerLeg) leftLowerLeg.scale.set(0.98, 1.07, 0.98);
      if (rightLowerLeg) rightLowerLeg.scale.set(0.98, 1.07, 0.98);
    } catch (_) { }
  }

  function frameVrm(v) {
    updateHeadScale(v);
    v.scene.updateMatrixWorld(true);

    if (framing === "bust") {
      let headPos = new THREE.Vector3(0, 1.4, 0);
      try {
        const head = v.humanoid?.getNormalizedBoneNode?.("head");
        const hips = v.humanoid?.getNormalizedBoneNode?.("hips");
        if (head) {
          head.getWorldPosition(headPos);
        } else if (hips) {
          hips.getWorldPosition(headPos);
          headPos.y += 0.5;
        }
      } catch (_) { }

      // Cadrage portrait aéré centré sur la tête et le haut du buste :
      // On vise légèrement sous le nez (headPos.y - 0.02) avec recul (dist = 1.30)
      // pour que toute la chevelure soit entièrement visible dans l'encart avec une belle marge au-dessus,
      // tout en révélant le cou, les épaulières mecha et le buste.
      const lookY = headPos.y - 0.02;
      const dist = 1.30;
      targetCamPos.set(headPos.x, lookY, headPos.z + dist);
      targetLookAt.set(headPos.x, lookY, headPos.z);
      targetFov = 24;

      if (!cameraInitialized) {
        currentCamPos.copy(targetCamPos);
        currentLookAt.copy(targetLookAt);
        currentFov = targetFov;
        camera.fov = currentFov;
        camera.position.copy(currentCamPos);
        camera.lookAt(currentLookAt);
        camera.updateProjectionMatrix();
        cameraInitialized = true;
      }
      return;
    }

    const box = new THREE.Box3().setFromObject(v.scene);
    const size = new THREE.Vector3();
    const center = new THREE.Vector3();
    box.getSize(size);
    box.getCenter(center);
    if (!Number.isFinite(size.y) || size.y < 0.2) {
      center.set(0, 0.9, 0);
      size.set(0.45, 1.45, 0.4);
    }
    const fovRad = (28 * Math.PI) / 180;
    // Cadrage compact avec respiration latérale et supérieure (+12% marge tête et mains)
    const neededH = size.y * 1.12;
    const dist = neededH / (2 * Math.tan(fovRad / 2));
    const visibleH = 2.0 * dist * Math.tan(fovRad / 2);
    // Alignement parfait au sol : les pieds reposent sur le bord inférieur (barre des tâches)
    const lookY = Math.max(0, box.min.y) - 0.005 + (visibleH / 2);
    // Caméra centrée de manière inébranlable sur l'axe d'origine (X=0, Z=0)
    targetCamPos.set(0, lookY, dist);
    targetLookAt.set(0, lookY, 0);
    targetFov = 28;

    if (!cameraInitialized) {
      currentCamPos.copy(targetCamPos);
      currentLookAt.copy(targetLookAt);
      currentFov = targetFov;
      camera.fov = currentFov;
      camera.position.copy(currentCamPos);
      camera.lookAt(currentLookAt);
      camera.updateProjectionMatrix();
      cameraInitialized = true;
    }
  }

  function faceTheCamera(v) {
    targetHeadingY = 0;
    currentHeadingY = 0;
    v.scene.rotation.y = 0;
    v.scene.position.set(0, 0, 0);
    v.scene.updateMatrixWorld(true);
  }

  function setFraming(next) {
    baseFraming = String(next || "").toLowerCase() === "bust" ? "bust" : "full";
    framing = baseFraming;
    isDanceFraming = false;
    if (vrm) {
      updateHeadScale(vrm);
      frameVrm(vrm);
    }
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

    const textureLoader = new THREE.TextureLoader();
    const base = modelUrl.includes("/") ? modelUrl.substring(0, modelUrl.lastIndexOf("/")) : "./vrm";
    const vrmDir = base || "./vrm";
    const androidBodyTex = textureLoader.load(
      `${vrmDir}/body_skin_android.png?v=cyber_concert_v1`,
      (tex) => {
        tex.colorSpace = THREE.SRGBColorSpace;
        tex.flipY = false;
        tex.needsUpdate = true;
      },
      undefined,
      (err) => console.warn("[vrm_pet] err loading body texture:", err)
    );
    const androidFaceTex = textureLoader.load(
      `${vrmDir}/face_skin_android.png?v=mecha_face_restored_v2`,
      (tex) => {
        tex.colorSpace = THREE.SRGBColorSpace;
        tex.flipY = false;
        tex.needsUpdate = true;
      },
      undefined,
      (err) => console.warn("[vrm_pet] err loading face texture:", err)
    );
    const androidHairTex = textureLoader.load(
      `${vrmDir}/hair_android.png?v=cyber_concert_v1`,
      (tex) => {
        tex.colorSpace = THREE.SRGBColorSpace;
        tex.flipY = false;
        tex.needsUpdate = true;
      },
      undefined,
      (err) => console.warn("[vrm_pet] err loading hair texture:", err)
    );
    const metallicMatcapTex = textureLoader.load(
      `${vrmDir}/metallic_matcap.png?v=mecha_v17`,
      (tex) => {
        tex.colorSpace = THREE.SRGBColorSpace;
        tex.needsUpdate = true;
      },
      undefined,
      (err) => console.warn("[vrm_pet] err loading matcap texture:", err)
    );
    const rimMultiplyMaskTex = textureLoader.load(
      `${vrmDir}/rim_multiply_mask.png?v=mecha_v17`,
      (tex) => {
        tex.colorSpace = THREE.NoColorSpace;
        tex.flipY = false;
        tex.needsUpdate = true;
      },
      undefined,
      (err) => console.warn("[vrm_pet] err loading rim multiply mask:", err)
    );

    createdTextures.push(
      cyanTexture,
      cyanBrightTexture,
      darkSocketTexture,
      androidBodyTex,
      androidFaceTex,
      androidHairTex,
      metallicMatcapTex,
      rimMultiplyMaskTex
    );

    v.scene.traverse((child) => {
      if (!child.isMesh) return;
      const materials = Array.isArray(child.material) ? child.material : [child.material];

      for (const m of materials) {
        const name = (m.name || "").toLowerCase();

        // 1. Optiques cybernétiques : Yeux néon cyan lumineux (comme l'illustration mascotte)
        if (name.includes("iris") || name.includes("eyeiris")) {
          if (m.color) m.color.setHex(0x00f5d4);
          if (m.shadeColor) m.shadeColor.setHex(0x00b894);
          m.map = cyanTexture;
          m.shadeMultiplyTexture = cyanTexture;
          if (m.emissive) {
            m.emissive.setHex(0x00f5d4);
            m.emissiveIntensity = 3.8;
          }
          m.needsUpdate = true;
        } else if (name.includes("eyehighlight")) {
          if (m.color) m.color.setHex(0xffffff);
          if (m.shadeColor) m.shadeColor.setHex(0xa0ffff);
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
          if (m.color) m.color.setHex(0x102038);
          m.needsUpdate = true;
        } else if (name.includes("mouth")) {
          if (m.color) m.color.setHex(0x182c4a);
          m.needsUpdate = true;
        }
        // 2a. Carrosserie mécanique du corps (Fidélité 2D directe : zéro bavure, reflets peints dans la texture)
        else if (name.includes("body")) {
          if (m.color) m.color.setHex(0xffffff);
          if (m.shadeColor) m.shadeColor.setHex(0x223348); // Ombre cel-shade titane propre
          m.map = androidBodyTex;
          m.shadeMultiplyTexture = androidBodyTex;
          // Zéro matcap ni rim dynamique pour éliminer toute bavure hors des plaques
          m.matcapTexture = null;
          m.rimMultiplyTexture = null;
          if (m.parametricRimColor) m.parametricRimColor.setHex(0x000000);
          if (m.rimLightingMix !== undefined) m.rimLightingMix = 1.0;
          if (m.shadingToonyFactor !== undefined) m.shadingToonyFactor = 0.95; // Découpe nette d'armure mecha
          m.needsUpdate = true;
        }
        // 2b. Visage androïde : Teint azur doux & détails expressifs préservés
        else if (name.includes("face") || name.includes("skin")) {
          if (m.color) m.color.setHex(0xffffff);
          if (m.shadeColor) m.shadeColor.setHex(0x385478);
          m.map = androidFaceTex;
          m.shadeMultiplyTexture = androidFaceTex;
          if (m.parametricRimColor) m.parametricRimColor.setHex(0x80ffff);
          if (m.rimLightingMix !== undefined) m.rimLightingMix = 0.35;
          if (m.parametricRimFresnelPower !== undefined) m.parametricRimFresnelPower = 2.5;
          m.needsUpdate = true;
        }
        // 3. Chevelure métallique indigo -> cyan (Reflet chrome fluide)
        else if (name.includes("hair")) {
          if (m.color) m.color.setHex(0xffffff);
          if (m.shadeColor) m.shadeColor.setHex(0x142036);
          m.map = androidHairTex;
          m.shadeMultiplyTexture = androidHairTex;
          m.matcapTexture = metallicMatcapTex;
          if (m.matcapFactor) {
            if (m.matcapFactor.setHex) m.matcapFactor.setHex(0x99ccff);
            else if (m.matcapFactor.set) m.matcapFactor.set(0.65, 0.8, 1.0);
          }
          if (m.parametricRimColor) m.parametricRimColor.setHex(0x00f5d4);
          if (m.rimLightingMix !== undefined) m.rimLightingMix = 0.0; // Reflet chrome vif non atténué
          if (m.parametricRimFresnelPower !== undefined) m.parametricRimFresnelPower = 2.2;
          m.needsUpdate = true;
        }
      }
    });

    // 4. Proportions harmonisées : tête équilibrée selon le cadrage (buste vs corps)
    updateHeadScale(v);
  }

  const loader = new GLTFLoader();
  loader.register((parser) => new VRMLoaderPlugin(parser));
  loader.register((parser) => new VRMAnimationLoaderPlugin(parser));

  // Système d'accessoires 3D modulaires pour l'avatar (lunettes HUD, datapad, écouteurs)
  const accessoryLoader = new GLTFLoader();
  const loadedAccessories = new Map();
  const equippedAccessories = new Map();

  const ACCESSORY_DEFS = {
    visor: {
      url: "accessories/cyber_visor.glb",
      bone: "head",
      offset: [0, 0.05, 0.08],
      rotation: [0, 0, 0],
      scale: 0.95,
    },
    datapad: {
      url: "accessories/holo_datapad.glb",
      bone: "leftHand",
      offset: [0.02, 0.04, 0.01],
      rotation: [0.2, 0.3, 1.2],
      scale: 0.85,
    },
    headset: {
      url: "accessories/neural_headset.glb",
      bone: "head",
      offset: [0.005, 0.045, 0.01],
      rotation: [0, 0, 0],
      scale: 0.95,
    },
  };

  async function equipAccessory(type, equip = true) {
    if (!vrm?.humanoid) return false;
    const def = ACCESSORY_DEFS[type];
    if (!def) {
      console.warn(`[vrm_pet] Accessoire inconnu: "${type}"`);
      return false;
    }

    // Priorité au bone physique du squelette dans le scene graph (Raw), fallback Normalisé
    const rawBone = (typeof vrm.humanoid.getRawBoneNode === "function" && vrm.humanoid.getRawBoneNode(def.bone));
    const normBone = (typeof vrm.humanoid.getNormalizedBoneNode === "function" && vrm.humanoid.getNormalizedBoneNode(def.bone));
    const boneNode = rawBone || normBone;
    if (!boneNode) {
      console.warn(`[vrm_pet] Os introuvable pour accessoire: "${def.bone}"`);
      return false;
    }

    if (!equip) {
      if (equippedAccessories.has(type)) {
        const obj = equippedAccessories.get(type);
        boneNode.remove(obj);
        equippedAccessories.delete(type);
        console.info(`[vrm_pet] Accessoire retiré: ${type}`);
      }
      return true;
    }

    if (equippedAccessories.has(type)) return true;

    let model = loadedAccessories.get(type);
    if (!model) {
      try {
        let base = "./vrm";
        if (modelUrl && modelUrl.includes("/")) {
          base = modelUrl.substring(0, modelUrl.lastIndexOf("/"));
        }
        const fullUrl = `${base}/${def.url}`;
        console.info(`[vrm_pet] Chargement accessoire ${type} depuis ${fullUrl}...`);
        const gltf = await accessoryLoader.loadAsync(fullUrl);
        model = gltf.scene;
        model.traverse((child) => {
          if (child.isMesh) {
            child.castShadow = true;
            child.receiveShadow = true;
            child.frustumCulled = false;
            if (child.material) {
              child.material.depthWrite = true;
              child.material.needsUpdate = true;
            }
          }
        });
        loadedAccessories.set(type, model);
      } catch (err) {
        console.warn(`[vrm_pet] Échec chargement accessoire "${type}":`, err);
        return false;
      }
    }

    model.position.set(def.offset[0], def.offset[1], def.offset[2]);
    model.rotation.set(def.rotation[0], def.rotation[1], def.rotation[2]);
    model.scale.set(def.scale, def.scale, def.scale);
    model.visible = true;
    boneNode.add(model);
    equippedAccessories.set(type, model);
    console.info(`[vrm_pet] Accessoire équipé: ${type} sur ${def.bone}`);
    return true;
  }

  function toggleAccessory(type) {
    const isEquipped = equippedAccessories.has(type);
    return equipAccessory(type, !isEquipped);
  }

  loader.load(
    modelUrl,
    (gltf) => {
      if (disposed) return;
      try {
        vrm = gltf.userData.vrm;
        if (!vrm) throw new Error("pas de VRM dans le fichier");

        VRMUtils.removeUnnecessaryVertices(gltf.scene);
        VRMUtils.combineSkeletons?.(gltf.scene);

        // Initialisation de l'AnimationMixer pour les clips VRMA
        mixer = new THREE.AnimationMixer(vrm.scene);
        mixer.addEventListener("finished", (e) => {
          if (e.action === activeVrmaAction) {
            stopVRMA(0.35);
            poseFrom = poseTo;
            poseTo = "idle";
            poseBlend = 0;
          }
        });

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
    animId = requestAnimationFrame(animate);
    const dt = Math.min(0.05, clock.getDelta());
    const t = clock.elapsedTime;
    if (vrm) {
      if (mixer) {
        mixer.update(dt);
      }
      updatePoseSystem(t, dt);

      // Projecteurs de scène pulsants pendant un spectacle (iStripper canon)
      if (isShowing()) {
        const pulseCyan = 2.4 + Math.sin(t * 6.0) * 1.5;
        const pulseMag = 2.4 + Math.cos(t * 6.0) * 1.5;
        stageLightCyan.intensity = pulseCyan;
        stageLightMagenta.intensity = pulseMag;
      } else if (stageLightCyan.intensity > 0) {
        stageLightCyan.intensity = Math.max(0, stageLightCyan.intensity - dt * 4.0);
        stageLightMagenta.intensity = Math.max(0, stageLightMagenta.intensity - dt * 4.0);
      }
      // Rotation fluide vers targetHeadingY (+ rotation continue si pirouette)
      const turnSpeed = 6.0;
      const diff = targetHeadingY - currentHeadingY;
      currentHeadingY += diff * Math.min(1, dt * turnSpeed);
      if (poseTo === "spin" && !activeVrmaAction) {
        spinAngle = (spinAngle + dt * 4.2) % (Math.PI * 2);
        vrm.scene.rotation.y = currentHeadingY + spinAngle;
      } else {
        spinAngle = 0;
        vrm.scene.rotation.y = currentHeadingY;
      }

      // 1. Clignements naturels des yeux cyber
      if (t > nextBlinkTime) {
        blinkProgress += dt * 10.0;
        const blinkVal = Math.sin(Math.min(Math.PI, blinkProgress));
        try {
          vrm.expressionManager?.setValue("blink", blinkVal);
        } catch (_) { }
        if (blinkProgress >= Math.PI) {
          blinkProgress = 0;
          nextBlinkTime = t + 2.5 + Math.random() * 3.5;
        }
      }

      // 2. Micro-gestes autonomes vivants pendant les pauses sur la barre des tâches
      // Postures calmes et contenues qui restent dans le cadre (bras croisés, réflexion, observation, repos, étirement)
      if (poseTo === "idle" && poseHoldUntil === 0 && !activeVrmaAction && !isShowing()) {
        if (t > nextHeartPoseTime) {
          // Petite danse spontanée "Finger Heart" K-Pop 1 à 2 fois par heure (toutes les 25 à 35 minutes)
          nextHeartPoseTime = t + 1500.0 + Math.random() * 600.0;
          setPose("fingerHeart", 8500);
        } else if (t > nextIdleFidgetTime) {
          nextIdleFidgetTime = t + 12.0 + Math.random() * 12.0;
          const gestures = ["crossArms", "think", "lookaround", "relax", "stretch"];
          const pick = gestures[Math.floor(Math.random() * gestures.length)];
          const holdMs = pick === "crossArms" ? 4500 : (pick === "think" ? 3500 : 5000);
          setPose(pick, holdMs);
        }
      }

      // Gestion visuelle des particules de cœurs et expression lors du fingerHeart
      if (poseTo === "fingerHeart" && vrm) {
        wasInHeartPose = true;
        let handPos = new THREE.Vector3(0.12, 1.30, 0.22);
        try {
          const rh = vrm.humanoid?.getNormalizedBoneNode?.("rightHand");
          if (rh) rh.getWorldPosition(handPos);
        } catch (_) { }

        heartSprites.forEach((sp, i) => {
          sp.visible = true;
          const phase = (t * 2.0 + i * 0.65) % 2.0;
          const life = phase / 2.0;
          const yOffset = life * 0.16;
          const xOffset = Math.sin(life * Math.PI * 2.0 + i) * 0.03;
          sp.position.set(handPos.x + xOffset, handPos.y + 0.02 + yOffset, handPos.z + 0.04);
          const scale = 0.045 + Math.sin(life * Math.PI) * 0.03;
          sp.scale.set(scale, scale, 1);
          sp.material.opacity = Math.sin(life * Math.PI) * 0.90;
        });

        // Expression espiègle idol / tehepero : grands yeux vifs ouverts, sourire éclatant avec dents
        try {
          const em = vrm.expressionManager;
          if (em) {
            // Yeux grands ouverts (NE PAS utiliser happy qui ferme les deux yeux en ^ ^)
            em.setValue("happy", 0);
            em.setValue("relaxed", 0.75); // Pommettes hautes, regard doux et bienveillant
            em.setValue("surprised", 0.12); // Yeux grands et pétillants
            em.setValue("ih", 0.32); // Dents visibles dans un sourire éclatant
            em.setValue("aa", 0.14); // Lèvres délicatement entrouvertes

            // Clin d'œil joueur unilatéral (œil droit uniquement) toutes les 3,2s
            const winkCycle = (t * 0.75) % 3.2;
            const winkVal = winkCycle < 0.35 ? Math.sin((winkCycle / 0.35) * Math.PI) * 0.95 : 0;
            em.setValue("blinkRight", winkVal);
            em.setValue("blinkLeft", 0); // L'œil gauche reste toujours grand ouvert
          }
        } catch (_) { }
      } else {
        heartSprites.forEach((sp) => {
          sp.visible = false;
        });
        if (wasInHeartPose) {
          wasInHeartPose = false;
          try {
            const em = vrm?.expressionManager;
            if (em) {
              em.setValue("blinkRight", 0);
              em.setValue("blinkLeft", 0);
              em.setValue("happy", 0);
              em.setValue("relaxed", 0);
              em.setValue("surprised", 0);
              em.setValue("ih", 0);
              em.setValue("aa", 0);
            }
          } catch (_) { }
          setMood("serene");
        }
      }

      // Gestion du Micro 3D et du chant scénique lors du Cyber Groove, Aeysa Singing et danses scéniques
      const isSingingScene = (poseTo === "cyberGroove" || poseTo === "aeysaSinging" || poseTo === "bellydance" || poseTo === "popdance" || poseTo === "femaledance" || poseTo === "dancing");
      if (isSingingScene && vrm) {
        wasInCyberGroove = true;
        // 1. S'assurer que le micro 3D est solidement attaché comme enfant de rightHand
        ensureMicAttached(vrm);
        cyberMicGroup.visible = true;

        // 2. Double anneau néon du micro qui pulse au kick
        const tempo = t * 13.404;
        const kickPulse = Math.sin(tempo) > 0.25;
        ringMat.color.setHex(kickPulse ? 0x00ffff : 0x0088ff);
        ringMat2.color.setHex(kickPulse ? 0xff0088 : 0x8800ff);

        // 3. Lipsync & Émotion Scénique Authentique (regard passionné / extase vocale du storyboard)
        try {
          const em = vrm.expressionManager;
          if (em) {
            const mouthA = Math.pow(Math.max(0, Math.sin(tempo * 1.5)), 1.5) * 0.72;
            const mouthO = Math.pow(Math.max(0, Math.cos(tempo * 1.0)), 2.0) * 0.48;
            em.setValue("aa", mouthA);
            em.setValue("oh", mouthO);
            em.setValue("ih", 0.20);
            // Regard de diva habité : yeux mi-clos / extase scénique douce calée au tempo
            const vocalEcstasy = 0.50 + Math.sin(tempoHalf) * 0.25;
            em.setValue("blink", vocalEcstasy);
            em.setValue("relaxed", 0.60);
            em.setValue("surprised", 0);
            em.setValue("happy", 0);
          }
        } catch (_) { }
      } else {
        cyberMicGroup.visible = false;
        if (wasInCyberGroove) {
          wasInCyberGroove = false;
          try {
            const em = vrm?.expressionManager;
            if (em) {
              em.setValue("aa", 0);
              em.setValue("oh", 0);
              em.setValue("ih", 0);
              em.setValue("relaxed", 0);
              em.setValue("surprised", 0);
              em.setValue("blink", 0);
            }
          } catch (_) { }
        }
      }

      // Compensation dynamique de la descente du bassin (hips) dans walk.vrma (+8.8cm)
      // pour que les pieds restent exactement alignés sur le sol de la barre des tâches sans s'enfoncer
      const isWalking = (activeVrmaName === "walk" || activeVrmaName === "marche" || poseTo === "walk");
      const targetWalkY = isWalking ? 0.088 : 0.0;
      const lerpSpeed = isWalking ? 16.0 : 6.0;
      walkYOffset += (targetWalkY - walkYOffset) * Math.min(1, dt * lerpSpeed);

      // Micro bob / jump / dance / walk offset (repli procédural uniquement si pas de clip VRMA actif)
      if (activeVrmaAction) {
        vrm.scene.position.y = walkYOffset;
        vrm.scene.position.x = 0;
      } else if (poseTo === "jump") {
        const jumpBounce = Math.max(0, Math.sin(t * 4.0)) * 0.038;
        vrm.scene.position.y = walkYOffset + jumpBounce;
        vrm.scene.position.x = 0;
      } else if (poseTo === "cyberGroove") {
        const tempo = t * 13.404;
        const tempoHalf = tempo * 0.5;
        const cycleTime = (t * 0.42) % (Math.PI * 2.0);
        const dropFactor = Math.max(0, Math.sin(cycleTime));
        const divaFactor = 1.0 - dropFactor * 0.75;

        // Déport latéral physique de scène en X (balancement de 4.8 cm actif surtout debout)
        vrm.scene.position.x = Math.sin(tempoHalf) * 0.048 * divaFactor;

        // Rebond au kick + descente basse de 7.5 cm quand elle est en drop jambes fléchies !
        const kickDrop = Math.pow(Math.max(0, Math.sin(tempo)), 1.8) * 0.032;
        vrm.scene.position.y = walkYOffset - (0.075 * dropFactor) - kickDrop;
      } else if (poseTo === "aeysaSinging") {
        const tempo = t * 13.404;
        const tempoHalf = tempo * 0.5;
        // Déport latéral subtil (2.2 cm) pour un balancement naturel et doux
        vrm.scene.position.x = Math.sin(tempoHalf) * 0.022;
        // Hauteur Y parfaitement stable avec micro-amorti imperceptible
        const kickSoft = Math.pow(Math.max(0, Math.sin(tempo)), 2.0) * 0.005;
        vrm.scene.position.y = walkYOffset - kickSoft;
      } else if (poseTo === "dance") {
        const danceBounce = Math.abs(Math.sin(t * 6.5)) * 0.012;
        vrm.scene.position.y = walkYOffset + danceBounce;
        vrm.scene.position.x = 0;
      } else if (poseTo === "fingerHeart") {
        const heartBounce = Math.abs(Math.sin(t * 7.0)) * 0.014;
        vrm.scene.position.y = walkYOffset + heartBounce;
        vrm.scene.position.x = 0;
      } else if (poseTo === "samba") {
        const sambaBounce = Math.abs(Math.sin(t * 11.0)) * 0.010;
        vrm.scene.position.y = walkYOffset + sambaBounce;
        vrm.scene.position.x = 0;
      } else if (poseTo === "hiphop") {
        const hiphopBounce = Math.abs(Math.sin(t * 9.0)) * 0.018;
        vrm.scene.position.y = walkYOffset + hiphopBounce;
        vrm.scene.position.x = 0;
      } else if (poseTo === "disco") {
        const discoBounce = Math.abs(Math.sin(t * 8.0)) * 0.014;
        vrm.scene.position.y = walkYOffset + discoBounce;
        vrm.scene.position.x = 0;
      } else if (poseTo === "robot") {
        const robotBounce = (Math.floor(t * 4.5 * 2.0) % 2 === 0 ? 0.004 : 0);
        vrm.scene.position.y = walkYOffset + robotBounce;
        vrm.scene.position.x = 0;
      } else if (!activeVrmaAction && poseTo === "idle") {
        vrm.scene.position.y = -Math.abs(Math.sin(t * 1.25)) * (framing === "full" ? 0.002 : 0.005);
        vrm.scene.position.x = 0;
      } else {
        vrm.scene.position.y = walkYOffset;
        vrm.scene.position.x = 0;
      }
      // Mouse tracking interactif : regard qui suit doucement le curseur de la souris
      mouseNdc.lerp(mouseActive ? targetMouseNdc : new THREE.Vector2(0, 0), Math.min(1.0, dt * 6.0));
      const lookTarget = camera.position.clone();
      lookTarget.x += mouseNdc.x * 0.40;
      lookTarget.y += mouseNdc.y * 0.30;
      if (vrm.lookAt && typeof vrm.lookAt.lookAt === "function") {
        vrm.lookAt.lookAt(lookTarget);
      }
      const nowMs = performance.now();
      const hasVisemes = activeVisemes && activeVisemes.length > 0;
      const targetWeights = { aa: 0, ih: 0, ou: 0, ee: 0, oh: 0 };

      if (hasVisemes && nowMs < talkingUntil) {
        const elapsedSec = (nowMs - visemesStartTime) / 1000.0;
        let matched = false;
        for (let vi = 0; vi < activeVisemes.length; vi++) {
          const frame = activeVisemes[vi];
          const start = frame.time_offset;
          const end = start + frame.duration;
          if (elapsedSec >= start && elapsedSec <= end) {
            const vKey = frame.viseme;
            if (targetWeights[vKey] !== undefined) {
              targetWeights[vKey] = frame.weight || 0.85;
              matched = true;
            }
            break;
          }
        }
        if (!matched && elapsedSec < (talkingUntil - visemesStartTime) / 1000.0) {
          targetWeights.aa = 0.12;
        }
      } else if (nowMs < talkingUntil) {
        mouthAmp = 0.3 + 0.5 * Math.abs(Math.sin(t * 13));
        targetWeights.aa = mouthAmp;
      } else {
        mouthAmp *= 0.85;
        if (mouthAmp < 0.02) mouthAmp = 0;
      }

      const vLerp = Math.min(1.0, dt * 18.0);
      for (const vk of VISEME_KEYS) {
        currentVisemeWeights[vk] += (targetWeights[vk] - currentVisemeWeights[vk]) * vLerp;
        if (currentVisemeWeights[vk] < 0.01) currentVisemeWeights[vk] = 0;
      }

      if (vrm.expressionManager && typeof vrm.expressionManager.setValue === "function") {
        if (poseTo === "fingerHeart") {
          // Pendant le fingerHeart, maintenir le sourire entrouvert naturel (sans forcer 0.42)
          vrm.expressionManager.setValue("aa", Math.max(currentVisemeWeights.aa, 0.14));
        } else {
          for (const vk of VISEME_KEYS) {
            vrm.expressionManager.setValue(vk, currentVisemeWeights[vk]);
          }
        }
      }
      if (typeof vrm.update === "function") {
        vrm.update(dt);
      }
    }

    // Interpolation fluide de la caméra (zoom/dézoom cinématographique entre buste et corps entier)
    if (cameraInitialized) {
      const camLerp = Math.min(1, dt * 5.0);
      currentCamPos.lerp(targetCamPos, camLerp);
      currentLookAt.lerp(targetLookAt, camLerp);
      currentFov += (targetFov - currentFov) * camLerp;
      camera.fov = currentFov;
      camera.updateProjectionMatrix();
      camera.position.copy(currentCamPos);
      camera.lookAt(currentLookAt);
    }

    renderer.render(scene, camera);
  }

  resize();
  window.addEventListener("resize", resize);
  animate();

  /** Show Routine Manager — Séquenceur de spectacles continus (iStripper / vghd canon) */
  let currentShow = null;
  let showStepIndex = 0;
  let showStepTimer = null;
  let preShowFraming = null;

  const SHOW_ROUTINES = {
    idol: {
      name: "Show K-Pop Idol",
      steps: [
        { pose: "wave", duration: 3200, mood: "happy", speech: "Bonjour ! Place au spectacle !" },
        { pose: "dance", duration: 9500, mood: "happy", speech: "On commence avec le groove Pop !" },
        { pose: "samba", duration: 9000, mood: "happy", speech: "Accélération du rythme !" },
        { pose: "hiphop", duration: 9000, mood: "happy" },
        { pose: "spin", duration: 5000, mood: "happy", speech: "Tourbillon cyber !" },
        { pose: "fingerHeart", duration: 8500, mood: "happy", speech: "Petite danse idol pour vous !" },
        { pose: "bow", duration: 3500, mood: "serene", speech: "Merci d'avoir regardé le show." },
      ],
    },
    club: {
      name: "Show Club Electro",
      steps: [
        { pose: "lookaround", duration: 3500, mood: "curious", speech: "Ambiance Club activée." },
        { pose: "disco", duration: 11000, mood: "happy", speech: "Disco Fever sur le bureau !" },
        { pose: "robot", duration: 10000, mood: "serene", speech: "Synchronisation des servomoteurs." },
        { pose: "dance", duration: 9000, mood: "happy" },
        { pose: "spin", duration: 5500, mood: "happy" },
        { pose: "bow", duration: 3500, mood: "serene", speech: "Fin de la session Club." },
      ],
    },
    latino: {
      name: "Show Fiesta Caliente",
      steps: [
        { pose: "wave", duration: 3000, mood: "happy", speech: "Musica ! Que la fête commence !" },
        { pose: "samba", duration: 11000, mood: "happy", speech: "Rythme Samba Latino !" },
        { pose: "salsa", duration: 11000, mood: "happy", speech: "Salsa en continu !" },
        { pose: "spin", duration: 5000, mood: "happy" },
        { pose: "jump", duration: 4000, mood: "happy", speech: "Olé !" },
        { pose: "bow", duration: 3000, mood: "serene", speech: "Merci beaucoup !" },
      ],
    },
  };

  function isShowing() {
    return currentShow !== null;
  }

  function startShow(routineKey = "idol", onComplete) {
    stopShow();
    const key = String(routineKey || "idol").toLowerCase();
    const routine = SHOW_ROUTINES[key] || SHOW_ROUTINES.idol;
    currentShow = { key, routine, onComplete };
    showStepIndex = 0;

    // Bascule automatique en vue Corps Entier pour apprécier la danse
    preShowFraming = framing;
    if (framing !== "full") {
      setFraming("full");
    }

    console.info("[vrm_pet] Démarrage du show :", routine.name);
    executeShowStep();
    return routine.name;
  }

  function executeShowStep() {
    if (!currentShow) return;
    const steps = currentShow.routine.steps;
    if (showStepIndex >= steps.length) {
      endShow();
      return;
    }

    const step = steps[showStepIndex];
    if (step.mood) setMood(step.mood);
    if (step.pose) setPose(step.pose, step.duration + 500);
    if (step.speech) say(step.speech);

    showStepTimer = setTimeout(() => {
      showStepIndex += 1;
      executeShowStep();
    }, step.duration);
  }

  function endShow() {
    if (!currentShow) return;
    const cb = currentShow.onComplete;
    console.info("[vrm_pet] Fin du show :", currentShow.routine.name);
    currentShow = null;
    showStepIndex = 0;
    if (showStepTimer) {
      clearTimeout(showStepTimer);
      showStepTimer = null;
    }
    stopVRMA(0.2);
    if (vrm?.humanoid) {
      try { vrm.humanoid.resetNormalizedPose(); } catch (_) {}
    }
    setPose("idle", 0);
    setMood("serene");
    if (preShowFraming && preShowFraming !== framing) {
      setFraming(preShowFraming);
      preShowFraming = null;
    }
    if (typeof cb === "function") {
      try { cb(); } catch (_) {}
    }
  }

  function stopShow() {
    if (showStepTimer) {
      clearTimeout(showStepTimer);
      showStepTimer = null;
    }
    if (currentShow) {
      endShow();
    }
  }

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
    playVisemes,
    say,
    pulse,
    flip,
    setFraming,
    setPose,
    setHeading,
    equipAccessory,
    toggleAccessory,
    get equippedAccessories() {
      return Array.from(equippedAccessories.keys());
    },
    playVRMA,
    stopVRMA,
    loadVRMA,
    startShow,
    stopShow,
    isShowing,
    get activeVRMA() {
      return activeVrmaName;
    },
    get pose() {
      return poseTo;
    },
    get framing() {
      return framing;
    },
    destroy() {
      disposed = true;
      if (animId !== null) {
        cancelAnimationFrame(animId);
        animId = null;
      }
      window.removeEventListener("resize", resize);

      // 1. Arrêt du mixer et détachement de la scène
      if (mixer) {
        try {
          mixer.stopAllAction();
          if (vrm?.scene) {
            mixer.uncacheRoot(vrm.scene);
          }
        } catch (_) { }
        mixer = null;
      }

      // 2. Nettoyage du cache VRMA
      vrmaClips.clear();
      vrmaLoading.clear();

      // 3. Libération des textures créées dynamiquement et particules
      for (const sp of heartSprites) {
        try {
          scene.remove(sp);
          sp.geometry?.dispose();
        } catch (_) { }
      }
      try { heartMat.dispose(); } catch (_) { }

      for (const tex of createdTextures) {
        try {
          tex.dispose();
        } catch (_) { }
      }
      createdTextures.length = 0;

      // 4. Libération profonde du modèle VRM (VRAM GPU, géométries, buffers)
      if (vrm?.scene) {
        try {
          scene.remove(vrm.scene);
          VRMUtils.deepDispose(vrm.scene);
        } catch (e) {
          console.warn("[vrm_pet] deepDispose error:", e);
        }
      }

      // 5. Destruction du renderer WebGL et détachement du DOM
      try {
        renderer.dispose();
        if (renderer.forceContextLoss) {
          renderer.forceContextLoss();
        }
      } catch (_) { }
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
