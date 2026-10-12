# server_overlay — sous-package Compagnon (CT100)

Surcouches Python appliquées par-dessus le backend orchestrateur sur `CT .100`
(`/opt/orchestrateur`). Ce dossier est un **sous-package autonome** (ticket plan
5.1) : il a son propre `pyproject.toml` (source de vérité de version) et une
carte `overlay.map` qui décrit chaque fichier livré.

## Packaging atomique

```bash
# Construire le paquet versionné (tarball + MANIFEST.sha256 + VERSION)
bash packages/cortex/infra/scripts/build_server_overlay_package.sh --out /tmp/overlay

# Déploiement atomique complet (build → upload → checksum → apply + rollback)
bash packages/cortex/infra/scripts/deploy_compagnon_100.sh --smoke

# Vérifier la version déployée sur CT100
bash packages/cortex/infra/scripts/deploy_compagnon_100.sh --check
```

Le paquet est vérifiable par **checksum de version** (`package_sha`) : le
déploiement écrit `/opt/orchestrateur/.server_overlay_version`, et un échec de
smoke restaure automatiquement la sauvegarde précédente (rollback).

L'outil `server_overlay_package.py` expose `build`, `verify`, `apply`,
`rollback`, `status` — bibliothèque standard uniquement.

## Desktop (extrait)

Module `desktop_dispatch.py` : infère `open_app` depuis le chat, route vers le
worker Windows (`pc` `.10`, `portable` `.77` / PORTABLE-SDS, etc.).

- `notepad` reste `notepad` ; `notepad++` → `notepadpp`.
- Soft-confirm LAB pour kinds à faible risque (`open_url`, sondes…) — voir
  `FOCUS_COMPAGNON.md` § D5.
