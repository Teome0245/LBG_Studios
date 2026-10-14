# Avatar présence — contrat events v1

**Produit** : Compagnon Desktop (poste `.10`)  
**Date** : 2026-10-14  
**Statut** : P0 figé (bridge local)  
**Consommateurs** : overlay FaceRig Electron · adaptateurs externes (Mate Engine / VRM / liqu-companion)

## Objectif

Exposer l’état **présence visuelle** du Compagnon (humeur, parole, initiative) sur un bus local,
pour piloter :
1. l’overlay FaceRig déjà dans `packages/compagnon-desktop` ;
2. un **compagnon 3D externe** (Mate Engine, liqu-companion, etc.) sans dupliquer le cerveau `:5174`.

Invariant : le cerveau reste Orch / Compagnon UI. L’avatar n’est qu’un **rendu**.

## Bus

| Canal | Où | Endpoint |
|-------|-----|----------|
| HTTP SSE | localhost (Electron `.10`) | `GET /avatar/stream` |
| Snapshot | idem | `GET /avatar/state` |
| Commande UI | idem | `POST /avatar/command` |

Bind défaut : `127.0.0.1:8765` (opt-in `config.json` → `avatarBridge.enabled`).  
Jamais exposé sur le LAN (loopback only).

## Envelope

```json
{
  "v": 1,
  "event": "avatar.mood",
  "ts": "2026-10-14T19:30:00Z",
  "source": "compagnon-desktop",
  "mood": "serene",
  "talking": false,
  "text": null,
  "ms": null,
  "initiative": null,
  "detail": {}
}
```

| Champ | Règle |
|-------|--------|
| `event` | Voir table ci-dessous |
| `mood` | Vocabulaire FaceRig : `serene` · `curious` · `tense` · `happy` · `sad` · `alert` (string libre tolérée) |
| `talking` | `true` pendant TTS / bulle parole |
| `text` | Extrait ≤ 140 car. (jamais secrets / tokens) |
| `ms` | Durée estimée parole (lip-sync) |
| `initiative` | Objet Agir-ready (même forme que toast D3) ou `null` |

## Events

| `event` | Effet attendu | Émetteur |
|---------|---------------|----------|
| `avatar.mood` | Change expression / pose idle | overlay mood / initiative |
| `avatar.talking` | Lip-sync / mouth open `ms` ms | TTS SPA (`speakText`) |
| `avatar.say` | Bulle courte + anim parler | initiative / say |
| `avatar.initiative` | Pulse + CTA Agir | poll proactive D3 |
| `avatar.idle` | Retour pose calme | fin TTS / dismiss |
| `avatar.heartbeat` | Keep-alive (~30 s) | bridge |

## Commandes (`POST /avatar/command`)

```json
{ "v": 1, "cmd": "open_chat", "detail": {} }
```

| `cmd` | Effet |
|-------|--------|
| `open_chat` | Ouvre / focus fenêtre Compagnon |
| `open_agir` | Deep-link Agir (`sourceText` / `label` dans `detail`) |
| `set_mood` | Force mood (`detail.mood`) — debug |

## Mapping externe (Mate Engine / VRM)

| Event Compagnon | Suggestion rendu |
|-----------------|------------------|
| `avatar.mood` = `serene` | Idle loop |
| `avatar.mood` = `tense` / `alert` | Pose « attention » / look-at |
| `avatar.talking` | Visème / mouth open `ms` |
| `avatar.initiative` | Wave / jump + ouvrir chat au clic |
| `avatar.idle` | Retour idle |

Mate Engine n’expose pas d’API officielle : l’adaptateur peut (a) consommer le SSE et piloter un second overlay VRM (liqu-companion), ou (b) logger + AutoHotkey pour triggers manuels.  
**Chemin recommandé** : FaceRig natif **ou** liqu-companion branché sur ce SSE — Mate Engine en décor optionnel.

## Smoke `.10`

```powershell
# Bridge ON dans config.json → avatarBridge.enabled = true
Invoke-RestMethod http://127.0.0.1:8765/avatar/state
# Puis : curl -N http://127.0.0.1:8765/avatar/stream
```

Script : `packages/compagnon-desktop/adapters/Watch-AvatarBridge.ps1`

## Hors scope v1

- Piloter directement le process Mate Engine (pas d’API stable)
- Visèmes phonème-par-phonème
- Sync Omarchy `.143` (layer-shell séparé ; même contrat JSON possible plus tard)
