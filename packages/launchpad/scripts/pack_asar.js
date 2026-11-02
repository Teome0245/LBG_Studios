#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const root = path.resolve(__dirname, '..');
const outDir = process.argv[2] ? path.resolve(process.argv[2]) : path.join(root, 'dist', 'win-unpacked', 'resources');
const outAsar = path.join(outDir, 'app.asar');

if (!fs.existsSync(outDir)) {
  fs.mkdirSync(outDir, { recursive: true });
}

// Répertoire temporaire de staging propre sans dist / node_modules / .git
const os = require('os');
const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'lbg-asar-'));

try {
  const filesToCopy = ['index.html', 'main.js', 'package.json', 'launchpad.config.json'];
  for (const f of filesToCopy) {
    const src = path.join(root, f);
    if (fs.existsSync(src)) {
      fs.copyFileSync(src, path.join(tmpDir, f));
    }
  }

  const srcDir = path.join(root, 'src');
  if (fs.existsSync(srcDir)) {
    const destSrc = path.join(tmpDir, 'src');
    fs.mkdirSync(destSrc, { recursive: true });
    for (const f of fs.readdirSync(srcDir)) {
      fs.copyFileSync(path.join(srcDir, f), path.join(destSrc, f));
    }
  }

  execFileSync('npx', ['asar', 'pack', tmpDir, outAsar], { stdio: 'inherit' });
  const stat = fs.statSync(outAsar);
  console.log(`[pack_asar] OK ${outAsar} (${stat.size} bytes)`);
} finally {
  try {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  } catch (_) {}
}
