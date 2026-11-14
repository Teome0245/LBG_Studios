#!/usr/bin/env python3
"""
Ronde d'Audit Nocturne Autonome pour Gladys (LBG Studios)
Exécutée périodiquement de 00:30 à 07:00.
Mode 100% Read-Only / Diagnostic : consigne les métriques, latences et opportunités
dans docs/AUDIT_NOCTURNE_<DATE>.md sans altérer le code source.
"""

import datetime
import json
import os
import subprocess
import time
import urllib.error
import urllib.request

REPO_ROOT = "/home/lbg/Projets/LBG_Studios"
NOW = datetime.datetime.now()
DATE_STR = NOW.strftime("%Y-%m-%d")
TIME_STR = NOW.strftime("%H:%M:%S")
REPORT_PATH = os.path.join(REPO_ROOT, "docs", f"AUDIT_NOCTURNE_{DATE_STR}.md")

def probe_http(url, timeout=3.0):
    start = time.perf_counter()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Gladys-Nocturnal-Auditor/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            data = resp.read()
            parsed = None
            try:
                parsed = json.loads(data.decode("utf-8", errors="ignore"))
            except Exception:
                pass
            return {"ok": True, "status": resp.status, "ms": elapsed_ms, "data": parsed}
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return {"ok": False, "error": str(e), "ms": elapsed_ms}

def run_cmd(cmd, cwd=REPO_ROOT, timeout=15):
    try:
        res = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout
        )
        return {"returncode": res.returncode, "stdout": res.stdout.strip(), "stderr": res.stderr.strip()}
    except subprocess.TimeoutExpired:
        return {"returncode": -1, "stdout": "", "stderr": f"Timeout après {timeout}s"}
    except Exception as e:
        return {"returncode": -2, "stdout": "", "stderr": str(e)}

def audit_round():
    entries = []
    entries.append(f"\n### Ronde d'Audit — {TIME_STR}\n")

    # 1. Surfaces réseau LAN
    lan_targets = [
        ("Pilot UI (.140:8080)", "http://192.168.0.140:8080/healthz"),
        ("Cockpit UI (.100:8093)", "http://192.168.0.100:8093/pilot/"),
        ("Prime Hub Godot G5+ (.246:8787)", "http://192.168.0.246:8787/healthz"),
        ("MCP Healthz (.100:8766)", "http://192.168.0.100:8766/healthz"),
        ("Ollama Heavy (.110:11434)", "http://192.168.0.110:11434/api/tags"),
        ("Ollama Light (.111:11434)", "http://192.168.0.111:11434/api/tags"),
    ]

    entries.append("| Nœud / Service | Statut | Latence (ms) | Remarque |")
    entries.append("| :--- | :---: | :---: | :--- |")

    hub_data = None
    for name, url in lan_targets:
        res = probe_http(url)
        if res.get("ok"):
            status_str = f"**OK** ({res.get('status')})"
            ms_str = f"{res.get('ms', 0):.1f} ms"
            extra = ""
            if "8787" in url and res.get("data"):
                hub_data = res.get("data")
                extra = f"Uptime {hub_data.get('uptime_s', 0)}s, PNJ: {hub_data.get('npc_count')}, Bots: {hub_data.get('bot_count')}"
            entries.append(f"| {name} | {status_str} | {ms_str} | {extra} |")
        else:
            entries.append(f"| {name} | **KO** | - | {res.get('error', 'Erreur')} |")

    # 2. Vérification statique du code (Ruff)
    ruff = run_cmd("ruff check packages/cortex tools/", timeout=10)
    if ruff["returncode"] == 0:
        entries.append("\n- **Lint Ruff** : 100% propre (0 alerte).")
    else:
        entries.append(f"\n- **Lint Ruff** : {len(ruff['stdout'].splitlines())} alertes détectées.")

    # 3. Vérification Timer YouTube
    yt_timer = run_cmd("systemctl --user is-active lbg-content-daily.timer")
    yt_active = "Actif (waiting 09h00)" if yt_timer["stdout"] == "active" else f"Inactif ({yt_timer['stdout']})"
    entries.append(f"- **Studio Content Engine Timer** : {yt_active}")

    # 4. Écriture / Append dans le rapport
    header_needed = not os.path.exists(REPORT_PATH)
    with open(REPORT_PATH, "a", encoding="utf-8") as f:
        if header_needed:
            f.write(f"# Journal d'Audit Nocturne Gladys — {DATE_STR}\n\n")
            f.write("> Ronde automatique cadencée entre 00:30 et 07:00.\n")
            f.write("> Mode Read-Only non-destructif pour la stabilité du runtime.\n\n")
        f.write("\n".join(entries) + "\n")

    print(f"Ronde d'audit complétée à {TIME_STR}. Rapport mis à jour : {REPORT_PATH}")

if __name__ == "__main__":
    audit_round()
