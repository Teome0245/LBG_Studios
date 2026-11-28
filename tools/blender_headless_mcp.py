#!/usr/bin/env python3
"""Lance Blender en arrière-plan avec le serveur MCP actif pour Gladys/Antigravity."""
import os
import sys
import bpy

try:
    import blender_mcp
    blender_mcp.register()
    print("[Blender MCP] Addon enregistré.")
except Exception as e:
    print(f"[Blender MCP] Erreur import addon: {e}", file=sys.stderr)
    sys.exit(1)

# Démarrer le serveur socket
try:
    bpy.ops.blendermcp.start_server()
    print("[Blender MCP] Serveur démarré avec succès sur port 9876.")
except Exception as e:
    print(f"[Blender MCP] Erreur start_server: {e}", file=sys.stderr)
    sys.exit(1)
