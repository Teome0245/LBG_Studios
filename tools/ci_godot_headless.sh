#!/usr/bin/env bash
# tools/ci_godot_headless.sh — Runner de tests headless Godot pour prime-hub (Ticket 5.2)
#
# Exécute la suite complète de tests mécaniques et économiques en local / CI :
#   1. sim_selftest.gd : Simulateur HubSim modulaire (combat, présence, 60 ticks)
#   2. nav_selftest.gd : Navigation 3D navmesh (NavigationServer3D, 40 entités)
#   3. db_selftest.gd  : SQLite transactionnel WAL, auth, positions, état économique
#
# Aucun réseau LAN requis. Exécution complète en < 10 s.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PRIME_HUB_DIR="${REPO_ROOT}/packages/prime-hub"
PRIME_CLIENT_DIR="${REPO_ROOT}/packages/prime-client"

# Recherche du binaire Godot headless
GODOT_BIN="${GODOT_BIN:-}"
if [[ -z "${GODOT_BIN}" ]]; then
  if [[ -x "${PRIME_HUB_DIR}/tools/Godot_v4.6.3-stable_linux.x86_64" ]]; then
    GODOT_BIN="${PRIME_HUB_DIR}/tools/Godot_v4.6.3-stable_linux.x86_64"
  elif [[ -x "${PRIME_HUB_DIR}/tools/godot" ]]; then
    GODOT_BIN="${PRIME_HUB_DIR}/tools/godot"
  elif command -v godot >/dev/null 2>&1; then
    GODOT_BIN="$(command -v godot)"
  else
    echo "[-] ERREUR: Binaire Godot introuvable." >&2
    echo "    Spécifiez GODOT_BIN=/chemin/vers/godot ou installez Godot 4.6 headless." >&2
    exit 1
  fi
fi

echo "============================================================"
echo "  CI Godot Headless — Tests prime-hub (Ticket 5.2)"
echo "  Binaire : ${GODOT_BIN}"
echo "============================================================"

START_TS=$(date +%s)
FAILED=0

run_test() {
  local name="$1"
  local script_res="$2"
  echo ""
  echo "--- [TEST] ${name} (${script_res}) ---"
  local t0=$(date +%s)
  if "${GODOT_BIN}" --headless --path "${PRIME_HUB_DIR}" -s "${script_res}"; then
    local dt=$(( $(date +%s) - t0 ))
    echo "[+] PASS: ${name} (en ${dt}s)"
  else
    local dt=$(( $(date +%s) - t0 ))
    echo "[-] FAIL: ${name} (en ${dt}s)" >&2
    FAILED=$((FAILED + 1))
  fi
}

run_client_test() {
  local name="$1"
  local script_res="$2"
  echo ""
  echo "--- [TEST] ${name} (${script_res}) ---"
  local t0=$(date +%s)
  if "${GODOT_BIN}" --headless --path "${PRIME_CLIENT_DIR}" -s "${script_res}"; then
    local dt=$(( $(date +%s) - t0 ))
    echo "[+] PASS: ${name} (en ${dt}s)"
  else
    local dt=$(( $(date +%s) - t0 ))
    echo "[-] FAIL: ${name} (en ${dt}s)" >&2
    FAILED=$((FAILED + 1))
  fi
}

run_test "Simulateur HubSim (combat, présence, ticks)" "res://tools/sim_selftest.gd"
run_test "Navigation 3D (NavigationServer3D, navmesh)" "res://tools/nav_selftest.gd"
run_test "Bâtiments CAO & Portes découpées (HubBlueprintBuilder)" "res://tools/building_cad_selftest.gd"
run_test "Persistance & Économie (SQLite WAL, auth, state)" "res://tools/db_selftest.gd"
run_client_test "Client Prime modulaire & Inventaire DnD" "res://tools/client_modular_selftest.gd"

TOTAL_DURATION=$(( $(date +%s) - START_TS ))

echo ""
echo "============================================================"
if [[ ${FAILED} -eq 0 ]]; then
  echo "[OK] Tous les tests headless Godot ont réussi en ${TOTAL_DURATION}s (<10s DoD)."
  echo "============================================================"
  exit 0
else
  echo "[FAIL] ${FAILED} test(s) en échec (durée totale : ${TOTAL_DURATION}s)." >&2
  echo "============================================================"
  exit 1
fi
