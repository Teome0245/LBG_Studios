# Adaptateurs avatar externe (Windows `.10`)

Le Compagnon Desktop publie l’état avatar sur **loopback** (contrat
[`avatar_presence_events_v1.md`](../../cortex/docs/avatar_presence_events_v1.md)).

## Source sur `.10`

`A:` = `\\192.168.0.143\projects` (Omarchy). Package vivant :

`A:\LBG_Studios\packages\compagnon-desktop\`

Déploiement recommandé (agent desktop `:5005` ou manuel) :

```powershell
powershell -ExecutionPolicy Bypass -File A:\LBG_Studios\packages\compagnon-desktop\adapters\Apply-AvatarBridge-FromA.ps1 -Start
```

Sync → `C:\Agent_IA\compagnon-desktop` + relance Electron + smoke `:8765`.

## Activer

Dans `config.json` :

```json
"avatarBridge": {
  "enabled": true,
  "host": "127.0.0.1",
  "port": 8765
}
```

Optionnel : masquer l’overlay FaceRig si un rendu 3D externe le remplace :

```json
"overlay": { "enabled": false }
```

## Smoke

```powershell
powershell -ExecutionPolicy Bypass -File .\adapters\Watch-AvatarBridge.ps1
```

## Chemins

| Rendu | Intégration |
|-------|-------------|
| **FaceRig** (défaut) | Déjà dans `overlay/` — bridge optionnel pour debug |
| **liqu-companion** (VRM + Ollama) | Client SSE → map `avatar.mood` / `avatar.talking` → poses |
| **Mate Engine** | Pas d’API stable → décor manuel ; ou lancer liqu-companion à côté |
| **Shimeji** | Hors scope (sprites 2D, pas de mood LLM) |

## Commandes

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8765/avatar/command `
  -ContentType application/json -Body '{"v":1,"cmd":"open_chat"}'
```
