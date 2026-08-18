import "../../orchestrator_avatar/orchestrator_avatar.js";

export function getOrchestratorAvatar() {
  return globalThis.OrchestratorAvatar || null;
}
