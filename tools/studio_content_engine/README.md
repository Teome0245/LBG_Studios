# Studio Content Engine — Générateur Autonome de Vidéos TikTok / Shorts (0 €)

Pipeline d'automatisation de production vidéo courte verticale (9:16 - 1080×1920) pour TikTok, YouTube Shorts et Instagram Reels, 100% local et sans frais de cloud récurrents.

---

## Architecture de la Pipeline

```
[ Idée / Sujet Tech ]
         │
         ▼
[ 1. Script Viral LLM ] ──► Ollama local (.111:11434 / .110:11434)
  - Hook 3s anti-scroll    (qwen2.5:3b / gemma-4 / fallback canonique)
  - Douleur / Problème
  - Solution technique 0€
  - Call to Action
         │
         ▼
[ 2. Synthèse Vocale ]  ──► Piper TTS sidecar (.111:8098/v1/tts)
  - Rendu instantané WAV 22050 Hz
  - Concaténation et calage temporel des phrases
         │
         ▼
[ 3. Sous-titres TikTok ] ──► Moteur ASS (Advanced SubStation Alpha)
  - Style néon jaune & blanc, contour 6px noir
  - Découpage par bloc d'impact
         │
         ▼
[ 4. Rendu 3D Avatar & Composition FFmpeg ]
  - Poses clés 3D pré-calculées sous Blender 5.2.2 LTS (Mia.vrm) :
    * neutral.png, talk_a.png, talk_o.png, blink.png, joy.png
  - Lip-sync dynamique réagissant à l'enveloppe RMS audio
  - Clignements d'yeux procéduraux (toutes les 3.6s)
  - Micro-mouvements de respiration et balancement
  - Spectre audio réactif (28 barres néon animées)
  - En-tête Cyberpunk LBG Studios & badges
         │
         ▼
[ Vidéo MP4 Finalisée ] ──► 1080×1920 @ 30 FPS, H.264 / AAC (~3 Mo)
```

---

## Commandes Rapides

### 1. Génération de démonstration instantanée
```bash
packages/cortex/.venv/bin/python tools/studio_content_engine/content_bot.py --demo
```

### 2. Génération sur un sujet personnalisé
```bash
packages/cortex/.venv/bin/python tools/studio_content_engine/content_bot.py \
  --topic "Pourquoi nos 10 bots IA tournent sur Godot 4.6 headless"
```

### 3. Publication Automatique (YouTube Shorts & TikTok)

#### YouTube Shorts (@LBG-p8k)
1. Télécharger `client_secret.json` depuis la Google Cloud Console (API YouTube Data v3 activée) et le placer dans :
   `tools/studio_content_engine/config/client_secret.json`
2. Lancer la première authentification :
   ```bash
   packages/cortex/.venv/bin/python tools/studio_content_engine/youtube_publisher.py --setup
   ```
3. Publier directement :
   ```bash
   packages/cortex/.venv/bin/python tools/studio_content_engine/content_bot.py --demo --youtube
   ```

#### TikTok Studio (Assistance Instantanée 0 Clic)
Le module déclenche directement sur le poste Windows :
- L'ouverture du navigateur sur `https://www.tiktok.com/tiktokstudio/upload`
- La mise en surbrillance du MP4 dans l'explorateur Windows (`O:\OneDrive\Pictures\IA\Contenue\`)
- La copie automatique du titre et des hashtags dans le presse-papier Windows (prêt pour `Ctrl+V`)

```bash
packages/cortex/.venv/bin/python tools/studio_content_engine/content_bot.py --demo --tiktok
```

### 4. Automatisation Quotidienne (2 Vidéos par Jour)
Le système tourne de manière autonome via un timer systemd Linux :
- **Horaires** : Déclenchement automatique chaque jour à **11h30** et **17h30**.
- **Gestionnaire** : `cron_daily_publisher.py` dépile le fichier `topics_backlog.json`.
- **YouTube Shorts** : Publication 100% automatique en public sur la chaîne officielle **La Boite à Geek (`@lbg-p8k`)**.
- **TikTok Manual Helper** : La vidéo MP4 est synchronisée sur `O:\OneDrive\Pictures\IA\Contenue\` avec sa fiche mémo texte (`*_tiktok_memo.txt`) contenant la légende exacte et les hashtags viraux.

Vérifier le statut du planificateur :
```bash
systemctl --user status lbg-content-daily.timer
systemctl --user list-timers
```

Déclencher un drop manuellement hors planning :
```bash
packages/cortex/.venv/bin/python tools/studio_content_engine/cron_daily_publisher.py
```

### 5. (Re)génération des poses 3D sous Blender
Si vous modifiez l'éclairage, la caméra ou l'avatar (`Compagnon.vrm`, `NeonNeko.vrm`) :
```bash
blender -b --python tools/studio_content_engine/blender_render_keyframes.py
```

---

## Spécifications Techniques

| Paramètre | Valeur |
|---|---|
| **Résolution** | 1080 × 1920 (Vertical 9:16) |
| **Framerate** | 30 FPS |
| **Codec Vidéo** | H.264 (libx264, profile High, CRF 20, yuv420p) |
| **Codec Audio** | AAC LC mono 22050 Hz |
| **Poids moyen** | ~3.0 Mo pour 25 secondes |
| **Temps de génération** | ~30 secondes (0 coût API) |

