# Focus — Compagnon Studio (type Jarvis)

**Date** : 2026-09-28 (couche Character + dials lab)  
**Priorité** : **O1 Studio** — agents / UI / autonomie bornée.  
**Hors scope immédiat** : intégration persona dans le MMO (Rang 2).

## Pari produit

Les **30 premières secondes** sur le **chat produit** doivent sentir un **compagnon** (Jarvis / Mother / Kit / HAL), pas un hub technique.

Tu parles → il répond avec continuité → il propose d’agir (infra, studio, conception) → tu valides (L2).

## Surfaces (canon)

| Rôle | Où | Notes |
|------|-----|--------|
| **Compagnon (entrée produit)** | **http://192.168.0.100:5174/** | Sources : `packages/cortex/compagnon_ui` · deploy `infra/scripts/deploy_compagnon_100.sh` |
| **Studio ops / Team / L2** | http://192.168.0.140:8080/pilot/ | Pilot : équipe, jobs, desktop détaillé, approvals |
| **App bureau (cible)** | Poste **`.10`** | Overlay / tray « agent visible » — voir § Desktop |
| **Lab LLM** | `.100:3080` | Open WebUI — optionnel, pas le shell Compagnon |

**Décision** : on **inverse** le cutover « tout dans Pilot » pour le *feeling* Compagnon.  
Pilot reste le **cockpit ops** ; `:5174` redevient la **présence** conversationnelle.  
Sources Orch UI aujourd’hui : `_archive/LBG_IA/orchestrateur/frontend` (runtime `.100`).  
Travail cible : **extraire / greffer** le front Compagnon dans `LBG_Studios` (pas de feature longue dans `_archive/`).

Pas de second OS type CrewAI. Même backend (Orch API `:3000` + Cortex / Team).

## Persona

Profils dialogue : `compagnon` (défaut), `compagnon_lab` / `lab`, `jarvis`, `mother`, `kit`, `hal`  
(Orch overlays `compagnon_ui/server_overlay/router_prompts.py` + `lbg_agents/dialogue_llm.py`).  
Voix d’accueil : `lbg_agents/lbg_ia_voice.py`.

**Couche Character** (personnalité ≠ expression, inspirée MC / adaptée LBG) :  
[`packages/cortex/docs/character_layer.md`](../packages/cortex/docs/character_layer.md)  
— pack `knowledge/character/compagnon_v1.json`, 7 dials lab (UI `:5174`), blacklist anti-IA générique, ego soft, smoke voix V1–V5.

**LLM / morale** (infra LAN = LAB, non exposée) :  
[`packages/cortex/docs/compagnon_llm_moral_policy.md`](../packages/cortex/docs/compagnon_llm_moral_policy.md)  
— `LBG_COMPAGNON_LAB=1` → local only, softener média off, modèle `huihui_ai/qwen3.5-abliterated:2B` (`.111`).  
Prod-like : garde copyright = mise en garde + pistes légales (pas mur Groq, pas playbook pirate).

À brancher aussi côté Orch UI (`/ask` + profil) pour que `:5174` parle la même langue.

## Autonomie (bornée)

| Niveau | Comportement |
|--------|----------------|
| L1 | Timers / jobs / sondes sans merge destructeur |
| L2 | Toi (approvals Pilot / jeton desktop) + **contre-pouvoir** Agir |
| L3 | Miroir → propositions — pas d’auto-merge aveugle |

**Contre-pouvoir** (pas Lyra) : [`packages/cortex/docs/compagnon_contre_pouvoir.md`](../packages/cortex/docs/compagnon_contre_pouvoir.md) — revue avant Réel, auto dry-run soft, `block_real` + override humain.

## Desktop `.10` (vision « logiciel d’aide »)

Oui, c’est possible — et ça colle à l’étoile du nord (assistant **sur le PC**).

Ce que tu décris ≈ :

1. **Fenêtre toujours accessible** (tray / raccourci) — chat Compagnon  
2. **Présence visuelle** — avatar / FaceRig (petit overlay, pas un dashboard)  
3. **Actions poste** — via l’agent Windows déjà là (`:5005`, `desktop_control`, dry-run + approval)

Socle existant :

- Agent poste : `packages/cortex/windows_agent`  
- Pattern Electron Windows : `packages/launchpad` (réutiliser pour un **Compagnon Desktop**, pas pour le jeu)

Phasage réaliste :

| Phase | Livrable | État |
|-------|----------|--------|
| **D0** | `:5174` = Compagnon (branding + persona + chat-first) | **OK** |
| **D1** | Raccourci `.10` mode app Edge/Chrome + PWA manifest | **OK** — `compagnon_ui/desktop/` |
| **D2** | App Electron *Compagnon* (tray + fenêtre chat + avatar) | **OK** — `packages/compagnon-desktop` |
| **D3** | Overlay discret + notifications d’initiative (quota strict) | **OK** (2026-09-16) |

