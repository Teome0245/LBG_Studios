# Outillage Dev & Analyse MCP — LBG Studios

**Date** : 2026-10-12  
**Statut** : Actif / Intégré multi-environnements

---

## 1. REA — Reverse Engineer Anything

- **Dépôt upstream** : [`morluto/rea`](https://github.com/morluto/rea) (Licence MIT / Open Source)
- **Objectif** : Serveur MCP (*Model Context Protocol*) permettant aux agents de dev IA d'inspecter, décompiler et rétro-ingénierer des formats, applications ou exécutables sans accès au code source.

### Cibles supportées
- **Applications JavaScript / Electron** : dépaquetage d'archives `.asar`, analyse statique de code minifié/obfusqué.
- **Binaires natifs** : bridges locaux vers Ghidra, radare2, Hopper.
- **Assemblages .NET & APKs**.
- **Analyse de structures & protocoles réseau**.

---

## 2. Matrice d'intégration dans l'écosystème LBG Studios

Chaque outil dispose de sa configuration prête à l'emploi dans le monorepo :

| Environnement / Outil | Fichier de configuration | Prise en charge |
|-----------------------|--------------------------|-----------------|
| **Cursor IDE** | [`.cursor/mcp.json`](../.cursor/mcp.json) | Automatique au chargement du workspace |
| **Antigravity IDE / Gemini CLI** | [`.agents/mcp_config.json`](../.agents/mcp_config.json) | Automatique via le système de personnalisation `.agents/` |
| **Claude Code & OpenCode** | [`.mcp.json`](../.mcp.json) | Standard racine MCP lu nativement par Claude Code et OpenCode |
| **Cline (VS Code)** | [`.vscode/cline_mcp_settings.json`](../.vscode/cline_mcp_settings.json) | Chargé par Cline dans VS Code ou importable directement |
| **Studio (Cortex / Team / Métis / Iris)** | [`tools/rea_runner.sh`](../tools/rea_runner.sh) | Script wrapper exécutable en sub-process ou en CLI |

---

## 3. Configuration MCP standard

```json
{
  "mcpServers": {
    "rea": {
      "command": "npx",
      "args": [
        "-y",
        "rea-agents@latest"
      ]
    }
  }
}
```

---

## 4. Usage direct en ligne de commande (Studio / CLI)

Via le wrapper monorepo :
```bash
# Lancer le serveur MCP en direct (stdio) :
./tools/rea_runner.sh

# Analyser une application JavaScript / Electron :
./tools/rea_runner.sh analyze-javascript-application /chemin/vers/app --json
```

---

## 5. Règles de sécurité LBG Studios

1. **Local-first absolu** : l'exécution et l'analyse restent 100 % locales sur l'infrastructure LBG ; aucun binaire ni jeton n'est envoyé vers des tiers.
2. **Périmètre Dev/Studio uniquement (O1)** : cet outillage est réservé aux phases d'analyse, d'audit de legacy et d'ingénierie ; il n'est **jamais** embarqué dans le runtime joueur Godot (`prime-hub` / `prime-client`).
