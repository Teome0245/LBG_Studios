# Handoff ponctuel — spawn M11 + M12 (parallèle)

> **Ce n’est pas un preset Pilot.** C’est un **lot de tâches one-shot** (comme `spawn_team_prime_lbg_handoff.sh`).  
> À lancer **une fois** pour ouvrir le jalon ; pas prévu à être réutilisé chaque semaine.

**Gateway produit (2026-07-22)** : HTTP + WS sur **Prime `192.168.0.246`** — voir [`GATEWAY_PRIME_246.md`](GATEWAY_PRIME_246.md).
**Preset Pilot** = bouton réutilisable dans `#/team` (`teamPresets.ts`) : Smoke LAN, Brief réunif, Valider Godot…

---

## Lancer le handoff

```bash
bash LBG_IA_MMORPG/LBG_IA_MMO/infra/scripts/spawn_team_m11_m12.sh --dry-run
bash LBG_IA_MMORPG/LBG_IA_MMO/infra/scripts/spawn_team_m11_m12.sh
bash .../spawn_team_m11_m12.sh --only=m11_login

# Re-spawn CODE (forge write_files) — Thémis contrat + Hermès LoginPanel
bash LBG_IA_MMORPG/LBG_IA_MMO/infra/scripts/spawn_team_m11_code.sh
```

**Prérequis** : `LBG_ORCHESTRATOR_URL` (défaut `http://127.0.0.1:8010`).

---

## Où voir l’avancement et les livraisons

| Canal | Rôle | Réutilisable ? |
|-------|------|----------------|
| **Element — salle LBG Pilot LAN** | Push auto `✅ Terminé` / `❌ Échec` / L2 pending (`matrix_notify`) | Oui — suivi principal mobile |
| **Pilot `#/team`** | Détail tâche, output agent, approve L2 | Oui — vue complète |
| **Brief réunif** (preset Thémis) | Synthèse jalons M10–M12 à la demande | Oui — preset |
| **Cursor (moi)** | Revue diff / intégration **quand tu demandes** | Sur demande |
| **Ce fichier** | Archive des objectifs du handoff initial | Non — one-shot |

Element = **canal de suivi** (ADR 0018, `matrix_notify.py`). Commandes utiles dans la salle : `status`, `pending`, `approve <id>`, `help`.

La team **doit** clôturer chaque tâche avec dans l’output orchestrateur (visible Element + `#/team`) :

- `status` : done | failed  
- `deliverables` : chemins repo (`docs/jalon_m11_login_lbg.md`, `scripts/LbgAuthClient.gd`, …)  
- `blockers` : si échec  

→ push **Element** (`✅ Terminé` / `❌ Échec`) + détail **Pilot `#/team`**.

Pas de canal parallèle à maintenir : Element notifie, `#/team` détaille.

---

## Objectifs spawnés (référence)

### Thémis — contrat M11↔M12

```
M11↔M12 — rédiger le contrat d'interface (1 page max) : token session, URL WebSocket, messages login/select_character/enter_zone, erreurs (character_in_use, auth_failed), session kick_other. Référencer core3_zone_bridge_spec.md §2 et client.zone_command_v2.schema.json. Livrable : section « Contrat M11-M12 » dans docs/jalon_m11_login_lbg.md + lien depuis jalon_godot_client_live_team.md. ADR 0016.
```

### Hermès M11

```
Hermès M11 — Login compte LBG dans prime-client (sans lbgemu, sans retail). Livrables : (1) docs/jalon_m11_login_lbg.md complet ; (2) extension lbg_gateway auth + select_character ; (3) LoginPanel.tscn + LbgAuthClient.gd ; (4) remplacement progressif soe_handshake --play pour Teome. Output tâche : liste deliverables[] avec chemins. Revue humaine L2.
```

### Hermès M12

```
Hermès M12 — lbg-ws/2 Godot ↔ gateway ↔ LbgZoneBridge. Livrables : MAJ jalon_godot_client_live_team.md, LbgWsClient.gd, gateway WS, smoke token mock. Output : deliverables[]. Revue humaine L2.
```

### Iris M11 UI · Dédale ZB · Argus smokes

Voir `infra/scripts/spawn_team_m11_m12.py` (TASKS).

---

## Rôle Cursor après livraison

1. Tu vois `done` dans `#/team` (ou tu me dis le `task_id`).
2. Tu demandes : *« Revue livrable Hermès M11 »*.
3. J’intègre / corrige dans `prime-client` — pas de re-spawn du handoff.

Suivi récurrent : preset **Brief réunif** (Thémis), pas ce handoff.

---

## Filtres script

| Flag | Effet |
|------|--------|
| `--dry-run` | Affiche les objectifs sans orchestrateur |
| `--only=m11_login` | Sous-ensemble par track |

Tracks : `themis_contract`, `m11_login`, `m12_lbg_ws2`, `m11_ui`
