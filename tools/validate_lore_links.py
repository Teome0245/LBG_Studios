#!/usr/bin/env python3
"""
Validateur de liens wiki et extracteur de graphe de connaissances (Second Brain LBG).
Vérifie la cohérence du coffre Markdown dans docs/lore/ (format Obsidian).
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Extrait le frontmatter YAML basique et le corps markdown."""
    meta = {}
    body = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            raw_yaml = parts[1]
            body = parts[2]
            for line in raw_yaml.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    k = k.strip()
                    v = v.strip().strip('"\'')
                    if k:
                        meta[k] = v
    return meta, body


def extract_wiki_links(text: str) -> list[str]:
    """Trouve tous les liens [[target]] ou [[target|alias]]."""
    matches = re.findall(r"\[\[([^\]\|]+)(?:\|[^\]]+)?\]\]", text)
    return [m.strip() for m in matches]


def build_lore_graph(lore_dir: Path) -> dict:
    nodes = {}
    edges = []

    # 1. Recenser tous les fichiers et leurs IDs
    for p in lore_dir.rglob("*.md"):
        content = p.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(content)
        node_id = meta.get("id") or p.stem
        title = meta.get("title") or meta.get("name") or p.stem
        node_type = meta.get("type", "document")
        relative_path = str(p.relative_to(lore_dir))

        nodes[node_id] = {
            "id": node_id,
            "title": title,
            "type": node_type,
            "path": relative_path,
            "links_to": extract_wiki_links(content),
            "incoming_count": 0,
        }

    # 2. Résoudre les arêtes et détecter les liens cassés
    broken_links = []
    for src_id, node in nodes.items():
        for target_id in node["links_to"]:
            if target_id in nodes:
                nodes[target_id]["incoming_count"] += 1
                edges.append({"source": src_id, "target": target_id})
            else:
                broken_links.append({"source": src_id, "target": target_id, "file": node["path"]})

    return {
        "nodes": nodes,
        "edges": edges,
        "broken_links": broken_links,
    }


def main():
    parser = argparse.ArgumentParser(description="Validateur de graphe de connaissances Second Brain LBG")
    parser.add_argument("--dir", type=str, default="docs/lore", help="Répertoire racine du lore (défaut: docs/lore)")
    parser.add_argument("--json", action="store_true", help="Afficher le graphe au format JSON")
    parser.add_argument("--export", type=str, default=None, help="Exporter la topologie en JSON pour le Pilot UI")

    args = parser.parse_args()
    lore_path = Path(args.dir)

    if not lore_path.exists():
        sys.stderr.write(f"Dossier introuvable : {lore_path}\n")
        sys.exit(1)

    graph = build_lore_graph(lore_path)
    nodes = graph["nodes"]
    edges = graph["edges"]
    broken = graph["broken_links"]

    if args.json:
        print(json.dumps(graph, indent=2, ensure_ascii=False))
        sys.exit(0)

    if args.export:
        export_path = Path(args.export)
        export_path.parent.mkdir(parents=True, exist_ok=True)
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(graph, f, indent=2, ensure_ascii=False)
        print(f"Topologie exportée avec succès vers {export_path}")

    print("\n" + "=" * 60)
    print(" 🧠 SECOND BRAIN LBG — RAPPORT DE TOPOLOGIE DU LORE")
    print("=" * 60)
    print(f"• Total nœuds documentés : {len(nodes)}")
    print(f"• Total relations reliées : {len(edges)}")
    print(f"• Liens cassés (invalides) : {len(broken)}")

    orphans = [n_id for n_id, n in nodes.items() if n["incoming_count"] == 0]
    print(f"• Nœuds orphelins (sans référence entrante) : {len(orphans)}")

    if broken:
        print("\n❌ LIENS CASSÉS DÉTECTÉS :")
        for b in broken:
            print(f"  - [[{b['target']}]] introuvable dans {b['file']} (depuis {b['source']})")

    if orphans:
        print("\nℹ️  NŒUDS RACINES OU ORPHELINS :")
        for o in orphans:
            print(f"  - {o} ({nodes[o]['title']})")

    print("=" * 60)
    if broken:
        sys.exit(1)
    else:
        print("✅ Le graphe de connaissances Second Brain est parfaitement intègre !")
        sys.exit(0)


if __name__ == "__main__":
    main()

