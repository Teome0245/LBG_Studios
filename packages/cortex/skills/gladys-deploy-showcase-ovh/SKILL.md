---
name: gladys-deploy-showcase-ovh
description: Déploiement sécurisé du site vitrine La Boîte à Geeks Studios (laboiteageek.fr) sur le cluster OVH. Compile les assets Vite (packages/showcase-web), effectue les vérifications d'intégrité, et synchronise via rsync SSH vers le serveur de production.
inputs:
  dry_run: (bool) Mode pré-visualisation sans transfert effectif
commands:
  run: packages/cortex/infra/scripts/deploy_showcase_ovh.py
---

# Skill Gladys : Déploiement Vitrine OVH (`laboiteageek.fr`)

## Rôle et Contexte
Gladys assure le déploiement continu et la fraîcheur du site vitrine officiel [laboiteageek.fr](https://laboiteageek.fr), vitrine technologique des 3 piliers LBG Studios (Compagnon Lia/Gladys, MMO Prime Godot 3D, Joueurs IA Autonomes).

## Procédure d'Exécution
1. **Compilation des Assets** :
   - Exécution de `npm run build` dans `packages/showcase-web`.
   - Contrôle d'intégrité du répertoire `dist/` (HTML, CSS, JS minifié, médias).
2. **Synchronisation Sécurisée** :
   - Synchronisation `rsync` via clé SSH autorisée vers `/var/www/laboiteageek.fr/`.
3. **Gouvernance L2 (HITL)** :
   - Exécutable soit en dry-run (L1), soit en déploiement réel après validation explicite ou action Pilot `showcase_deploy_ovh`.

## Commande CLI
```bash
# Mode simulation (dry-run)
python3 packages/cortex/infra/scripts/deploy_showcase_ovh.py --dry-run

# Déploiement réel
python3 packages/cortex/infra/scripts/deploy_showcase_ovh.py
```
