/* CSS via <link> dans index.html — pas d'import .css ici (ESM nginx sans Vite). */
import "./modules/office_map_module.js";
import "./modules/orchestrator_avatar_module.js";
import "./modules/face_rig_module.js";
import { register as register_0 } from "./chunks/pilot_core.js";
import { register as register_1 } from "./chunks/pilot_chat.js";
import { register as register_2 } from "./chunks/pilot_assistant.js";
import { register as register_3 } from "./chunks/pilot_team.js";
import { register as register_4 } from "./chunks/pilot_jobs.js";
import { register as register_5 } from "./chunks/pilot_router.js";
import { register as register_6 } from "./chunks/pilot_pm.js";
import { register as register_7 } from "./chunks/pilot_lyra.js";
import { register as register_8 } from "./chunks/pilot_desktop.js";
import { installHuntYard } from "./modules/hunt_yard.js";
import { installOrchSurfaces } from "./modules/orch_surfaces.js";
import { installAssistantOrchChat } from "./modules/assistant_orch_chat.js";
import { installAssistantChannelMode } from "./modules/assistant_channel_mode.js";
import { installTeamFleet } from "./modules/team_fleet.js";
import { installAgenticUi } from "./modules/agentic_ui.js";
import { register as register_9 } from "./chunks/pilot_init.js";

register_0();
register_1();
register_2();
register_3();
register_4();
register_5();
register_6();
register_7();
register_8();
installHuntYard();
installOrchSurfaces();
installAssistantOrchChat();
installAssistantChannelMode();
installTeamFleet();
installAgenticUi();
register_9();

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
