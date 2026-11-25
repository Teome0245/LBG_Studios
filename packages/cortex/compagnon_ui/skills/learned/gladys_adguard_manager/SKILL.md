---
name: gladys_adguard_manager
description: Gestionnaire DNS AdGuard Home : consultation des requêtes bloquées sur 192.168.0.53 et déblocage de domaines sous garde-fous.
risk_level: high
allowed_roots: []
timeout_s: 30
commands:
  run: python3 run.py
---

# Skill Gladys Appris : gladys_adguard_manager

## Description
Gestionnaire DNS AdGuard Home : consultation des requêtes bloquées sur 192.168.0.53 et déblocage de domaines sous garde-fous.

## Risque & Gouvernance
- Niveau de risque : **HIGH**
- Exécution isolée en sous-processus sans accès réseau.
