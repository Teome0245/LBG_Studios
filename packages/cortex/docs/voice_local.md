# Voix locale Compagnon (`voice_local`)

**Date** : 2026-09-29 (maj 2026-10-02 — provider Edge)  
**Statut** : lot 2 — Edge TTS (DeniseNeural) + fallback Piper LAN + mute SPA  
**Surface** : Compagnon `:5174` → Orch `.100:3000` → **Edge** (défaut) ou Piper `.111:8098`

## Intention

Donner une **vraie voix** au Compagnon (audio), même famille que Hermes (`Edge` / `fr-FR-DeniseNeural`).  
Piper reste le **fallback LAN** (hors-ligne / Edge KO).  
Distinct de la « voix » écrite (`character_layer` / `lbg_ia_voice`).

## Architecture

```
SPA :5174  --POST /api/tts-->  Orch .100
                                 ├─ provider=edge  → edge-tts (Microsoft) → audio/mpeg
                                 │                    voix: fr-FR-DeniseNeural
                                 └─ fallback=piper → Piper .111:8098 → audio/wav
                                                      voix: fr_FR-siwis-medium
```

| Élément | Chemin / URL |
|---------|----------------|
| Proxy Orch | `compagnon_ui/server_overlay/tts.py` + `tts_api.py` |
| Service Piper (fallback) | `packages/cortex/voice_local/` → `/opt/lbg-piper-tts` sur `.111` |
| systemd Piper | `infra/systemd/lbg-piper-tts.service` · port **8098** |
| Deploy Piper | `infra/scripts/deploy_piper_tts_111.sh` |
| SPA | `compagnon_ui/src/lib/tts.js` · bouton **Voix** header |
| Deploy Compagnon | `deploy_compagnon_100.sh` (wire factory + env + `edge-tts`) |

## Env (`.100` `/opt/orchestrateur/.env`)

| Variable | Défaut | Rôle |
|----------|--------|------|
| `LBG_TTS_ENABLED` | `1` | Coupe le proxy |
| `LBG_TTS_PROVIDER` | `edge` | `edge` \| `piper` |
| `LBG_TTS_FALLBACK` | `piper` | si Edge échoue → Piper (`none` pour désactiver) |
| `LBG_EDGE_VOICE` | `fr-FR-DeniseNeural` | Voix Microsoft (comme Hermes) |
| `LBG_PIPER_URL` | `http://192.168.0.111:8098` | Upstream fallback |
| `LBG_PIPER_VOICE` | `fr_FR-siwis-medium` | Modèle FR Piper |
| `LBG_TTS_MAX_CHARS` | `500` | Truncation orale |
| `LBG_TTS_TIMEOUT_S` | `45` | Timeout proxy Piper |

Dépendance Docker backend : `edge-tts>=6.1.0` (ajoutée idempotente par le deploy).

## UX

- Bouton **Voix** dans le header `:5174` (off par défaut — opt-in).
- Si activé : lit les réponses assistant + messages d’initiative (texte sanitizé).
- FaceRig : `setTalking` approximatif pendant la lecture.
- Desktop Electron : `compagnonDesktop.notifyPresence({ kind: 'talking', ms })` → bridge SSE `:8765` ([`avatar_presence_events_v1.md`](avatar_presence_events_v1.md)).
- Headers utiles : `X-LBG-TTS-Provider`, `X-LBG-TTS-Voice`, `X-LBG-TTS-Fallback-From` (si secours).

## Install / smoke

```bash
# 1) Piper sur .111 (fallback)
bash packages/cortex/infra/scripts/deploy_piper_tts_111.sh --smoke

# 2) Compagnon .100 (proxy Edge + UI)
bash packages/cortex/infra/scripts/deploy_compagnon_100.sh --smoke

# Health (provider + fallback)
curl -s http://192.168.0.100:5174/api/tts/health | jq

# Synthèse
curl -s -X POST http://192.168.0.100:5174/api/tts \
  -H 'Content-Type: application/json' \
  -d '{"text":"Bonjour, Compagnon."}' -o /tmp/out.audio
file /tmp/out.audio
```

Forcer Piper uniquement :

```bash
# sur .100 /opt/orchestrateur/.env
LBG_TTS_PROVIDER=piper
```

## Tests locaux

```bash
python3 -m unittest packages/cortex/compagnon_ui/server_overlay/tests/test_tts.py
node --test packages/cortex/compagnon_ui/src/lib/tts.test.js
```

## Hors scope (lots suivants)

- STT micro → chat  
- Visèmes / phonèmes FaceRig  
- Multi-voix / clone  
- ASR Pilot unifié
