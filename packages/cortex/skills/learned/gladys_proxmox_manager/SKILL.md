---
name: gladys_proxmox_manager
description: Superviseur et pilote Proxmox VE (lbgr720 / 192.168.0.201) : inventaire LXC/VM, backups, snapshots et contrôle d'alimentation L2.
risk_level: high
allowed_roots: []
timeout_s: 30
commands:
  run: python3 run.py
---

# Skill Gladys Appris : gladys_proxmox_manager

## Description
Superviseur et pilote Proxmox VE (lbgr720 / 192.168.0.201) : inventaire LXC/VM, backups, snapshots et contrôle d'alimentation L2.

## Risque & Gouvernance
- Niveau de risque : **HIGH**
- Exécution isolée en sous-processus sans accès réseau.
