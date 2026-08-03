# Plan traction Rang 2 — Persona MMO / pont

**Date** : 2026-08-03  
**Réf.** : [`RESTAURATION_PRODUIT.md`](RESTAURATION_PRODUIT.md) · ADR 0004 · `docs/lyra.md`

| Étape | Parcours | Critère done | État |
|-------|----------|--------------|------|
| **1** | `session_summary` → `mmo_persona` (HTTP) | `meta.lyra_engagement_resolved=mmo_persona` + reply PNJ | **OK** — `tools/smoke_rang2_persona_dialogue.sh` |
| **2** | Skip `factual_status` en mode persona | Chat « quête » reste PNJ | **OK** — déployé sur `.140` (`lbg-agent-dialogue`) 2026-08-03 |
| **3** | Godot `DialogueBridge` | Clic PNJ → Pilot `:8000` invoke | **OK** code (`scripts/dialogue_bridge.gd` + `main.gd`) |
| **4** | Persistance `user://session_summary.json` | Clés ADR bornées | **OK** |
| **4b** | Multi-tours + historique pont | `context.history` + MAJ `session_summary` après reply + LineEdit follow-up | **OK** (2026-08-03) |
| **4c** | Sync J: + cache `.godot` + Launchpad | Chaque sync régénère `.godot` ; Launchpad refuse launch si cache incomplet | **OK** (`tools/sync_prime_client_to_j.sh`) |
| **5** | Enrichissement quête serveur (gateway 246) | Merge autoritatif quête/PNJ | **à faire** (hors MVP) |
| **6** | Wire `lbg-ws/2` `ia_context` | Équivalent protocole mmmorpg | **hors scope** tant que chemin HTTP suffit |

## Smoke

```bash
bash tools/smoke_rang2_persona_dialogue.sh
# ou : bash tools/smoke_rang2_persona_dialogue.sh http://192.168.0.140:8000
```

## Config client

`packages/prime-client/config/dialogue_bridge.json` — `pilot_base_url` (défaut `http://192.168.0.140:8000`).

## Garde-fous ADR 0004

- Pas de fuite mail/disque vers le MMO.
- Sens volontaire : résumé session → persona ; inverse = export Pilot déjà livré (Rang 1).
