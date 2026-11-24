---
name: gladys-blender-pipeline-143
description: Pilotage de l'Atelier Omarchy (.143) par Gladys pour la génération, l'optimisation et le baking de modèles 3D GLB et animations VRMA via Blender headless.
inputs:
  script: (string) Chemin relatif ou absolu du script Python Blender à exécuter
  background: (bool) Exécution en arrière-plan sans UI (default: true)
commands:
  run: tools/render_full_clip_143.py ou SSH .143 blender --background -P
---

# Skill Gladys : Atelier 3D Blender Headless (.143)

## Rôle et Contexte
Gladys délègue les tâches de modélisation 3D lourdes, de baking PBR et d'export d'animations à la station de travail Omarchy (`192.168.0.143`) via Blender en mode headless (CLI).

## Procédure d'Exécution
1. **Préparation du Script** :
   - Le script Blender Python (ex: baking, retargeting VRMA, génération d'armures mecha) est synchronisé ou référencé.
2. **Exécution Distribuée** :
   - Gladys déclenche Blender en tâche de fond sur `.143` via SSH :
     `ssh lbg@192.168.0.143 "blender --background --python <SCRIPT_PATH> -- <ARGS>"`
3. **Récupération des Assets** :
   - Les fichiers GLB / VRMA compilés sont rapatriés vers `packages/prime-client/assets/` ou déployés sur le serveur de patch `.246`.

## Commande CLI
```bash
bash packages/cortex/skills/gladys-blender-pipeline-143/run.sh <SCRIPT_BLENDER> [ARGS...]
```
