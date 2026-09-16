/**
 * P3 cutover : Orch UI `.100:5174` → Pilot hub `.140:8080/pilot/`.
 * Bypass : `?stay=1` (mémorisé) ou localStorage `lbg_orch_stay_5174=1`.
 */

const PILOT_BASE = "http://192.168.0.140:8080/";
const STAY_KEY = "lbg_orch_stay_5174";

const PATH_TO_HASH = {
  "/": "assistant",
  "/lyra": "lyra",
  "/agents/map": "agents/map",
  "/agents": "agents/map",
  "/providers/catalog": "providers",
  "/providers": "providers",
};

export function pilotUrlForPath(pathname) {
  const raw = String(pathname || "/").replace(/\/$/, "") || "/";
  const hash = PATH_TO_HASH[raw] || PATH_TO_HASH["/"] || "assistant";
  return PILOT_BASE + "#/" + hash;
}

export function wantsStayOn5174() {
  try {
    const q = new URLSearchParams(window.location.search || "");
    if (q.get("stay") === "1") {
      try {
        localStorage.setItem(STAY_KEY, "1");
      } catch (_) {}
      return true;
    }
    if (q.get("stay") === "0") {
      try {
        localStorage.removeItem(STAY_KEY);
      } catch (_) {}
      return false;
    }
    return localStorage.getItem(STAY_KEY) === "1";
  } catch (_) {
    return false;
  }
}

export function clearStayOn5174() {
  try {
    localStorage.removeItem(STAY_KEY);
  } catch (_) {}
}

/** @returns {boolean} true si redirect déclenché */
export function maybeRedirectToPilot() {
  if (typeof window === "undefined") return false;
  if (wantsStayOn5174()) return false;
  const target = pilotUrlForPath(window.location.pathname);
  window.location.replace(target);
  return true;
}

export { PILOT_BASE, STAY_KEY };
