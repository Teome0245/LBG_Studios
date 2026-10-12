# Écosystème LBG — développement depuis `.143`

**Date** : 2026-09-28  
**But** : que **Compagnon**, la **Team** et le **studio** portent le développement du monorepo — pas seulement Cursor humain.  
**Poste éditeur** : VM Omarchy **`.143`** — héberge **VS Code** pour que l’écosystème LBG puisse coder / Agir sur le monorepo.  
**LLM** : Ollama **`.110` / `.111`** (pas sur `.143`).  
**Leçon M2/M3** : [`lecon_m2_m3_self_compagnon_2026-09-27.md`](lecon_m2_m3_self_compagnon_2026-09-27.md).

Voir aussi : [`sans_cursor.md`](sans_cursor.md) · [`omarchy_vm_143.md`](omarchy_vm_143.md) · [`cline/SMOKE.md`](cline/SMOKE.md) · [`FOCUS_COMPAGNON.md`](../../../docs/FOCUS_COMPAGNON.md) · **catalogue outils** [`adr/0023-catalogue-outils-ide-second-avis.md`](adr/0023-catalogue-outils-ide-second-avis.md) (autorisé / expérimentation / interdit + second avis) · greffe **Prime Agent** [`adr/0024-prime-agent-greffe-peripherique.md`](adr/0024-prime-agent-greffe-peripherique.md) · [`prime_agent_143.md`](prime_agent_143.md).

---

## Qui fait quoi

| Acteur | Rôle développement | Surface |
|--------|--------------------|---------|
| **Humain** | Intention, L2, go/no-go | Compagnon `:5174`, Pilot, VS Code sur `.143` |
| **Compagnon** | Propose / Agir (dry-run → confirm) · ouvre éditeur `.143` · rappelle objectifs Studio | http://192.168.0.100:5174/ |
| **Team** (Lyra, Thémis, Dédale…) | Plans, tâches L1, smokes, leçons, Self | Pilot `#/team` · orch `:8010` |
| **VS Code sur `.143`** | Shell IDE Omarchy (workspace monorepo) | `/home/lbg/projects/LBG_Studios` |
| **Cline** *(composant IDE)* | Agent Plan→Act (Ollama `.110`) | Extension `saoudrizwan.claude-dev` |
| **Continue** *(composant IDE)* | Chat / edit / autocomplete (Ollama `.110`) | Extension Continue · `~/.continue` |
| **Claude Code** *(composant IDE)* | Agent UI VS Code branché Ollama local (souvent Act 12b) | Onglet Claude Code · **≠** Claude cloud |
| **Deploy lab** | git push + `deploy_*` (pas rsync massif) | ex. `deploy_compagnon_100.sh` |

**Séparation nette** : `.143` = **exécution VS + extensions** · `.110` = **inférence Ollama**.  
Cline, Continue et Claude Code sont **trois composants distincts** dans le même VS Code — pas Copilot (cloud, panneau Conversation client).

**Disponibilité ops (2026-10-08)** :
| Chemin | Comment | Prérequis |
|--------|---------|-----------|
| **OpenCode headless** (Team/Métis) | `context.ide_cli` + `desktop_approval` → `run_cli_agent` | ADR 0025 · `LBG_TEAM_IDE_CLI_ENABLED=1` |
| **Cline UI / CLI** | UI : `ouvre code sur omarchy` · CLI second avis : `lance cline sur omarchy` ([`cline/CLI_SECOND_AVIS.md`](cline/CLI_SECOND_AVIS.md)) | Provider **Ollama** `.110` · modèle plancher **`E4b-qat`** · **pas** d’auth Anthropic |
| **Claude Code UI** | Extension `anthropic.claude-code` | Distinct du CLI : si `WAITING FOR AUTH`, reconnecter dans le panneau (CLI `claude auth status` peut déjà être OK) |
| **Claude CLI** | `lance claude sur omarchy pour …` | Expérimental (hang Ollama) ; dry-run OK |

**Catalogue** : seuls ces trois (+ scripts Terminal) sont **autorisés** en chemin nominal. Tout autre agent = greffe expérimentale ou **second avis** ponctuel — ADR [`0023`](adr/0023-catalogue-outils-ide-second-avis.md). Pas d’empilement permanent.

Principe : **percevoir → vouloir → proposer → (humain/L2) → coder sur `.143` → commit/push → deploy → leçon**.

---

## Boucle cible (maturation M1+)

```text
Self / proactive (.140)  →  initiative Compagnon (:5174)
        ↓
  Agir L1 (dry-run)  ou  « ouvre VS Code / Cline sur omarchy »
        ↓
  Team run_task / plan  (Dédale, Argus…)
        ↓
  Édition sur .143 (Cline Plan→Act)  →  git commit/push
        ↓
  deploy_* lab  →  smoke  →  leçon / Self update
```

Compagnon **n’exécute pas** de Réel destructeur sans contre-pouvoir.  
Cline **n’est pas** un second OS : même monorepo, même matrice LLM (`.110`/`.111`).

---

## Actions Agir utiles (éditeur)

