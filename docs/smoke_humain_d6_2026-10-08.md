# Smoke humain D6 — 2026-10-08

**Surface** : Compagnon `:5174` · profil ask/auto · modèle `lbg-compagnon-e4b-v1` (tours LLM)  
**Fil** : causerie projet → MMORPG / incarnation joueurs IA / zone d’entraînement  
**Critères visés** : **C1** continuité · **C2** collègue d’abord  
**Verdict global** : **C1 PASS** · **C2 PARTIEL** (sauvé après déclencheur « collègues » ; ouverture greeting = FAIL)

---

## Transcription (abrégée)

| # | Humain | Compagnon (résumé) | Source | Note |
|---|--------|--------------------|--------|------|
| 1 | Bonjour, comment ça va aujourd’hui ? | Mur ops : validation déploiement, Agir+Team+`.143`, VS Code/Cline, mode LAB | — | **C2 FAIL** · 30 s hub, pas compagnon |
| 2 | bien merci, et toi ? | Identité studio + dry-run + question `.143`/`.10` | — | **C2 FAIL** · rebond ops |
| 3 | Discutons comme collègues du projet | Accusé « mode discussion » + « qu’est-ce qui t’amène » | LLM | **C2 faible** · pas d’avis / prise de position |
| 4 | MMORPG + incarnation joueurs IA | Enchaîne présence / humour / transposition studio→jeu | LLM | **C1 OK** |
| 5 | environnement = zone d’entraînement | Enchaîne sans reset ; terrain de test agents / dynamique de groupe | LLM | **C1 OK** |
| 6 | (demande plan d’action) | Méta : « le plan doit se concentrer sur… » **sans livrable** | LLM | Gap **C4/délivrance** |
| 7 | préparer le plan pour le studio et commencer | Encore méta (« je peux structurer… ») **sans artefact** | LLM | Gap délivrance |
| 8 | allons y | « Allons-y. Je te suis. » | **`short_social`** | **Bug routing** : go-ahead capturé par `SHORT_SOCIAL_RE` |

---

## Score critères D6

| Critère | Résultat | Preuve |
|---------|----------|--------|
| **C1 Continuité** | **PASS** | Tours 4→5 (et 5→6 thème) sans reset identité / « objectif » |
| **C2 Collègue** | **PARTIEL** | Tours 1–2 récitent Agir/`.143` ; tour 3 sans avis ; tours 4–5 OK une fois en sujet projet |
| **C3 Retours** | n/a | Pas de tour frustration explicite type V8 |
| **C4 Deux postures** | **FAIL** (suite) | Demande d’exécution / plan → méta LLM puis `short_social`, pas Agir ni livrable |

---

## Gaps à traiter (input plan)

1. **Greeting → causerie** : « bonjour / ça va » ne doit pas charger le prompt ops / Agir.  
2. **C2 strict** : « collègues du projet » → 1 avis concret, pas seulement bascule de mode.  
3. **`short_social` vs go-ahead** : `allons-y` / `allez` / `on y va` ne doivent **pas** short-circuiter un fil où un livrable ou une action est en cours (contexte sticky).  
4. **Délivrance collègue** : « prépare le plan / soumets au studio / commence » → artefact structuré (markdown plan) + proposition Agir/Team si outillage, pas roman méta.

---

## Références

- Critères : [`FOCUS_COMPAGNON.md`](FOCUS_COMPAGNON.md) § D6  
- Smoke auto V6–V8 : [`SMOKE_LAN.md`](SMOKE_LAN.md) § Compagnon D6  
- Code `short_social` : `packages/cortex/compagnon_ui/server_overlay/router_prompts.py` (`_SHORT_SOCIAL_RE`, `short_social_reply`)
