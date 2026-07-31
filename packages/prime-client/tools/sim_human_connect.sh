#!/usr/bin/env bash
# Simule la connexion d'un joueur humain au hub Lost Heaven (UDP :12345).
set -euo pipefail
HOST="${1:-127.0.0.1}"
PORT="${2:-12345}"
OID="${3:-999001}"
X="${4:-4749}"
Z="${5:--737}"
PL="${6:-tatooine}"
PAYLOAD=$(printf '{"t":"cn","id":%s,"x":%s,"y":%s,"z":5,"pl":"%s"}' "$OID" "$X" "$Z" "$PL")
echo "→ $PAYLOAD"
echo "$PAYLOAD" | nc -u -w1 "$HOST" "$PORT"
echo "Packet cn envoyé. Dans Godot : H pour hub, ZQSD si prime_controller écoute :12346."
