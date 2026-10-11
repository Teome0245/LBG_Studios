#!/usr/bin/env bash
# Smoke ticket 2.1 — SQLite prime-hub : selftest + crash-safety.
#
# 1. selftest headless (schéma / insert / reload / async / intégrité)
# 2. writer Godot headless qui enqueue des écritures en continu → kill -9
#    en pleine écriture → PRAGMA integrity_check ok + données lisibles.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GODOT="${GODOT_BIN:-$ROOT/tools/godot}"
[[ -x "$GODOT" ]] || GODOT="$(command -v godot)"
if [[ -z "$GODOT" ]]; then echo "ERR: godot introuvable" >&2; exit 1; fi
command -v sqlite3 >/dev/null || { echo "ERR: sqlite3 CLI requis" >&2; exit 1; }

TMP="$(mktemp -d /tmp/opencode/db_smoke.XXXXXX)"
STATE="$TMP/state"
mkdir -p "$STATE"
cleanup() { rm -rf "$TMP"; rm -f "$ROOT/tools/.db_writer.gd"; }
trap cleanup EXIT

echo "==> selftest (1/3)"
SELF_LOG="$TMP/selftest.log"
LBG_PRIME_HUB_STATE_DIR="$STATE" \
  "$GODOT" --headless --path "$ROOT" --script "res://tools/db_selftest.gd" 2>&1 | tee "$SELF_LOG"
if ! grep -q "selftest: .* OK$" "$SELF_LOG"; then
  echo "ERR: selftest échoué" >&2
  exit 1
fi
DB="$STATE/prime_hub.sqlite3"
[[ -f "$DB" ]] || { echo "ERR: $DB absent" >&2; exit 1; }

echo "==> writer kill -9 (2/3)"
cat > "$ROOT/tools/.db_writer.gd" <<'GDS'
extends SceneTree
const HubDb = preload("res://scripts/hub_db.gd")
func _init() -> void:
	var out: Array = []
	OS.execute("sqlite3", ["-version"], out, true)
	print("writer start ok")
	var db := HubDb.get_shared()
	for i in range(3000):
		db.enqueue([
			"INSERT INTO player_positions(oid,x,y,z,name,ts) VALUES(%d,%f,0.15,%f,'smoke',%d) "
			% [100000 + i, 5000.0 + i, -800.0 + i, i]
			+ "ON CONFLICT(oid) DO UPDATE SET x=excluded.x,y=excluded.y,z=excluded.z,name=excluded.name,ts=excluded.ts;",
		])
		if i % 100 == 0:
			OS.delay_msec(1)
	print("writer loop done")
GDS

LBG_PRIME_HUB_STATE_DIR="$STATE" \
  "$GODOT" --headless --path "$ROOT" --script "res://tools/.db_writer.gd" >"$TMP/writer.log" 2>&1 &
PID=$!
sleep 2
kill -9 "$PID" 2>/dev/null || true
wait "$PID" 2>/dev/null || true
rm -f "$ROOT/tools/.db_writer.gd"

echo "==> attestation (3/3)"
INTEGRITY="$(sqlite3 -readonly "$DB" "PRAGMA integrity_check;" | head -1)"
NROWS="$(sqlite3 -readonly "$DB" "SELECT count(*) FROM player_positions WHERE oid >= 100000;" | head -1)"
if [[ "$INTEGRITY" != "ok" ]]; then
  echo "ERR: corruption après kill -9 (integrity=$INTEGRITY)" >&2
  exit 1
fi
[[ "$NROWS" =~ ^[0-9]+$ ]] || { echo "ERR: lecture données impossible (nrows=$NROWS)" >&2; exit 1; }
echo "OK — kill -9 sans corruption: integrity=$INTEGRITY · lignes positions smoke=$NROWS (ticket 2.1 LIVE)"