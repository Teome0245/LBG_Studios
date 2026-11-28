#!/usr/bin/env python3
"""
gladys_skill_factory.py — Usine à Skills Locale 0 € pour Gladys (LBG Studios).
Transforme automatiquement n'importe quelle documentation, script ou consigne en Skill standardisée LBG.
Génère le dossier conforme sous packages/cortex/skills/<nom_skill>/ avec son SKILL.md et run.sh.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "packages/cortex/skills"
OLLAMA_URL = os.environ.get("LBG_OLLAMA_URL", "http://192.168.0.110:11434")
OLLAMA_MODEL = os.environ.get("LBG_SKILL_MODEL", "huihui_ai/qwen3-coder-abliterated:30b")

META_PROMPT = """Tu es l'architecte en chef des Skills de Gladys pour le studio LBG Studios (Monorepo LBG).
Ton rôle est de créer une Skill standardisée et opérationnelle à partir de la documentation ou consigne fournie.

Une Skill chez LBG Studios se compose d'un fichier `SKILL.md` avec un frontmatter YAML strict, suivi des consignes :

```yaml
---
name: {skill_name}
description: Courte description claire du rôle de la skill (en français).
inputs:
  param1: (type) description
commands:
  run: chemin vers le script d'exécution ou commande CLI
---
```

Suivi de sections Markdown précises :
# Skill Gladys : {Nom Lisible}
## Rôle et Contexte
## Prérequis & Dépendances
## Procédure d'Exécution étape par étape
## Commandes CLI / Intégration Gladys

RÈGLES IMPÉRATIVES :
- Tout doit respecter les canons LBG (0€, local Ollama 110/111, Python/Godot, pas de mutation libre sur combat/éco).
- Sois concis, pragmatique, sans blabla.
- Réponds UNIQUEMENT avec le contenu du fichier SKILL.md complet (commençant par --- et finissant par la dernière ligne Markdown).
"""

def slugify(text: str) -> str:
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    return re.sub(r"[\s_-]+", "-", slug).strip("-")

def generate_skill(name: str, source_text: str) -> str:
    slug = slugify(name)
    meta = META_PROMPT.replace("{skill_name}", slug)
    prompt = f"{meta}\n\nDOCUMENTATION / SOURCE À TRANSFORMER EN SKILL :\n{source_text}"
    
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": "Tu es un générateur expert de spécifications de skills IA en Markdown."},
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 2048,
        }
    }
    
    try:
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data.get("message", {}).get("content", "").strip()
            # Nettoyer les balises de code si entouré
            if content.startswith("```yaml") or content.startswith("```markdown"):
                lines = content.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                content = "\n".join(lines).strip()
            return content
    except Exception as e:
        print(f"⚠️ Erreur d'appel Ollama ({OLLAMA_URL}) : {e}", file=sys.stderr)
        print("Génération du gabarit canonique par défaut en mode fallback offline...")
        return f"""---
name: {slug}
description: Skill automatique {name} générée par l'Usine à Skills Gladys.
inputs:
  target: (string) Cible ou argument principal
commands:
  run: bash packages/cortex/skills/{slug}/run.sh
---

# Skill Gladys : {name}

## Rôle et Contexte
Skill générée à partir des spécifications sources.

## Procédure d'Exécution
1. Analyse de la cible
2. Exécution de la commande
3. Contrôle de validité

## Commandes CLI
```bash
bash packages/cortex/skills/{slug}/run.sh "$@"
```
"""

def main():
    parser = argparse.ArgumentParser(description="Usine à Skills Locale pour Gladys")
    parser.add_argument("name", help="Nom de la skill (ex: blender-mcp-props)")
    parser.add_argument("--source", "-s", help="Fichier source (doc, script, markdown) ou URL", required=True)
    parser.add_argument("--force", "-f", action="store_true", help="Écraser si la skill existe déjà")
    args = parser.parse_args()

    slug = slugify(args.name)
    target_dir = SKILLS_DIR / slug
    if target_dir.exists() and not args.force:
        print(f"❌ La skill {slug} existe déjà dans {target_dir}. Utilise --force pour écraser.")
        sys.exit(1)

    source_path = Path(args.source)
    if source_path.is_file():
        source_text = source_path.read_text(encoding="utf-8")
    else:
        source_text = args.source

    print(f"🏭 [Usine à Skills] Génération de la skill '{slug}'...")
    skill_content = generate_skill(args.name, source_text)

    target_dir.mkdir(parents=True, exist_ok=True)
    skill_md = target_dir / "SKILL.md"
    skill_md.write_text(skill_content, encoding="utf-8")

    run_sh = target_dir / "run.sh"
    if not run_sh.exists():
        run_sh.write_text(f"""#!/usr/bin/env bash
# Script d'exécution automatique pour la skill {slug}
set -euo pipefail
echo "=== Exécution Skill Gladys: {slug} ==="
# Insérer la logique de la skill ici
""", encoding="utf-8")
        run_sh.chmod(0o755)

    print(f"✅ Skill '{slug}' générée avec succès dans {target_dir} !")
    print(f"📄 Spécification : {skill_md}")
    print(f"🚀 Runner CLI : {run_sh}")

if __name__ == "__main__":
    main()
