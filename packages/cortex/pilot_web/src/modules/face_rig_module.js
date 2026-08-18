import "../../face_rig/face_rig.js";

export function getFaceRig() {
  return globalThis.FaceRig || null;
}
