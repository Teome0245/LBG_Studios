# Studio Content Engine V3.3 — Usine Autonome YouTube (Shorts + Longs 16:9) & TikTok

Pipeline de production et publication vidéo 3D **100 % local** (zéro abonnement Cloud récurrent) propulsé par **Lia** (`Compagnon.vrm` sous Three-VRM WebGL déterministe à `30.00 FPS`), couvrant l'ensemble de l'écosystème **LBG Studios** (O1 Compagnon/Gladys, O2 MMO Prime Godot 4.6 SWG+T4C, O3 Joueurs IA, Hardware & Self-Hosting).

---

## 1. Cadencement Automatique & Budget Quota API YouTube (`10 000 u/jour`)

Les 3 timers utilisateur `systemd` (`~/.config/systemd/user/`) orchestrent la chaîne `@LBG-p8k` et le compte TikTok en parallèle sans jamais dépasser le plafond gratuit de **10 000 unités/jour** de YouTube Data API v3 (reset à 09h00 CET) :

| Timer `systemd` | Fréquence & Horaires | Format produit | Cibles de diffusion | Coût Quota YouTube |
|---|---|---|---|---|
| `lbg-content-daily.timer` | **5× / jour** (`09h30, 12h15, 15h30, 18h30, 21h15`) | Shorts 9:16 (`1080×1920`, 30 FPS) alternant `stage3d` (Tech/MMO parlés) et `music3d` (Clips chorégraphiés) | **YouTube Shorts + TikTok en `//`** (avec retry Playwright auto) | `5 × 1 600 = 8 000 u` |
| `lbg-longform-weekly.timer` | **3× / semaine** (`Mar, Jeu, Dim à 16h30`) | Vidéos Longues 16:9 (`1920×1080`, 7–10 min, style `@KiaraIAFR` + Lia 3D) + Miniature `1280×720` + Chapitres | **YouTube Long-Form** | `1 600 + 50 = 1 650 u` *(jours dédiés → total `9 650 u`)* |
| `lbg-music-weekly.timer` | **1× / semaine** (`Samedi à 13h45`) | **1 Clip Musical Original inédit** : Master `60s` 16:9 complet + **2 Shorts `30s`** (*Part 1* & *Part 2*) | **YouTube 16:9** (Samedi) + **2 Shorts YouTube/TikTok** dans la file | `1 600 + 50 = 1 650 u` *(Samedi → total `9 650 u`)* |

Vérifier l'état des planificateurs :
```bash
systemctl --user list-timers --no-pager | grep lbg-
```

---

## 2. Formats & Briques Techniques

### A. Shorts Verticaux 9:16 (`stage3d` & `music3d`)
- **Rendu déterministe `30.00 FPS` zéro saccade** ([stage3d_compositor.py](stage3d_compositor.py) + [assets/stage3d/render_stage3d.html](assets/stage3d/render_stage3d.html)) : horloge virtuelle verrouillée (`1/30 s`) streamant chaque frame JPEG sur WebSocket vers `ffmpeg -f image2pipe`.
- **`stage3d` (Shorts Tech / MMO parlés)** : gestuelle mocap `.vrma` sémantique (`select_semantic_tech_motion`), sous-titres karaoké courts (2–3 mots pop néon en zone sûre), voix de Lia + nappe synthwave discrète (`-17.5 dB`) + égaliseur 24 bandes.
- **`music3d` (Clips Musicaux / Chorégraphies 3D)** : micro cyber 3D en main, chorégraphies mocap `.vrma` (Maraschino, Bellydance, Hip-Hop, danses natives SWG Poplock/Moonwalk, Capoeira) sur nos masters originaux et sur `custom_music_tracks.json`.
- **TikTok en parallèle garanti** ([cron_daily_publisher.py](cron_daily_publisher.py)) : inspection du statut JSON de `content_bot.py --youtube --tiktok`, traçabilité `tiktok_status` dans `topics_backlog.json` et **second essai automatique direct** via Playwright headless (`tiktok_playwright_direct.py`, `tiktok_cookies.txt`) en cas d'échec réseau initial.