## Jalons (ordre)

1. **Presence sur 5174** — branding Compagnon + profils + overlay prompts — **OK** (2026-09-16)  
2. **D1 Desktop** — raccourci / mode app `.10` + PWA manifest — **OK** (2026-09-16)  
3. **D2 Electron** — tray + chat + avatar overlay — **OK** (2026-09-16) — `packages/compagnon-desktop`  
4. **Continuité** — historique serveur (déjà Orch) + moins de chrome ops — **OK** (2026-09-16)  
   - Bannière Pilot masquée par défaut ; un lien **Pilot** dans le header  
   - CPU/RAM derrière un toggle ; labels « Compagnon / Avec Compagnon »  
5. **Agir** — depuis le chat : proposer → dry-run → réel (jeton) — **OK** (2026-09-16)  
   - Bouton **Agir** dans `:5174` → `POST /api/pilot/action-proposal` (nginx → `.140:8000/v1/pilot/`)  
   - Carte `ActionCard` : Dry-run / Réel (+ token `desktop_approval`) via `POST /api/pilot/route`  
   - Jeton repris depuis Pilot (`lbg_pilot_desktop_approval_v1`) ; garde avant Réel  
6. **D3** — notifications d’initiative (quota) — **OK** (2026-09-16)  
   - `:5174` toast `InitiativeToast` (poll `/api/pilot/orchestrator/proactive/status`)  
   - Quota client : max 3/h, min 10 min entre toasts, silence ≥ 90 s — **jamais d’auto-exec**  
   - Electron : notif OS + pulse overlay (`packages/compagnon-desktop`)
   - Discuter = réponse locale (pas de faux `open_app`)
7. **Pilotage** — palette Ctrl+K + encart activité — **OK** (declutter 2026-09-18)  
   - Ctrl+K / Agir / chat ; plus de barre d’actions rapides ni chips suite dans le fil  
   - Deploy : `bash packages/cortex/infra/scripts/deploy_compagnon_100.sh`
8. **D4 Autonomie émergente** — **OK** (2026-09-18)  
   - 1 objectif persistant : **Veiller Jobs L2** (`studioGoal.js`)  
   - Feedback Agir / Ignorer → freine les signaux souvent ignorés (`learned_dismiss`)  
   - Toast : 1 CTA + badge objectif ; empty state affiche l’objectif actif  
9. **D5 Initiative typée (plus que Jarvis)** — **OK** (2026-09-27)  
   - Voir § **D5 — 4 types de propositions** ci-dessous  
   - Code : `compagnon_ui/src/lib/mandate.js` + `initiativeQuota.js` + `studioGoal.js` · toast Mandat  
   - Empty state `:5174` : chips Mandat si pas encore confirmé (demande la priorité tout de suite)  
   - Soft-confirm LAB : `open_url` / `mail_imap_preview` / sondes → **Réel sans case** (`ActionCard` + `_SOFT_KINDS`)  
   - Tests : `mandate.test.js` + `initiativeQuota.test.js` (12 verts)  
10. **Character layer** — **OK** (2026-09-28)  
   - Pack worldview + 7 dials + blacklist + ego soft — [`character_layer.md`](../packages/cortex/docs/character_layer.md)  
   - UI lab panneau caractère (header) · API `/character/*` · smoke voix V1–V5  
   - Tests : `test_character_layer.py` + `characterDials.test.js`
11. **Voix TTS (`voice_local`)** — **OK** lot 2 (2026-10-02)  
   - Provider **Edge** `fr-FR-DeniseNeural` + fallback Piper `.111:8098` + bouton Voix `:5174` — [`voice_local.md`](../packages/cortex/docs/voice_local.md)  
   - Deploy : `deploy_piper_tts_111.sh` (fallback) puis `deploy_compagnon_100.sh`  
12. **D6 Causerie crédible** — **OK** (2026-10-06) — *gate O2 feeling*  
   - Lots D6.1–D6.4 livrés · smoke LAN **V6→V7→V8** vert (`SMOKE_D6_V6V8 OK`, fil `smoke-d6-v6v8-*`, modèle `lbg-compagnon-e4b-v1`)  
   - Voir § **D6 — Causerie crédible** ci-dessous

## D6 — Causerie crédible (avant O2)

**Problème** : O1 est « done » checklist (presence / Agir / dials), mais l’échange ne sent pas encore Jarvis / MC — mur d’incompréhension, reset de fil, récitation ops.

**Invariant** : contre-pouvoir + dry-run inchangés pour **Agir**. D6 = posture **Discuter** distincte.

