# Gladys 3D Studio & Usine à Skills Locale (0 €)

Ce document décrit l'intégration de **Blender MCP** et de l'**Usine à Skills Locale** dans l'écosystème **LBG Studios** (O1 Compagnon Gladys / O2 MMO Godot).

---

## 1. Contrôle de Blender par Gladys (Blender MCP)

### Contexte & Rôle
Permet à Gladys (ainsi qu'aux agents Antigravity, Cursor et Claude Code) de piloter Blender en local via le **Model Context Protocol (MCP)**. Gladys peut ainsi créer des props, manipuler la scène 3D, ajuster des matériaux ou déclencher des exports GLTF/GLB pour notre client Godot 4 sans intervention manuelle.

### Architecture
- **Addon Blender** : `~/.config/blender/5.2/scripts/addons/blender_mcp.py` (v2.0, écoute sur le port socket local `9876`).
- **Serveur MCP Client** : Déclaré dans `~/.gemini/settings.json` :
  ```json
  "blender": {
    "command": "/home/lbg/.local/bin/uvx",
    "args": ["mcp-for-blender"]
  }
  ```
- **Lanceur Unifié (`tools/gladys_blender.sh`)** :
  - Détecte automatiquement l'environnement graphique.
  - S'il y a un écran actif (`$DISPLAY`), lance Blender avec l'interface graphique et le serveur MCP actif.
  - En mode headless (serveur distant ou tâche sans écran), démarre automatiquement sous un serveur virtuel X via `xvfb-run -a blender --python tools/blender_headless_mcp.py`.

### Utilisation CLI
```bash
# Lancer Blender avec MCP actif
bash tools/gladys_blender.sh
```

---

## 2. Usine à Skills Locale 0 € (`tools/gladys_skill_factory.py`)

### Contexte & Rôle
Inspirée des concepts de méta-génération d'instructions (comme l'utilisation de carnets IA en "usine à skills"), cette usine CLI locale permet de transformer n'importe quel document brut, script Python ou consigne technique en une **Skill standardisée LBG Studios**.

### Spécification des Skills LBG
Chaque skill produite est placée sous `packages/cortex/skills/<nom_skill>/` et contient :
1. **`SKILL.md`** : Frontmatter YAML strict (`name`, `description`, `inputs`, `commands`) suivi des sections canoniques (Rôle, Prérequis, Procédure d'exécution pas à pas, Commandes CLI).
2. **`run.sh`** : Script bash exécutable servant de point d'entrée pour l'exécution autonome par Gladys.

### Fonctionnement & IA Locale
- Se connecte directement sur notre VM d'inférence locale **`.110`** (`http://192.168.0.110:11434`) sur le modèle `huihui_ai/qwen3-coder-abliterated:30b`.
- Coût d'inférence : **0 €**.
- Mode hors-ligne / fallback automatique : si le serveur Ollama est inaccessible, génère un squelette canonique propre sans bloquer le workflow.

### Utilisation CLI
```bash
# Générer une nouvelle skill à partir d'un fichier source
python3 tools/gladys_skill_factory.py "nom-de-la-skill" --source /chemin/vers/doc.txt

# Écraser une skill existante
python3 tools/gladys_skill_factory.py "nom-de-la-skill" --source "Texte ou consignes brutes..." --force
```

### Première Skill Déployée
- `packages/cortex/skills/gladys-blender-mcp/` : Skill permettant à Gladys d'orchestrer la modélisation et l'export GLTF via Blender.
