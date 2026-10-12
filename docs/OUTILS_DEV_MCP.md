# Outillage Dev & Analyse MCP — LBG Studios

**Date** : 2026-10-12  
**Statut** : Actif / Intégré

---

## 1. REA — Reverse Engineer Anything

- **Dépôt upstream** : [`morluto/rea`](https://github.com/morluto/rea) (Licence MIT / Open Source)
- **Objectif** : Serveur MCP (*Model Context Protocol*) permettant aux agents de dev IA (Cursor, Antigravity, Claude Code) d'inspecter, décompiler et rétro-ingénierer des formats ou exécutables sans accès au code source.

### Cibles supportées
- **Applications JavaScript / Electron** : dépaquetage d'archives `.asar`, analyse statique de code minifié/obfusqué.
- **Binaires natifs** : bridges locaux vers Ghidra, radare2, Hopper.
- **Assemblages .NET & APKs**.
- **Analyse de structures & protocoles réseau**.

### Configurations dans le monorepo
Les fichiers suivants déclarent le serveur REA en mode transport `stdio` :
- [`.cursor/mcp.json`](../.cursor/mcp.json) (Cursor IDE)
- [`.agents/mcp_config.json`](../.agents/mcp_config.json) (Antigravity IDE / Gemini CLI)

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

### Usage direct en ligne de commande (CLI)
Il est également possible d'invoquer l'outil ponctuellement depuis le terminal :
```bash
npx -y rea-agents@latest analyze-javascript-application /chemin/vers/app --json
```

### Règles de sécurité LBG Studios
1. **Local-first** : l'exécution et l'analyse restent 100 % locales sur la machine de dev.
2. **Périmètre Dev/Studio uniquement (O1)** : cet outillage est réservé aux phases d'analyse, d'audit de legacy et d'ingénierie ; il n'est **jamais** embarqué dans le runtime joueur Godot (`prime-hub` / `prime-client`).
