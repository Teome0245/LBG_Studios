"""Point d'entrée gateway LBG — stub monorepo (runtime Prime :8765).

Négocie proto ``lbg-ws/1`` et preview ``lbg-ws/2`` via ``lbg_ws2``.
Le déploiement runtime complet reste sur Prime ; ce module sert les audits Team.
"""

from __future__ import annotations

# Branche lbg-ws/2 (audit readiness)
SUPPORTED = ("lbg-ws/1", "lbg-ws/2", "lbg-ws/2-preview")


def supported_protos() -> list[str]:
    from services.lbg_gateway import lbg_ws2

    return lbg_ws2.supported_protos()
