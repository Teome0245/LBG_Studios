---
name: gladys_opnsense_manager
description: Superviseur et pilote pare-feu OPNsense (192.168.0.20) : santé, passerelles, logs bloqués, DHCP et gestion L2 des alias.
risk_level: high
allowed_roots: []
timeout_s: 30
commands:
  run: python3 run.py
---

# Skill Gladys Appris : gladys_opnsense_manager

## Description
Superviseur et pilote pare-feu OPNsense (192.168.0.20) : santé, passerelles, logs bloqués, DHCP et gestion L2 des alias.

## Risque & Gouvernance
- Niveau de risque : **HIGH**
- Exécution isolée en sous-processus sans accès réseau.