### Critères done (concrets)

| # | Critère | Mesure |
|---|---------|--------|
| C1 | **Continuité** | Sur 5 tours d’un même fil `:5174` (LAB), le Compagnon reprend le sujet sans redemander « l’objectif » ni repartir en fiche d’identité. |
| C2 | **Collègue d’abord** | Ouverture type « discutons comme collègues du projet » → réponse avec prise de position / avis, **sans** réciter Agir / `.143` / dry-run / `deploy_*` (sauf demande explicite d’action). |
| C3 | **Retours constructifs** | Sur un avis produit (« ça me frustre / j’aimerais X ») → 1 diagnostic + 1 proposition, pas un questionnaire ni un audit Team inventé. |
| C4 | **Deux postures** | `Discuter` ≠ `Agir` : le bouton Agir / proposition d’action n’apparaît que si l’humain demande une exécution ou un outillage. |
| C5 | **Smoke humain** | Batterie manuelle 5 tours (causerie projet) + tests unitaires `chat_intent` / nudge causerie verts. **V6→V8 auto PASS** 2026-10-06. Humain 2026-10-08 : [`smoke_humain_d6_2026-10-08.md`](smoke_humain_d6_2026-10-08.md) — C1 PASS · C2 PARTIEL. |
| C6 | **Gate O2** | ~~Tant que C1–C5 ne sont pas verts…~~ **ouvert** 2026-10-06 (smoke V6–V8 + D6.1–D6.4). |

### Lots

| Lot | Livrable | État |
|-----|----------|------|
| **D6.1** | `short_ctx` LAB conservé (cap 6 msgs) + nudge causerie + élargissement heuristiques collègue/ami | **OK** code (2026-10-01) — deploy `deploy_compagnon_100.sh` |
| **D6.2** | Prompt `compagnon_lab` scindé « causerie courte » vs « ops » + character slim + anti-rebond | **OK** code (2026-10-01) — `resolve_lab_system_prompt` |
| **D6.2b** | Combo feeling : sticky fil + anti-fausse investigation + OpenClaw pas sur « évoluer » causerie | **OK** code (2026-10-02) |
| **D6.2c** | Campus conceptuel ≠ Team live (`team_routing`) + rôles Compagnon/Lyra dans prompt causerie ; Pilot 502 = `lbg-backend` / `pydantic-settings` | **OK** (2026-10-02) |
| **D6.3** | UI : chrome ops replié par défaut en mode réponse / ask (timeline tags moins bruyants) | **OK** code (2026-10-06) — `ChatFlow.vue` details timeline/réflexion/méta |
| **D6.4** | Smoke voix causerie V6–V8 + critère C1 documenté dans `SMOKE_LAN` ou voice-smoke | **OK** (2026-10-06) — `voice_smoke_cases` + [`SMOKE_LAN.md`](../../docs/SMOKE_LAN.md) § Compagnon D6 |
| **D6.5** | Greeting + sticky go-ahead + livrer plan + **persist Team** (`plan_submit` → mission Campus) | **OK live** 2026-10-08 — `SMOKE_D65_V9V10 OK` sur `:5174` · A1/A3/A4/A4b · [`PLAN_PRESENCE_ZONE_ENTRAINEMENT.md`](PLAN_PRESENCE_ZONE_ENTRAINEMENT.md) |

### Ops Agir / Pilot (rappel 2026-10-02)

- **HTTP 502** « Pilotage impossible » / Team : souvent `lbg-backend` down sur `.140` (ex. `ModuleNotFoundError: pydantic_settings` dans `/opt/LBG_IA_MMO/.venv`). Fix : install deps venv + `systemctl restart lbg-backend` ; vérifier `curl -m 20 http://192.168.0.140:8080/v1/pilot/status` → 200 (peut prendre 10–20 s si healthz agents lents).
- **« c’est quoi le campus »** doit rester en chat LLM (causerie), pas un compte-rendu Team live — overlay `compagnon_ui/server_overlay/team_routing.py`.

## Chemins / surfaces (ne pas confondre)

| Surface | URL | Rôle |
|---------|-----|------|
| **Compagnon produit** | http://192.168.0.100:5174/ | Présence, dialogue, initiative, Agir |
| **Compagnon via Pilot** | http://192.168.0.140:8080/#/assistant | Même canal ops (dry-run / jeton) |
| **Accueil Pilot** | http://192.168.0.140:8080/#/ | Hub liens — **pas** le chat produit |
| **Bureau Team** | http://192.168.0.140:8080/#/team/office | Campus / présence agents |
| **Jobs L2** | http://192.168.0.140:8080/#/jobs | Approbations |

