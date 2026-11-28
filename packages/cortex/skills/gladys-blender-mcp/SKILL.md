---
name: gladys-blender-mcp
description: Permet d'exécuter des scripts Python bpy dans Blender pour manipuler la scène 3D, créer des objets low poly et exporter en GLTF.
inputs:
  script_path: (string) Chemin vers le script Python bpy à exécuter
  output_path: (string) Chemin de sortie pour l'export GLTF
commands:
  run: tools/gladys_blender.sh
---

# Skill Gladys : Blender MCP

## Rôle et Contexte
Cette skill permet d'exécuter des scripts Python bpy dans Blender afin de manipuler des scènes 3D, créer des objets low poly et exporter le résultat au format GLTF pour une utilisation dans Godot 4.

## Prérequis & Dépendances
- Blender installé localement
- Accès au script `tools/gladys_blender.sh`
- Port 9876 disponible pour la connexion MCP
- Python 3.9+ avec les dépendances nécessaires à l'exécution des scripts bpy

## Procédure d'Exécution étape par étape
1. Vérifier que Blender est installé et accessible via le script `tools/gladys_blender.sh`
2. Spécifier le chemin vers le script Python bpy à exécuter dans `script_path`
3. Définir le chemin de sortie pour l'export GLTF dans `output_path`
4. Lancer la commande d'exécution via `tools/gladys_blender.sh` avec les paramètres fournis
5. Attendre la connexion MCP sur le port 9876 et l'exécution du script
6. Récupérer le fichier GLTF généré à l'emplacement spécifié

## Commandes CLI / Intégration Gladys
- `tools/gladys_blender.sh` : Point d'entrée principal pour exécuter les scripts bpy dans Blender
- Port utilisé : 9876 (MCP)
- Format de sortie : GLTF
- Langage d'exécution : Python bpy via Blender
- Architecture cible : Godot 4 compatible