# Restauration produit — étoile du nord

**Date** : 2026-10-13 (réalignée sur P3–P6 G5+ · canon `:8787`)  
**Créée** : 2026-08-18  
**But** : ne pas perdre l’objectif d’origine pendant le recentrage O0/O1.

Vision (note 2026-04-28) : IA incarnée sur **PC/infra** → même famille au **cœur du MMO** → **évolution contrôlée** du monde / code.

Doc pivot : [`packages/cortex/docs/vision_projet.md`](../packages/cortex/docs/vision_projet.md) · [`plan_de_route.md`](../packages/cortex/docs/plan_de_route.md) § *Étoile du nord*.  
Canon runtime : [`RUNTIME_GODOT.md`](RUNTIME_GODOT.md) · plan jeu : [`PLAN_MMO_O2.md`](PLAN_MMO_O2.md) · priorités : [`PRIORITES_ACTUELLES.md`](PRIORITES_ACTUELLES.md).

Légende : **vert** = utilisable aujourd’hui · **jaune** = partiel / à solidifier · **rouge** = pas encore / gelé volontairement.

---

## Rang 1 — Assistant PC & infra

| Fonction | État | Où / note |
|----------|------|-----------|
| Ouvrir une app sur le PC (`open_app`, vghd…) | **vert** | Cockpit Supervisé / Chat GIR ; jetons 140 ↔ `C:\Agent_IA\desktop.env` alignés ; inject approval serveur |
| Dry-run Desktop | **vert** | Réglages Cockpit + smoke `--functional` |
| `open_url` réel (allowlist host) | **vert** | 2026-08-03 : `https://example.org` OK sur worker |
| `search_web_open` | **vert** | 2026-08-03 : DDG réel OK (`LBG_DESKTOP_WEB_SEARCH=1`) |
| `notepad_append` (proxy dictée) | **vert** | 2026-08-03 : `C:\Users\Public\lbg_rang1_notes.txt` |
| Mail IMAP lecture | **vert** | 2026-08-03 : `mail_imap_preview` OK (`.51`, user `sdesharches`, INBOX ; TLS **993** + `INSECURE_SSL`) |
| Dictée micro → STT → Notepad | **jaune** | Append texte OK ; micro/STT **reporté** (pas urgent) |
| `session_summary` poste ↔ Assistant | **vert** | 2026-08-03 : `export` + bridge HTTP OK (Pilot Cortex) |
| Audit disque / selfcheck infra (SSH, healthz) | **vert** | Supervisé GIR (ex. « audit disque prime 246 ») |
| Team ops (Héphaïstos) hors dry-run | **vert** | Dry-run Cockpit propagé + inject `devops_approval` à la création tâche (2026-07-31) |
| Approval sans double collage | **vert** | Inject serveur si Bearer Pilot OK |
| Compagnon Studio (présence) | **vert** | `.100:5174` + Desktop Electron · D0–D6 + feeling C1/C2 OK · [`FOCUS_COMPAGNON.md`](FOCUS_COMPAGNON.md) |

## Rang 2 — Persona MMO / pont

| Fonction | État | Où / note |
|----------|------|-----------|
| Autorité joueur `prime-hub` `.246:8787` | **vert** | G5+ live 2026-10-07 · HTTP+WS unifiés · [`RUNTIME_GODOT.md`](RUNTIME_GODOT.md) |
| Client Godot `prime-client` + Launchpad ≥ 2.1.4 | **vert** | Login M11 + WS · hub `:8787` · Core3 hors chemin joueur |
| Flotte IA / sièges hub (`ai_seats`) | **vert** | Triplons + autonomie bots sur `prime-hub` · [`HUB_LIFE_TRIPLONS.md`](design/HUB_LIFE_TRIPLONS.md) |
| Dialogue / persona *en jeu* (P3) | **vert** | Invoke + history + Chœur V50–V53 · C3–C8 live (wiki `/v1/wiki`) 2026-10-07 |
| World Stream + mémoire relationnelle Studio↔Monde | **vert** | Compagnon `:5174` ↔ hub `:8787` · tickets 3.1 / 3.2 2026-10-12 |
| Sidecar Core3 joueurs IA `:8791` / comptes `:8792` | **rouge** | Hors chemin joueur (ADR 0026) · lab optionnel uniquement |
| Bac Python `mmmorpg_server` / web `/mmo/` | **rouge** | Gelé volontairement |

## Rang 3 — Évolution monde / code par l’IA

| Fonction | État | Où / note |
|----------|------|-----------|
| Forge OpenGame (staging) | **jaune** | Proposition / dry-run ; pas merge tronc |
| Auto-patch / rebuild DevOps aveugle | **rouge** | Hors scope |
| Équipe Fable autoconsult 12 h | **vert** | Timer `lbg-team-autoconsult-job` sur 140 |
| Sprint évolution 7j (Thémis) | **vert** | Timer `lbg-team-evolution-sprint-job` ; L1 auto / L2 Pilot |
| Méta-autonomie L3 + ops health 7j | **vert** | L3 `days_ok=3/3` · Fleet `metrics_7d` · 2026-10-13 |
| Suggestions monde (file Studio) | **vert** | `world_suggestions.jsonl` · pas de mutation auto-monde |

## Cadre O0 / O1 (remise en forme)

| Item | État |
|------|------|
| Repo `LBG_Studios` source de vérité | **vert** |
| `packages/cortex` Pilot 140 + Compagnon CT100 | **vert** |
| Surfaces LAN (Pilot, Compagnon, hub `:8787`) | **vert** · smoke 2026-10-13 : 24 OK / 1 WARN / 0 KO |
| Smoke `tools/smoke_lan_surfaces.sh --functional` | **vert** · Godot G5+ nominal · Core3 `:8792` offline toléré |
| Pas de réintro client web legacy `/mmo/` | **vert** |
| Pilot Vite (modules ES, Three npm, bundle `dist/`) | **vert** · modularisé ticket 1.3 |
| Orchestrateur local sans `hybrid_proactive_agent` legacy | **vert** |
| LLM local `.110` heavy (CPU) + `.111` light | **vert** · OpenCode nominal mains code · Cline second avis |

---

## Prochaine traction

Jalons P1–P6 documentés **faits / clos** — voir [`PLAN_MMO_O2.md`](PLAN_MMO_O2.md) · [`PRIORITES_ACTUELLES.md`](PRIORITES_ACTUELLES.md).

**Reste produit** (backlog léger) :

1. **O-OPS-3** — F3 O2 jeu (hors plan gaps A–F2) — [`SUJETS_OUVERTS.md`](SUJETS_OUVERTS.md).
2. Polish gameplay hub (quêtes terrain POI, craft UX) — suite post-G5 dans [`RUNTIME_GODOT.md`](RUNTIME_GODOT.md).
3. Unification chemin client Git vs `/opt/new_mmo/prime-client` sur 140 — [`REGISTRE.md`](REGISTRE.md).
4. Dictée micro → STT (Rang 1, reporté).
5. Optionnel : review Bugbot `O-DOC-2`.

**Rang 1** (déjà largement vert) — dictée STT reste le seul jaune volontaire.
