# Face Rig (Pilot) — calques 2D

Avatar expressif **2D** pour `#/assistant` : yeux + bouche (+ base) pilotés par l’humeur orchestrateur et la parole.

- Brief art : `Infographiste_IA/pipelines/face_parts/BRIEF_lyra_face_rig.md`
- Contrat : `packages/cortex/docs/face_rig_pilot_mmo.md`
- Assets attendus : `assets/<character_id>/{eyes,mouth,base,manifest}.png|json`
- Sans assets : fallback CSS automatique

## API

`FaceRig.init(hostId, opts)` · `setMood(mood)` · `setExpression(expr)` · `setTalking(ms|bool)` · `say(text)` · `destroy()`
