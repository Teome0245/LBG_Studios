# ADR 0023 — Catalogue d’outils IDE / agents (autorisés · expérimentation · interdits) + second avis

**Statut** : accepté  
**Date** : 2026-10-02  
**Complète** : [`lbg_agentic_os.md`](../lbg_agentic_os.md) § 6.1 · [`ecosystem_dev_143.md`](../ecosystem_dev_143.md) · [`local_llm_route_matrix.md`](../local_llm_route_matrix.md) · ADR [`0020`](0020-dsh-greffe-peripherique.md) · [`0022`](0022-ecc-greffe-peripherique.md)

## Contexte

Le poste éditeur **`.143`** (et éventuellement `.10`) peut brancher de nombreux agents coding / harness
vers Ollama **`.110` / `.111`**. Empiler tous les outils « qui marchent avec Ollama » crée :

- un **second OS** opaque à côté de Cortex / Team / Compagnon ;
- de la **contention** sur `.110` (`OLLAMA_MAX_LOADED_MODELS=1`, CPU) ;
- des configs divergentes hors matrice LLM ;
- une dilution du chemin nominal « sans Cursor » (Compagnon → Team → Cline).

Besoin produit : **figer une politique claire** (autorisé / expérimentation / interdit), tout en
gardant la possibilité d’un **outil concurrent / similaire** pour un **second avis** ponctuel
quand une décision technique le justifie (revue, arbitrage plan, doute qualité).

## Décision

### 1. Trois statuts, un cerveau

| Statut | Signification | Où |
|--------|---------------|-----|
| **Autorisé (chemin nominal)** | Installé, documenté, smoke ; usage quotidien | `.143` (+ `.10` miroir) |
| **Expérimentation (greffe)** | Opt-in, désactivable, hors chemin critique ; **au plus 1 actif** hors second avis | `.143` / `.10` uniquement |
| **Interdit (chemin Studio)** | Pas d’install sur le chemin Compagnon/Team/Pilot ; lab perso éventuel hors Studio | Hors 140 / hors boucle Agir |

**Cortex / Team / Pilot / Compagnon restent le cerveau.** Aucun outil de ce catalogue ne se substitue
au bus Team, à la file SQLite, ni à l’orchestrateur `.140`.

### 2. Catalogue figé (inventaire 2026-10-02)

#### Autorisé — chemin nominal

| Outil | Rôle | LLM | Doc / smoke |
|-------|------|-----|-------------|
| **Cline** | Agent Plan→Act IDE (dominant) | Matrice : Plan `9b` `.110` · Act `12b` `.110` · triage light `.111` | [`cline_local_llm.md`](../cline_local_llm.md) · [`cline/SMOKE.md`](../cline/SMOKE.md) |
| **Continue** | Chat / edit / autocomplete | Act 12b · Forge e2b · Plan 9b · autocomplete 0.8B | [`sans_cursor.md`](../sans_cursor.md) |
| **Claude Code** | Agent CLI / onglet VS Code | `ANTHROPIC_BASE_URL` → `.110:11434` (souvent Act 12b) | [`ecosystem_dev_143.md`](../ecosystem_dev_143.md) |
| **Terminal / scripts** | Pattern OpenAI-compat / Anthropic pour smokes | `…:11434` ou `…/v1` selon client | scripts `infra/` · Atlas audit |

#### Expérimentation — greffe périphérique (opt-in)

| Outil | Rôle possible | Conditions |
|-------|---------------|------------|
| **OpenCode** | Alternative CLI OSS (OpenAI `/v1`) | Matrice respectée ; ctx local OK ; pas de deploy 140 |
| **Codex CLI** | Surface Responses / OSS | Idem ; provider custom (éviter collision noms réservés) |
| **Copilot CLI (BYOK)** | Terminal GH + endpoint local | BYOK → Ollama ; pas de dépendance cloud pour le LLM Studio |
| **Pi** / **Oh My Pi** | Harness minimal / fork enrichi | Lab ; un seul des deux à la fois |
| **DeepSeek Harness (`dsh`)** | Lab Cordis / patterns | ADR 0020 — poste only, capability Team OFF par défaut |
| **ECC (plugin Claude Code)** | Harness skills/hooks | ADR 0022 — **parké** tant que ctx Gemma ~4k |

**Règle de charge** : hors procédure *second avis* (§ 3), **au plus une** greffe d’expérimentation
active en parallèle du trio autorisé. Promotion vers « autorisé » = ADR amendé + smoke + leçon.

#### Interdit — chemin Studio / écosystème LBG

| Outil / classe | Motif |
|----------------|-------|
| **OpenClaw** (runtime OS / multi-IM) | Second OS messagerie ; concurrencent Compagnon + Team. Skills greffés via adaptateur existant OK ; **pas** le runtime comme cerveau. |
| **Hermes Agent / Hermes Desktop** | Assistant généraliste / GUI type OS ; redondant + hors greffe IDE. |
| **Qwen Code** | Clone Claude Code ; redondance pure. |
| **Droid** (Factory.ai) | Clone niche vs Cline / Claude Code. |
| **Tout agent coding supplémentaire** hors catalogue | Par défaut interdit jusqu’à revue ADR. |
| **Ollama sur `.143`** | Inférence = `.110`/`.111` uniquement. |
| **Remplacement de Pilot / Team / Compagnon** par UI d’un harness tiers | Substitution du bus. |
| **Harness always-on** incompatible ctx local (ex. ECC enabled) | Parké / interdit tant que matrice ctx insuffisante. |

> Cursor IDE / Cursor Cloud restent **optionnels** (humain `.10`) — pas chemin critique
> « sans Cursor » ; voir [`sans_cursor.md`](../sans_cursor.md).

