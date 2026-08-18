/**
 * Three.js + GLTFLoader via npm (Vite bundle ou import map en dev statique).
 * Expose globalThis.THREE pour orchestrator_avatar.js (IIFE legacy).
 */
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";

/** Namespace mutable pour l’IIFE legacy `orchestrator_avatar.js`. */
const three = { ...THREE, GLTFLoader };
globalThis.THREE = three;

export { three as THREE, GLTFLoader };
