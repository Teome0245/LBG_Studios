---
name: gladys_mailcow_manager
description: Gestionnaire et superviseur Mailcow/SOGo : état des services, file SMTP et synthèse des courriers non lus.
risk_level: high
allowed_roots: []
timeout_s: 30
commands:
  run: python3 run.py
---

# Skill Gladys Appris : gladys_mailcow_manager

## Description
Gestionnaire et superviseur Mailcow/SOGo : état des services, file SMTP et synthèse des courriers non lus.

## Risque & Gouvernance
- Niveau de risque : **HIGH**
- Exécution isolée en sous-processus sans accès réseau.
