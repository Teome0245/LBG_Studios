/* CSS via <link> dans index.html — pas d'import .css ici (ESM nginx sans Vite). */
import "./modules/office_map_module.js";
import "./modules/orchestrator_avatar_module.js";
import "./modules/face_rig_module.js";
import { register as register_metrics } from "./chunks/pilot_metrics.js";
import { register as register_core } from "./chunks/pilot_core.js";
import { register as register_state } from "./chunks/pilot_state.js";
import { register as register_chat } from "./chunks/pilot_chat.js";
import { register as register_assistant } from "./chunks/pilot_assistant.js";
import { register as register_views } from "./chunks/pilot_views.js";
import { register as register_actions } from "./chunks/pilot_actions.js";
import { register as register_orch } from "./chunks/pilot_orch.js";
import { register as register_office } from "./chunks/pilot_office.js";
import { register as register_team } from "./chunks/pilot_team.js";
import { register as register_cards } from "./chunks/pilot_cards.js";
import { register as register_jobs } from "./chunks/pilot_jobs.js";
import { register as register_router } from "./chunks/pilot_router.js";
import { register as register_pm } from "./chunks/pilot_pm.js";
import { register as register_lyra } from "./chunks/pilot_lyra.js";
import { register as register_desktop } from "./chunks/pilot_desktop.js";
import { installHuntYard } from "./modules/hunt_yard.js";
import { installOrchSurfaces } from "./modules/orch_surfaces.js";
import { installAssistantOrchChat } from "./modules/assistant_orch_chat.js";
import { installAssistantChannelMode } from "./modules/assistant_channel_mode.js";
import { installTeamFleet } from "./modules/team_fleet.js";
import { installTeamBrain } from "./modules/team_brain.js";
import { installAgenticUi } from "./modules/agentic_ui.js";
import { register as register_init } from "./chunks/pilot_init.js";

// Ordre = CHUNK_ORDER (tools/gen_chunks.mjs). pilot_metrics avant pilot_core
// (les écouteurs de core référencent les fonctions métriques par valeur).
register_metrics();
register_core();
register_state();
register_chat();
register_assistant();
register_views();
register_actions();
register_orch();
register_office();
register_team();
register_cards();
register_jobs();
register_router();
register_pm();
register_lyra();
register_desktop();
installHuntYard();
installOrchSurfaces();
installAssistantOrchChat();
installAssistantChannelMode();
installTeamFleet();
installTeamBrain();
installAgenticUi();
register_init();

if (typeof globalThis.orchestratorAvatarInit === "function") {
  try { globalThis.orchestratorAvatarInit(); } catch (_) {}
}
if (typeof globalThis.faceRigInit === "function") {
  try { globalThis.faceRigInit(); } catch (_) {}
}

// Three.js optionnel (carte 3D / avatar GLTF) — ne doit JAMAIS tuer le routeur.
// Si node_modules/three manque, nginx SPA renvoyait index.html → MIME error → Accueil collé.
import("./modules/three_setup.js").catch(function (err) {
  try {
    console.warn("[pilot] three.js indisponible — bureau 2D OK, carte 3D désactivée", err);
  } catch (_) {}
});
