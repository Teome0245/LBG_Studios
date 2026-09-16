/**
 * Deep-links Orch UI (5174) → Pilot studio (.140:8080).
 * Chat reste sur 5174 ; Pilot = desktop / team / ops.
 *
 * Canonique nginx 8080 = racine `/` (pas `/pilot/…` — sinon `src/main.js` relative
 * résout en `/pilot/src/main.js` → try_files → index.html → pas de routeur).
 */

export const PILOT_BASE = "http://192.168.0.140:8080/";

/** @param {string} hashSansDieze ex. "desktop" ou "team/office" */
export function pilotHash(hashSansDieze) {
  const h = String(hashSansDieze || "assistant").replace(/^#\/?/, "");
  return PILOT_BASE + "#/" + h;
}

export const PILOT_LINKS = {
  home: PILOT_BASE,
  assistant: pilotHash("assistant"),
  desktop: pilotHash("desktop"),
  team: pilotHash("team"),
  teamOffice: pilotHash("team/office"),
  jobs: pilotHash("jobs"),
};

/** Liens affichés dans la nav / header (ouvrir dans un nouvel onglet). */
export const PILOT_NAV = [
  { id: "desktop", label: "Desktop", href: PILOT_LINKS.desktop, title: "Pilot · Desktop (poste)" },
  { id: "team", label: "Team", href: PILOT_LINKS.teamOffice, title: "Pilot · Bureau Team Campus" },
  { id: "jobs", label: "Jobs", href: PILOT_LINKS.jobs, title: "Pilot · Jobs / approbations" },
  { id: "assistant", label: "Ops", href: PILOT_LINKS.assistant, title: "Pilot · canal ops" },
];
