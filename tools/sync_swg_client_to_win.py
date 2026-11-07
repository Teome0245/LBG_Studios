#!/usr/bin/env python3
"""Wrapper de compatibilité — voir tools/sync_client_to_win.py."""

import subprocess
import sys
from pathlib import Path

UNIFIED = Path(__file__).resolve().parent / "sync_client_to_win.py"
sys.exit(subprocess.run([sys.executable, str(UNIFIED), "--client", "swg"] + sys.argv[1:]).returncode)
