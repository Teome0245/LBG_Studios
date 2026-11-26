# Méthodologie de Développement Solo/Micro-Équipe — MMO Prime (O2)

> **Boussole & Garde-fous Anti-Abandon**  
> *Inspiré des retours d'expérience du jeu indé (Taku @Taku_GD, Stardew Valley, SWG Pre-CU, T4C) et adapté à l'organisme LBG Studios (Gladys + Prime Godot 4.6).*

---

## 1. Le Paradoxe du « MMO Solo »

Dans l'industrie du jeu vidéo, l'adage est catégorique : **« Ne développe jamais un MMORPG seul »**.  
95 % des projets de MMO indés meurent pour quatre raisons fondamentales :
1. **Le Scope Creep infini** : Vouloir rivaliser avec World of Warcraft ou Star Citizen en codant 40 sous-systèmes incomplets.
2. **Le piège de l'Over-Engineering réseau** : Passer deux ans sur une architecture micro-services, des passerelles complexes ou du Rust prématuré avant même d'avoir un personnage qui bouge.
3. **Le « Monde Fantôme »** : Un MMO nécessite des centaines de joueurs pour être amusant. Sans communauté le jour 1, le monde est mort et les premiers testeurs partent.
4. **L'épuisement du Dev Solo** : Devoir gérer simultanément le code serveur, le client 3D, les animations, le son, le game design, les tests QA et le marketing.

---

## 2. Les 4 Piliers LBG pour Briser la Malédiction

Pour que **Prime** reste un projet vivant, fini et jouable au quotidien, l'équipe applique 4 principes stricts :

### Pilier 1 : Le Core Loop Sacré (Une boucle fermée, pas 50 systèmes)
* Comme le rappelle Taku, **une seule mécanique centrale forte suffit** si elle est satisfaisante.
* Le cœur de Prime est l'**interdépendance sociale et économique** (héritée de *Star Wars Galaxies* et *T4C*) :
  $$\text{Exploration / Récolte} \longrightarrow \text{Artisanat de composants} \longrightarrow \text{Échange / Cantina (Buffs & Karma)}$$
* **Règle d'or** : Tout ajout de feature (combat, quête, météo) doit alimenter cette boucle, sans jamais la diluer ni inventer des systèmes satellites non finis.

### Pilier 2 : Le Runtime Vivant & Frugal (Zéro usine à gaz)
* Remplacement des 40 micro-serveurs legacy par **un binaire unique Godot 4.6 Headless** (`packages/prime-hub`) sur `.246:8787`.
* Persistance déterministe via **SQLite local**, consommant moins de **800 Mo de RAM**.
* **Règle d'or** : Le serveur doit tourner H24 sur notre LAN. Si une feature casse le runtime ou nécessite une infrastructure complexe inaccessible sur un serveur modeste, elle est rejetée.

### Pilier 3 : Le Remède au Monde Vide (Joueurs IA - O3 & PNJ MiniMind)
* Prime ne dépend pas de l'arrivée massive de joueurs humains pour avoir du sens.
* **36 PNJ autonomes** animés par notre micro-modèle local (`prime-npc:25m` MiniMind) ont des routines de vie (travail aux vaporateurs GX-8, repos, loisir à la cantina).
* **10 bots Joueurs IA autonomes** parcourent le monde, minent des ressources et interagissent selon les mêmes règles physiques et économiques que les humains (sans triche).
* **Résultat** : Même pour un joueur solo connecté à 3 heures du matin, **le monde est habité et organique**.

### Pilier 4 : Gladys comme Co-développeuse (O1)
* Le dev solo ne doit pas s'épuiser sur les tâches répétitives.
* **Tests de non-régression instantanés** : `tools/ci_godot_headless.sh` teste la navigation 3D et la simulation en 3 secondes.
* **Studio Content Engine** : Lia produit les devlogs, vidéos YouTube et captures de suivi de manière automatisée.
* **Audit Nocturne** : Ronde quotidienne de vérification des services LAN sans intervention humaine.

---

## 3. Garde-fous Opérationnels (Checklist avant tout commit O2)

Avant d'ajouter du code dans `packages/prime-client` ou `packages/prime-hub`, vérifier :

- [ ] **Testabilité immédiate** : Est-ce vérifiable en moins de 30 secondes dans le client ou via `client_modular_selftest.gd` ?
- [ ] **Impact mémoire / CPU** : La feature reste-t-elle compatible avec notre enveloppe sobre (serveur sans GPU dédié) ?
- [ ] **Pas de LLM libre sur les règles dures** : L'économie, les dégâts, le craft et la réputation restent 100 % déterministes (code GDScript / SQLite).
- [ ] **Respect de la Direction Artistique Multiverse** : Technologie patinée / bricolée (Gunnm/SWG), alchimie / Chi (FMA/T4C), et ton pragmatique.