**Audit 2026-09-27** : les liens Accueil → 5174 / `#/assistant` / `#/team/*` / `#/jobs` / Cockpit répondent HTTP 200.  
Pièges fréquents (pas des routes « perdues », mais de la confusion) :

1. Menu **Studio** ouvert sur Accueil ≠ navigation vers Bureau — vérifier le hash (`#/` vs `#/team/office`).
2. Canon présence = `:5174` ; Pilot = cockpit ops. Carte Accueil doublon « Chat produit (Orch) » **retirée** (2026-09-27).
3. Routes Pilot étendues (`#/hunt`, `#/agents/map`, `#/providers`, `#/team/metrics`) passent par `src/main.js` (patches ESM) — pas par le monolithe `pilot.js` orphelin (plus chargé par `index.html`).

## D5 — 4 types de propositions

Invariant : **jamais d’auto-exec L2**. Toast / message → Agir (dry-run) → Réel.  
Quota global : max 3/h · ≥10 min entre toasts · silence ≥90 s.

| Type | Fingerprint / id | Déclencheurs | Contenu | Priorité |
|------|------------------|--------------|---------|----------|
| **Garde** | `infra:*`, `disk:*`, `jobs:l2:*`, `tension:high` | Alerte factuelle | 1–2 CTA Agir (sonde, Jobs) | P0 |
| **Mandat** | `mandate:ask` | Pas de mandat frais (TTL 4 h) **ou** 1er idle session ; silence ≥2 h si mandat expiré | Chips : Jobs / LAN / Mail / Studio — « priorité ? » | P1 |
| **Opportunité** | `jobs:idle` (+ rotation catalogue) | Silence ≥10 min, curiosité ≥0.7, pas d’alerte, mandat OK | mail / selfcheck / Jobs… dans le périmètre mandat | P2 |
| **Studio** | `studio:*` | Mandat inclut `studio` ; silence ≥30 min **ou** Self `pending_will` | Veille évolution, synth doc focus, micro-tâche conception | P2 |

### Ordre de sélection

1. Garde si signal infra / jobs L2 / tension réelle  
2. Sinon Mandat si aucun mandat actif / expiré (max 1 / 4 h)  
3. Sinon Studio si mandat ⊇ `studio` et fingerprint non snoozé  
4. Sinon Opportunité (idle) bornée au mandat  

### Mandat (stockage)

`localStorage` clé `lbg_compagnon_mandate_v1` :

```json
{ "watch": ["jobs_l2"], "updatedAt": 0, "until": 0 }
```

Scopes : `jobs_l2` | `lan` | `mail` | `studio`.  
Réponse chips / toast met à jour le mandat **et** aligne `studioGoal` (objectif affiché empty state).

## Correctifs livrés (2026-09-18)

### Sonde AD & boucle d'initiative résolues
1. **Cible AD corrigée** : `_infra_signals()` cible désormais le vrai agent Windows `192.168.0.10:5005` (aligné dans `proactive.py`, `lbg.env.example` et `/etc/lbg-ia-mmo.env` sur 140). `ad_agent_reachable` passe à `true`, `ad_agent_down` éliminé.
2. **Quota stabilisé** : le fingerprint d'initiative est aligné sur le signal/intent effectif (plus de faux positifs via `last_job_id` changeant).
3. **Snooze persistant** : bouton « Ignorer » snooze le fingerprint pendant 4h (et 6h après Agir réussi). Tests unitaires verts (`initiativeQuota.test.js`).

### Polish visuel & UX Compagnon (:5174)
1. **Socle Tailwind v4 & Tokens** : `@source` explicites pour tous les composants, suppression du hack `svg 40px`, tokens studio sobres, arrière-plan sans 404.
2. **Empty state 30s** : présence Compagnon ; **post-revue** = 3 pistes (Selfcheck / Échanger / ⌘K), pas 4.
3. **Hiérarchie & Pilotage** : barre limitée à **4 actions + Plus ⌘K** (catalogue complet dans la palette) ; réglages agent/mode/persona repliés.
4. **Toast unique** : InitiativeToast seul pour les actions ; le pet Lyra pulse sans bulle doublon.
5. **Déploiement & Smokes** : deploy CT100 (`5174`) vert avec smoke chat + Agir.

## Ne pas rouvir

- Remplacer Pilot (Team / Jobs / office) par un clone 5174  
- Feature longue uniquement dans `_archive/LBG_IA` sans extraction  
- Microservice compagnon basé sur packages absents du monorepo  
- Focus MMO « 30 s Lost Heaven » tant que le Compagnon n’est pas crédible sur `:5174`

Réf. archivée jeu : [`FOCUS_WAHOU.md`](FOCUS_WAHOU.md).  
Ancien cutover Pilot-first (assoupli) : `packages/cortex/docs/plan_pilot_hub_orch_absorb.md`.
