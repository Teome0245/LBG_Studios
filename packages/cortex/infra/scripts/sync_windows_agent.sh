#!/usr/bin/env bash
set -euo pipefail

# Sync du module Windows Agent_IA vers C:\Agent_IA (WSL).
#
# Usage:
#   bash LBG_IA_MMO/infra/scripts/sync_windows_agent.sh
#
# Prérequis:
# - WSL avec montage /mnt/c

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/windows_agent/Agent_IA"
DST="/mnt/c/Agent_IA"

if [ ! -d "$SRC" ]; then
  echo "ERREUR: source introuvable: $SRC" >&2
  exit 1
fi
if [ ! -d "/mnt/c" ]; then
  echo "ERREUR: /mnt/c introuvable (WSL?)" >&2
  exit 1
fi

mkdir -p "$DST"

# Copie "miroir" des fichiers de code/doc.
cp -f "$SRC/main.py" "$DST/main.py"
cp -f "$SRC/executor.py" "$DST/executor.py"
cp -f "$SRC/models.py" "$DST/models.py"
cp -f "$SRC/program_resolver.py" "$DST/program_resolver.py"
cp -f "$SRC/mail_imap_preview.py" "$DST/mail_imap_preview.py"
cp -f "$SRC/face_parts_import_action.py" "$DST/face_parts_import_action.py"
cp -f "$SRC/comfyui_lifecycle.py" "$DST/comfyui_lifecycle.py"
cp -f "$SRC/requirements.txt" "$DST/requirements.txt"
cp -f "$SRC/run_agent.cmd" "$DST/run_agent.cmd"
cp -f "$SRC/start_agent.cmd" "$DST/start_agent.cmd"
cp -f "$SRC/restart_agent.cmd" "$DST/restart_agent.cmd"
cp -f "$SRC/start_comfyui.cmd" "$DST/start_comfyui.cmd"
cp -f "$SRC/run_comfyui.cmd" "$DST/run_comfyui.cmd"
cp -f "$SRC/restart_comfyui.cmd" "$DST/restart_comfyui.cmd"
cp -f "$SRC/comfyui_process.ps1" "$DST/comfyui_process.ps1"
cp -f "$SRC/start_comfyui.ps1" "$DST/start_comfyui.ps1"
cp -f "$SRC/restart_comfyui.ps1" "$DST/restart_comfyui.ps1"
cp -f "$SRC/agent_ia_process.ps1" "$DST/agent_ia_process.ps1"
cp -f "$SRC/start_agent.ps1" "$DST/start_agent.ps1"
cp -f "$SRC/restart_agent.ps1" "$DST/restart_agent.ps1"
cp -f "$SRC/install_agent_ia_scheduled_tasks.ps1" "$DST/install_agent_ia_scheduled_tasks.ps1"
cp -f "$SRC/desktop.env.example" "$DST/desktop.env.example"

# Ne pas écraser `desktop.env` utilisateur s’il existe déjà.
if [ ! -f "$DST/desktop.env" ]; then
  cp -f "$SRC/desktop.env" "$DST/desktop.env"
fi

# Pipeline Murrik texture (DDS -> ComfyUI -> DDS)
INFRA="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LBG_MMO="$(cd "${INFRA}/../.." && pwd)"
mkdir -p "$DST/workflows" "$DST/tools"
cp -f "$INFRA/murrik_texture_dds_to_dds.ps1" "$DST/murrik_texture_dds_to_dds.ps1"
cp -f "${LBG_MMO}/infra/workflows/murrik_texture_reskin_tile_v2_api.json" "$DST/workflows/murrik_texture_reskin_tile_v2_api.json"
cp -f "$INFRA/tools/gimp_dds_convert.scm" "$DST/tools/gimp_dds_convert.scm"

echo "OK: sync -> $DST"

