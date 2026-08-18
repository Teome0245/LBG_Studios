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
register_9();


if (typeof globalThis.orchestratorAvatarInit === "function") {
  try { globalThis.orchestratorAvatarInit(); } catch (_) {}
}
if (typeof globalThis.faceRigInit === "function") {
  try { globalThis.faceRigInit(); } catch (_) {}
}
