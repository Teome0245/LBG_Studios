# Studio Musical & Vocal IA — LBG Studios (0 € Cloud)

Ce module fournit un pipeline complet de création musicale, écriture de paroles, synthèse vocale chantée et mastering studio pour l'incarnation de Lia et l'Atelier de Chorégraphie 3D.

---

## 1. Architecture Générale (100% Local)

```
[Prompt Thème / Style]
        │
        ├──▶ 1. Écriture des Paroles : Ollama (.110 / .111) [Qwen 2.5 14B / 3B]
        │       Structure multi-strophes (Couplets + Refrain avec montée en énergie)
        │
        ├──▶ 2. Composition Instrumentale : MusicGen Small (PyTorch CPU / GPU)
        │       Génération par segments de 30s max avec crossfade studio automatique
        │
        ├──▶ 3. Synthèse Vocale de Lia : Edge-TTS (Vivienne Neural)
        │       Modulation de cadence, pitch et volume selon le rôle de la strophe
        │
        ├──▶ 4. Mixage & Mastering : FFmpeg
        │       Ducking dynamique, égalisation de présence (+3dB @ 3kHz), compression
        │       Effets de timbre : Diva Scénique, Cyber Vocoder, Autotune, Whisper
        │
        └──▶ 5. Déploiement Automatique
                - VM Atelier (.140) : Nginx `/audio/` + mise à jour `choreographer.html`
                - Windows (.10) : Agent Desktop port 5005
```

---

## 2. Bibliothèque des 7 Styles Musicaux Calibrés

| Identifiant | Style d'affichage | BPM | Description & Ambiance |
| :--- | :--- | :--- | :--- |
| `cyberpunk` | **Cyberpunk Club** | **128** | Basses lourdes, kicks électro percutants, synthés néon |
| `tatooine_sunset` | **Tatooine Sunset Groove** | **124** | Électro désertique hypnotique, percussions ethniques, flûte synth |
| `synthwave` | **80s Retro Synthwave** | **115** | Ambiance Outrun rétro, batterie gated reverb, synthés analogiques |
| `kpop_energy` | **K-Pop Future Dance** | **130** | Électro pop brillante, basse bondissante, rythmique pétillante |
| `dark_techno` | **Dark Industrial Techno** | **132** | Techno d'entrepôt sombre, kicks 4/4 lourds, basses acides |
| `chill_lofi` | **Lo-Fi Night Chill** | **85** | Vinyle, accords de piano Rhodes doux, basse chaude feutrée |
| `french_touch` | **French Touch Funk** | **120** | Basse slappée groovy, guitares filtrées, house dansante |

---

## 3. Timbres Vocaux de Chant (Lia)

1. **Diva Scénique (`diva`)** : Clarté studio, égalisation brillance à 3 kHz (+3 dB), compression dynamique douce (`threshold=-12dB`, `ratio=4`).
2. **Cyber Vocoder (`vocoder`)** : Effet robotique style Daft Punk via flanger dynamique (`delay=4:depth=2:regen=50`) et égalisation passe-bande à 1.5 kHz.
3. **Autotune Pop (`autotune`)** : Harmoniques aiguës boostées à 4.5 kHz et compression dure (`threshold=-14dB`, `ratio=5`).
4. **Intime Whisper (`whisper`)** : Filtrage passe-bas à 4.5 kHz, égalisation de proximité à 250 Hz et cadence ralentie.

---

## 4. Utilisation

### A. Depuis l'Atelier 3D (`choreographer.html`)
1. Ouvrir l'Atelier : [http://192.168.0.140/choreographer.html](http://192.168.0.140/choreographer.html).
2. Cliquer sur l'onglet **`🎵 Studio IA`** dans le panneau de gauche.
3. Choisir le style musical, le timbre vocal et la durée (15s, 30s ou 60s).
4. Cliquer sur **`⚡ Composer & Charger le Morceau`** :
   - La barre de progression affiche l'état en direct.
   - Dès la fin du mastering, le morceau est injecté dans le lecteur et synchronisé avec la Timeline.

### B. En Ligne de Commande (CLI)
Depuis le venv audio :
```bash
./.venv_audio/bin/python3 tools/studio_music_generator_v3.py \
  --style synthwave \
  --voice vocoder \
  --duration 30 \
  --title "Lia - Neon Overdrive"
```

### C. Serveur API HTTP (Port 8099)
Le serveur démon `tools/studio_music_api.py` tourne en arrière-plan sur `.143` :
- `GET /api/music/styles` : Retourne la liste des styles et timbres.
- `POST /api/music/generate` : Déclenche la génération en thread non-bloquant.
- `GET /api/music/status` : Suivi d'état et progression en temps réel.
- `GET /api/music/tracks` : Catalogue des morceaux audio produits.
