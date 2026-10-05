# Couche Character Compagnon (inspirée MC, adaptée LBG)

**Date** : 2026-09-28  
**Statut** : lots 1–3 livrés (pack + dials lab + profondeur soft)  
**Surface** : Compagnon `:5174` + overlay Orch `.100`

## Intention

Enrichir le **Compagnon** (et par extension l’écosystème studio) avec une couche **caractère** distincte de la politique morale / du Self ops :

| Couche | Rôle | Exemple LBG |
|--------|------|-------------|
| **Personnalité** | Ce qu’il *est* (worldview studio) | craft, vérité ops, contre-pouvoir |
| **Caractère** | *Comment* il s’exprime (7 dials) | piquant, densite, ego, … |
| **Morale / légal** | Garde-fous inchangés | `compagnon_llm_moral_policy.md` |
| **Self / Agir** | Agency ops | drives, initiative, `companion_review` |

Inspiration TikTok MC (Mec Chill) : blacklist anti-langage IA, ego + triggers, curseurs, formules signature — **sans** reprendre l’ego toxique / vulgarité haute en prod.

## Fichiers

| Élément | Chemin |
|---------|--------|
| Pack canon | `packages/cortex/knowledge/character/compagnon_v1.json` |
| Copie overlay | `compagnon_ui/server_overlay/character/compagnon_v1.json` |
| Moteur | `compagnon_ui/server_overlay/character_layer.py` |
| API | `compagnon_ui/server_overlay/character_api.py` → `/character/*` |
| Injection chat | `compagnon_ui/server_overlay/llm_chat_phase.py` |
| UI lab | `compagnon_ui/src/components/CharacterDialsPanel.vue` + `lib/characterDials.js` |
| Deploy | `infra/scripts/deploy_compagnon_100.sh` |

## API

- `GET /character/` — snapshot (dials, catchphrases, pack_id)
- `GET|PUT /character/dials` — lire / écrire dials (`/var/lib/lbg/character/dials.json`)
- `POST /character/catchphrases` — mémoriser une formule (opt-in, quota fichier)
- `GET /character/voice-smoke` — batterie V1–V5

Depuis le SPA : préfixe `/api` (nginx) → `/api/character/…`.

## 7 dials

`piquant`, `densite`, `ego`, `familiarite`, `politesse`, `humour`, `enthousiasme` (0–1).

- **Prod** : caps (`ego_max` 0.55, `piquant_max` 0.5, …) dans le pack  
- **Lab** (`LBG_COMPAGNON_LAB=1` ou `lab=true` sur PUT) : `lab_max` par dial

UI : bouton curseurs dans le header Compagnon → panneau latéral → **Appliquer** (sync PUT).

## Ego soft + blacklist

- Triggers regex (grille-pain, clone GPT, « obéis ») → nudge session dans le system prompt  
- Post-LLM : `reshape_blacklist` retire « En tant qu’IA », « n’hésitez pas à », etc.

## Smoke voix (manuel)

```bash
curl -s http://192.168.0.100:5174/api/character/voice-smoke | jq
# Puis POST /ask avec chaque case.prompt — vérifier expect
```

Cases : identité, ego toaster, blacklist, vérité ops, contre-pouvoir Agir.

## Tests locaux

```bash
# Python
python3 -m unittest packages/cortex/compagnon_ui/server_overlay/tests/test_character_layer.py

# JS
node --test packages/cortex/compagnon_ui/src/lib/characterDials.test.js
```

## Feature flag

`LBG_CHARACTER_LAYER=0` désactive injection + reshape (API reste lisible).

## Hors scope

- Persona MMO (ADR 0004)  
- Contournement contre-pouvoir / auto L2  
- Fine-tuning modèle
