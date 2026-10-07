# ADR 0026 — Runtime joueur hors Core3 (étude + spike)

**Date** : 2026-10-06  
**Statut** : **Godot-first G5** — `prime-hub` `.246:8787` HTTP+WS unifiés, peel natif ; Python hub_runtime OFF ; Core3 hors chemin joueur
**Décideurs** : Pilote  
**Amende** : ADR 0017 (seuils « Core3 = prison » atteints) · complète ADR docs 0002 (veille)  
**Canon** : Bible V3 (lore sans assets SWG) · `PLAN_MMO_O2` · contrat SpaceMolt C9–C12

---

## Contexte

1. **Produit** : Scrapaltai / Lost Heaven — canon LBG, **zéro** référence univers SWG côté joueur.
2. **Runtime actuel** : Core3 Prime 246 + SOE + `ia_bridge` Lua + `pending.jsonl` + sidecar `:8791` + Godot `prime-client`.
3. **Constat ops 2026-10-06** : bots Lia/Nix « visibles mais figés » — file pending saturée (inject Teome), crash tick (`switchZone` nil), snapshots périmés, redémarrages Prime sans gain. Le coût n’est plus le contenu : c’est **le moteur SWG**.
4. ADR 0017 (2026-07) gardait Core3 tant que les seuils « prison » n’étaient pas atteints. Ils le sont :
   - objectif **zéro** SOE / TRE / structures SWG au runtime joueur ;
   - sim + file Lua ne tiennent plus la boucle hub fiable ;
   - équipe prête à **étudier** un runtime mince **en parallèle** du hub Godot.

---

## Décision

### 1. Étudier un runtime **Godot-first** (autorité monde hors Core3)

| Garde (réutiliser) | Coupe (hors spike / hors cible runtime) |
|--------------------|----------------------------------------|
| `prime-client` Godot, assets Prime, Lost Heaven | Protocole SOE client↔serveur |
| Bible + M10 JSON + catalogs C10 | `ia_bridge` Lua / `pending.jsonl` |
| Contrat agents C9–C12 (`agent_catalog`, tick free vs mutation) | Dépendance joueur à Core3 246 pour marcher / voir bots |
| Sidecar / HTTP comme **API contrat** (peut être réimplémenté) | PreCU 245 **runtime** (reste **lecture seule** data, V4) |

### 2. Cible technique du spike (48 h)

**Option retenue pour le spike** : serveur mince (Python ou Godot headless) + WebSocket `lbg-ws/2` (déjà amorcé) + sim Lost Heaven **locale** :

- 1 humain + ≥1 bot IA marchent sur le hub ;
- positions poussées au client **sans** Core3 ;
- mutations filetées (C11) côté serveur mince.

**Hors spike** : Unreal, Agones, rewrite Three.js, tokens, abandon Godot.

### 3. Core3 pendant la transition

| Rôle | Statut |
|------|--------|
| **Lab / référence** Pre-CU + data M10 | Conservé (245 lecture seule, catalogues) |
| **Prod joueur** (login → marche hub → bots visibles) | **Cible = hors Core3** après go spike |
| Ops 246 | Mode **maintenance** : pas de nouvelle feature gameplay dépendante du tick Lua |

### 4. Go / no-go (après spike)

**Go** si les 3 critères sont verts :

1. Humain + bot bougent de façon visible dans Godot **sans** Core3 allumé.  
2. Latence / stabilité meilleure qu’un soir type « pending mort + restart Prime ».  
3. Contrat catalog + tick (C10/C11) branché sur le serveur mince (même flags).

**No-go** → documenter pourquoi + revenir peel ADR 0017 sans pivot ; Core3 reste autorité.

### 5. Autorité durable + charge moteur (anti double-build) — 2026-10-06

**`hub_runtime` (Python, `.246:8787`) n’est pas un jetable.** C’est l’**autorité joueur hub** tant que le contrat tient. On ne reconstruit pas Core3/SpaceMolt une seconde fois « en Godot pour refaire pareil ».

| Couche | Source de vérité | Peut changer |
|--------|------------------|--------------|
| **Contrat** `lbg-ws/2` + HTTP C10/C11 + JSON M10 | **Gelé** (client Godot + peel) | Non (sauf version proto) |
| **Process autorité** (`hub_runtime`) | Actuel | Oui → Godot headless / autre **sans** casser le contrat |
| **Sim interne** (pathfinding, tick bots, combat) | Implémentation | Oui — c’est le seul vrai rewrite éventuel |

**Stabilité / charge — clarifications :**

