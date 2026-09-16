export const STATE_TO_ICON = {
  // IA-CORE
  "ia_core_active": "ia-core_happy",
  "ia_core_idle": "ia-core_neutral",

  // AGENT-LOCAL / AGENT-I
  "agent_local_running": "agent-local_happy",
  "agent_local_idle": "agent-local_sad",

  // ORCHESTRATOR (EN ANGLAIS, comme ton backend)
  "orchestrator_happy": "orchestrateur_happy",
  "orchestrator_neutral": "orchestrateur_neutral",
  "orchestrator_sad": "orchestrateur_sad",
  "orchestrator_routing": "orchestrateur_neutral",
  "orchestrator_fallback": "orchestrateur_neutral",

  // PERCEPTION
  "perception_analyzing": "perception-lyra_brain-v1",
  "perception_idle": "perception-lyra_brain-v2",

  // AUTO-UPGRADE
  "autoupgrade_success": "ia-core_happy",
  "autoupgrade_error": "ia-core_sad",

  // fallback
  "unknown": "orchestrateur_happy"
};

