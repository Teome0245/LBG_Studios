# Cerveau 3D (Studio Brain 3D) — Campus Team

Visualisation 3D volumétrique cybernétique du Studio Brain et du réseau synaptique de l'IA (Inspiration @ccodelabfr — *"J'ai donné un cerveau à mon IA 🧠⚡"*).

Accessible sur le Pilot Web via l'URL :
`#/team/brain` (ou `#/brain`)

## Architecture & Caractéristiques

- **Moteur 3D procédural** : Three.js WebGL autonome (`brain_3d.js`), 0 asset externe binaire.
- **Modèle anatomique stylisé** :
  - Double hémisphère avec scissure centrale, circonvolutions gyri/sulci, tronc cérébral et cervelet.
  - ~1500 particules neuronales luminescentes colorées par région.
  - Réseau synaptique d'axones interconnectés (`LineSegments` en blending additif).
  - Train d'impulsions synaptiques circulantes en temps réel.
- **6 Pôles Cognitifs Interactifs** :
  1. ⚡ **Cortex Frontal** : Orchestrateur & Planification des intentions (`intent`).
  2. 💖 **Système Limbique** : Homéostasie en direct (`confidence`, `curiosity`, `stress`, `fatigue`).
  3. 📚 **Hippocampe & RAG** : Corpus philosophique Mec Chill / Stoïcisme et grounding d'atelier.
  4. 🤖 **Noyau Campus & Fleet** : Supervision des agents de la Team.
  5. 🌐 **Perception Monde** : Simulation Godot Prime `.246:8787` et signaux SWG.
  6. 🎭 **Lobe Compagnon** : Lyra Desktop Pet SDS `.10` et présence.
- **Télémétrie en direct** : Polling automatique sur `/v1/pilot/orchestrator/brain/status`.
- **Interactivité** :
  - Rotation orbitale 360° souris/touch, zoom molette.
  - Survol Raycaster avec tooltips HUD.
  - Clic sur un pôle pour focaliser la caméra et afficher la fiche détaillée.
  - Bouton *Impulsion Synaptique* (onde de stimulation visuelle).
  - Filtres d'hémisphères (Global, Analytique, Émotionnel/RAG).
