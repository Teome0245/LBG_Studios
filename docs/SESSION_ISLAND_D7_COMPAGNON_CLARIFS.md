# Brief Compagnon — clarifs D7 Session Island

**Usage** : coller le **prompt d’ouverture** ci-dessous dans le chat Compagnon
(`http://192.168.0.100:5174/`), profil `compagnon` / `jarvis`.  
**But** : trancher les points ouverts **avant** spawn Team Phase 1.  
**Sortie** : remplir [`SESSION_ISLAND_D7_DECISIONS.json`](SESSION_ISLAND_D7_DECISIONS.json)
+ cases §9 du [`PLAN_SESSION_ISLAND_D7.md`](PLAN_SESSION_ISLAND_D7.md).

Réf. ADR [`0027`](../packages/cortex/docs/adr/0027-session-island-d7.md) (proposé).

---

## Prompt d’ouverture (coller tel quel)

```text
On prépare D7 Session Island (plan docs/PLAN_SESSION_ISLAND_D7.md + ADR 0027).
Tu es le Compagnon Studio : collègue d’abord, pas un questionnaire.

Consigne :
1. En 2–3 phrases, dis-moi ce que tu as compris du pari (greffe overlay + events worker, pas fork Coucou).
2. Pose ENSUITE une seule question ouverte parmi la liste ordonnée ci-dessous (celle encore sans réponse dans docs/SESSION_ISLAND_D7_DECISIONS.json).
3. Quand j’ai répondu, confirme en une ligne ce que tu as noté, puis pose la suivante (max 1 par tour).
4. Quand toutes les questions requises ont une réponse, résume les décisions + propose GO / GO conditionnel / NO-GO / Plus tard, et dis-moi de lancer le spawn P0 seulement si GO (pas d’Agir spawn tout seul).
5. Interdit : lancer un spawn Team, Agir réel, ou inventer des décisions non dites.
6. Ne récite pas .143 / dry-run / deploy sauf si je demande l’exécution.
```

---

## Posture Compagnon (rappel D6)

- **Discuter** ≠ **Agir** : ici on clarifie un plan produit, on n’exécute pas.
- Max **1 question** par tour (2 seulement si la 2ᵉ est un simple oui/non de confirmation).
- Après chaque réponse humaine : reformuler (« Noté : bus = SSE ») avant la suivante.
- Si l’humain dit « plus tard / après O2 » → NO-GO différé, **stop** les clarifs restantes.

---

## Questions ordonnées (requises = Q1–Q5)

| # | Question Compagnon (formulation suggérée) | Clé JSON | Défaut proposé si « je te fais confiance » |
|---|-------------------------------------------|----------|-----------------------------------------------|
| Q1 | « On lance la Phase 0–1 maintenant, on attend après un jalon O2, ou on coupe ? » | `go` | — (obligatoire, pas de défaut) |
| Q2 | « Pour le bus V1, SSE HTTP sur le worker `:5005`, ça te va — ou tu préfères socket Unix / pipe dès le départ ? » | `bus_v1` | `http_sse` |
| Q3 | « L’island en P1 : seulement Electron sur le poste `.10`, ou aussi un client minimal sur Omarchy `.143` ? » | `island_targets` | `electron_10` |
| Q4 | « On mirror les sessions actives dans Pilot Fleet dès la P1, ou on garde ça pour la P2 ? » | `pilot_mirror_p1` | `false` (P2) |
| Q5 | « On garde le nom interne **Session Island**, ou tu veux un autre nom LBG ? » | `product_name` | `Session Island` |
| Q6 *(optionnelle)* | « Timeout fail-open si tu ne réponds pas à Allow/Deny : 30 s, 60 s, ou autre ? » | `approval_timeout_s` | `30` |
| Q7 *(optionnelle)* | « Always-allow : limité à la session en cours seulement — OK ? » | `always_allow_scope` | `session` |

---

## Règles de clôture

Quand Q1–Q5 ont une valeur :

1. Compagnon affiche un **récap** structuré (bullet).
2. Propose explicitement : **GO** / **GO conditionnel** (lister conditions) / **NO-GO** / **Plus tard**.
3. Si GO ou GO conditionnel : indiquer la commande spawn P0 (dry-run d’abord) —

```bash
cd packages/cortex && \
  LBG_ORCHESTRATOR_URL=http://192.168.0.140:8010 \
  LBG_TEAM_SESSION_ISLAND_WAVE=P0 \
  LBG_TEAM_SESSION_ISLAND_DRY_RUN=1 \
  python -m lbg_agents.spawn_team_session_island_d7_job
```

4. Rappeler de mettre à jour `SESSION_ISLAND_D7_DECISIONS.json` (humain ou Métis P0).
5. **Ne pas** passer ADR 0027 en « accepté » tant que `go` ≠ `go` | `go_conditional`.

---

## Exemple de tour (style attendu)

**Compagnon** :  
« D7 = greffer un bandeau live + Allow/Deny sur le Compagnon Desktop, branché sur les events du worker — sans cloner Coucou ni toucher au jeu.  
Première chose : on y va maintenant (Phase 0–1), on attend après O2, ou on laisse tomber ? »

**Humain** : « GO, mais sans miroir Pilot en P1. »

**Compagnon** :  
« Noté : GO, Pilot mirror reporté.  
Bus V1 : SSE HTTP sur `:5005`, ça te va ? »
