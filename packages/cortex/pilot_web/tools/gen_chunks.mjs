#!/usr/bin/env node
/**
 * Générateur des chunks Pilot (pilot_web/src/chunks).
 *
 * Le runtime ESM de Pilot charge des « chunks » : chaque module source
 * `pilot_<nom>.js` est embarqué sous forme de chaîne et exécuté dans un
 * `with (PilotApp)` (voir `src/runtime.js`). Ce script garantit que les
 * chunks sont toujours dérivés des sources — plus de dérive manuelle.
 *
 * Usage :
 *   node tools/gen_chunks.mjs            # (re)génère src/chunks/*.js
 *   node tools/gen_chunks.mjs --check     # échoue si un chunk diverge
 */
import { readFileSync, writeFileSync, readdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const CHUNKS_DIR = resolve(ROOT, "src/chunks");

/**
 * Ordre de chargement (doit rester stable pour les effets de bord
 * d'enregistrement ; `pilot_init` en dernier).
 */
export const CHUNK_ORDER = [
  "pilot_metrics",
  "pilot_core",
  "pilot_state",
  "pilot_chat",
  "pilot_assistant",
  "pilot_views",
  "pilot_actions",
  "pilot_orch",
  "pilot_office",
  "pilot_team",
  "pilot_cards",
  "pilot_jobs",
  "pilot_router",
  "pilot_pm",
  "pilot_lyra",
  "pilot_desktop",
  "pilot_init",
];

/** Monolithe historique non chargé (voir README) — pas de chunk. */
const IGNORED = new Set(["pilot"]);

const DECL_RE =
  /^ {4}(?:async function|function|class)\s+([A-Za-z_$][\w$]*)|^ {4}(?:const|let|var)\s+([A-Za-z_$][\w$]*)/;

export function detectExports(code) {
  const names = [];
  for (const line of code.split("\n")) {
    const m = line.match(DECL_RE);
    if (m) names.push(m[1] || m[2]);
  }
  return names;
}

export function renderChunk(name, code) {
  const names = detectExports(code);
  const namesJson = JSON.stringify(names).replaceAll(",", ", ");
  return (
    'import { registerLegacyChunk } from "../runtime.js";\n\n' +
    `const code = ${JSON.stringify(code)};\n` +
    `const exportNames = ${namesJson};\n\n` +
    "export function register() {\n" +
    `  return registerLegacyChunk("${name}.js", code, exportNames);\n` +
    "}\n"
  );
}

function discoverModules() {
  return readdirSync(ROOT)
    .filter((f) => /^pilot.*\.js$/.test(f))
    .map((f) => f.replace(/\.js$/, ""))
    .filter((n) => !IGNORED.has(n))
    .filter((n) => existsSync(resolve(ROOT, `${n}.js`)))
    .sort();
}

function main() {
  const check = process.argv.includes("--check");
  const found = discoverModules();
  const modules = CHUNK_ORDER.filter((n) => found.includes(n));
  const missing = found.filter((n) => !modules.includes(n));
  if (missing.length) {
    console.error(
      `Modules source non listés dans CHUNK_ORDER: ${missing.join(", ")}`,
    );
    process.exit(2);
  }

  let drift = 0;
  for (const name of modules) {
    const code = readFileSync(resolve(ROOT, `${name}.js`), "utf8").replace(
      /\s+$/,
      "",
    );
    const out = renderChunk(name, code);
    const target = resolve(CHUNKS_DIR, `${name}.js`);
    if (check) {
      const cur = existsSync(target) ? readFileSync(target, "utf8") : "";
      if (cur !== out) {
        console.error(`DRIFT ${name}.js`);
        drift += 1;
      }
    } else {
      writeFileSync(target, out, "utf8");
    }
  }

  if (check) {
    if (drift) {
      console.error(`${drift} chunk(s) en dérive — lancer gen_chunks.mjs`);
      process.exit(1);
    }
    console.log(`OK ${modules.length} chunks alignés`);
    return;
  }
  console.log(`OK écrit ${modules.length} chunks`);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}
