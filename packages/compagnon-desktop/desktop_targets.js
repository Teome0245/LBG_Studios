"use strict";

/**
 * Cibles bureau Windows (fenêtres visibles) pour le mode guide avatar.
 * Omarchy / Linux : liste vide — le guide reste sur points manuels / démos.
 */

const { execFile } = require("child_process");
const { screen } = require("electron");

function listWindowsWin32() {
  const ps = `
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class User32Rect {
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
  [StructLayout(LayoutKind.Sequential)]
  public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
}
"@
Get-Process |
  Where-Object { $_.MainWindowHandle -ne 0 -and $_.MainWindowTitle } |
  ForEach-Object {
    $r = New-Object User32Rect+RECT
    [void][User32Rect]::GetWindowRect($_.MainWindowHandle, [ref]$r)
    $w = $r.Right - $r.Left
    $h = $r.Bottom - $r.Top
    if ($w -lt 100 -or $h -lt 60) { return }
    [PSCustomObject]@{
      title  = $_.MainWindowTitle
      x      = $r.Left
      y      = $r.Top
      width  = $w
      height = $h
      pid    = $_.Id
    }
  } |
  ConvertTo-Json -Compress
`.trim();

  return new Promise((resolve) => {
    execFile(
      "powershell.exe",
      ["-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
      { timeout: 10_000, windowsHide: true, maxBuffer: 2_000_000 },
      (err, stdout) => {
        if (err) {
          resolve([]);
          return;
        }
        try {
          const raw = String(stdout || "").trim();
          if (!raw) {
            resolve([]);
            return;
          }
          const parsed = JSON.parse(raw);
          const arr = Array.isArray(parsed) ? parsed : [parsed];
          resolve(
            arr
              .filter((w) => w && w.title)
              .map((w) => ({
                title: String(w.title),
                x: Number(w.x) || 0,
                y: Number(w.y) || 0,
                width: Number(w.width) || 0,
                height: Number(w.height) || 0,
                pid: Number(w.pid) || 0,
              }))
          );
        } catch (_) {
          resolve([]);
        }
      }
    );
  });
}

async function listWindows() {
  if (process.platform !== "win32") return [];
  return listWindowsWin32();
}

function findWindowByTitle(windows, needle) {
  const n = String(needle || "")
    .trim()
    .toLowerCase();
  if (!n) return null;
  const exact = windows.find((w) => String(w.title).toLowerCase() === n);
  if (exact) return exact;
  return windows.find((w) => String(w.title).toLowerCase().includes(n)) || null;
}

/** Zone approximative des icônes bureau (coin haut-gauche du moniteur principal). */
function desktopIconsZone() {
  const wa = screen.getPrimaryDisplay().workArea;
  return {
    title: "Icônes bureau",
    x: wa.x + 8,
    y: wa.y + 8,
    width: 220,
    height: 320,
  };
}

/** Zone barre des tâches / systray. */
function taskbarZone() {
  const d = screen.getPrimaryDisplay();
  const wa = d.workArea;
  const b = d.bounds;
  return {
    title: "Barre des tâches",
    x: wa.x + Math.floor(wa.width * 0.35),
    y: wa.y + wa.height - 8,
    width: Math.floor(wa.width * 0.3),
    height: Math.max(40, b.height - wa.height),
  };
}

module.exports = {
  listWindows,
  findWindowByTitle,
  desktopIconsZone,
  taskbarZone,
};
