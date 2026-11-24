---
name: gladys-nocturnal-audit
description: Ronde d'audit nocturne autonome 0€ pour Gladys. Sonde la santé globale du LAN, vérifie l'intégrité des services, consigne les résultats dans un journal Markdown daté et alerte sur Slack #lbg-ops si anomalie critique.
inputs:
  dry_run: (bool) Mode simulation sans écriture ni alerte
commands:
  run: tools/nocturnal_gladys_auditor.py
---

# Skill Gladys : Audit Nocturne Autonome (0€ Cloud)

## Rôle et Contexte
Gladys opère une veille nocturne continue pour garantir la haute disponibilité de l'écosystème LBG Studios sans consommer le moindre centime en API Cloud propriétaire.

## Procédure d'Exécution
Le skill exécute la sonde complète des organes vitaux :
1. **Sonde Réseau & Services** :
   - Pilot / Cortex (`192.168.0.140:8000` & `:8080`)
   - Compagnon Chat & Orchestrateur (`192.168.0.100:5174` & `:3000`)
   - Hub Godot Lost Heaven (`192.168.0.246:8787`)
   - Cerveaux d'Inférence Locaux Ollama (`.110:11434` Heavy & `.111:11434` Light)
2. **Consignation** :
   - Génération du rapport Markdown canonique dans `docs/AUDIT_NOCTURNE_<DATE>.md`.
3. **Escalade HITL** :
   - En cas de panne critique (ex: rupture de stockage NAS `.51`, service hors-ligne), notification sur Slack `#lbg-ops`.

## Commande CLI
```bash
python3 tools/nocturnal_gladys_auditor.py
```
