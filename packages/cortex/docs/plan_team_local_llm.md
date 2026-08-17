# Plan opérationnel Team — LLM locaux

**Canon** : [`local_llm_route_matrix.md`](local_llm_route_matrix.md) — heavy `.110` = `qwen3.8:27b` (code/PM/dialogue) + `gemma4:e2b` (forge) ; light `.111` = 3B.

## Décisions de cadrage

- Priorités à améliorer : `raisonnement`, `code`, `routage agentique`, `JSON/actions structurées`
- `dialogue` : moins prioritaire pour le moment
- Latence sur `110` : hors dialogue, une latence élevée est acceptable si la qualité progresse
- Politique de souveraineté : garder le plus possible `strictement local`, avec priorité à `raisonnement`, `code` et `routage agentique`

## Objectif

Faire "plus de choses" en local sans coût cloud additionnel, en spécialisant les modèles, en outillant le bench, en mettant de l'observabilité, puis en activant un routage multi-modèles piloté par l'usage.

## Workstreams officiels

### 1. Audit infra locale LLM

Owner principal : `admin_infra`

Tâches :
- Inventorier `110`, `140`, `.10` : RAM, swap, CPU, disponibilité, reboot, stockage modèles
- Mesurer `ollama list`, temps de chargement, disponibilité service, stabilité après redémarrage
- Relever les variables LLM réellement actives dans les services LBG
- Produire une matrice `rôle -> modèle -> hôte -> coût de latence`
- Identifier les goulots : swap, modèles trop gros, timeout, contention CPU

Livrables :
- état des lieux par machine
- shortlist de contraintes réelles
- runbook de reprise minimale

Critère de sortie :
- on sait exactement ce qui tourne localement, où, et avec quel budget machine

### 2. Shortlist + bench candidats

Owner principal : `qa`

Contributeurs : `admin_infra`, `pm`, `dev_game`

Tâches :
- figer un corpus LBG de prompts comparables
- bencher 3 à 5 candidats maximum, pas plus
- mesurer : latence, stabilité JSON, qualité raisonnement, qualité code, suivi d'instructions
- comparer les résultats par usage, pas en score global unique
- documenter les modèles éliminés et pourquoi

Livrables :
- corpus versionné
- résultats bench par modèle
- recommandation par tier : `fast`, `default`, `deep`

Critère de sortie :
- un mapping clair par usage avec un candidat principal et un fallback local

### 3. Routage multi-modèles

Owner principal : `dev_game`

Contributeurs : `pm`, `admin_infra`

Tâches :
- définir des classes de requêtes : `reason`, `code`, `agentic_router`, `json_actions`, `dialogue`
- brancher chaque classe sur un tier local
- ajouter fallback local avant tout fallback distant
- journaliser le modèle choisi, la raison, la latence et l'issue
- garder le dialogue comme piste secondaire tant que les autres usages ne sont pas stabilisés

Livrables :
- table de routage
- règles de fallback
- traces exploitables

Critère de sortie :
- les usages prioritaires restent locaux par défaut, avec routage explicite et observable

### 4. Rôle `admin_infra` / observabilité

Owner principal : `ops`

Contributeurs : `admin_infra`, `qa`

Tâches :
- formaliser un rôle Team dédié à la supervision LLM locale
- ajouter des checks périodiques : disponibilité Ollama, dérive latence, saturation mémoire, modèles manquants
- exposer un mini tableau de bord texte ou JSON
- documenter les actions de récupération : redémarrage, délestage, réduction de tiers
- centraliser les anomalies dans les CR Team / Element si nécessaire

Livrables :
- rôle Team `admin_infra`
- traces d'audit
- checklist d'exploitation

Critère de sortie :
- les incidents infra LLM sont détectés tôt, décrits clairement, et récupérables

## Répartition concrète par rôle

### `admin_infra`

- persona Team : `Atlas`
- mandat explicite : `Responsable plateforme LLM locale : capacité, déploiement, bench, stabilité, watchdogs, reprise auto, budgets matériels`
- périmètre hôtes LAN : **110** (Ollama), **140** (orchestrateur), **245** (PreCU), **246** (Prime gateway + sidecar IA)
- tenir l'inventaire réel des hôtes LLM
- lancer l'audit Ollama et consolider les écarts
- maintenir la shortlist technique admissible
- publier les recommandations d'allocation par rôle
- surveiller les dérives de latence et de mémoire

### `ops`

- fiabiliser les services de fond : Ollama, timers, redémarrages, logs
- sécuriser les variables d'environnement et les emplacements de modèles
- préparer les watchdogs de reprise après reboot
- assister `admin_infra` sur les incidents machine

### `qa`

- maintenir le corpus de bench
- exécuter les benches comparatifs
- contrôler la validité JSON et la reproductibilité
- produire les comptes rendus comparatifs

### `pm`

- arbitrer les priorités d'usage
- valider les critères de succès par catégorie
- transformer les résultats bench en décisions de routage
- maintenir la feuille de route de déploiement

### `dev_game`

- implémenter le routage multi-modèles
- brancher les bons tiers sur les agents et workflows
- ajouter les traces utiles côté orchestrateur
- intégrer les règles de fallback local

## Phasage d'exécution

### Semaine 1

- lancer l'audit infra locale
- figer le corpus de bench
- créer les premiers artefacts de bench dans le dépôt
- ajouter le rôle `admin_infra`
- installer le timer Atlas : `bash infra/scripts/install_team_admin_infra_job_vm.sh`
- watchdog bench (seuil + retry KO + Element) : `bash infra/scripts/install_atlas_bench_watchdog_job_vm.sh`
- alerte Element périmètre KO (110/140/245/246) : active par défaut sur run Atlas (`LBG_ADMIN_INFRA_PERIMETER_ALERT=1`)
- variables : `LBG_ATLAS_BENCH_MIN_OKS=3` (défaut), `LBG_ATLAS_BENCH_ALERT_DISABLE=0`
- variables périmètre : `LBG_ADMIN_INFRA_PERIMETER_ALERT_COOLDOWN_S=3600` (anti-spam même signature)

### Semaine 2

- lancer les benches sur les candidats retenus
- publier le premier comparatif
- proposer une table de routage cible

### Semaine 3

- brancher le routage multi-modèles
- activer les premiers signaux d'observabilité
- faire un dry-run complet avec CR

### Semaine 4

- stabiliser les valeurs par défaut
- documenter l'exploitation
- décider les modèles "prod locale"

## Candidats à bencher en premier

- `gemma4:e2b`
- `gemma4:12b`
- `gemma4:26b`
- un candidat `qwen` orienté instruct/code si empaquetage local disponible

## Règles de décision

- on préfère un modèle plus lent si son gain est net sur raisonnement, code ou JSON
- on évite un modèle "polyvalent moyen" si un duo `fast + deep` local fait mieux
- un modèle non fiable en JSON ne doit pas piloter d'actions structurées
- un modèle impossible à stabiliser sur `110` sort de la shortlist