### 3. Second avis — outil concurrent / similaire

**But** : faciliter une décision (plan, patch, revue) en confrontant **deux agents de même classe**,
sans ouvrir un second OS permanent.

#### Définition

Un **second avis** = session ponctuelle d’un outil **similaire** (même classe fonctionnelle)
au primaire, sur le **même mandat** (même brief / même diff / même question), avec sortie
comparable, puis **arbitrage humain ou L2**.

| Classe | Primaire (nominal) | Concurrent autorisé pour second avis |
|--------|--------------------|--------------------------------------|
| Agent IDE Plan→Act | **Cline** | Claude Code *ou* 1 greffe expérimentale de la classe (OpenCode / Codex / Copilot BYOK) |
| Chat / edit léger | **Continue** | Claude Code (chat) — pas un 3ᵉ IDE agent |
| CLI agent | **Claude Code** | OpenCode *ou* Codex *ou* Copilot BYOK (un seul) |
| Review / critique | Team (Argus / Thémis) + humain | Second agent IDE **en lecture** ; pas d’écriture parallèle non revue |

#### Règles opératoires

1. **Déclencheur** : doute qualité, arbitrage architecture, revue L2, smoke divergent, ou demande
   explicite humaine / Compagnon (« second avis sur … »).
2. **Un concurrent à la fois** — jamais Cline + OpenCode + Codex en écriture parallèle.
3. **Même matrice LLM** — les deux sessions pointent `.110`/`.111` via
   [`local_llm_route_matrix.md`](../local_llm_route_matrix.md) (pas de modèle « secret »
   hors inventaire). Préférer **même profil** (ex. tous deux Act 12b) pour comparabilité ;
   variante Plan 9b vs Act 12b autorisée si le mandat le dit.
4. **Isolation** : branches / worktrees séparés si les deux écrivent ; sinon un seul écrit,
   l’autre en **review-only**.
5. **Sortie** : note courte (accord / désaccord / points divergents) → leçon Team ou
   commentaire L2 ; pas de merge auto du second avis.
6. **Durée** : session bornée ; le concurrent ne reste pas « toujours on » après la décision.
7. **Compagnon / Agir** : peut *proposer* un second avis (ouvrir l’outil concurrent sur `.143`) ;
   l’écriture Réel reste soumise au contre-pouvoir existant.

#### Flux type

```text
Mandat (humain / Team / Compagnon)
  → Primaire (ex. Cline Plan→Act) produit proposition A
  → Si doute : concurrent (ex. Claude Code ou OpenCode) produit avis B (même brief)
  → Arbitrage L2 / humain  →  une seule branche appliquée
  → Leçon (divergence utile ? promouvoir / garder / retirer le concurrent)
```

### 4. Critères d’admission d’un nouvel outil

Pour entrer en **expérimentation** (puis éventuellement **autorisé**) :

1. Compatible Ollama LAN (natif ou `/v1` / Anthropic Messages) sans cloud obligatoire.
2. Config reproductible (script seed ou snippet dans `docs/`) alignée matrice.
3. Scope **poste** (`.143` / `.10`) — zéro runtime sur `.140` sans ADR dédiée L2.
4. Smoke minimal documenté (tags + 1 chat).
5. Pas de substitution Cortex ; greffe périphérique explicite.
6. Si classe déjà couverte → uniquement via **second avis**, pas comme second primaire.

### 5. Non-décisions (volontaires)

- Ne pas installer « le pack des 14 » sur `.143`.
- Ne pas router Open WebUI / lab chat comme agent IDE (lab `.100:3080` seulement).
- Ne pas réactiver ECC tant que le ctx local n’est pas compatible (ADR 0022).

## Alternatives rejetées

| Alternative | Raison |
|-------------|--------|
| Autoriser tous les outils Ollama-compat | Contention `.110`, chaos config, second OS |
| Interdire tout concurrent | Perte du second avis utile aux décisions |
| Second avis via cloud (Claude/GPT) par défaut | Hors politique LAN-first ; cloud = secours `LBG_REASON_CLOUD_*` seulement |
| Deux primaires permanents (Cline + OpenCode always-on) | Dilue le chemin nominal et la responsabilité |

## Risques

| Risque | Mitigation |
|--------|------------|
| « Second avis » devient double écriture non revue | Review-only + worktrees ; une branche appliquée |
| Contention Ollama pendant dual session | Sérialiser si `MAX_LOADED=1` ; préférer même modèle déjà chargé |
| Catalogue obsolète | Amender cet ADR (pas de side-doc fantôme) ; date + leçon |
| Greffe expérimentale oubliée active | Checklist smoke ; désactivation après spike |

## Conséquences

- Politique unique pour IDE/agents LAN : ce fichier = source de vérité catalogue.
- Trio autorisé inchangé ; expérimentations listées et bornées.
- Second avis = capacité **explicite** et **encadrée**, pas une excuse pour empiler.
- ADR 0020 / 0022 restent les détails de greffe DSH / ECC ; ce catalogue fixe leur **statut**.

## Références

- [`ecosystem_dev_143.md`](../ecosystem_dev_143.md) · [`sans_cursor.md`](../sans_cursor.md) · [`omarchy_vm_143.md`](../omarchy_vm_143.md)
- [`local_llm_route_matrix.md`](../local_llm_route_matrix.md) · [`cline_local_llm.md`](../cline_local_llm.md)
- [`lbg_agentic_os.md`](../lbg_agentic_os.md) § 6.1
- [`adr/0020-dsh-greffe-peripherique.md`](0020-dsh-greffe-peripherique.md) · [`adr/0022-ecc-greffe-peripherique.md`](0022-ecc-greffe-peripherique.md)
