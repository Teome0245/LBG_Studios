# Studio Content Engine — Générateur Autonome de Vidéos 3D TikTok / Shorts (0 €)

Pipeline d'automatisation de production vidéo courte verticale (9:16 - 1080×1920 @ 30 FPS) pour TikTok, YouTube Shorts et Instagram Reels, 100% local et sans frais de cloud récurrents.

---

## Modes de Rendu (Style Nexura Domina WebGL Three-VRM)

1. **`stage3d` (Défaut — Shorts Tech / MMO Parlés 3D)** :
   - Scène 3D temps réel (`Compagnon.vrm` sous Three-VRM + projecteurs volumétriques cyan/magenta, grille perspective animée, particules).
   - Poses et gestes mocap `.vrma` face caméra + caméras cinématiques mobiles (`push_in`, `front_arc`, `sway`, `pull_out`, `bust`).
   - Sous-titres karaoké courts (2–3 mots pop néon) positionnés en zone sûre TikTok/Shorts au-dessus de l'égaliseur.
   - Mixage voix de Lia (`Vivienne` / repli `Piper`) + nappe instrumentale synthwave discrète (-17.5 dB) + égaliseur FFT 24 bandes.
2. **`music3d` (Clips Musicaux / Chorégraphies 3D)** :
   - Mode concert virtuel 3D inspiré de *Nexura Domina* (`uLV_0kI2ogM`).
   - Micro cyber 3D néon en main, enchaînements de danses mocap `.vrma` (Maraschino, Bellydance, Hip-Hop, danses natives SWG Poplock/Moonwalk, Capoeira) et caméras drone.
   - Masters audio stéréo 0€ cloud (`nexura_domina_v1`, `lia_cyberpunk_song_30s_master`, `lia_synthwave_30s_master`, `lia_synthwave_energy_master_60s`).
3. **`jrpg` / `standard` (Legacy)** :
   - Conserves pour rétro-compatibilité.

### Exécution Hybride GPU `.10` ↔ `.143`
- Si le PC Windows `.10` est allumé **et** inactif depuis au moins 3 minutes (`LBG_WIN10_MIN_IDLE_SEC=180`), le rendu s'effectue avec accélération matérielle GPU dans un profil isolé sans toucher aux fenêtres de l'utilisateur.
- Sinon, repli 100% automatique et transparent en tâche de fond sur `.143` (`Xvfb` + Chromium WebGL + FFmpeg).

---

## Commandes Rapides

### 1. Générer un Short Tech / MMO parlé en scène 3D (défaut)
```bash
packages/cortex/.venv/bin/python tools/studio_content_engine/content_bot.py \
  --topic "Pourquoi fusionner Star Wars Galaxies Pre-CU et La 4ème Prophétie en 3D"
```

### 2. Générer un Clip Musical / Chorégraphie 3D
```bash
packages/cortex/.venv/bin/python tools/studio_content_engine/content_bot.py \
  --style music3d --music-preset nexura_drop_highlight
```
Presets musicaux disponibles : `nexura_drop_highlight`, `cyberpunk_protocol_30s`, `swg_cantina_groove`, `synthwave_energy_show`, `nexura_climax_encore`.

### 3. Publication Automatique (YouTube Shorts & TikTok)
```bash
packages/cortex/.venv/bin/python tools/studio_content_engine/content_bot.py \
  --style stage3d --topic "Mon sujet Tech" --youtube --tiktok
```

### 4. Automatisation Quotidienne Alternée (`cron_daily_publisher.py`)
Le planificateur systemd (`lbg-content-daily.timer`) dépile `topics_backlog.json` en alternant automatiquement les **Shorts Tech/MMO parlés 3D (`stage3d`)** et les **Clips Musicaux 3D (`music3d`)**, et réapprovisionne automatiquement la file sans jamais tomber à sec.

```bash
systemctl --user status lbg-content-daily.timer
packages/cortex/.venv/bin/python tools/studio_content_engine/cron_daily_publisher.py
```

### 5. Vidéos Longues YouTube 16:9 (4 à 15 min — Style Kiara + Lia 3D)
Génère des épisodes complets en `1920×1080` @ 30.00 FPS avec **plateau Hero + Split-Screen (1/3 Lia 3D + 2/3 slides techniques animées : comparatifs, schémas d'architecture, terminaux bash, barres de benchmarks)**, chapitres YouTube horodatés et miniature `1280×720` automatique.

1. **Mode Brouillon validé par défaut** (génère `script_long.json` + `BROUILLON_A_VALIDER.md` pour relecture avant rendu) :
   ```bash
   packages/cortex/.venv/bin/python tools/studio_content_engine/longform_bot.py --minutes 6
   ```
2. **Rendu HD 16:9 après validation du brouillon** :
   ```bash
   packages/cortex/.venv/bin/python tools/studio_content_engine/longform_bot.py --render tools/studio_content_engine/output/long_xxx --youtube
   ```
3. **Mode `--auto` d'une traite** (écriture → voix → miniature HD → rendu 16:9 → publication YouTube) :
   ```bash
   packages/cortex/.venv/bin/python tools/studio_content_engine/longform_bot.py --topic "Mon sujet IA locale" --minutes 8 --auto --youtube
   ```

---

## Spécifications Techniques

| Paramètre | Valeur |
|---|---|
| **Résolution** | 1080 × 1920 (Vertical 9:16) |
| **Framerate** | 30 FPS |
| **Codec Vidéo** | H.264 (`libx264`, High Profile, CRF 18–19, `yuv420p`) |
| **Codec Audio** | AAC LC 256 kb/s, 44.1 kHz stéréo |