| Intention | Texte Agir typique |
|-----------|-------------------|
| Ouvrir l’IDE studio | `ouvre code sur omarchy` / `ouvre vscode sur omarchy` |
| **Mains code headless** (ADR [`0025`](adr/0025-mains-code-143-run-cli-agent.md)) | `lance opencode sur omarchy pour …` (nominal, `big-pickle`) · `lance cline sur omarchy pour …` (second avis, Ollama `.110`) — kind `run_cli_agent` ; Iris/Dédale/Pygmalion/Métis via `context.ide_cli` ; Claude CLI expérimental ; UI Cline = `open_app` — [`cline/CLI_SECOND_AVIS.md`](cline/CLI_SECOND_AVIS.md) |
| Second avis (concurrent) | `second avis claude code sur omarchy` · `deuxième avis opencode` — ADR [`0023`](adr/0023-catalogue-outils-ide-second-avis.md) § 3 |
| Mettre à jour VS Code | `mets à jour vscode sur omarchy` (dry-run → confirm ; **pas** pendant Cline critique) |
| Compagnon | `ouvre http://192.168.0.100:5174/ dans le navigateur` |
| Team / Jobs | `ouvre http://192.168.0.140:8080/#/team` · `#/jobs` |
| Smoke Cline | voir `docs/cline/SMOKE.md` (tags + chat 9b/12b) |
| Brief matinal | `fais mon brief du matin` (Self / proactive / infra RO) |

Cible desktop : agent Omarchy `:5005` (alias `omarchy` / `.143`). Soft-confirm LAB si `LBG_DESKTOP_APPROVAL_MODE=confirm`.

Brief matinal (P0) : [`morning_brief.md`](morning_brief.md) — initiative 7h–10h, mandat `morning`, jamais auto-Réel.

### MAJ VS Code — chemin reproductible (écosystème, pas Cursor)

Toute livraison IDE/agent doit être rejouable par Compagnon / Team / scripts LAN :

```bash
# Depuis LBG_Studios (poste .143 ou WSL .10)
bash packages/cortex/infra/scripts/deploy_update_vscode_ecosystem.sh
# Smoke dry-run seul (jamais yay Réel) :
bash packages/cortex/infra/scripts/smoke_update_vscode_143.sh
```

| Étape | Acteur | Commande / Agir |
|-------|--------|-----------------|
| 1 Deploy agent | script | `deploy_linux_agent_143.sh` (préserve `linux.env`) |
| 2 Deploy orch | script | `tools/deploy_cortex_140.sh --full` + restart `lbg-orchestrator` |
| 3 Deploy Compagnon | script | `deploy_compagnon_100.sh --smoke` |
| 4 Vérifier | smoke | `smoke_update_vscode_143.sh` → dry-run 1.x → 1.y |
| 5 Réel | Compagnon Agir | `mets à jour vscode sur omarchy` → confirm L2 **hors Cline critique** |

Kind worker : `update_vscode` · paquet AUR `visual-studio-code-bin` · `requires_review=true`.

---

## Checklist « écosystème prêt à porter un sujet »

- [x] Dirty tree sauvé (lots M1) — pas de secrets dans git  
- [x] Compagnon déploie depuis `.143` (`deploy_compagnon_100.sh --smoke`)  
- [x] Orch Self joignable (`GET /v1/self/status`) + proxy Pilot slim (`/v1/pilot/orchestrator/self/status`)  
- [x] Initiative toast (silence → `jobs:idle` **ou** Self drives / `pending_will`)  
- [x] Bandeau **Self** sur `:5174` (curiosité / tension / intent)  
- [x] Team L1 depuis toast Compagnon (`POST /api/pilot/team/tasks` + run)  
- [x] Contre-pouvoir Agir (`companion/review-proposal` dans ActionCard)  
- [x] VS Code + Cline sur `.143` — ext. Cline OK ; smoke tags+chat Plan 9b / Act 12b (alias `:12b`→`:12b-qat` sur `.110`) ; UI Plan→Act reste un check manuel ponctuel  
- [x] **Mains code headless** ADR 0025 — OpenCode nominal ; `smoke_ide_cli_143.sh` ; Cline CLI hors scope ; Métis (`dev_studio`) ; live = `LBG_LINUX_CLI_AGENT_ENABLED=1` + soft-confirm  
- [x] Doc sujet + leçon — [`lecon_m2_m3_self_compagnon_2026-09-27.md`](lecon_m2_m3_self_compagnon_2026-09-27.md)  
- [x] Brief matinal P0 — Agir `fais mon brief du matin` + initiative 7h–10h ([`morning_brief.md`](morning_brief.md))
- [x] Couche Character Compagnon — pack + dials lab + smoke voix ([`character_layer.md`](character_layer.md))
- [x] Spontanéité initiatives — LLM light + seeds évolution ([`spontaneity.md`](spontaneity.md))


Quand cette liste tient, on peut confier un sujet O2 (Core3/Prime…) à la boucle — pas avant.

---

## Hors scope immédiat

- Réintroduire Cursor Cloud comme unique chemin (optionnel via `cursor_agent_workflow`, pas obligatoire).  
- Features O2 jeu tant que M1–M3 maturité studio ne tiennent pas.  
- Rsync massif projects → `.100`/`.140`.
