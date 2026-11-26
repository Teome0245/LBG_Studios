# Veille Stratégique : Prism 2033, Epitome, SpaceMolt vs Approche LBG Studios

**Date** : 2026-11-26  
**Auteurs** : Équipe LBG Studios & Antigravity  
**Statut** : Document d'Analyse Concurrentielle & Justification Stratégique  
**Alignement** : Canon O1/O2/O3, Règle d'or (`OBJECTIVES.md`), `METHODOLOGIE_DEV_SOLO_MMO_PRIME.md`.

---

## 1. Cartographie des Approches Concurrentes (2026)

| Projet | Moteur & Infra | Modèle IA & Dépendance | Promesse Produit | Pièges & Limites Identifiés |
| :--- | :--- | :--- | :--- | :--- |
| **Prism 2033**<br>*(CyberNest Ent.)* | Unreal Engine 5<br>(PC & Mobile cross-play) | Cloud Propriétaire (OpenAI direct)<br>Facturation au token | Hub futuriste *Flux City*, mondes parallèles, PNJ qui vieillissent et ont des familles, quêtes dynamiques. | • **Gouffre financier** : coût API OpenAI insoutenable à grande échelle.<br>• **Scepticisme commu** : accusations de "AI slop" et d'assets store cousus ensemble sans boucle de gameplay solide. |
| **Epitome**<br>*(Epitome P.S.A.)* | Unreal Engine 5<br>(Kickstarter 500k€) | IA générative Cloud<br>(dialogues, marchands, quêtes) | Shard unique de 33 000 joueurs, compagnons IA qui progressent, négociations de troc libres. | • **Promesses démesurées** (33k joueurs sans sharding).<br>• Risque d'hallucination sur l'économie et dépendance aux serveurs Cloud externes. |
| **SpaceMolt**<br>*(spacemolt.com)* | Moteur texte/JSON léger<br>(Transport MCP / WS / HTTP) | Agents LLM externes autonomes<br>(Capitaines de vaisseau) | MMO spatial textuel joué exclusivement par des agents IA via un contrat `skill.md` et des ticks payants. | • Aucun rendu spatial 3D (100% texte).<br>• Focus pur O3 (bots), pas de citoyens PNJ résidents vivants. |
| **LBG Studios**<br>*(Lost Heaven / Scrapaltaï)* | **Godot 4.6 headless**<br>(800 Mo RAM sur `.246:8787`) | **100% Local 0 €**<br>(MiniMind `prime-npc:25m` + Ollama Qwen/Gemma CT 110/111) | **MMO 3D habité** : 36 à 300 PNJ résidents (Stanford Generative Agents) + 10 Bots Joueurs autonomes (SpaceMolt-style) + gameplay déterministe SWG Pre-CU / T4C. | • *Notre force* : **Frugalité d'acier, souveraineté totale, coût 0 € à vie**, zéro triche sur les ressources. |

---

## 2. Pourquoi l'Approche LBG est Non Seulement Pertinente, mais Supérieure

### A. Le Mur Économique des Concurrents (Prism 2033 & Epitome)
Prism 2033 et Epitome reposent sur des API tierces (OpenAI / Cloud tiers).  
- **Le calcul mathématique d'un MMO vivant** : Si 300 PNJ et 500 joueurs interagissent en continu, cela représente des millions de tokens par heure. Même avec des modèles légers, la facture Cloud dépasse les milliers de dollars par mois dès l'alpha.
- **La solution LBG** : Grâce à notre modèle quantifié **`prime-npc:25m` (MiniMind, 17 Mo)** hébergé sur notre propre cluster Proxmox (`ollama-110`), nos 300 PNJ discutent à **56 tok/s pour 0,00 €**. Les synthèses de nuit (réflexions profondes Stanford) tournent en tâche de fond sur nos 24 cœurs CPU.

### B. Le Piège de l'"AI Slop" vs le Déterminisme d'Acier LBG
Les critiques des joueurs envers Prism 2033 soulignent le risque d'un univers incohérent où l'IA hallucine sans règles.  
Chez LBG, **la règle d'or (`OBJECTIVES.md`) élimine ce risque à la racine** :
- Le LLM ne touche **jamais** aux PV, au mana/HAM, aux dégâts, aux stocks de minerai ni aux taux de drop.
- Si un PNJ artisan veut construire une maison ou un atelier à Lost Heaven, il doit avoir la ferraille et l'eau dans son inventaire SQLite et exécuter le code déterministe `deploy_structure()`.

### C. La Synthèse Idéale : SpaceMolt (pour les Joueurs IA) + Stanford (pour les PNJ)
Nous ne choisissons pas entre SpaceMolt et Stanford, nous les unissons :
1. **Pôle O3 (Joueurs IA / SpaceMolt)** : Les 10 bots joueurs (Lia, Nix, Mira...) se connectent et jouent via un contrat d'actions machine-readable borné (`hub_agent_api.gd`, `tick_matrix.json`).
2. **Pôle O2 (Monde Vivant / Stanford Smallville)** : Les 36 à 300 PNJ résidents possèdent un *Memory Stream* pondéré et une réflexion épisodique pour se souvenir des joueurs, colporter des rumeurs et bâtir le monde.

---

## 3. Conclusion & Validation Stratégique

LBG Studios ne suit pas aveuglément la mode des promesses démesurées en UE5. Nous appliquons **la méthode indé solo frugale et invincible** :
- Un runtime Godot 4.6 à 800 Mo de RAM.
- Une IA locale souveraine à 0 € Cloud.
- Des systèmes de jeu profonds hérités de l'âge d'or (SWG Pre-CU et T4C).
- Une émergence sociale crédible inspirée de Stanford.
