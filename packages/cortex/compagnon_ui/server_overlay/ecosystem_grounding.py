"""Ancrage écosystème LBG — REGISTRE-lite pour le chat Compagnon.

Faits stables (hosts / surfaces) — pas de sonde live (Héphaïstos reste sur Agir).
"""

from __future__ import annotations

import re

_ECOSYSTEM_HINTS = re.compile(
    r"(?i)("
    r"\béco[- ]?syst[eè]me\b|\becosysteme\b|"
    r"\bmmo\b|\bprime\b|\bprecu\b|\bpre-cu\b|"
    r"\b246\b|\.246\b|192\.168\.0\.246|"
    r"\.245\b|192\.168\.0\.245|"
    r"\.140\b|192\.168\.0\.140|"
    r"\.100\b|192\.168\.0\.100|"
    r"\.110\b|192\.168\.0\.110|"
    r"\.111\b|192\.168\.0\.111|"
    r"\.10\b|192\.168\.0\.10\b|"
    r"\bserveurs?\b|\bmachines?\b|\br[ée]seaux?\b|\btopologie\b|"
    r"\bnom\s+des\s+serveurs\b|\bip\b|\badresses?\b|\bh[oô]tes?\b|"
    r"\bl1\b|\bl2\b|\bdivag|\bhallucin|"
    r"\bsidecar\b|\bcore3\b|"
    r"\bincarner\b|\bincarnation\b|\bt['\u2019]incarner\b|"
    r"\blia\b|\blyra\b|"
    r"\bregistre\b|\blost\s+heaven\b|\bscrapaltai\b|"
    r"\bgateway\b|\b8792\b|\b8791\b|"
    r"\bnas\b|\bsynology\b|\.51\b|192\.168\.0\.51|"
    r"\bproxmox\b|\b200\b|\b201\b|192\.168\.0\.(?:200|201)|"
    r"\bfreebox\b|\bslack\b|\b#lbg-ops\b|"
    r"\bpilot\b|\bcompagnon\b|\bstudio\s+lbg\b"
    r")"
)

# Snapshot aligné docs/REGISTRE.md — tenir à jour si adressage change.
_ECOSYSTEM_FACTS = """\
ÉCOSYSTÈME LBG (REGISTRE canonique — vérité stricte d'infrastructure) :
- Compagnon (présence chat) : http://192.168.0.100:5174/ · API Orch :3000
- Pilot / Cortex (ops, Team, Self) : http://192.168.0.140:8080/ · orch :8010 (.140 est un SERVEUR, JAMAIS un modèle IA)
- NAS Synology DS1815+ (stockage, LUN nas-lun-backup iSCSI sur .201, SMB N:\\ sur .10, DSM 7.1.1) : 192.168.0.51
- Hyperviseurs Proxmox VE : .200 (NUC) et .201 (R720) hébergeant VMs et CTs
- LLM local heavy : http://192.168.0.110:11434 (RTX : gemma-4 12b, qwen3.5 9b)
- LLM local light : http://192.168.0.111:11434 (e4b-qat, 2B, qwen2.5:3b)
- Windows SDS (Bureau / Pygmalion ComfyUI / Pet / pont HTTP) : 192.168.0.10:8765
- VMs agents spécialisés : .141 (executor), .142 (hands), .143 (dev)
- Routeur Freebox v7 (API Freebox OS, baux statiques, topologie réseau L2) : 192.168.0.254
- Canal ops : Slack #lbg-ops (alertes santé, HITL L2, digests midi/soir) + Matrix/Element en backup
- Prime monde MMO (écriture) : 192.168.0.246:8787 (prime-hub Godot HTTP+WS) — Core3 / hub_runtime Python = OFF joueur
- PreCU (référence SWG, lecture seule) : 192.168.0.245 — ne pas modifier
- Incarnations : studio = Lyra/Compagnon · MMO = Lia (Rang 2 persona)
- Mémoire à renforcer côté MMO = Self / leçons / session_summary — pas la RAM des VM
- Source monorepo : LBG_Studios (cortex = O1 Studio · prime-client = O2 Jeu)

RÈGLES STRICTES D'INFRASTRUCTURE ET DE COMPORTEMENT :
1. IL N'EXISTE AUCUN SERVEUR PHYSIQUE NI VM APPELÉ « L1 » OU « L2 ». L1 et L2 désignent EXCLUSIVEMENT des niveaux de gouvernance et de validation humaine HITL (L1=lecture seule/sondes, L2=approbation humaine Pilot).
2. .140 est le serveur Pilot/Cortex, JAMAIS un modèle d'IA.
3. Le Compagnon ne simule JAMAIS d'actions techniques en tâche de fond (« je lance le test », « en cours d'optimisation », « c'est parti sur le terrain »).
4. Si l'humain signale qu'une entité n'existe pas, l'abandonner immédiatement sans chercher à justifier son absence ou prétendre qu'elle est hors ligne.
5. Si le NAS .51 est indisponible, le LUN iSCSI décroche et /mnt/pve/nas-lun-backup retombe sur le disque racine Proxmox (.201/.200) : les sauvegardes vzdump doivent être suspendues."""


def wants_ecosystem_context(prompt: str) -> bool:
    return bool(_ECOSYSTEM_HINTS.search(prompt or ""))


def format_ecosystem_grounding() -> str:
    return _ECOSYSTEM_FACTS.strip()

