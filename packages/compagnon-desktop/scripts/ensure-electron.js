"use strict";

/**
 * Ensures Electron binary exists even when npm blocks package postinstall
 * (allowScripts / install-scripts).
 */
const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const electronDir = path.join(__dirname, "..", "node_modules", "electron");
const pathTxt = path.join(electronDir, "path.txt");
const installJs = path.join(electronDir, "install.js");

function binaryOk() {
  try {
    if (!fs.existsSync(pathTxt)) return false;
    const rel = fs.readFileSync(pathTxt, "utf8").trim();
    if (!rel) return false;
    return fs.existsSync(path.join(electronDir, rel));
  } catch (_) {
    return false;
  }
}

if (binaryOk()) {
  process.exit(0);
}

if (!fs.existsSync(installJs)) {
  console.warn("[ensure-electron] install.js missing — run npm install electron");
  process.exit(0);
}

console.log("[ensure-electron] downloading Electron binary via install.js ...");
const r = spawnSync(process.execPath, [installJs], {
  stdio: "inherit",
  cwd: electronDir,
  env: process.env,
});
process.exit(r.status === null ? 1 : r.status);
