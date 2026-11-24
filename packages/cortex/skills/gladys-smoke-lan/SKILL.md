---
name: gladys-smoke-lan
description: Smoke test rapide et déterministe des 4 surfaces LAN critiques (Pilot .140, Cockpit/Orch .100, Hub Godot .246:8787, Ollama .110/.111). Détecte immédiatement les régressions d'API ou de connectivité.
commands:
  run: tools/smoke_lan_surfaces.sh --functional
---

# Skill Gladys : Smoke Test Surfaces LAN

## Rôle et Contexte
Gladys vérifie l'accessibilité fonctionnelle et réseau des 4 surfaces vitales du studio en moins de 10 secondes :
1. **Pilot UI / Cortex** (`192.168.0.140:8000` & `:8080`)
2. **Cockpit Compagnon** (`192.168.0.100:5174` & `:3000`)
3. **Hub Joueur Godot Headless** (`192.168.0.246:8787`)
4. **Centres d'Inférence Locaux** (`.110:11434` Heavy & `.111:11434` Light)

## Commande CLI
```bash
tools/smoke_lan_surfaces.sh --functional
```
