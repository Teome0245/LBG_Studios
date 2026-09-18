# Focus — Compagnon Studio (type Jarvis)

**Date** : 2026-09-17 (pilotage + handoffs Antigravity)  
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

Profils dialogue : `compagnon` (défaut), `jarvis`, `mother`, `kit`, `hal`  
(`lbg_agents/dialogue_llm.py` → `ASSISTANT_PROFILES`).  
Voix d’accueil : `lbg_agents/lbg_ia_voice.py`.

À brancher aussi côté Orch UI (`/ask` + profil) pour que `:5174` parle la même langue.

## Autonomie (bornée)

| Niveau | Comportement |
|--------|----------------|
| L1 | Timers / jobs / sondes sans merge destructeur |
| L2 | Toi (approvals Pilot / jeton desktop) |
| L3 | Miroir → propositions — pas d’auto-merge aveugle |

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
7. **Pilotage** — barre + palette Ctrl+K + encart activité + suites Agir — **OK** (2026-09-17)  
   - `PilotageBar` / `PilotagePalette` / `ActivityEncart` / `pilotageActions.js`  
   - Après Dry-run/Réel : chips « Suite — pilotage » sur `ActionCard`  
   - Deploy : `bash packages/cortex/infra/scripts/deploy_compagnon_100.sh`

## Correctifs livrés (2026-09-18)

### Sonde AD & boucle d'initiative résolues
1. **Cible AD corrigée** : `_infra_signals()` cible désormais le vrai agent Windows `192.168.0.10:5005` (aligné dans `proactive.py`, `lbg.env.example` et `/etc/lbg-ia-mmo.env` sur 140). `ad_agent_reachable` passe à `true`, `ad_agent_down` éliminé.
2. **Quota stabilisé** : le fingerprint d'initiative est aligné sur le signal/intent effectif (plus de faux positifs via `last_job_id` changeant).
3. **Snooze persistant** : bouton « Ignorer » snooze le fingerprint pendant 4h (et 6h après Agir réussi). Tests unitaires verts (`initiativeQuota.test.js`).

### Polish visuel & UX Compagnon (:5174)
1. **Socle Tailwind v4 & Tokens** : `@source` explicites pour tous les composants, suppression du hack `svg 40px`, tokens studio sobres, arrière-plan sans 404.
2. **Empty state 30s** : présence Compagnon chaleureuse, 4 suggestions interactives (Sonde LAN, Action poste Notepad, Dialogue, Palette ⌘K).
3. **Hiérarchie & Pilotage** : présence en ligne prioritaire, métriques ops repliées par défaut, boutons Pilotage et carte d'entrée harmonisés.
4. **Déconfliction spatiale** : toast d'initiative repositionné (`bottom: 6rem; right: 6.5rem`) sans conflit avec l'avatar LyraWidget ni la zone d'input.
5. **Déploiement & Smokes** : deploy CT100 (`5174`) vert avec smoke chat (`/api/ask`) et smoke agir (`/api/pilot/action-proposal`).

## Ne pas rouvir

- Remplacer Pilot (Team / Jobs / office) par un clone 5174  
- Feature longue uniquement dans `_archive/LBG_IA` sans extraction  
- Microservice compagnon basé sur packages absents du monorepo  
- Focus MMO « 30 s Lost Heaven » tant que le Compagnon n’est pas crédible sur `:5174`

Réf. archivée jeu : [`FOCUS_WAHOU.md`](FOCUS_WAHOU.md).  
Ancien cutover Pilot-first (assoupli) : `packages/cortex/docs/plan_pilot_hub_orch_absorb.md`.
