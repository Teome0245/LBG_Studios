#!/usr/bin/env bash
# FALLBACK atelier — écrase J:\ (dangereux si Godot / Launchpad ouverts).
# Canal joueur : deploy_prime_client_patch_246.sh puis Launchpad « Vérifier Mises à Jour ».
#
# Sync complet prime-client (WSL) → J: + tampon build_info.json + cache .godot
# + alignement Launchpad (profil prime → J:\swgemu\clients\prime-client)
set -euo pipefail

SRC="${PRIME_SRC:-/home/sdesh/projects/LBG_Studios/packages/prime-client}"
DST="${PRIME_DST:-/mnt/j/swgemu/clients/prime-client}"
GODOT_WIN_EXE="${GODOT_WIN_EXE:-J:\\mmmorpg\\Godot_v4.6.1-stable_win64\\Godot_v4.6.1-stable_win64_console.exe}"

if [[ ! -d "$SRC" ]]; then
  echo "SRC absent: $SRC" >&2
  exit 1
fi
if [[ ! -d "$(dirname "$DST")" ]]; then
  echo "J: non monté — DST=$DST" >&2
  exit 1
fi

STAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
SCHEMA="$(python3 -c "import json; print(json.load(open('$SRC/assets/maps/scrapaltai_map_config.json')).get('schema_version',0))" 2>/dev/null || echo 0)"

export STAMP SRC SCHEMA
mkdir -p "$SRC/assets"
python3 - <<'PY'
import json, os
out = {
    "client_id": "prime-client",
    "synced_at": os.environ["STAMP"],
    "sync_source": os.environ["SRC"],
    "expected_launch_path_windows": "J:\\\\swgemu\\\\clients\\\\prime-client",
    "launchpad_profile": "prime",
    "map_config_schema": int(os.environ.get("SCHEMA") or 0),
}
path = os.path.join(os.environ["SRC"], "assets", "build_info.json")
with open(path, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2)
    f.write("\n")
print("OK build_info.json", out["synced_at"])
PY

rsync -a --delete \
  --exclude '.git/' \
  --exclude '.godot/' \
  --exclude '*.import' \
  "$SRC/" "$DST/"

echo "OK rsync → $DST"

# Régénère le cache class_name Godot (sinon main.gd / entrée zone cassent).
rm -rf "$DST/.godot"
DST_WIN="$(wslpath -w "$DST")"
powershell.exe -NoProfile -Command \
  "\$g='${GODOT_WIN_EXE}'; \$p='${DST_WIN}'; if (-not (Test-Path \$g)) { Write-Output 'WARN Godot absent'; exit 0 }; & \$g --headless --path \$p --import --quit-after 40 | Out-Null; if (Test-Path (Join-Path \$p '.godot\\global_script_class_cache.cfg')) { 'OK godot import' } else { 'WARN cache .godot manquant'; exit 1 }" \
  || { echo "WARN: import Godot échoué — ouvrir le projet une fois" >&2; }

CACHE="$DST/.godot/global_script_class_cache.cfg"
if [[ -f "$CACHE" ]] && grep -q 'EntityManager' "$CACHE" && grep -q 'LbgWsClient' "$CACHE"; then
  echo "OK .godot cache (EntityManager + LbgWsClient)"
else
  echo "ERROR: cache .godot invalide après sync — ne lance pas Godot ainsi" >&2
  exit 1
fi

# Alignement Launchpad : profil prime → dossier J: syncé
python3 - <<'PY'
import json
from pathlib import Path

target = r"J:\swgemu\clients\prime-client"
godot = r"J:\mmmorpg\Godot_v4.6.1-stable_win64\Godot_v4.6.1-stable_win64.exe"
paths = [
    Path("/mnt/j/swgemu/dist/launchpad.config.json"),
    Path("/mnt/j/swgemu/dist/win-unpacked/launchpad.config.json"),
    Path("/home/sdesh/projects/LBG_Studios/packages/launchpad/launchpad.config.json"),
]
for p in paths:
    if not p.exists():
        print("skip launchpad", p)
        continue
    data = json.loads(p.read_text(encoding="utf-8"))
    changed = False
    for prof in data.get("profiles", []):
        if prof.get("id") != "prime":
            continue
        if prof.get("gameDir") != target:
            prof["gameDir"] = target
            changed = True
        if prof.get("gameExe") != godot:
            prof["gameExe"] = godot
            changed = True
        args = ["--path", target]
        if prof.get("launchArgs") != args:
            prof["launchArgs"] = args
            changed = True
        prof["clientKind"] = "godot"
        prof["skipPatch"] = True
    if changed:
        p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print("OK launchpad retarget", p)
    else:
        print("OK launchpad déjà aligné", p)
PY

echo "Relance via LBG Launchpad (profil Prime) ou Godot --path J:\\swgemu\\clients\\prime-client"
