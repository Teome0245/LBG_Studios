const test = require("node:test");
const assert = require("node:assert/strict");
const { categorizeFocus } = require("../desktop_targets");

test("categorizeFocus: détecte l'environnement de dev / code (Cursor, VSCode)", () => {
  const c1 = categorizeFocus({ process: "cursor", title: "main.js — LBG_Studios" });
  assert.equal(c1.category, "coding");
  assert.equal(c1.attitude, "think");

  const c2 = categorizeFocus({ process: "Code", title: "ChatInput.vue - Visual Studio Code" });
  assert.equal(c2.category, "coding");
  assert.equal(c2.attitude, "think");
});

test("categorizeFocus: détecte le moteur de jeu Godot / 3D", () => {
  const g1 = categorizeFocus({ process: "Godot_v4.6", title: "Lost Heaven - Godot Engine" });
  assert.equal(g1.category, "gamedev");
  assert.equal(g1.attitude, "curious");

  const b1 = categorizeFocus({ process: "blender", title: "Compagnon_rig.blend - Blender" });
  assert.equal(b1.category, "gamedev");
  assert.equal(b1.attitude, "curious");
});

test("categorizeFocus: détecte la console / terminal", () => {
  const t1 = categorizeFocus({ process: "powershell", title: "Windows PowerShell" });
  assert.equal(t1.category, "terminal");
  assert.equal(t1.attitude, "alert");

  const t2 = categorizeFocus({ process: "WindowsTerminal", title: "bash" });
  assert.equal(t2.category, "terminal");
  assert.equal(t2.attitude, "alert");
});

test("categorizeFocus: détecte le jeu MMO Lost Heaven", () => {
  const m1 = categorizeFocus({ process: "prime_client", title: "Lost Heaven" });
  assert.equal(m1.category, "gaming");
  assert.equal(m1.attitude, "cheer");
});

test("categorizeFocus: détecte le navigateur web", () => {
  const w1 = categorizeFocus({ process: "chrome", title: "Documentation Godot - Google Chrome" });
  assert.equal(w1.category, "browsing");
  assert.equal(w1.attitude, "serene");
});

test("categorizeFocus: repli propre sur inactivité (null ou vide)", () => {
  const i1 = categorizeFocus(null);
  assert.equal(i1.category, "idle");
  assert.equal(i1.attitude, "relax");

  const i2 = categorizeFocus({});
  assert.equal(i2.category, "idle");
  assert.equal(i2.attitude, "relax");
});