### B. Vidéos Longues 16:9 (`4 à 15 min` — Style Kiara + Lia 3D)
- **Plateau TV / Ingénierie 16:9** ([longform_bot.py](longform_bot.py) + [assets/stage3d/render_longform_16x9.html](assets/stage3d/render_longform_16x9.html)) :
  - Barre supérieure de progression des chapitres en temps réel.
  - Alternance **Plateau Hero** (intro/conclusion) et **Split-Screen 1/3 Lia 3D + 2/3 Slides Techniques Animées** (`comparison` 2 colonnes, `diagram` flux d'architecture, `terminal` bash colorisé, `benchmarks` barres animées).
  - Génération automatique de la **miniature HD `1280×720`** (`thumbnail_1280x720.png`) et de `youtube_description.txt` avec **horodatages exacts des chapitres** (`00:00`, `00:42`…).
- **Sources Officielles (E-E-A-T) & Transparence Matérielle** ([longform_script_builder.py](longform_script_builder.py)) :
  - Chaque épisode cite ses sources vérifiées (`📚 SOURCES OFFICIELLES & DOCUMENTATION TECHNIQUE` : ArXiv Qwen3 MoE, Dell PowerEdge R720 Technical Guide, Godot Engine 4.6 Docs, Proxmox VE Docs, SQLite WAL, RFC Stalwart Mail).
  - Transparence sur les coûts réels du Homelab (ex. Épisode 2 : investissement initial du **Dell PowerEdge R720 reconditionné ~150 €** + électricité vs ~960 €/an de SaaS Cloud).
  - Calibrage à **7–10 minutes** sur les guides techniques (`longform_backlog.json`) pour maximiser le *Watchtime* et l'éligibilité aux coupures *mid-roll* (≥ 8 min).

### C. Usine Musicale Originale Hebdomadaire (`cron_weekly_original_clip.py`)
- Appelle `tools/studio_music_generator_v3.py` via `.venv_audio/bin/python` pour générer chaque semaine un morceau inédit de `60 s` (instrumental MusicGen + paroles originales Ollama + chant Lia mixé).
- Publie le clip complet `60 s` en 16:9 avec miniature `1280×720` sur YouTube et injecte automatiquement **2 extraits verticaux de `30 s`** dans `custom_music_tracks.json` et `topics_backlog.json`.

### D. Prononciation & Phonétique TTS (`voice_engine.py`)
- Table `PHONETIC_ORAL_RULES` corrigeant les pièges phonétiques de `fr-FR-VivienneMultilingualNeural` uniquement dans le flux audio envoyé au TTS (sans altérer le texte affiché à l'écran) :
  - `0€` / `0 €/mois` / `zéro euro(s)` → `« zéro centime (par mois) »` (élimine le hiatus *« héro euros »*),
  - `150€` → `« 150 euros »`,
  - Francisation orale de `MoE` (`M O E`), `VRAM` (`vé-rame`), `CPU`, `GPU`, `PCIe`, `WAL`, `4x4`, `P2P`, `homelab`, `self-hosting`.

### E. Exécution Hybride GPU `.10` ↔ `.143` (& Upgrade R720 prévu 3–4 déc. 2026)
- Si le PC Windows `.10` est allumé **et** inactif depuis ≥ 3 minutes (`LBG_WIN10_MIN_IDLE_SEC=180`), rendu GPU matériel invisible (`chrome --headless=new --use-angle=d3d11`).
- Sinon, repli automatique transparent sur `.143` (`Xvfb` + Chromium WebGL + FFmpeg — qui passera en accélération matérielle NVENC/WebGL H24 lors du montage de la GTX 1050 Ti sur le R720 `.201`).

---

## 3. Commandes Manuelles Rapides

### Générer et publier un Short 3D (YouTube Shorts + TikTok)
```bash
packages/cortex/.venv/bin/python tools/studio_content_engine/content_bot.py \
  --style stage3d --topic "Mon sujet Tech ou MMO" --youtube --tiktok
```

### Générer un Clip Musical 3D court
```bash
packages/cortex/.venv/bin/python tools/studio_content_engine/content_bot.py \
  --style music3d --music-preset nexura_drop_highlight --youtube --tiktok
```

### Vidéo Longue 16:9 — Mode Brouillon Humain (par défaut) puis Rendu
```bash
# Étape 1 : génère script_long.json + BROUILLON_A_VALIDER.md
packages/cortex/.venv/bin/python tools/studio_content_engine/longform_bot.py \
  --topic "visite guidée de notre infrastructure Gladys" --minutes 8

# Étape 2 : rendu HD 16:9 + miniature + publication YouTube
packages/cortex/.venv/bin/python tools/studio_content_engine/longform_bot.py \
  --render tools/studio_content_engine/output/long_xxx --youtube
```

### Vidéo Longue 16:9 — Mode `--auto` de bout en bout
```bash
packages/cortex/.venv/bin/python tools/studio_content_engine/longform_bot.py \
  --topic "Mon sujet IA locale" --minutes 8 --auto --youtube
```

### Lancer manuellement un nouveau Clip Musical Original (1 Long 60s + 2 Shorts 30s)
```bash
packages/cortex/.venv/bin/python tools/studio_content_engine/cron_weekly_original_clip.py --genre electro_cyber
```

---

## 4. Spécifications d'Export

| Format | Résolution | Framerate | Vidéo | Audio |
|---|---|---|---|---|
| **Shorts / TikTok (9:16)** | `1080 × 1920` | `30.00 FPS` constant | H.264 High (`CRF 18`, `yuv420p`, `+faststart`) | AAC LC `192–256 kb/s`, `44.1 kHz` stéréo |
| **Long-Form & Clips 16:9** | `1920 × 1080` + Miniature `1280 × 720` | `30.00 FPS` constant | H.264 High (`CRF 19`, `yuv420p`, `+faststart`) | AAC LC `192 kb/s`, `44.1 kHz` stéréo |
