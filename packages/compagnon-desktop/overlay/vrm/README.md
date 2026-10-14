# Overlay VRM (desktop pet 3D)

Rendu **three.js + @pixiv/three-vrm** dans la fenetre overlay Electron.
Pilote par le meme bus que FaceRig (mood / TTS / initiative).

## Config (`config.json`)

```json
"overlay": {
  "enabled": true,
  "mode": "vrm",
  "width": 240,
  "height": 420,
  "vrmModel": "./vrm/default.vrm"
}
```

- `mode`: `vrm` | `face` (FaceRig 2D)
- `vrmModel`: chemin relatif sous `overlay/` ou URL https

## Modele

`default.vrm` = sample public pixiv/three-vrm (demo). Remplace par ton `.vrm`
(VRoid Hub / VRoid Studio) en gardant le meme nom, ou change `vrmModel`.

Premier lancement : CDN three.js (jsdelivr) requis une fois.

## Retour FaceRig

```json
"overlay": { "mode": "face", "width": 188, "height": 280 }
```