1. **Godot serveur ≠ plus stable par magie.** La stabilité Core3 a cassé sur Lua/pending/SOE, pas sur « pas assez Godot ». Un Dedicated Server Godot mal cadencé plante autant.
2. **Charge hub actuelle** (dizaines d’humains + flotte IA + PNJ) : un serveur mince Python + WS **tient** ; le plafond n’est pas la langue, c’est tick budget, broadcast, et pathfinding.
3. **Seuils de bascule** vers Godot headless (option, pas obligation) — **un** des critères suffit à ouvrir l’étude :
   - tick sim > budget (ex. pathfinding / combat trop lourd en Python) ;
   - besoin fort de **même** navmesh/physique que le client ;
   - > ~50–100 joueurs **même zone** avec latence/CPU inacceptables *mesurés* (pas anticipés).
4. **Migration** = swap du process derrière le même contrat (WS/HTTP). Client + peel + catalogs **inchangés**. Pas de second spike parallèle « tout refaire ».

**Règle produit** : enrichir le hub **ici** (pathfinding, agents, PNJ, dialogue). Godot serveur = **changement de boîte**, pas de jeu.

### 5b. Décision pilote — swap Godot (2026-10-07)

**Choix** : passer l’autorité hub sur **Godot headless** (`packages/prime-hub`) même si la charge actuelle est tenue par Python — anticiper navmesh / même moteur que `prime-client`.

| Règle | Détail |
|-------|--------|
| Contrat | **Inchangé** : `lbg-ws/2` + HTTP C10/C11 ; `prime-client` ne change pas |
| Live pendant transition | `hub_runtime` **reste** `.246:8787` jusqu’à cutover (phase G4) |
| Spike Godot | ports **8788** WS / **8789** HTTP — parité move+flotte avant bascule |
| Anti double-build | pas de 2ᵉ protocole, pas de rewrite SpaceMolt ; on **porte** ou **proxifie** |

Phases : voir [`packages/prime-hub/README.md`](../../../prime-hub/README.md) (G0→G4a).

### 5c. Post-cutover (2026-10-07) — Godot = prod joueur

| Rôle | Process | Port |
|------|---------|------|
| Monde + peel HTTP + WS | **`lbg-prime-hub`** | **8787** unifié (G5) |
| Python `hub_runtime` | OFF | — |
| Core3 bots + gateway | coupés | `stop_core3_player_path_246.sh` |

**Spike Python terminé** (monde + peel). Doc ops : [`docs/RUNTIME_GODOT.md`](../../../docs/RUNTIME_GODOT.md).

---

## Conséquences

- Doc d’exécution spike : [`SPIKE_48H_GODOT_RUNTIME.md`](../../../docs/SPIKE_48H_GODOT_RUNTIME.md) (historique).
- Doc runtime live : [`RUNTIME_GODOT.md`](../../../docs/RUNTIME_GODOT.md).
- ADR docs 0002 « pas de pivot » = **amendé** : pivot **runtime** autorisé sous go/no-go ; canon lore inchangé.
- ADR 0017 reste vrai pour l’historique peel ; la **phase actuelle** est B′ **Godot live**.
- Runtime joueur hub live = **`prime-hub`** ; peel Python jusqu’à portage HTTP natif ; Core3 = lab //.

---

## Historique

| Date | Changement |
|------|------------|
| 2026-10-06 | Accepté étude + spike — seuils prison Core3 constatés ops |
| 2026-10-06 | **Go spike** — humain+Nix sur `.246:8787` sans Core3 ; collision hub AABB |
| 2026-10-06 | Flotte Lia/Mira + PNJ hub + chat + dialogue stub ; peel inv/quests |
| 2026-10-06 | **§5** — `hub_runtime` = autorité durable ; Godot = swap optionnel anti double-build |
| 2026-10-06 | Flotte +**Kael** ; PNJ vivants (wander+ambient) — parité hub Core3 en cours |
| 2026-10-07 | **§5b** — décision pilote swap Godot ; scaffold `packages/prime-hub` (G0) ; Python live jusqu’à G4 |
| 2026-10-07 | **G1–G2** — Godot WS `:8788` + HTTP `:8789` proxy peel → Python `:8787` ; client patch pointe les deux |
| 2026-10-07 | **G4 cutover** — Godot WS `:8787` + HTTP `:8789` ; Python lab `:8797` |
| 2026-10-07 | **G4a** A* bots ; persistance position joueur ; **§5c** Godot-first ; Core3 chemin joueur coupé |
| 2026-10-07 | **G5** peel natif (auth/inv/quests/craft/catalog/dialogue) + HTTP+WS unifiés `:8787` ; Python hub_runtime OFF |
