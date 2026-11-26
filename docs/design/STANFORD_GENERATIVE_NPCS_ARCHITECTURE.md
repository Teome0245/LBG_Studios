# Architecture : Stanford Generative Agents pour les PNJ de Lost Heaven

**Date** : 2026-11-26  
**Auteurs** : Équipe LBG Studios & Antigravity  
**Statut** : Approuvé — Implémentation en cours  
**Inspiration canonique** : Joon Sung Park et al. (Stanford / Google, 2023) — *Generative Agents: Interactive Simulacra of Human Behavior* (Smallville 25 agents).

---

## 1. Objectifs & Philosophie LBG

Appliquer les mécanismes cognitifs des *Generative Agents* aux PNJ de Lost Heaven pour créer un monde vivant et émergent, tout en respectant les **gardes-fous d'acier** de LBG Studios :

1. **Zéro hallucination sur le gameplay dur (`OBJECTIVES.md`)** :
   - Les transactions économiques, l'inventaire, les points de vie, les dégâts de combat et les quêtes restent sous l'autorité absolue et déterministe du moteur Godot 4.6 (`packages/prime-hub`) et de SQLite.
   - Le système génératif contrôle exclusivement la **mémoire épisodique**, la **perception sociale**, les **réflexions d'ambiance** et la **répartie conversationnelle**.
2. **Souveraineté & Coût 0 € Cloud** :
   - Stockage local immédiat dans `prime_hub.sqlite3` (WAL non bloquant).
   - Inférence locale sur nos clusters Proxmox :
     - Modèle lourd de réflexion / nuit : Qwen 30B / Gemma sur CT 110 (`ollama-110`).
     - Modèle réactif de dialogue : `prime-npc:25m` (MiniMind) ou Gemma 4B local.

---

## 2. Les 3 Piliers de l'Architecture Cognitive

### Pilier 1 : Le Memory Stream (Flux Mémoriel Continu)
Chaque interaction, observation ou événement impliquant un PNJ génère un enregistrement mémoriel :
- `npc_id` : Identifiant du PNJ (ex: `npc:core3_barman_jax`).
- `timestamp` : Horodatage unix.
- `event_type` : `dialogue`, `observation`, `reflection`, `transaction`, `rumor`.
- `content` : Description textuelle de l'événement.
- `importance` : Note de 1 à 10 évaluant l'impact émotionnel ou social de l'événement.
- `tags` : Mots-clés pour le filtrage thématique rapide (ex: `water`, `caravan`, `bounty`, `nix`).

### Pilier 2 : Le Retrieval Pondéré (Formule Stanford)
Lors d'une interaction (joueur qui parle, croisement d'un autre PNJ, décision de routine), le PNJ extrait les $K$ souvenirs les plus saillants selon la formule de Stanford :

$$\text{Score}(m) = w_r \cdot \text{Récence}(m) + w_i \cdot \text{Importance}(m) + w_s \cdot \text{Pertinence}(m)$$

- **Récence** : $e^{-\lambda \cdot \Delta t}$ où $\Delta t$ est le temps écoulé depuis l'événement.
- **Importance** : Note intrinsèque du souvenir normalisée sur $[0, 1]$.
- **Pertinence** : Score de correspondance textuelle/lexicale (FTS5 ou Jaccard/overlap de mots-clés) entre la requête actuelle et le contenu du souvenir.

### Pilier 3 : Le Cycle de Réflexion (Pensées d'Ordre Supérieur)
Quand la somme des scores d'importance des souvenirs récents non réfléchis dépasse un seuil (ex: $\sum \text{importance} \ge 35$), ou lors de la transition vers le repos/sommeil :
1. Le PNJ synthétise ses dernières observations via une requête batch sur Ollama.
2. Une nouvelle entrée de type `reflection` est insérée (ex: *« Les nomades du Ksar et la milice de Zalem semblent tous deux inquiets des raids près du canyon »*).
3. Cette pensée d'ordre supérieur alimente les futures conversations et peut déclencher une diffusion de rumeurs via `HubWiki`.

---

## 3. Calendrier de Déploiement Progressif en Cohortes

Conformément à la directive produit :

| Phase | Durée | Nombre de PNJ | Périmètre / PNJ Inclus |
| :--- | :--- | :--- | :--- |
| **Phase 1 (Pilote)** | **2 semaines** | **10 PNJ** | **Les 10 PNJ Emblématiques de Lost Heaven** :<br>1. Jax Moro (`npc:core3_barman_jax`) — Barman La Perle<br>2. Daan Oth (`npc:core3_daan_oth`) — Missions & Survie<br>3. Kell Asa (`npc:core3_artisan_trainer_c`) — Atelier d'artisanat<br>4. Tobin Ress (`npc:core3_brawler_trainer_c`) — Entraîneur combat<br>5. Odo Merr (`npc:core3_medic_trainer_c`) — Clinique / Médecine<br>6. Yara Nis (`npc:core3_scout_trainer_c`) — Pistes & prospection<br>7. Capitaine Vael (`npc:capitaine_vael`) — Milice Avant-poste Zalem<br>8. Soren Kray (`npc:mecanicien_soren`) — Mécanique Zalem<br>9. Ancien Nadir (`npc:ancien_nadir`) — Chef Ksar Nomade<br>10. Rumeuriste (`npc:rumeuriste`) — Marché de Lost Heaven |
| **Phase 2** | **1 semaine** | **+10 PNJ (Total 20)** | Miran Sael, Talen Ress, Scribe, Sergent de rue, Videur, Fermier Valen, Durn Vane, Sela Kore, Klik'Tik, U'Ror'K |
| **Phase 3** | **1 semaine** | **+10 PNJ (Total 30)** | Artisans relais, Artiste de scène, Kane Rill, Agents circulation, Scientifique Fel'Rani, etc. |
| **Phase 4** | **1 semaine** | **Flotte Complète (36 PNJ + 10 Bots)** | Généralisation à tous les résidents et joueurs IA autonomes. |

---

## 4. Schéma de Données SQLite (`prime_hub.sqlite3`)

```sql
CREATE TABLE IF NOT EXISTS npc_memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    npc_id TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    event_type TEXT NOT NULL DEFAULT 'observation', -- observation, dialogue, reflection, rumor
    content TEXT NOT NULL,
    importance INTEGER NOT NULL DEFAULT 5, -- échelle 1-10
    reflected INTEGER NOT NULL DEFAULT 0, -- 0 = brut, 1 = déjà intégré dans une réflexion
    tags TEXT NOT NULL DEFAULT '' -- mots-clés séparés par des virgules
);

CREATE INDEX IF NOT EXISTS idx_npc_memories_lookup 
ON npc_memories(npc_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_npc_memories_reflection 
ON npc_memories(npc_id, reflected, importance);
```
