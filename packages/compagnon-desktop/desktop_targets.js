"use strict";

/**
 * Cibles bureau Windows (fenêtres visibles) pour le mode guide avatar.
 * Omarchy / Linux : liste vide — le guide reste sur points manuels / démos.
 */

const { execFile } = require("child_process");
let screen = null;
try {
  screen = require("electron").screen;
} catch (_) {}

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
  if (!screen) return { title: "Icônes bureau", x: 8, y: 8, width: 220, height: 320 };
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
  if (!screen) return { title: "Barre des tâches", x: 400, y: 700, width: 300, height: 40 };
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


/**
 * Récupère les métadonnées de la fenêtre active au premier plan (Windows).
 * Respect strict de la vie privée : aucun contenu de fenêtre, uniquement titre et nom de processus.
 */
function getActiveWindowWin32() {
  const ps = `
Add-Type @"
using System;
using System.Text;
using System.Runtime.InteropServices;
public class User32Active {
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
}
"@
$hwnd = [User32Active]::GetForegroundWindow()
if ($hwnd -ne [IntPtr]::Zero) {
  $sb = New-Object System.Text.StringBuilder 512
  [void][User32Active]::GetWindowText($hwnd, $sb, 512)
  $pidVal = 0
  [void][User32Active]::GetWindowThreadProcessId($hwnd, [ref]$pidVal)
  $proc = Get-Process -Id $pidVal -ErrorAction SilentlyContinue
  [PSCustomObject]@{
    title   = $sb.ToString()
    process = if ($proc) { $proc.ProcessName } else { "" }
    pid     = $pidVal
  } | ConvertTo-Json -Compress
}
`.trim();

  return new Promise((resolve) => {
    execFile(
      "powershell.exe",
      ["-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
      { timeout: 5_000, windowsHide: true },
      (err, stdout) => {
        if (err) {
          resolve(null);
          return;
        }
        try {
          const raw = String(stdout || "").trim();
          if (!raw) {
            resolve(null);
            return;
          }
          const parsed = JSON.parse(raw);
          resolve({
            title: String(parsed.title || ""),
            process: String(parsed.process || ""),
            pid: Number(parsed.pid) || 0,
          });
        } catch (_) {
          resolve(null);
        }
      }
    );
  });
}

async function getActiveWindow() {
  if (process.platform !== "win32") return null;
  return getActiveWindowWin32();
}

/**
 * Catégorise l'activité de l'utilisateur à partir du titre et du nom de processus.
 * Renvoie une micro-attitude avatar cohérente (think, curious, cheer, alert, relax, serene).
 * @param {{ title?: string, process?: string } | null} windowInfo
 */
function categorizeFocus(windowInfo) {
  if (!windowInfo || (!windowInfo.title && !windowInfo.process)) {
    return {
      category: "idle",
      attitude: "relax",
      app: "unknown",
      label: "En veille / Inactif",
    };
  }

  const p = String(windowInfo.process || "").toLowerCase();
  const t = String(windowInfo.title || "").toLowerCase();

  // Code & Édition de texte dev
  if (
    p.includes("cursor") ||
    p.includes("code") ||
    p.includes("devenv") ||
    p.includes("pycharm") ||
    p.includes("sublime") ||
    t.includes("cursor") ||
    t.includes("visual studio code")
  ) {
    return {
      category: "coding",
      attitude: "think",
      app: "ide",
      label: "Édition de code & architecture",
    };
  }

  // Moteur de jeu & 3D
  if (
    p.includes("godot") ||
    p.includes("unreal") ||
    p.includes("unity") ||
    p.includes("blender") ||
    t.includes("godot engine") ||
    t.includes("blender")
  ) {
    return {
      category: "gamedev",
      attitude: "curious",
      app: p.includes("godot") ? "godot" : "3d_engine",
      label: "Création 3D & Moteur de jeu",
    };
  }

  // Console / Terminal / CI
  if (
    p.includes("terminal") ||
    p.includes("powershell") ||
    p.includes("cmd") ||
    p.includes("wt") ||
    p.includes("bash") ||
    p.includes("alacritty") ||
    t.includes("terminal") ||
    t.includes("powershell")
  ) {
    return {
      category: "terminal",
      attitude: "alert",
      app: "terminal",
      label: "Console & Déploiement système",
    };
  }

  // Jeux & simulation MMO
  if (
    p.includes("prime") ||
    p.includes("swg") ||
    t.includes("lost heaven") ||
    t.includes("prime-client")
  ) {
    return {
      category: "gaming",
      attitude: "cheer",
      app: "game",
      label: "Test en jeu & MMO",
    };
  }

  // Web & documentation
  if (
    p.includes("chrome") ||
    p.includes("msedge") ||
    p.includes("firefox") ||
    p.includes("brave") ||
    p.includes("opera")
  ) {
    return {
      category: "browsing",
      attitude: "serene",
      app: "browser",
      label: "Navigation & Documentation",
    };
  }

  return {
    category: "general",
    attitude: "serene",
    app: p || "desktop",
    label: "Activité bureau",
  };
}

module.exports = {
  listWindows,
  findWindowByTitle,
  desktopIconsZone,
  taskbarZone,
  getActiveWindow,
  categorizeFocus,
};
