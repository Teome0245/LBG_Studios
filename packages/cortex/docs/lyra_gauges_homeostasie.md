# Jauges Lyra — moteur d’origine + homéostasie

**UI** : http://192.168.0.100:5174/ → colonne droite **Lyra — Personnalisation** (`LyraPanel.vue`)  
**Face** : `face_rig` sous le header du panneau (même contrat Pilot/MMO).

## Où vit la gestion des jauges (projet d’origine)

| Couche | Fichier | Rôle |
|--------|---------|------|
| **Moteur** | `_archive/LBG_IA/.../lyra_engine_v2.py` (`LyraEngineV2`) | Règles énergie / transfert / HAL / buff |
| **Tick** | `lifecycle.py` → `lyra_tick_loop` | `apply_decay()` **toutes les 30 s** |
| **API** | `routers/lyra.py` | `GET /lyra/state`, `POST /lyra/update` |
| **UI** | `LyraPanel.vue` (+ `LyraWidget.vue`, `/lyra`) | Affiche + ± manuels |

Jauges UI (0–100) : **`chaleur` · `energie` · `patience` · `confiance`**.

### Règles correctrices (v2.3.1)

D’après `LyraEngineV2` :

- Énergie décroît ~100 % en 4 h
- Si **énergie &lt; 30 %** **et** un donneur ≥ 40 % : auto-transfert (1 % → +3 % énergie)
- Si **une jauge &lt; 35 %** : **repos** +4 % / tick (30 s) vers 50 % — **anti-zéro**, sans cannibaliser
- Si **énergie &gt; 90 %** : toutes les 10 min, +5 % chaleur / patience / confiance
- Si **chaleur &lt; 20 %** → profil HAL9000 ; &gt; 30 % → retour normal

Sans le plancher, le transfert seul mangeait chaleur/patience/confiance jusqu’à ~26 % puis vers 0 (observé 2026-08-14, uptime Lyra ~22 h).

C’est l’orchestrateur (tick backend `.100`) qui maintient la bande saine. Pas de mission Team « fill gauges ».

## Cortex (complément, pas doublon)

| Mécanisme | Rôle |
|-----------|------|
| `packages/cortex/backend/services/lyra_regulator.py` | Sur routes Pilot (`kind=assistant`) : remonte energie/patience/confiance si &lt; 50 (cooldown 60 s, `LBG_LYRA_REGULATOR_ENABLED=1`) |
| Brain / proactive | Humeur / tension — **signale**, ne remplace pas `LyraEngineV2` |
| Team (conductor, jobs) | **Pas** une boucle de correction des jauges — laisser le tick + regulator |

Monde MMO (`hunger/thirst/fatigue`) = autre échelle (`lyra_engine.gauges` / `lyra_bridge`) — ne pas confondre avec le panneau Personnalisation.

## Face ↔ jauges (5174)

Sur chaque poll `/lyra/state` (5 s) :

- chaleur basse / patience basse → expression `angry` / mood `tense`
- énergie très basse → `sad` / `waiting`
- énergie + chaleur hautes → `happy` / `curious`
- sinon → `neutral` / `serene`

## Recommandation produit

1. **Garder** le tick `LyraEngineV2` comme vérité temps-réel de `:5174`
2. **Ne pas** créer une mission Team « fill gauges » en boucle
3. Optionnel : exposer un endpoint Team **lecture seule** des jauges + alerte si HAL / énergie &lt; 15 % (boost humain : cookie / pause / compliment déjà dans le moteur)
4. Assets Infographiste → `face_rig/assets/lyra_assistant/` (Pilot + `frontend/public/face_rig/` Orch UI)
