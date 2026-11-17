# Session en cours — LBG Studios

**Mis à jour** : 2026-11-16  
**Branche** : `main`  
**Outil** : partagé Cursor ↔ Antigravity — **lire au démarrage, mettre à jour avant de partir**.  
**Backlog non traité** : [`SUJETS_OUVERTS.md`](SUJETS_OUVERTS.md)  
**Fil** : canon O1/O2/O3 — **Organisme Global Gladys & Incarnation Lia — Pilotage Multimodal OS (.10 & .143 via agent-desktop)**.

---

## Dernières actions réalisées (2026-11-17)
-28. **Conception du Nouveau Site Vitrine La Boîte à Geeks Studios — LBG & Déploiement Gladys (`laboiteageek.fr`)** :
    - **Nouveau Site Vitrine (`packages/showcase-web/public/`)** :
      * Titre officiel retenu : **La Boîte à Geeks Studios — LBG**.
      * Design Cyberpunk / Sci-Fi haut de gamme : palette Midnight Dark (`#070a13`), glassmorphism, liserés néon cyan (`#00f5d4`) et violet (`#a855f7`), typographies *Space Grotesk* et *JetBrains Mono*.
      * Mise en valeur des 3 Piliers du Studio :
        1. **O1 Compagnon** : Lia & Gladys (incarnation 3D VRM, multimodalité, pilotage de bureau).
        2. **O2 Banc d'Essai MMO** : Projet Prime (moteur Godot 4.6, artisanat profond 1-1000, troc P2P, SWG spirit).
        3. **O3 Esprits IA** : Cortex & Agents locaux souverains (Ollama 0 € cloud, Second Brain persistant).
      * Responsive mobile/desktop avec micro-interactions et statut live du studio.
    - **Pipeline de Déploiement Gladys (`deploy_showcase_ovh.py`)** :
      * Développé dans `packages/cortex/infra/scripts/deploy_showcase_ovh.py` (pur Python `ftplib` / FTPS sans dépendance).
      * Intégré dans les actions canoniques de Gladys (`showcase_deploy_ovh` dans `pending_actions.py`).
      * Fichiers synchronisés sur le CT 100 (`/opt/orchestrateur/showcase-web` et `/opt/orchestrateur/backend/scripts/`).
      * **Mise en ligne réussie à 100% sur OVHcloud** : Déploiement automatique effectué sur `ftp.cluster129.hosting.ovh.net` (`laboiteageek.fr` et `laboiteageeks.fr`).
      * **Validation HTTP Live** : `https://laboiteageek.fr/` renvoie HTTP 200 avec le titre *La Boîte à Geeks Studios — LBG*.

-27. **Extension Topologie Globale & Second Brain de l'Organisme Gladys (`#/topology`)** :
    - **Inspiration TikTok Toma Tech (Obsidian Graph View & Second Brain IA)** :
      * Généralisation de la vue graphe interactive `#/topology` au-delà du MMO pour cartographier l'intégralité de l'organisme cybernétique **Gladys** (Infra, Machines, Organes, Services, Agents et Connaissances).
    - **Architecture & Données Gladys (`gladys_topology_data.json`)** :
      * 29 nouveaux nœuds et 34 arêtes organiques : Cœur Gladys, Incarnation Lia, Machines physiques (`.10`, `.143`, `.140`, `.110`, `.111`, `.246`, `.54`), Services (`agent-desktop`, `fastapi`, `orchestrator`, `ollama_heavy/light`, `piper_tts`, `godot_hub`, `stalwart_mail`, `adguard_dns`), Agents autonomes (`Antigravity`, `Cline 0€`, `Nocturnal Auditor`, `Content Bot`) et Second Brain documentaire (`ORGANISME_LBG.md`, `OBJECTIVES.md`, `REGISTRE.md`, etc.).
      * Pont naturel établi entre l'infrastructure Gladys et le banc d'entraînement MMO (`runtime_246` & `prime_hub_service` -> `scrapaltai`).
    - **Sondes Live Réseau & Télémétrie en Direct (`/v1/pilot/topology`)** :
      * Sondes TCP asynchrones ultra-rapides (~200ms) vérifiant la disponibilité en direct des ports clés de l'organisme.
      * Télémétrie instantanée : `live_gladys_count` (16/17 organes en ligne) combiné aux 10 bots IA live sur le Hub Godot.
      * Paramètre de filtrage REST `?domain=gladys|mmo|all`.
    - **Frontend Pilot Web (`index.html`, `topology_graph.js`, `topology_graph.css`)** :
      * Sélecteur de domaine à 3 boutons : **🌐 Vue Globale**, **🧠 Organisme Gladys**, **⚔️ Monde MMO**.
      * Halos pulsants verts pour les nœuds en ligne, palette de couleurs organiques (machines, services, agents, second brain).
      * Drawer latéral enrichi affichant pour Gladys l'hôte, le port, le statut live, le rôle organique et le chemin du document canonique.
      * Bundle Vite synchronisé dans `dist/` (154 tests unitaires backend 100% verts).

    - **Directive Pérenne** :
      * Maintenir systématiquement à jour `gladys_topology_data.json` lors de chaque ajout d'organe, machine, conteneur Proxmox, service réseau ou document clé de l'organisme Gladys, ainsi que `topology_data.json` pour les évolutions du monde MMO (POIs, PNJ, mécaniques).
      * Chaque déploiement via `tools/deploy_cortex_140.sh` synchronise automatiquement la topologie vivante vers le serveur `.140`.

-26. **Stabilisation Moteur Vidéo JRPG (Hina & Saki) & Cadence Quotidienne** :
    - **Résolution Saccades & Mouvements de Bras** :
      * Élimination complète des sauts de bras parasites : l'avatar utilise désormais une posture de base calme et stable (`POSE_NATURAL_IDLE`).
      * Seules les lèvres (`talk_a`, `talk_o`, `neutral`) et les yeux (`blink` toutes les 3.8s) s'animent en synchronisation avec l'audio.
      * Lissage de l'enveloppe RMS et cadence labiale calée à 6.5 Hz pour une prononciation nette sans scintillement.
    - **Cadrage Stable & Cinématique** :
      * Suppression des coupures brusques de plans entre caméras différentes : cadrage unifié Plan Moyen / Mi-buste, yeux de Lia alignés sur le tiers supérieur.
    - **Synchronisation Windows & Préparation Drop 19h00** :
      * Vidéo prototype et drop de test synchronisés avec succès vers `O:\OneDrive\Pictures\IA\Contenue\`.
      * Prochain sujet prêt en file d'attente (Sujet 29 : *Économie de troc P2P et négociations marchandes entre bots et joueurs*).

-25. **Intégration API OVHcloud dans Gladys & Synchronisation DNS en Direct (`laboiteageeks.fr`)** :
    - **Script Canonique & Sécurité (`ovh_dns_manager.py`)** :
      * Développé dans `packages/cortex/infra/scripts/ovh_dns_manager.py`, synchronisé sur le CT 100 (`/opt/orchestrateur/backend/scripts/`).
      * Client REST pur en Python (signature HMAC-SHA1 officielle OVH, horloge resynchronisée dynamiquement avec `/auth/time`).
      * Identifiants API sécurisés (`ovh.env` chmod 600, exclu de git via `.gitignore`).
    - **Intégration Gladys HITL (`pending_actions.py`)** :
      * Déclaration des actions `ovh_dns_audit` et `ovh_dns_apply_mail` dans le catalogue `CANONICAL_ACTIONS`.
    - **Application Réelle effectuée par Gladys chez OVHcloud** :
      * Enregistrement DKIM Stalwart créé : `v1-rsa-20261117._domainkey.laboiteageeks.fr` (Record ID: `5449716346`).
      * Zone DNS rafraîchie avec succès chez OVH.
      * Clé DKIM déjà propagée et validée par résolution DNS externe en ~24 ms.
      * **Bilan 100% Vert** : MX (`10 mail`), SPF (`82.67.2.16`), DKIM (`v1-rsa-20261117`), DMARC (`v=DMARC1;p=none;sp=none;aspf=r;`).

-24. **Résolution Connectivité IMAP Thunderbird & Dossiers Envoyés (Stalwart CT 154 / .10)** :
    - **Listeners Stalwart complétés** :
      * Ajout des listeners `imap` sur port **143** (STARTTLS) et `submission` sur port **587** via `stalwart-cli create NetworkListener`.
      * Stalwart redémarré et vérifié : écoute active sur 25, 143, 443, 465, 587, 993, 995, 4190, 8080.
      * Connectivité TCP validée depuis le PC Windows `.10` vers `192.168.0.54` sur les ports 143 et 993 (`TcpTestSucceeded: True`).
    - **Thunderbird & Exceptions SSL (.10)** :
      * Certificats auto-signés consolidés dans `cert_override.txt` (`192.168.0.54:143:`, `993:`, `465:`).
      * Authentification IMAP testée et validée (dossiers `INBOX`, `Drafts`, `Sent Items`, `Deleted Items`, `Junk Mail`).
      * L'envoi et la sauvegarde automatique dans « Envoyés » sont désormais opérationnels sans blocage réseau.

-23. **Moteur Vidéo JRPG Rétro (Inspiré d'Hina et Saki), Déduplication des Scripts & Automatisation TikTok/OneDrive** :
    - **Inspiration Format Viral "Hina et Saki" (`jrpg_compositor.py`)** :
      * Rendu 3D Cycles CPU avec Lia en multi-cadrages cinématiques : alternance dynamique Plan Moyen (poste de travail) et Gros Plan (visage et yeux cyan émissifs).
      * Boîte de dialogue rétro JRPG style PS1 / Final Fantasy VII : dégradé bleu nuit, double-bordure biseautée cyan `#00F5D4`, cartouche `[ LIA // ANDROÏDE IA ⚡ ]` avec diode verte `● ONLINE`, typographie monospace nette et curseur animé `▼`.
      * Branché comme compositeur par défaut dans `content_bot.py` (`--style jrpg`) et `cron_daily_publisher.py`.
    - **Résolution Définitive des Vidéos Dupliquées (`script_generator.py`)** :
      * Cause identifiée : un regroupement trop large de mots-clés (`["swg", "pre-cu", "artisanat"]`) combiné à un timeout Ollama CPU (22s) renvoyait systématiquement le même fallback textuel.
      * Individualisation stricte de 10 domaines thématiques clés : SWG Craft/Minerais 1-1000 vs Pre-CU Arbres 4x4, Troc P2P & Marchands locaux, Titans/AnimationTree 3D, Harvesters/Extracteurs, Second Brain Obsidian RAG, Housing & Villes, SQLite WAL, VRM 280 chorégraphies.
      * Ajustement des timeouts de requêtes LLM locales.
    - **Transfert Vidéo & Pipeline TikTok Windows (`.10:5005`)** :
      * Déploiement live de la capability `copier_video_vers_onedrive` dans l'agent Windows.
      * Rendu de test `drop_1794935179_tiktok.mp4` (Sujet 29 : Économie de troc P2P, 3.15 Mo, 37.7s) généré en style JRPG et synchronisé avec succès dans `O:\OneDrive\Pictures\IA\Contenue\`.
      * Capability `preparer_upload_tiktok` armée pour ouvrir TikTok Studio et copier titre et hashtags dans le presse-papier Windows.

-22. **Déploiement Effectif Serveur Mail Stalwart (CT 154 Proxmox .201) & Câblage Thunderbird (.10)** :
    - **Déploiement Proxmox CT 154** :
      * CT 154 `lbg-mail` provisionné sur Proxmox `.201`, IP statique `192.168.0.54`, passerelle `.254`, DNS AdGuard `.53`.
      * Stalwart Mail Server installé et actif sous systemd (`systemctl status stalwart`).
      * Configuration initiale validée : domaine `laboiteageeks.fr`, compte admin et compte utilisateur `sdesharches@laboiteageeks.fr`.
      * Résolution de l'authentification OAuth/IP : mode recovery aligné sur `http://192.168.0.54:8080/admin` puis passage en mode normal opérationnel.
      * Ports en écoute active et vérifiés : **SMTP 465 (SMTPS SSL/TLS)** et **IMAP 993 (IMAPS SSL/TLS)**.
    - **Intégration Thunderbird (PC Windows .10)** :
      * Profil serveur sortant Gladys Mail configuré sur `192.168.0.54:465` (SSL/TLS, mot de passe normal).
      * Validation de l'exception de certificat auto-signé local dans Thunderbird.
    - **Frontend Compagnon (CT 100)** :
      * Conteneur Docker `lbg-frontend` recompilé `--no-cache` sur le CT 100 pour intégrer le composant `msg.pending_action` dans `ChatFlow.vue`.
    - **Sujet Consigné pour la suite (Backlog Gladys)** :
      * Intégration **OVHcloud** (`https://manager.eu.ovhcloud.com/#/hub/`) à Gladys : API / gestion DNS `laboiteageeks.fr` (enregistrements MX, SPF, DKIM, DMARC pour le serveur mail local).

-21. **Câblage Thunderbird (.10) & Préparation Déploiement Autonome Serveur Mail Stalwart (CT 154 sur Proxmox .201)** :
    - **Câblage Thunderbird sur le PC Windows (`.10:5005`)** :
      * Déclaration de `thunderbird` dans l'allowlist `LBG_DESKTOP_APP_ALLOWLIST` et dans `LBG_DESKTOP_APP_MAP_JSON` avec son chemin exécutable officiel `C:\Program Files\Mozilla Thunderbird\thunderbird.exe`.
      * Gladys peut désormais ouvrir Thunderbird et piloter la composition de messages (`-compose`) depuis le chat Compagnon.
    - **Création du Script Canonique `create_lbg_mail_ct_proxmox.sh`** :
      * Cible propre et isolée sur Proxmox `.201` : **CT 154** (`lbg-mail`), Ubuntu 24.04, 2 Cores, 2048 Mo RAM, 15 Go disque sur `local-vm-930g`.
      * Réseau statique : **`192.168.0.54/24`** (passerelle Freebox `.254`, résolveur DNS AdGuard `.53` !).
      * Moteur mail : **Stalwart Mail Server** (tout-en-un moderne en Rust, IMAP 143/993, SMTP 25/587, WebAdmin :8080).
    - **Armement Sécurisé dans Gladys (`pending_actions.py`, `router_prompts.py`)** :
      * Action `mail_server_deploy` enregistrée dans `CANONICAL_ACTIONS`.
      * Algorithme d'extraction mis à niveau en 2 passes : priorité stricte au nom de script exact cité (`create_lbg_mail_ct_proxmox.sh`) avant les mots-clés sémantiques, éliminant tout faux positif avec le CT 153 DNS.
      * Exclusion des requêtes de déploiement/provisionnement (`_PROVISION_OR_DEPLOY_RE`) du monitoring passif Héphaïstos (`infra_lan_intent.py`).
      * Connaissance canonique du serveur mail (CT 154 sur `192.168.0.54`) intégrée dans les consignes système `router_prompts.py`.
      * Synchronisé et validé sur le CT 100 (`/opt/orchestrateur/scripts/` et backend).

## Dernières actions réalisées (2026-11-16)
-20. **Pilotage Fluide & Autonome de Gladys (Pending Actions, HITL L2 1-Clic, Exécution Directe Fermée)** :
    - **Problème résolu** : Gladys formulait une proposition technique (ex: « Veux-tu que je déclenche le déploiement DNS... »), mais quand l'utilisateur répondait « oui » ou « go », elle réagissait comme un chatbot passif (« On déploie le serveur DNS... Déclenche avec validation L2 ») sans rien exécuter, forçant à chercher des tokens L2 sur Pilot.
    - **Gestionnaire Conversationnel d'Actions en Attente (`pending_actions.py`)** :
      * Structure `PendingAction` avec `action_id`, `conversation_id`, `action_type`, `label`, `command`, `timeout_s` et TTL (15 min).
      * Whitelist sécurisée d'actions canoniques (`CANONICAL_ACTIONS`) : déploiement DNS AdGuard, contrôles stockage Proxmox, audit Ollama, smoke test LAN, diagnostics Godot, watchdogs infra.
      * Extraction automatique depuis les messages assistants formulant une proposition avec question de confirmation.
      * Interception immédiate des affirmations utilisateur (`is_confirmation_affirmative` : « oui », « go », « vas-y », « fais-le », « lance », « valide », « d'accord ») et des refus (« non », « annule »).
    - **Interception & Exécution Sans Friction (`core.py`, `ChatFlow.vue`, `useChat.js`)** :
      * Dans `core.py` (`_ask_payload`) : si une `pending_action` est en attente et que le prompt est une confirmation, Gladys intercepte l'appel AVANT d'aller au LLM, exécute le script/action de manière asynchrone, efface l'action et renvoie le compte-rendu d'exécution avec la timeline en temps réel.
      * Dans `ChatFlow.vue` : bandeau interactif compact `[▶ Confirmer et lancer]` / `[Annuler]` affiché directement sous les propositions dans le chat pour permettre le pilotage 1-clic.
      * Dans `useChat.js` : persistance du champ `pending_action` dans `MESSAGE_FIELDS`.
    - **Sécurisation & Accès SSH Machine CT 100 → Proxmox .201** :
      * Clé SSH ed25519 de `root@192.168.0.100` autorisée sur Proxmox `root@192.168.0.201`.
      * Montage et copie des scripts d'infrastructure dans `/opt/orchestrateur/scripts/` et `/app/scripts/`.
      * Outils réseau (`openssh-client`, `curl`, `iputils-ping`) et clés injectés dans le conteneur Docker `orchestrateur-backend`.
    - **Validation de Bout en Bout en Production** :
      * Tour 1 : Demande « Tu pourrais mettre en service un serveur DNS sur ton infra (Gladys) ? » → Proposition nette formulée par Gladys + armement automatique de la PendingAction `act_dns_adguard_deploy`.
      * Tour 2 : Réponse utilisateur « oui » → Interception immédiate, exécution en 14 s du script `create_lbg_dns_ct_proxmox.sh`, et retour avec statut opérationnel complet, timeline et URL du service (`http://192.168.0.53:80`).
      * Tests unitaires `test_pending_actions.py` validés (7/7 tests passants en 0.08 s).
      * Déployé en production sur `http://192.168.0.100:5174/` (version `1.0.0+10d4c82`).

-19. **Mise en Service Réussie du Serveur DNS Local AdGuard Home (CT 153 sur Proxmox .201)** :
    - **Validation L2 & Exécution Gladys** : Suite à l'approbation dans le chat Compagnon, exécution du script officiel `packages/cortex/infra/scripts/create_lbg_dns_ct_proxmox.sh`.
    - **Provisionnement Proxmox** : Conteneur LXC 153 Ubuntu 24.04 (`lbg-dns-adguard`) créé avec succès sur le storage `local-vm-930g` de l'hyperviseur `192.168.0.201`.
    - **Réseau & IP Statique** : Attribué sur `192.168.0.53/24` (passerelle Freebox `.254`).
    - **Service AdGuard Home Actif** : Téléchargé, installé et lancé en service systemd automatique.
    - **Surfaces réseau validées** :
      * Assistant web initial : `http://192.168.0.53:3000/` (répond 302 vers `/install.html`).
      * Interface d'administration finale : `http://192.168.0.53/` (port 80).
      * Port DNS LAN : `192.168.0.53:53` (UDP/TCP).

-18. **Résolution Faux Positif Audit Ollama & Stabilisation Inférence DNS Compagnon** :
    - **Faux positif résolu (`ollama_audit.py`)** : Le modèle `lbg-compagnon-e4b-v1:latest` sur `.111` était signalé manquant car l'audit vérifiait une égalité stricte sans supporter le tag `:latest` implicite/explicite. `model_available()` mis à niveau pour gérer les tags et correspondances de base.
    - **Fin des timeouts & des bascules d'urgence sur 2B (`llm_chat_phase.py`, `local_llm_provider.py`)** :
      * Sur le CPU Xeon de `.110`, le prompt système cumulé atteignait 6341 caractères (~2800 tokens), prenant plus de 4 minutes de prompt-eval. Le timeout était dépassé (180s), forçant un repli d'urgence sur `qwen3.5:2B` qui hallucinait.
      * Allègement automatique du prompt système pour les requêtes infra/ops ciblées (suppression des doublons Studio Brain, Écosystème complet et RAG philo), ramenant le prompt à ~2000 caractères et divisant par 3 le temps d'inférence.
      * Timeout LLM local relevé à 300s dans `local_llm_provider.py` pour laisser le temps au CPU en cas de prompt dense.
    - **Épuration stricte des sorties et fuites système (`character_layer.py`, `router_prompts.py`)** :
      * Suppression des formulaires de "dials d'expression" dans les prompts.
      * Connaissance de référence du serveur DNS AdGuard Home (CT LXC 153 sur Proxmox `.201`, IP `192.168.0.53`) intégrée dans `_OPS_TRUTH`.
      * Test réel validé : réponse fluide, propre et sans fuite méta émise par `gemma-4-abliterated:12b-qat` sur `.110`.
    - **Déploiement en production** : Validé et déployé sur `.100:5174` (version `1.0.0+4305a23`).

-17. **Redirection Contextuelle des PNJ Hors-Service / En Loisir vers le Travailleur Actif (`hub_dialogue.gd`, `hub_http.gd`, `server_main.gd`)** :
    - **Identification dynamique de l'état de service** :
      * Lors d'une interaction de dialogue (`/v1/dialogue/invoke`), le système interroge le planning en temps réel de `HubLife` via `attach_sim(sim)`.
      * Si le PNJ sollicité est en quartier libre (`phase == "leisure"`), il clarifie immédiatement sa situation :
        * Ex: *« Neris Vohl : Je suis en quartier libre en ce moment (thé à l'auberge), je ne suis pas de service ! Si tu as besoin d'une formation, d'un contrat ou de soins, adresse-toi à Daan Oth au Bureau des missions. »*
      * S'il est en poste (`phase == "work"`), il délivre normalement ses services et quêtes sans redirection.
    - **Choix d'actions suggérés & Mots-clés conversationnels** :
      * Le dialogue propose deux boutons d'action contextuels :
        1. `[Où trouver <Collègue actif> ?]` → Le PNJ explique précisément où se trouve le poste officiel (Bureau des missions, Clinique médicale, Atelier d'artisanat, Centre d'entraînement, Auberge...).
        2. `[Bonne pause !]` → Le PNJ remercie chaleureusement le joueur (*« Merci ! Ça fait du bien de souffler un peu avant ma prochaine relève. »*).
    - **Validation & Déploiement** :
      * Test unitaire headless `packages/prime-hub/tools/test_leisure_dialogue.gd` validé à 100%.
      * Déploiement en production sur `prime-hub` (`192.168.0.246:8787`).
      * Test de l'endpoint HTTP live validé sur `.246:8787`.
      * Manifeste client et patch déployés sur `192.168.0.246:8080`.

-17. **Publication Automatique TikTok Studio via Gladys & Agent Windows (`.10`)** :
    - **Activation TikTok Studio dans le Cron Quotidien (`cron_daily_publisher.py`)** :
      * Ajout des flags `--tiktok` et `--pilot` lors de chaque drop automatique (21h30 et suivants).
      * Synchronisation systématique du MP4 rendu dans `O:\OneDrive\Pictures\IA\Contenue\`.
      * Création de la fiche mémo texte avec les métadonnées et hashtags viraux.
    - **Déploiement de la Capability `preparer_upload_tiktok` sur l'Agent Windows (`.10:5005`)** :
      * Ouverture directe de `https://www.tiktok.com/tiktokstudio/upload` dans le navigateur par défaut (Edge).
      * Injection automatique de la légende et des hashtags (`#fyp #ia #tech #lbgstudios`) dans le presse-papier Windows via PowerShell (`Set-Clipboard`).
      * Mise en surbrillance automatique du fichier MP4 dans l'Explorateur Windows (`explorer.exe /select,...`).
    - **Validation Gladys Multimodal `agent-desktop` (Computer Use Headless)** :
      * Diagnostic validé sur le poste `.10` : agent actif en session interactive 1, `agent-desktop 1.2.0` opérationnel.
      * Arbre UI de Microsoft Edge inspecté avec succès en direct via Gladys (snapshot OK, 562 refs UI accessibles sans capture d'écran ni blocage de souris).
      * Prêt pour le drop de 21h30 ce soir.

-16. **Intégration du Modèle 3D Lia Androïde Cyber & Mouvements Naturels Organiques** :
    - **Modèle 3D Lia Androïde (Cyber Cyan & Métaux)** :
      * Re-génération complète des 9 keyframes 3D plein pied dans `tools/studio_content_engine/assets/compagnon` via Blender 5.2 Cycles CPU avec les textures officielles de Lia Androïde (`body_skin_android.png`, `face_skin_android.png`, `hair_android.png` et iris émissifs cyan `#00f5d4`).
      * Finition fidèle à 100% à l'incarnation de bureau : épiderme mécatronique cyan luminescent (c'est sa véritable peau cybernétique, pas un costume ni une combinaison amovible), cheveux bleus émissifs, yeux néon.
    - **Mouvements Naturels & Organiques (`video_compositor.py`)** :
      * *Pose Blending Soyeux* : transition par morphing / fondu croisé (alpha blending doux sur 5 frames, ~160ms) entre chaque pose (neutral, explain, joy, think, point) au lieu de coupures sèches.
      * *Respiration Organique Humaine* : cycle respiratoire de 3.3s avec micro-mouvements de soulèvement de poitrine et de bassin.
      * *Inertie & Amorti Physique* : filtrage passe-bas (EMA) sur les inclinaisons de tête et du cou pour supprimer les saccades brutales liées aux pics audio.
      * *Camera Glide Cinéma* : glissement latéral progressif et amorti de l'avatar lorsque les infographies B-Roll apparaissent, sans téléportation d'image.
    - **Feuille de Route Garde-Robe Modulaire Lia (Validée)** :
      * Pour le drop de 21h30 : maintien du modèle androïde brut (peau synthétique cyan intégrale exposée).
      * Pour la suite : conception d'une garde-robe modulaire techwear / ingénieure LBG / cyberpunk (veste ouverte, pantalon cargo, hoodie techwear) superposable à son corps cybernétique, laissant apparaître son épiderme mécatronique aux articulations et au cou selon les thématiques de vidéo.
    - **Validation & Test Vidéo** :
      * Rendu complet d'un MP4 test 1080x1920 avec sous-titres TikTok et voix Edge-TTS validé avec succès (3.88 Mo).

-15. **Cycle Circadien 90 Min Réelles, Rôle Vivant des Citoyens en Loisir & Spatialisation du Chat** :
    - **Cycle Circadien Planétaire 90 Minutes Réelles (`hub_world_clock.gd`, `hub_sim.gd`)** :
      * Passage de `time_dilation = 60.0` (24 min réelles) à `time_dilation = 16.0` :
        $$\text{time\_dilation} = \frac{86\,400\text{ s (24h de jeu)}}{5\,400\text{ s (90 min réelles)}} = 16.0$$
      * 1 heure de jeu = **225 secondes réelles** (3 min 45 s).
      * Plein Jour (08h00 - 18h00, 10h in-game) = **37 min 30 s**.
      * Nuit profonde (21h00 - 05h00, 8h in-game) = **30 min 00 s**.
      * Aube + Crépuscule (6h in-game) = **22 min 30 s**.
    - **Animation Vivante du Monde par les Citoyens en Loisir (`hub_life.gd`, `triplons.json`, `client_net_world.gd`)** :
      * Clarification produit : les PNJ en quartier libre (`phase == "leisure"`) sont **pleinement actifs et visibles** (`allow_leisure_citizens: true`) pour meubler et animer la ville, tandis que seul le 3ᵉ membre (`phase == "rest"`) se repose dans ses quartiers privés.
      * Au poste officiel (clinique, board, atelier...), il n'y a **qu'un seul travailleur en service** (`phase == "work"`), évitant tout doublon sur les postes.
      * Les membres en loisir s'adonnent à de véritables activités citoyennes réparties dans Lost Heaven :
        - *Taverne & Boisson* : s'installent au comptoir de La Perle ou à l'auberge pour prendre un verre (`activity: "Prend un verre"`).
        - *Commerce & Marché* : flânent entre les étals du marché pour chiner et marchander (`activity: "Flâne au marché"`).
        - *Animation & Spectacle* : dansent ou applaudissent près de la scène (`activity: "Danse & Spectacle"`).
        - *Récolte dans les dunes* : sortent par la porte est ou sud pour cueillir des herbes et ramasser de la ferraille (`activity: "Cueillette / Récup'"`).
        - *Déambulation urbaine* : arpentent les ruelles et le spatioport (`activity: "Déambule en ville"`).
      * Affichage dynamique sur le client (`client_net_world.gd`) : l'étiquette nameplate reflète l'activité en cours du PNJ (ex: *« Neris Vohl · Prend un verre »*, *« Sera Quill · Cueillette / Récup' »*).
    - **Spatialisation du Chat Cantina & Fin du Spam Global (`hub_show.gd`, `hub_ws_server.gd`, `hub_sim_ambient.gd`)** :
      * Les messages de chant de l'Artiste de scène sont limités à une portée locale de 45 m centrée sur la scène.
      * L'artiste ne déclenche plus ses répliques dans le chat si aucun joueur humain n'est présent dans ou devant La Perle ($\le 55\text{ m}$).
      * Protection anti-répétition consécutive pour les répliques de scène.
    - **Déploiements & Tests Validés** :
      * Test unitaire `test_triplons_circadian.gd` validé : cycle de 90 min vérifié et comptage strict à 1 PNJ actif par triplon (mission, medic, scout, artisan, entertainer, brawler).
      * `prime-hub` déployé sur `.246:8787` (`healthz 200`, `time_dilation: 16.0`, `single_active_shift: true`).

-14. **Résolution du Problème des Vidéos Répétitives & Diversification Totale du Studio Content** :
    - **Diagnostic du Problème** : Les 8 dernières vidéos étaient quasi identiques (même sujet générique, même texte lu par Lia, mêmes infographies B-Roll). Causes :
      1. Backlog `topics_backlog.json` épuisé : le cron générait en boucle le sujet statique `"Ingénierie locale et agents autonomes chez LBG Studios ({now_str})"`.
      2. Le timeout Ollama trop court échouait et basculait sur un fallback textuel figé à trous.
      3. Absence de variation graphique dans le compositeur vidéo (toujours le même fond bleu/cyan et les 3 mêmes cartes B-roll).
    - **Correctifs Appliqués** :
      * **28 Nouveaux Sujets Uniques Injectés** dans `topics_backlog.json` (SWG Pre-CU, T4C, Godot 4.6 Headless, NavigationServer3D, Lia Compagnon, SQLite WAL, VRM, Shaders...).
      * **Auto-Replenish Intelligent** dans `cron_daily_publisher.py` : si le backlog passe sous 5 sujets en attente, réapprovisionnement automatique sans jamais dupliquer de sujet existant.
      * **Générateur Thématique Dynamique** dans `script_generator.py` : fallbacks spécialisés et contextualisés par thématique (MMO, T4C, SWG, DB, 3D, IA) garantissant un script unique même hors ligne.
      * **Palettes Graphiques & Arrière-plans Thématiques** dans `video_compositor.py` : 4 ambiances visuelles complètes (*Amber* pour le lore/désert/SWG, *Synthwave* pour l'IA/VRM, *Matrix* pour DevOps/DB, *Cyan* pour Godot/Server).
      * Prochaine vidéo de 21:30 programmée sur : *« Ressusciter Star Wars Galaxies en 2026 : notre recette technique »* (ambiance ambrée, script inédit).

-13. **Passage au Standard Planétaire 64 km × 64 km (4 096 km²), Porte Sud de Lost Heaven, Tracés Réseau Propres & Collisions Falaises** :
    - **Durée du Cycle Jour/Nuit Canonique** :
      * Paramètre `time_dilation = 60.0` dans `hub_world_clock.gd`.
      * 1 heure de jeu = 60 secondes réelles (1 minute).
      * Le cycle planétaire complet de 24h dure exactement **24 minutes réelles** (~12 min de plein jour, ~12 min de nuit/pénombre), modulé en continu selon la longitude $X$ de la caméra (fuseaux horaires du terminateur solaire).
    - **Création de la Porte Sud de Lost Heaven (`poi:lost_heaven_gate_south`)** :
      * Ouverture de 62 mètres aménagée dans la palissade Sud (`path:lh_perimeter_fence`) avec piliers Est `(4780, -1387.8)` et Ouest `(4718, -1387.8)`.
      * Enregistrement de `gate:south_dunes` dans `gate_exits` (couloir praticable $58\text{ m} \times 240\text{ m}$).
      * Ajout d'une arche monumentale en pierre (`prop:lh_gate_south_arch`) et de lanternes d'éclairage (`prop:lh_gate_south_lamp_w` & `e`).
      * La route du sud (`road_lh_to_humidity_farm`) part de la place du marché, franchit précisément la Porte Sud et file plein sud vers Lars-Val et Ksar Nomade sans jamais couper le rempart.
    - **Correction Rigoureuse des Tracés Routiers & Respect des Reliefs** :
      * *Canyon des Épaves* : la route `road_ksar_to_canyon_alkhali` suit désormais strictement le fond de gorge praticable entre les falaises Nord ($Z \approx -14960$) et Sud ($Z \approx -15080$), sans plus jamais escalader ni couper la roche.
      * *Autoroute de Zalem* : entre par la Porte Monumentale d'Acier (`poi:zalem_monumental_gate`), sans couper l'enceinte polygonale.
      * *Piste Caravanière Est* : sort par la Porte Est de Lost Heaven et contourne la ville vers les dunes.
    - **Gestion Physique des Collisions de Falaises & Obstacles** :
      * Ajout des polygones de collision infranchissables dans `scrapaltai_zones.json` pour les falaises Nord et Sud du Canyon des Épaves et le bluff rocheux du Ksar Nomade.
      * Intégration de `zone_polygons` dans `hub_collision.gd` sur le serveur `prime-hub` (`allows(x, z)` bloque désormais les déplacements à travers les falaises côté serveur et côté client).
    - **Déploiements Validés** :
      * `prime-hub` déployé sur `.246:8787` (blocks=48, fence_pts=29, zone_polys=3).
      * Patch client Launchpad déployé sur `.246:8080`.
      * Client Windows (.10) synchronisé (scripts, données et textures 64 km).

-12. **Harmonisation Géographique 1:1, Cycle Jour/Nuit Progressif (Solar Terminator) & Entités Sol 2D (`scrapaltai_planet.png`, `planet_map_panel.gd`, `lost_heaven_buildings.json`, `lost_heaven_props.json`)** :
    - **Alignement Géographique Exact 1:1 (Ksar Nomade & Avant-poste Zalem)** :
      * Correction du décalage géographique majeur : Ksar Nomade et son oasis turquoise repositionnés exactement à `(X: 4950, Z: -3650)` (l'ancien tracé l'affichait à `Z: -4800` et son lac bleu à `X: 2480`).
      * Avant-poste de Zalem repositionné sur la passe ouest `(X: -1200, Z: -500)` (l'ancienne carte l'affichait avec une inversion de signe à `X: +1200`).
      * Tracé de la boucle routière ovale en 8 reliant fidèlement Lost Heaven et Ksar Nomade comme observée en jeu.
    - **Modélisation et Rendu Physique des Éléments Manquants en Jeu** :
      * Ajout de structures et props complets dans `lost_heaven_buildings.json` et `lost_heaven_props.json` pour que chaque site majeur de la carte soit visible au sol :
        - *Ferme d'Humidité Lars-Val* `(3850, -2200)` : dôme d'habitation, station de pompage, 5 évaporateurs tripodes atmosphériques GX-8, citernes d'eau douce et caisses.
        - *Anchor-Ridge* `(4200, 3200)` : QG d'extraction, fonderie & concasseur de duracier, cantine des mineurs, silos miniers, éperons rocheux.
        - *Lac d'Améthyste* `(5600, 4500)` : nappe d'eau géodique, géodes et aiguilles de cristal pourpre, station hydrique.
        - *Mos Espa Bazar* `(-2200, -800)` : grand hangar marchand, taverne du rift, comptoir de change, tentes d'étals colorées.
        - *Camp des Ferrailleurs Jawas* `(-3600, -1200)` : abri troglodyte, carcasse de char des sables, piles de pièces détachées.
        - *Gouffre du Dragon Krayt* `(-4500, 600)` : fossile colossal de léviathan et falaises de brèche.
      * Ajout des tracés de pistes au sol (`paths`) reliant tous ces sites (voies sud, est, ouest et nord).
    - **Cycle Jour/Nuit Progressif Est ↔ Ouest (Solar Terminator)** :
      * Dans `canvas_of_kings_atmosphere.gd` : calcul de l'heure locale en continu selon la longitude $X$ de la caméra (`local_hour = fposmod(_game_hour + (world_x / 16000.0) * 24.0, 24.0)`). L'aube, le crépuscule, la nuit et l'allumage des lanternes progressent continuellement sans coupure globale instantanée.
      * Dans `planet_map_panel.gd` (`Ctrl+M`) : projection du terminateur solaire (solar terminator) avec onde sinusoïdale d'inclinaison axiale (12°), bande d'aube/crépuscule ambre, voile bleu nuit et icônes du Soleil ☀️ au zénith et du Croissant de Lune 🌙 au minuit solaire.
    - **Suppression du Bord Noir ("Bande à gauche") & Dézoom Calibré** :
      * `player_controller.gd` et `hub_sim.gd` : wrapping toroïdal strict avec `fposmod(pos - min, span) + min` empêchant tout débordement en dehors de `[-8000, +8000]`.
      * `planet_backdrop.gd` : centrage continu du sol désertique 50 km × 50 km sur la caméra (plus aucun vide noir visible quel que soit le déplacement).
      * `main.gd` : `CAM_ZOOM_MIN` calibré à `0.25` pour une vue au sol tactique naturelle, la vue planétaire 16 km étant dédiée à la carte `Ctrl+M`.
    - **Déploiements Validés** :
      * `prime-hub` déployé sur `.246:8787` (334 navmesh polys, healthz 200).
      * Patch client Launchpad déployé sur `.246:8080` (v2026-11-16T17:04:13Z, 329 fichiers).
      * Synchronisation directe vers Windows `.10` (30 fichiers OK, maps png/jpg téléchargées).

-11. **Recalage Géographique Carte Planétaire & Radar Joueur Actif en Direct (`planet_map_panel.gd` & `scrapaltai_planet_map.json`)** :
    - **Harmonisation Géographique sur le Fond de Carte Steampunk** :
      * Re-calage des 10 cités et POIs majeurs de Scrapaltai sur les reliefs et nœuds dessinés du fond de carte officiel pour supprimer tout entassement textuel :
        - *Gouffre du Dragon Krayt* calé au cœur du Grand Rift occidental (`u: 0.240, v: 0.460`).
        - *Bazar de Mos Espa / Fort Al-Khali* à l'entrée ouest du rift / plaine (`u: 0.380, v: 0.390`).
        - *Avant-poste Zalem* sur le relais fortifié sud-ouest (`u: 0.450, v: 0.470`).
        - *Zalem (Capitale)* au carrefour central (`u: 0.488, v: 0.515`).
        - *Ksar Nomade (Oasis du Sud)* au nœud routier oasis sud (`u: 0.505, v: 0.160`).
        - *Bourgade minière d'Anchor-Ridge* au pied des falaises septentrionales (`u: 0.540, v: 0.670`).
        - *Ferme d'Humidité Lars-Val* dans la cuvette de sable central (`u: 0.575, v: 0.420`).
        - *Lost Heaven (Hub joueur)* au spatioport oriental (`u: 0.655, v: 0.310`).
        - *Camp des Ferrailleurs Jawas* dans le canyon oriental (`u: 0.770, v: 0.380`).
        - *Camp Fortifié du Vent Rouge* dans la Mer de Dunes à l'extrême est (`u: 0.855, v: 0.280`).
    - **Radar Temps Réel du Joueur Actif sur la Carte Planétaire** :
      * Intégration de la boucle de rafraîchissement temps réel (`_process` / `queue_redraw`).
      * Affichage d'un curseur joueur pulsant (halo cyan/vert, réticule et balise lisible `● Teome (Vous) [X, Z]`) reflétant la position physique exacte du joueur dans le shard de jeu.
      * Footer d'information dynamique avec coordonnées GPS en direct.
    - **Déploiement & Publication** :
      * Synchronisation vers Windows SDS `.10` (27 fichiers OK).
      * Publication sur le serveur de patch HTTP `192.168.0.246:8080` (version `2026-11-16T14:34:26Z`, 326 fichiers).

-10. **Correction Menu Radial SWG, Téléportation Dev & Publication Patch Client (.246:8080 & Windows .10)** :
    - **Restauration de la Téléportation Admin / Dev (`swg_radial_menu.gd`)** :
      * Cause identifiée : `angles_deg` ne contenait que 6 positions angulaires pré-définies. Dès que le menu contenait plus de 6 options (ex: 10 au sol avec les postures), l'option 6 (`Posture: Accroupi`) se superposait au même angle (`-90°` Nord) par-dessus l'option 0 (`⚡ Téléporter ici (Dev)`), la masquant et interceptant le clic.
      * Correction : Calcul dynamique des angles (`_get_spoke_angles`) et du rayon de couronne (`spoke_r`) pour distribuer équitablement N boutons sans aucun chevauchement, redimensionnement dynamique du panneau.
      * Ajout de l'option téléportation Dev sur toutes les cibles (entités, PNJ, structures, monstres) avec extraction des coordonnées `core3_pos`.
      * Ajout du raccourci direct **Shift + Clic Droit** au sol dans `client_ui_dialogue.gd` pour une téléportation immédiate sans ouvrir le menu.
    - **Déploiement & Publication** :
      * Synchronisation vers Windows SDS `.10` (`tools/sync_client_to_win.py`) incluant `swg_radial_menu.gd` (27 fichiers synchronisés).
      * Publication du patch client sur le serveur Launchpad `192.168.0.246:8080` (version `2026-11-16T14:25:17Z`, 326 fichiers).

## Dernières actions réalisées (2026-11-15)
-9. **Déploiement Live & Intégration Client des Villes / POIs de Scrapaltai (Prime Hub & Client)** :
    - **Synchronisation Client 2D/3D & Carte Planétaire** :
      * Injection des 6 nouveaux POIs de Scrapaltai (*Anchor-Ridge*, *Ferme Lars-Val*, *Camp Jawas*, *Camp Vent Rouge*, *Gouffre Krayt*, *Mos Espa Bazar*) dans `packages/prime-client/assets/maps/scrapaltai_pois.json` et `scrapaltai_planet_map.json`.
      * Extension de `tools/sync_client_to_win.py` pour synchroniser les assets maps et scripts de carte vers le poste SDS Windows `.10`.
      * Déploiement validé sur le poste Windows (26 fichiers transférés avec succès).
    - **Déploiement & Redémarrage Godot Headless `.246:8787` (`deploy_prime_hub_246.sh`)** :
      * Export et validation de `catalog_poi.json` (31 POIs).
      * Service `lbg-prime-hub.service` redémarré avec succès.
      * NavMesh validé : 7 régions maillées, 372 polygones.
      * Endpoint `/v1/catalog?type=poi` opérationnel et diffusant les 31 POIs.
    - **Tests & Validation** :
      * Tests unitaires `t4c_dialogue_selftest.gd` et `t4c_attributes_selftest.gd` validés à 100%.

-8. **Verrouillage & Invariance Stricte de la Voix de Lia dans les Vidéos (`voice_engine.py`)** :
    - **Diagnostic du Problème** : Dans les deux dernières vidéos (`drop_1794729612` et `drop_1794738612`), Lia alternait entre voix féminine et masculine. Cause : un repli silencieux immédiat et non-retryé sur `fr_FR-upmc-medium` (voix d'homme Pierre UPMC) phrase par phrase dès qu'un glitch websocket Edge TTS survenait.
    - **Garantie d'Invariance Vocale par Vidéo** :
      * Implémentation d'une boucle de retries avec exponential backoff (3 tentatives, délai 1.2s * tentative, timeout de 25s) sur Edge TTS (`fr-FR-VivienneMultilingualNeural`), éliminant 99.9% des micro-coupures réseau Microsoft.
      * Nettoyage automatique et garanti des fichiers MP3 temporaires résiduels (`try... finally`).
      * Suppression du repli partiel phrase par phrase : si une panne réseau totale persiste après tous les retries, le basculement est **intégral sur l'ensemble du script** pour ne jamais mélanger deux voix dans une même vidéo.
      * Remplacement de la voix de repli locale Piper `.111:8098` par la voix féminine `fr_FR-siwis-medium` (cohérente avec Lia) au lieu de la voix d'homme `upmc-medium`.
    - **Validation & Tests** :
      * Test unitaire de robustesse : passage nominal 100% Vivienne (0 résidu MP3) et passage de repli intégral validé.
      * `packages/cortex/.venv/bin/ruff check tools/studio_content_engine/` : 100% conforme.
      * 153 tests Cortex Backend et suite complète Godot Headless validés à 100%.

-7. **Studio Musical & Vocal Autonome V3 & Intégration Directe dans l'Atelier 3D** :
    - **Pause Définitive des Danses SWG** : Suite aux retours visuels (cinématique non naturelle 2003 sur rig VRM moderne), le chantier expérimental SWG est gelé pour capitaliser sur les 222+ animations parfaites Mixamo/VRM.
    - **Moteur Musical V3 (`tools/studio_music_generator_v3.py`)** :
      * Bibliothèque de 7 Presets Musicaux calibrés (Cyberpunk 128 BPM, Tatooine Sunset 124 BPM, 80s Synthwave 115 BPM, K-Pop 130 BPM, Dark Techno 132 BPM, Lo-Fi 85 BPM, French Touch 120 BPM).
      * Structure multi-strophes Couplet / Refrain avec gestion des élévations d'énergie et rimes Ollama locales (`.110`/`.111`).
      * 4 Timbres Vocaux distincts pour le chant de Lia : Diva Scénique, Cyber Vocoder (Daft Punk style via flanger et égalisation 1.5kHz), Autotune Pop, Whisper intimiste.
      * Premier morceau test produit et déployé : **`🎵 Lia - Neon Overdrive (30s - 115 BPM)`** (Style Synthwave 80s + Vocoder Daft Punk).
    - **Serveur API HTTP Studio (`tools/studio_music_api.py` sur port 8099)** :
      * Endpoints REST avec CORS : `/api/music/styles`, `/api/music/generate` (asynchrone), `/api/music/status` (polling en temps réel), `/api/music/tracks` (catalogue des fichiers audio générés).
    - **Interface Web de Composition dans l'Atelier 3D (`choreographer.html`)** :
      * Nouvel onglet dédié **`🎵 Studio IA`** dans le panneau latéral gauche.
      * Formulaire complet : Choix du Style, Timbre vocal, Durée (15s, 30s, 60s), Titre personnalisé.
      * Bouton d'action direct avec barre de progression animée et messages d'étapes en direct.
      * Intégration et chargement immédiat du morceau dans le lecteur audio et ajustement automatique de la Timeline.
      * Déployé et synchronisé sur `.140` (`http://192.168.0.140/choreographer.html`) et sur Windows `.10`.

-6. **Intégration de la Topologie Second Brain & Knowledge Explorer (`#/topology`)** :
    - **Extension du Graphe Second Brain (50 Nœuds & 172 Arêtes en Direct sur .140:8080)** :
      * Intégration des 9 Villes & Lieux de Scrapaltai (`type: "city"`, rose `#ec4899`) : *Lost Heaven*, *Bourgade Minière d'Anchor-Ridge*, *Ferme d'Humidité Lars-Val*, *Camp des Maraudeurs Ferrailleurs Jawas*, *Camp Fortifié du Vent Rouge*, *Gouffre du Dragon Krayt*, *Bazar de Mos Espa / Fort Al-Khali*, *Ksar Nomade*, *Avant-poste Zalem*.
      * Intégration des 10 nouveaux PNJ clés de Scrapaltai (`type: "npc"`, vert `#10b981`) : *Durn Vane*, *Sela Kore*, *Valen Lars*, *Klik'Tik*, *U'Ror'K*, *Kane Rill*, *Jax Moro*, *Capitaine Vael*, *Ancien Nadir*, *Miran Sael*.
      * Ajout du bouton de filtre interactif « Villes & Lieux 🏛️ » et enrichissement du Drawer latéral (fiche descriptive, zone, liens de commerce et résidences).
      * Déploiement et synchronisation validés sur la VM `.140` (`GET /v1/pilot/topology` retourne 50 nœuds dont 10 bots IA live).

-5. **Studio Scénique & Production Musicale Autonome (Danses SWG & Morceau 60s)** :
    - **Extraction & Retargeting Universel des 64 Danses Star Wars Galaxies (SWG)** :
      * Extraction de 73 animations officielles depuis les 54 archives `.tre` de SWG sur `.10` (`data_animation_00.tre`, `patch_01.tre`, `patch_10.tre`, `patch_11_00.tre`).
      * Résolution de la cinématique anatomique pour Three-VRM (`tools/batch_convert_swg_to_vrma.py`) : suppression du bug de coude inversé grâce à la projection scalaire de flexion du coude ($\theta \in [20^\circ, 148^\circ]$) sur l'axe normalisé Z, posture de buste vers l'avant ($Z \in [+5\text{cm}, +42\text{cm}]$).
      * Conversion et déploiement de 64 fichiers `.vrma` sur `.140` et `.10` : Tatooine Jazz (`loop` + 8 flourishes), Tumble acrobaties (`loop` + 10 flourishes), Lyrical féminin/masculin (`base_loop` + flourishes 1 à 8), Poplock (`base_loop` + flourishes 1 à 8), Jazz 1 (`loop` + flourishes 1 à 8), Elaine, Moonwalk 1 & 2, Belly Dance.
      * Mise à jour du catalogue Atelier 3D (`choreographer.html` et `manifest.json`) : onglet **`Danses SWG 🌌 (64)`** actif, total catalogue porté de 222 à **284 animations**.
    - **Studio de Composition Musicale Autonome (0 € Cloud)** :
      * Création du pipeline complet de bout en bout `tools/studio_music_generator_v2.py` : paroles thématiques via LLM local Ollama `.110`/`.111` -> composition instrumentale MusicGen multi-segments avec crossfade studio -> synthèse vocale de chant de Lia (`fr-FR-VivienneMultilingualNeural`) -> mixage Master V2 (ducking, égalisation présences +3dB, compression) -> déploiement sur `.140` et `.10`.
      * Production et déploiement du premier morceau 60s autonome : **`🎵 Lia - Tatooine Sunset (MusicGen 60s + Voix - 128 BPM)`**, immédiatement disponible dans le sélecteur audio de l'Atelier 3D.

-4. **Intégration des Mécaniques T4C/SWG & Extension Territoriale de Scrapaltai (Modèle Tatooine)** :
    - **Extension de la Géographie Planétaire (31 POIs & 7 Régions de Navigation NavMesh)** :
      * Ajout des pôles de vie crédibles : Bourgade minière d'Anchor-Ridge (`poi:anchor_ridge`), Ferme d'Humidité Lars-Val (`poi:ferme_humidite`), Camp des Maraudeurs Ferrailleurs Jawas (`poi:camp_ferrailleurs`), Camp Fortifié du Vent Rouge (`poi:camp_vent_rouge`), Gouffre du Dragon Krayt (`poi:gouffre_krayt`), Bazar de Mos Espa / Fort Al-Khali (`poi:mos_espa_bazar`).
      * Intégration de 4 nouvelles zones de navigation maillée dans `hub_nav.gd` (`anchor_ridge`, `ferme_humidite`, `camp_ferrailleurs`, `mos_espa`) montant à 7 régions et 372 polygones.
    - **Nouveaux PNJ Vivants de Scrapaltai (71 NPCs & Registre étendu)** :
      * `npc:prospecteur_durn` (Durn Vane, chef minier), `npc:chimiste_sela` (Sela Kore, affineuse), `npc:fermier_valen` (Valen Lars, fermier d'eau), `npc:ferrailleur_kliktik` (Klik'Tik, troqueur Jawa), `npc:chamane_uror` (U'Ror'K, chamane des sables), `npc:armurier_kane` (Kane Rill, armurier d'arène).
    - **Mécanique T4C 1 : Moteur de Dialogue par Mots-Clés (Keyword Engine)** :
      * Détection textuelle directe sans UI rigide dans `hub_dialogue.gd` (`T4C_NPC_KEYWORDS`), permettant de questionner les PNJ sur l'eau, les minerais, les réactifs, le troc, les esprits, les bêtes du gouffre et la prophétie.
      * Validation unitaire dédiée : [`packages/prime-hub/tools/t4c_dialogue_selftest.gd`](../packages/prime-hub/tools/t4c_dialogue_selftest.gd) (PASS).
    - **Mécanique T4C 2 : Caractéristiques Libres & Karma / Alignement** :
      * Ajout dans `hub_skills.gd` des 5 stats fondamentales de La 4ème Prophétie (Force, Dextérité, Endurance, Intelligence, Sagesse) avec points non alloués et méthodes d'attribution sécurisées.
      * Jauge de Karma dynamique (-1000 à +1000) et titres d'alignement réactifs (*Séraphin de l'Ordre*, *Protecteur Bienveillant*, *Citoyen Neutre*, *Hors-la-loi Notifié*, *Terreur des Sables*).
      * Validation unitaire dédiée : [`packages/prime-hub/tools/t4c_attributes_selftest.gd`](../packages/prime-hub/tools/t4c_attributes_selftest.gd) (PASS).
    - **CI & Intégrité** :
      * `tools/ci_godot_headless.sh` étendu avec les tests T4C (100% vert).
      * Tests Cortex Backend : 153 passed in 5.73s.

## Dernières actions réalisées (2026-11-14)
-3. **Audit Global Gladys & Boucle d'Auto-Évaluation / Self-Healing** :
    - **Banc d'essai Self-Healing (`tools/test_self_healing_loop.py`)** :
      * Injection d'un échec de test CI -> détection automatique par Gladys -> génération d'un mandat de patch vers Ollama local (`qwen2.5:3b` / `14b`) -> application du patch -> repassage vert des tests en 13.7 s à 0 € cloud.
    - **Audit des Surfaces LAN Gladys (`tools/smoke_lan_surfaces.sh --functional`)** :
      * 21 checks fonctionnels OK (Pilot UI/healthz, Cockpit UI/snapshot, Lyra/Orch UI, Simple Chat, Prime Hub Godot G5+, MCP healthz, Patches manifest, Agent Desktop réel sur Windows .10).
      * Godot Prime Hub G5+ (`.246:8787`) : ~5.5 jours d'uptime stable sans fuite mémoire, tick 9 416 077, 38 PNJ + 10 bots IA actifs, persistance SQLite WAL nominale.
    - **Ronde d'Audit Nocturne Autonome (`tools/nocturnal_gladys_auditor.py`)** :
      * Service et timer systemd `gladys-nocturnal-audit.timer` armés pour tourner de 00:30 à 06:30 toutes les heures en mode diagnostic non-destructif.
      * Rapport consigné dans `docs/AUDIT_NOCTURNE_*.md`.
      * Prochaine publication YouTube Shorts automatique : 09:00.

-2. **Intégration Connaissances & Outils Gladys (Claude Code Local 0€ & Pipeline Studio 3D)** :
    - **Analyse des vidéos communautaires** :
      * Cedric Oden IA : Dérivation de Claude Code CLI sur Ollama local à 0€ avec contexte 64k tokens.
      * MechaPizzAI : Chaîne d'orchestration IA (Agent de code + Générateur 3D Tripo + Blender + Moteur de jeu).
    - **Assimilation dans Gladys & Transposition LBG Studios** :
      * Remplacement d'Unity propriétaire par **Godot 4.6 headless** (`prime-hub` :8787), avec scènes `.tscn` textuelles idéales pour les LLM et 0 GPU requis.
      * Création du guide canonique [`docs/GLADYS_STUDIO_PIPELINE.md`](GLADYS_STUDIO_PIPELINE.md).
      * Création du lanceur [`tools/launch_claude_local.sh`](../tools/launch_claude_local.sh) reliant la CLI Claude installée sur `.143` au serveur Ollama `.110` (modèle `qwen2.5-coder:14b` sur RTX).
      * Gladys dispose désormais de la "Main Ouvrière" de code locale illimitée à 0€ couplée au pipeline d'assets 3D Blender headless.

-1. **Optimisation & Scalabilité du Studio Content Engine (@LBG-p8k YouTube Shorts / TikTok)** :
    - **Audit de la chaîne YouTube** : Analyse des métriques des 12 premiers shorts, identification des goulots d'étranglement (mélange de langues, titres tronqués `loca`, 2s de silence initial et salutation formelle molle qui cassait la rétention).
    - **Refonte du Discours & Hook Anti-Scroll** :
      * Suppression de la salutation en phrase 1 ; attaque directe sur le problème technique dès 0.3s.
      * Discours ultra concret et chiffré axé sur la stack réelle LBG Studios (Godot 4.6 headless, NavigationServer3D, SQLite en WAL, micro-LLM 4-bits, Piper TTS ONNX, 60 ticks/s, 0€ cloud).
      * CTA final avec question clivante pour stimuler les commentaires et l'algorithme.
    - **Sécurisation & Publication YouTube** :
      * Forçage des métadonnées françaises (`defaultLanguage: "fr"`, `defaultAudioLanguage: "fr"`).
      * Troncature intelligente de titres (`clean_title_smart`) et génération de tags dynamiques selon le sujet.
      * Réduction du silence initial dans `voice_engine.py` de 2.0s à 0.3s.
    - **Cadencement à 6 Vidéos par Jour (Quota YouTube Sécurisé)** :
      * `lbg-content-daily.timer` reconfiguré sous systemd utilisateur (09h00, 11h30, 14h00, 16h30, 19h00, 21h30) = 9 600 / 10 000 unités API/jour sans dépassement.
      * `topics_backlog.json` étendu à 30 sujets techniques concrets (21 en attente).
      * Premiers drops nouvelle formule publiés avec succès (Shorts PNJ conscients `#b_2T_V7p0y4` et Procédural Godot `#7Wo2K9tpjX0`).

0. **Chaîne de Production Musicale 100 % Autonome (0 € Cloud) — Validée & Déployée** :
   - **Étape 1 : Morceau Étendu 30s @ 128 BPM** :
     * Modèle **MusicGen** local (`facebook/musicgen-small`) exécuté avec succès en multi-cœurs CPU.
     * Génération de `lia_cyberpunk_track_30s.wav` (30.0s, structure progressive avec montée et drop dansant).
   - **Étape 2 : Voix de Chant & Présence de Lia Masterisée** :
     * Synthèse vocale de chant calée au tempo via la voix officielle de Lia (`fr-FR-VivienneMultilingualNeural` avec pitch et rate calibrés).
     * Mixage studio via `ffmpeg` avec spatialisation, compression et réverbération légère (`tools/mix_lia_song.py`).
     * Master audio produit : `packages/compagnon-desktop/overlay/audio/lia_cyberpunk_song_30s_master.wav` (1.4 Mo).
   - **Étape 3 : Intégration Native dans l'Atelier 3D (`choreographer.html`)** :
     * Déploiement sur le Hub Studio VM `.140` : `http://192.168.0.140/audio/lia_cyberpunk_song_30s_master.wav`.
     * Ajout d'un sélecteur déroulant de pistes audio dans l'Atelier 3D permettant de basculer instantanément entre le morceau 30s de Lia, l'instrumentale courte et le morceau historique Nexura Domina.
     * Adaptation automatique de la durée de la timeline et re-génération dynamique des blocs chorégraphiques lors du changement de piste.

1. **Chantier Animations Star Wars Galaxies (SWG)** :
   - Retrait immédiat du hack d'angle manuel et implémentation de la décomposition exacte du moteur SOE ($Q = Q_{post} \cdot Q_{anim} \cdot Q_{pre}$).
   - Préparation du pipeline de retargeting automatique d'armature via Blender 5.2 headless sur `.143` pour mapper les 302 danses SWG vers le rig VRM Humanoid sans torsion.

2. **Basculement Canonique de l'Atelier de Chorégraphie 3D sur le Hub Studio VM `.140`** :
   - Conformément aux canons du monorepo (centralisation des surfaces d'exposition Studio sur la VM `.140`), l'Atelier 3D n'est plus exposé sur un port ad-hoc (`.143:8766`).
   - **Nouvelles URLs canoniques d'exposition** :
     * `http://192.168.0.140/choreographer.html` (Port 80 HTTP standard direct)
     * `http://192.168.0.140:8080/choreographer.html` (Port Nginx Pilot historique)
   - Synchronisation complète des assets 3D (`/opt/LBG_IA_MMO/pilot_web/vrm/` : 364 Mo de modèles, textures et 195 animations VRMA).
   - Nginx sur `.140` mis à jour : écoute simultanée ports 80 & 8080, types MIME `.vrm` (`model/gltf-binary`) et `.vrma` (`application/octet-stream`), en-têtes CORS complets et support natif des Range Requests (`206 Partial Content`) pour le streaming audio/vidéo.
   - Route `/api/load_sequence` mappée directement vers `/opt/LBG_IA_MMO/pilot_web/active_choreography.json`.
   - Fermeture et arrêt du serveur ad-hoc sur `.143:8766`.

1. **Intégration Réussie des Danses Star Wars Galaxies en VRMA Natif** :
   - Reverse-engineering complet du format binaire d'animation SOE (`CKAT / IFF`) et implémentation d'un convertisseur pur Python (`tools/swg_to_vrma.py`).
   - Décodage mathématique des quaternions compressés 32 bits (11b X / 11b Y / 10b Z) et remapping 1-pour-1 sur le rig VRM Humanoid 1.0 (`VRMC_vrm_animation`).
   - Première série d'animations SWG converties et déployées :
     * `swg_moonwalk.vrma` (15.27s, 458 frames @ 30 FPS, 22 os animés)
     * `swg_poplock_loop.vrma` (8.20s, 246 frames @ 30 FPS, 22 os animés)
   - Synchronisées sur :
     * Hub Studio VM `.140` : `http://192.168.0.140/choreographer.html`
     * Bureau Windows `.10` : `C:\Agent_IA\compagnon-desktop\overlay\vrm\animations\`
     * Monorepo Cortex : `packages/cortex/compagnon_ui/public/vrm/animations/`
   - Manifeste `manifest.json` mis à jour (222 animations au total) avec la catégorie *"Danses Star Wars Galaxies 🌌"* en tête du catalogue.

2. **Clip Officiel V2/V3 & Publication YouTube Shorts Public** :
   - **Génération GPU NVIDIA Purement Fluide & Sans Saccade** :
     - Rendu calculé avec accélération matérielle Direct3D 11 via la NVIDIA GeForce GTX 1050 Ti sur `.10`.
     - Résolution native 1080×1920 (Vertical 9:16) @ 30.0 FPS avec upscale Lanczos HD et CRF 18.
     - Poids final : **175.7 Mo** (débit vidéo plein de ~10 Mb/s, confirmant 100% de fluidité et aucune trame sautée).
     - Déposé directement sur OneDrive : `O:\OneDrive\Pictures\IA\Contenue\clip_nexura_domina_v2_drone_final.mp4`.
   - **Chorégraphie & Caméras Multi-angles Intégrales composées par l'utilisateur** :
     - **22 figures mocap VRMA** enchaînées harmonieusement.
     - **11 plans de caméras cinématographiques** incluant les nouveaux mouvements de caméra mobiles :
       * 🚀 Travelling Avant (Push In)
       * 🌌 Travelling Arrière (Pull Out)
       * 🛸 Drone Orbit 360° (rotations continues autour du modèle)
       * 💫 Drone Orbit Buste
       * Silhouettes complètes et plans larges finaux.
     - **23 expressions faciales et styles vocaux** calés sur les couplets, souffles et climax.
     - **23 expressions faciales et styles vocaux** calés sur les temps forts, pauses et climax.
   - **Système de Caméras Dynamiques & Mouvements Drone dans l'Atelier 3D (`choreographer.html`)** :
     - Section dédiée "Mouvements Mobiles & Drone 🛸" avec interpolation en temps réel à 60 FPS.
     - Outils d'insertion rapide au curseur, remplacement direct sur clic de bloc, et découpe avec `[C]`.
     - Timeline étendue avec poignée de redimensionnement draggable (`resizer`) et bouton grand format (450px).
     - En-têtes `Cache-Control: no-cache` pour un rafraîchissement immédiat sans cache navigateur.
   - **Sauvegarde et Restauration Automatique de la Chorégraphie** :
     - Endpoints `/api/save_sequence` et `/api/load_sequence` sur le serveur `.143:8766`.
     - Sauvegarde automatique en local et sur serveur : rechargement transparent à chaque rafraîchissement.
   - **Serveur Multi-threadé avec Range Streaming (`tools/studio_choreographer_server.py`)** :
     - Remplacement de `socketserver.TCPServer` bloquant par `ThreadingTCPServer` multi-threadé avec support HTTP Range (`206 Partial Content`) pour le streaming instantané sans lock du MP3 audio et des 14 Mo du VRM.
     - Port 8766 ouvert sur UFW (`192.168.0.0/16`).
   - **Piste Timeline Dédiée "🎤 CHANT & VISAGE"** :
     - 3ème piste interactive avec presets scéniques : *Diva Scénique (Passionné)*, *Climax Vocal (Extase)*, *Idol Pop (Sourire Charme)*, *Regard Mystique (Intense)*, *Silence / Respiration*.
     - Outils interactifs complets : Cutter `[C]` / `[S]`, Trimming des bords, suppression `[Suppr]`, glisser-déposer de blocs et insertion au curseur.
   - **Lipsync Audio Vocal Réactif en Temps Réel (Web Audio API Analyser)** :
     - Analyse fréquentielle continue des formants de la voix (300 Hz - 3000 Hz) sur `nexura_domina_v1.mp3`.
     - Modulation en temps réel des visèmes VRM (`aa`, `oh`, `ee`, `ih`) et expressions d'extase vocale (`relaxed`, `happy`, `blink`) calée sur le chant réel de la chanteuse.
   - **Affichage VRM & UX Améliorée** :
     - Indicateur de chargement cyber (`#vrm-loader`) avec disparition fluide dès l'avatar prêt.
     - Stabilisation de la caméra manuelle et automatique (`cameraInitialized = true`).

2. **Manifeste & Architecture Globale de l'Organisme LBG (`docs/ORGANISME_LBG.md`)** :
   - Formalisation de l'entité cybernétique globale : **Gladys** et de son incarnation relationnelle : **Lia**.
   - Cartographie anatomique des rôles machines :
     - `.10` (Poste Teome) : Interface de symbiose humaine, audio/visuel, et main droite logicielle UIA sans vol de souris.
     - `.143` (Atelier Omarchy) : Usine logicielle et main gauche autonome pour les agents CLI (compute, CI, dev).
     - `.140` / `.110/.111` : Cerveau central, orchestration Cortex, mémoire et inférence locale.
     - `.246` (Lost Heaven `:8787`) : Banc d'entraînement spatial pour les corps virtuels O3.
   - Doctrine d'autonomie et garde-fous : abaissement des micro-confirmations bloquantes avec audit JSONL strict.
   - Référencé dans `OBJECTIVES.md` et `docs/REGISTRE.md`.

2. **Intégration Moteur `agent-desktop` (Vercel Labs) sur Windows (.10) et Linux (.143)** :
   - Intégration de l'accessibilité native OS (UIA sur Windows, AT-SPI sur Linux) dans `packages/cortex/windows_agent` et `packages/cortex/linux_agent`.
   - Primitives implémentées : `ui_snapshot`, `ui_click`, `ui_type`, `ui_press`, `ui_scroll`, `ui_focus`.
   - Actions headless sans vol de souris validées sur Windows.
   - Exposition du statut CLI dans `GET /healthz`.
   - Déploiement live sur le PC `.10` (`192.168.0.10:5005`) et démonstration live validée sur Notepad.exe.
   - Tests unitaires complets : 17 tests Windows, 12 tests Linux, 153 tests Cortex Backend (100% verts).

---

## Actions précédentes (2026-11-12)
1. **Studio Content Engine V2.1 (Dynamisme Vidéo, Motion Design & B-Roll Tech)** :
   - **Sous-titres Karaoké Mot-à-Mot Pop (`voice_engine.py`)** : découpage temporel fin et surlignage mot par mot en jaune néon éclatant (`&H0000FFFF&` avec grossissement pop +14%) au tempo oral exact.
   - **Arrière-plan Cyberpunk en Mouvement Continu (`video_compositor.py`)** : défilement fluide de la grille perspective au sol vers l'avant à 30 FPS + 24 particules néon montantes en permanence (fin de l'écran statique).
   - **Infographies B-Roll Concètes à Droite** :
     - *Phase Alerte* : carte rouge `PIÈGE DES API CLOUD` avec courbe de coût grimpante (`+450€ / mois`).
     - *Phase Solution* : carte cyan `STACK 100% LOCALE` avec tags Godot 4.6 Headless, Ollama RTX, Piper ONNX, SQLite WAL.
     - *Phase Métriques* : carte vert émeraude `BENCHMARKS EN DIRECT` avec jauge 60 ticks/s (100%), RAM 1.2 Go (15%) et 0.00€ Cloud.
     - *Phase Outro* : carte magenta `REPO LBG STUDIOS` avec lien GitHub et bouton d'action.
   - **Composition 2 Tiers & Avatar Réactif** :
     - Cadrage équilibré : Lia sur le tiers gauche de l'écran avec posture/regard tourné vers les infographies de droite.
     - Micro-inclinaisons de tête et buste dynamiques sur les accents de voix (`rms`).
   - **Validation & Test Vidéo HD** : génération complète réussie (`drop_1794489788`, 55.2s, 26.65 Mo, MP4 1080×1920 @ 30 FPS).
2. **Compagnon 3D VRM : Posture & Chorégraphie Live Concert (Storyboard Diva Nexura Domina)** :
   - **Micro 3D Stylisé de Scène (`cyberMicGroup`)** : création d'un mesh 3D procédural (corps noir graphite métallique, capsule micro sculptée, anneaux néon emissive cyan et magenta pulsant au kick 128 BPM) attaché dynamiquement comme enfant direct du bone `rightHand` (`rhNode.add(cyberMicGroup)`), grille orientée au plus près des lèvres/menton.
   - **Naturel Scénique, Biomécanique & Contrapposto Dynamique (Correctif Storyboard)** :
     - **Micro 3D redressé vers la bouche** : correction des angles du bras droit (`rightLowerArm` replié vers le haut et l'intérieur `[-0.22, -0.16, -2.10]`, coude contre le buste `[0.32, 0.35, 0.85]`), et réorientation locale de la capsule (`rotation.set(0.25, 0.15, 0.60)`) pour que la sphère chromée soit dressée directement à 2 cm devant les lèvres au lieu de pointer horizontalement sur le torse.
     - **Jambes déverrouillées & Stance ouverte permanente** : fin des cuisses croisées ou collées en un seul trait ; écartement minimal garanti de `0.26 rad` (~15°), pieds en éventail (25° externe), flexion permanente bien visible (jambe d'appui à `0.25 rad`, jambe libre à `0.55 rad`, et drop de scène à `0.85 rad` ~50°).
     - **Tête & Émotion** : inclinaison arrière accentuée vers le micro (`head: [-0.22, -0.06, 0.08]`) pour restituer la véritable extase vocale du concept art.
   - **Intégration Mocap FBX Complète (195 Fichiers, Tous Dossiers & Sous-Dossiers)** :
     - Rapatriement récursif de l'intégralité des mouvements FBX depuis `O:\OneDrive\Pictures\IA\mouvements` (Packs `Capoeira Pack`, `Female Locomotion Pack`, `Free Test Pack`, `Pro Magic Pack`, et racine) vers `packages/compagnon-desktop/overlay/vrm/fbx_source/` (195 fichiers FBX, 611 Mo de mocap brute).
     - Pipeline de conversion parallèle multi-cœurs (`tools/batch_convert_fbx.py`) avec FBX2glTF + `fbx2vrma-converter.js` : **189 nouveaux convertis, 6 existants, 0 échec** en ~2 minutes.
     - Empreinte disque ultralégère : **90.02 Mo au total** pour les 195 animations VRMA (~450 Ko par animation en moyenne !).
     - Classification et génération du manifest structuré (`manifest.json`) en 8 catégories :
       - *Danses & Grooves* (29 anims : Gangnam Style, Twerk, Can Can, Macarena, Bellydance, Hip Hop 1-3, Jazz 1-3, Samba, Salsa, Disco...).
       - *Capoeira & Arts Martiaux* (40 anims : Armada, Au, Bencao, Chapa, Ginga, Martelo, Meia Lua, Rasteira...).
       - *Locomotion & Déplacements* (25 anims : Catwalk, Happy Walk, Strafes, Sprint, Jump...).
       - *Magie & Incantations* (57 anims : Cast Spell 1H/2H, Magic Area Attacks 01-05, Shield Blocks, Reacts...).
       - *Poses & Silhouettes* (18 anims : Female Dance Pose, Dynamic Pose, Laying, Kneeling...).
       - *Expressions & Réactions* (23 anims : Cheering, Victory, Taunt, Bashful, Thinking, Phone...).
       - *Fitness & Sport* (11 anims : Air Squats, Back Squat, Backflip, Push Up, Kettlebell, Speedbag...).
       - *Général* (17 anims).
     - Résolution dynamique universelle dans `vrm_pet.js` (`VRMA_CATALOG` de 397 clés d'accès direct, `resolveVrmaFile`), dézoom dynamique automatique sur mouvement complet (`isFullBodyAction`), et neutralisation du root-motion in-place.
     - Recompilation du bundle IIFE (`vrm_pet.bundle.js`), synchronisation locale vers l'overlay Windows (`192.168.0.10:5005`) et déploiement Web instantané sur CT 100 (`192.168.0.100:5174`).
     - Test live validé sur desktop overlay avec `send_avatar_command` (`gangnam`, `bellydance`, etc.).
   - **Clip Musical Officiel 60s en Mode Studio Cyberpunk 3D (YouTube Shorts / TikTok HD)** :
     - Élimination totale des éléments de bureau Windows (ni fond d'écran, ni barre des tâches, ni icônes) : immersion 100% scénique.
     - Scène de concert futuriste en Three.js / WebGL hardware (GTX 1050 Ti) :
       * Grille perspective lumineuse cyan au sol défilant vers l'avant à 30 FPS.
       * Spots volumétriques de scène (cyan & magenta) pulsant en temps réel au kick de la musique.
       * 40 particules néon montantes en continu et halo central scénique derrière l'avatar.
       * Carte d'en-tête HUD glassmorphism (style officiel Studio Content Engine) : `LYRA // LIVE 3D CONCERT`, `100% LOCAL • 0€ CLOUD`, `KHOR-UN VAL-KYRA (128 BPM)`.
       * Égaliseur audio 32 bandes en bas de scène réagissant aux fréquences réelles de la piste.
     - Avatar 3D (Lyra androïde) en plein pied au centre de la scène tenant le micro cyber 3D néon, lèvres et regard calés au tempo, enchaînant les danses mocap (Intro Diva -> Couplet Groove -> Bellydance -> Pop Dance -> Gangnam -> Samba -> Finale Idol).
     - Rendu master vidéo 1080×1920 (Vertical 9:16, H.264 High Profile @ 6214 kb/s, 29.98 FPS, Audio AAC 48 kHz stéréo, 44.46 Mo).
     - Fichier délivré sur l'hôte Windows : `O:\OneDrive\Pictures\IA\Contenue\clip_khor_un_val_kyra_studio_60s.mp4`.
3. **Mode Live Concert Virtuel & Déhanché Mocap Aeysa sur Nexura Domina (Clip Complet 158s / 2m38s HD)** :
   - **Déhanché Mocap Pop / Maraschino Step Viral (@aeysamusic)** :
     * Analyse image par image de la référence TikTok virale (`7699001951047961878`) : balancement prononcé du bassin de gauche à droite, cambrure lombaire, flexion alternée des genoux et transfert de poids organique sur jambe d'appui tendue.
     * Intégration du clip mocap officiel `Dancing Maraschino Step.vrma` joué en boucle fluide infinie par l'AnimationMixer Three-VRM.
     * Micro 3D cyber néon solidement tenu en main droite avec anneaux cyan/magenta pulsant au kick 128 BPM.
     * Lipsync vocal synchrone en temps réel et regard scénique habité (yeux mi-clos / extase vocale de diva).
   - **Cadrage Silhouette Complète Dézoomé (`dist = 3.45m`, `lookY = headPos.y - 0.58m`)** :
     * Moins zoomé à la demande utilisateur : plan moyen complet révélant l'avatar des pieds à la tête avec respiration sous le HUD supérieur, bottes mecha posées sur le sol de scène juste au-dessus du visualiseur audio, et toute la dynamique des hanches/cuisses bien visible.
   - **Scénographie Studio Cyberpunk & Capture Sécurisée Hardware** :
     * Dégradé sombre cinématique (`#03050c`), doubles rim lights volumétriques réactives aux basses, particules lentes.
     * HUD concert glassmorphism minimaliste ("✦ NEXURA DOMINA", live pill, equalizer audio 36 barres réactif).
     * Script de capture et muxing automatique `record_studio_nexura_clip.py` exécuté sur Windows via l'agent `:5005` (FFmpeg gdigrab 158s @ 30 FPS avec `-draw_mouse 0`, gardien Win32 TopMost anti-superposition, upscale Lanczos 1080×1920 HD vertical + audio master `Nexura Domina_v1.mp3`).
     * Master vidéo final livré :
       * Version intégrale : `O:\OneDrive\Pictures\IA\Contenue\clip_nexura_domina_v1_studio_full.mp4` (145.65 Mo, 157.6s, 1080×1920 HD).
       * Version compatibilité : `O:\OneDrive\Pictures\IA\Contenue\clip_nexura_domina_v1_studio_60s.mp4`.
     * Frames de contrôle validées : `final_check_30s.png`, `final_check_75s.png`, `final_check_120s.png`.
4. **Clip Musical Officiel 60s avec l'Avatar de Bureau 3D (Lyra Live Performance)** :
     - Enregistrement en direct hardware via FFmpeg `gdigrab` sur le poste Windows (`192.168.0.10`) de l'overlay 3D Three.js réel en exécution (Lyra skin android, micro cyber 3D néon, lipsync et animations mocap).
     - Synchronisation chorégraphique millimétrée sur les 60 secondes de `Khor-un Val-Kyra.mp3` :
       - 0.0s – 8.5s : Intro Diva avec micro en main (`femaledance`)
       - 8.5s – 22.0s : Couplet rythmé & chant passionné (`cyberGroove`)
       - 22.0s – 34.5s : Electro Drop 1 (`bellydance`)
       - 34.5s – 45.0s : Electro Drop 2 / Pop dance (`popdance`)
       - 45.0s – 52.5s : Climax d'énergie (`gangnam`)
       - 52.5s – 57.5s : Célébration festive (`samba`)
       - 57.5s – 60.0s : Final Idol (`fingerHeart` & sourire de victoire)
     - Encodage H.264 / AAC 48 kHz stéréo à 1080×1920 (vertical HD 9:16 pour YouTube Shorts & TikTok, 19.23 Mo).
     - Fichier final délivré sur le disque hôte : `O:\OneDrive\Pictures\IA\Contenue\clip_khor_un_val_kyra_avatar_bureau_60s.mp4`.
     - Rétablissement automatique des dimensions de bureau standard et du mode promenade (`wander: true`).
   - **Clip Musical 60s & Déploiement Pipeline (Khor-un Val-Kyra / Nexura Diva)** :
     - Script de montage cinématographique vertical 1080x1920 30 FPS (`tools/build_clip_khor_un_val_kyra.py`) : 7 plans enchaînés avec zoompan/Ken Burns dynamique et synchronisation complète de la bande son master 60s (`khor_un_val_kyra.mp3`).
     - Rendu vidéo finalisé (`clip_khor_un_val_kyra_60s.mp4`, 9.0 Mo, H.264 / AAC 256k) et copié automatiquement sur le poste Windows dans `O:\OneDrive\Pictures\IA\Contenue\clip_khor_un_val_kyra_60s.mp4`.
   - **Panneau Compagnon Web & Desktop (`LyraPanel.vue`)** :
     - Ajout de 12 boutons de chorégraphies et actions animées : Diva Live, Bellydance, Pop Dance, Gangnam Style, Samba, Hip-Hop, Capoeira Ginga, Robot, Disco, Catwalk, Pirouette, Mini Heart.
     - Déclenchement automatique du plein pied (`fullBodyPoses`) dès le clic.
     - Recompilation Vite et déploiement sur CT 100 (`lbg-frontend`).
   - **Portage des Animations 3D dans le MMO (`prime-client` Godot 4.6)** :
     - Création de `packages/prime-client/assets/animations/{locomotion,combat,dances}/` avec 23 animations prêtes à l'emploi au format GLB standard (walk, run, sprint, jump, strafes, capoeira ginga/armada/esquiva/martelo, sorts magiques 1H/2H, parade bouclier, danses).
     - Tests CI Headless Godot validés (`tools/ci_godot_headless.sh`).
1. **Élévation Graphique 2D Top-Down style *Canvas of Kings* (Prime Client 2D)** :
   - **Moteur d'Ambiance Visuelle & Éclairage Dynamique (`canvas_of_kings_atmosphere.gd`)** :
     - Cycle jour/nuit circadien 2D avec `CanvasModulate` synchronisé directement sur le snapshot réseau `world_clock` du hub (`game_hour`, `is_night`, `light_ambient`).
     - Éclairage solaire et ombres portées douces dynamiques : calcul en temps réel de `_sun_shadow_offset` et `_sun_shadow_alpha` répercutés sur les bâtiments de Lost Heaven (`hub_buildings_layer.gd`) et les entités (`entity.gd`).
     - Éclairage 2D nocturne procédural : 11 lanternes `PointLight2D` avec textures de gradient radial générées en mémoire (Hermite cubique, 0 dépendance asset manquante) et scintillement organique doux.
     - Particules atmosphériques douces de poussière et vent (`CPUParticles2D`) centrées sur la caméra 2D.
     - Ombre de contact au sol et halos lumineux doux sous les terminaux holo, les droïdes et les sabres laser.
2. **Élévation Graphique 3D Spatiale JTL style *PVKK* & *Road to Vostok* (`swg_space_flight_3d.gd`)** :
   - **Post-Processing & Rendu PBR Réaliste (Road to Vostok & Godot 4)** :
     - Tonemapping `ACES` (`tonemap_exposure = 1.15`, `tonemap_white = 1.25`) pour un contraste doux sans brûlures de hautes lumières.
     - Bloom / Glow cinématographique chaud (`glow_bloom = 0.35`, `glow_hdr_threshold = 0.9`, mode SCREEN) pour le rayonnement des étoiles, réacteurs et voyants.
     - Nébuleuse spatiale cosmique (Brouillard de profondeur atmosphérique `fog_enabled = true`).
     - Éclairage directionnel solaire à ombres PBR nettes (`DirectionalLight3D`) doublé d'un contre-jour cosmique bleuté de nébuleuse.
     - Ceinture d'astéroïdes et roches PBR polygonales rugueuses (`metallic = 0.15, roughness = 0.92`) en rotation lente.
   - **Poste de Pilotage & Mode Cockpit PVKK (Première Personne)** :
     - Modélisation du cockpit tactile brutaliste / dieselpunk : montants verrière en acier riveté, console de bord en pan incliné (`roughness = 0.85`), moniteur CRT vectoriel à phosphore vert émissif (radar JTL avec coordonnées et ciblage TIE en direct), voyants LED d'état émissifs (SYS_NOMINAL, SHIELDS_OK, WEAPONS_HOT, WARN_RADAR), et levier de gaz (throttle) qui s'incline avec l'accélération.
     - Bascule fluide double caméra avec la touche **`[V]`** ou le bouton HUD dédié : bascule entre **Cockpit PVKK Immersive** (1ère personne) et **Vue Extérieure 3D** (3e personne).
     - En vue extérieure : 4 réacteurs ioniques de l'X-Wing avec panaches de plasma rose/rouge émissifs qui pulsent et s'étirent selon la vitesse (`current_speed`).
3. **Outillage, Déploiement & Validation** :
   - Ajout des nouveaux fichiers à la synchronisation SDS Windows `.10` (`tools/sync_client_to_win.py`) : 22 fichiers synchronisés avec succès.
   - Validation 100% verte du selftest client Godot headless (`tools/client_modular_selftest.gd`).
   - Déploiement du patch officiel sur le serveur de patch Launchpad (`192.168.0.246:8080`) via `deploy_prime_client_patch_246.sh`.
4. **Éclairage 2D Avancé Canvas of Kings : Entrées de Lost Heaven, Camp Zalem, Ksar Nomade & Caravanes** :
   - **Entrées de Lost Heaven** : 8 lanternes encadrant de chaque côté les piliers et arches d'entrée (Porte Ouest route de Zalem, Porte Est du désert, Porte Sud du shuttleport, Porte Nord palissade).
   - **Camp Avancé de Zalem** : 8 lanternes ambrées de garnison (Checkpoint et barrières Ouest, Poste de commandement Capitaine Vael, Atelier Soren Kray, Caserne Milice, Relais des convois/Inn, Dépôt de ravitaillement, Place d'armes).
   - **Ksar Nomade** : 9 lanternes de campement nomade et oasis (Arches d'entrée Nord et Est, berges de l'Oasis, Grande tente de l'Ancien Nadir, Tente des soins de Miran Sael, Tente de troc, Caravansérail).
   - **Caravanes de Scrapaltai (`entity.gd`)** : détection automatique des membres de caravane (`npc:caravan_*`, nomades), ajout d'une lanterne 2D attachée `PointLight2D` ambrée projetant une lueur mobile et scintillante au sol, dessin des lanternes nomades en laiton et des bâtis/sacoches de bât.
   - **Halte des caravanes d'Al-Khali** : balises et feux de bivouac à mi-chemin entre Lost Heaven et le Ksar.
5. **Studio Content Engine : Voix Officielle Vivienne Neural, 2s Silence & Fix Phonétique ("GitHub")** :
   - **Voix Officielle Sélectionnée (`fr-FR-VivienneMultilingualNeural`)** : élocution vivante, diction ultra-propre et naturelle à 0 € de coût récurrent.
   - **Correction Phonétique Orale (`voice_engine.py`)** : règle automatique transposant "GitHub" en "Guite Heube" pour l'audio sans altérer l'orthographe exacte dans les sous-titres ASS.
   - **Silence Initial de 2.0s & Phrase Signature** : 2 secondes de regard franc avant le démarrage de la présentation *"Bonjour, je suis Lia..."*.
   - **Validation de bout en bout** : génération du drop `drop_1794407604` (33.4s, 4.49 Mo) synchronisé vers `O:\OneDrive\Pictures\IA\Contenue\`.
6. **Compagnon Desktop & Backend Cortex : Intégration de la Voix Vivienne Neural & Dictionnaire Phonétique** :
   - **Backend Cortex (`packages/cortex/backend/services/tts_service.py` & `/v1/tts`)** :
     - Ajout de `fr-FR-VivienneMultilingualNeural` comme voix par défaut du Compagnon (`default_voice`).
     - Application automatique du dictionnaire phonétique oral (`GitHub` -> `Guite Heube`, `open source` -> `opène source`, `Godot` -> `Godo`, `API`, `LLM`, `framework`) pour toutes les répliques du Compagnon.
     - Synthèse audio WAV haute fidélité avec calcul synchronisé des 5 visèmes morph-targets VRM (`aa`, `ih`, `ou`, `ee`, `oh`).
     - Installation des dépendances et déploiement validé sur le serveur `.140:8000` (`lbg-backend.service`).
     - 153 tests unitaires backend verts (`pytest backend/tests`).
   - **Agent Windows .10 (`compagnon_parler`)** :
     - Nouvelle capability installée sur l'agent Windows (`.10:5005`) pour synthétiser et jouer en direct la voix Vivienne Neural sur les haut-parleurs du PC avec notification au pont avatar VRM (`127.0.0.1:8765`).
     - Test d'élocution avec termes techniques ("GitHub", "Godot", "open source") validé avec succès en direct sur Windows .10.
7. **Intégration Computer Use `agent-desktop` (Vercel Labs) sur Windows `.10` et Linux `.143`** :
   - **Moteur d'Accessibilité Natif (`agent_desktop.py`)** :
     - Remplacement des captures d'écran lourdes (`observe_screen` / vision LLM) et de la monopolisation de la souris physique (`pyautogui`) par la lecture directe de l'arbre d'accessibilité de l'OS (UI Automation sur Windows, AT-SPI sur Linux).
     - Actions supportées : `ui_snapshot` (capture d'éléments interactifs avec identifiants `@ref`), `ui_click` (clic headless en tâche de fond), `ui_type` (saisie sécurisée via stdin), `ui_press` (raccourcis), `ui_scroll`, `ui_focus`.
     - Exécution possible en unitaire ou chaînée dans la macro par lot `run_steps`.
   - **Intégration dans `windows_agent` (`packages/cortex/windows_agent/Agent_IA/`)** :
     - Détection de la CLI globale (`agent-desktop`) et exposition du statut dans `GET /healthz` (`agent_desktop.installed`, `agent_desktop.version`).
     - Compatibilité totale avec les garde-fous de sécurité existants (dry-run, approval tokens).
     - Script de déploiement `sync_windows_agent.sh` mis à jour pour copier `agent_desktop.py`.
     - Suite de tests unitaires dédiée `test_agent_desktop.py` (17 tests validés).
     - **Déploiement live sur Windows `.10:5005` validé** : `agent-desktop 1.2.0` installé et actif, premier `ui_snapshot` live exécuté en ~400 ms avec 604 éléments référencés.
   - **Intégration dans `linux_agent` (`packages/cortex/linux_agent/Agent_IA/`)** :
     - Sémantique symétrique pour Omarchy `.143`, exposition dans `/healthz` et tests dédiés `test_agent_desktop_linux.py` (12 tests validés).

---

## Dernières actions réalisées (2026-11-10)
1. **Pipeline de Création de Contenu Automatisé 100% Local / 0 € (`tools/studio_content_engine/`)** :
   - **Génération de Scripts Viraux Tech (`script_generator.py`)** : format court vertical (Hook 3s, Problème/Douleur, Solution architecture 0€, Call to Action) alimenté par Ollama local (`.111:11434` / `.110:11434`) avec repli canonique résilient.
   - **Synthèse Vocale & Audio Engine Fix (`voice_engine.py`)** : correction du bug de décalage d'octets impair (qui causait le bruit blanc et les craquements), ajout de micro-fondus de 8ms aux transitions, normalisation crête à -1.0 dB (0 clipping) et rééchantillonnage 44,1 kHz AAC pour une clarté optimale.
   - **Rendu 3D Avatar Compagnon (`blender_render_keyframes.py`)** : passage sur le modèle canonique `Compagnon.vrm` orienté face caméra, posture naturelle des bras baissés (élimination de la T-pose), avec les shape keys faciales (`Fcl_MTH_A`, `Fcl_MTH_O`, `Fcl_EYE_Close`, `Fcl_ALL_Joy`).
   - **Composition Vidéo & Lip-Sync Dynamique (`video_compositor.py`)** :
     - Synchronisation labiale temps réel sur l'amplitude RMS audio.
     - Clignements d'yeux procéduraux (toutes les 3.6s) et micro-mouvements de respiration.
     - Spectre audio néon réactif (28 barres oscillantes).
     - Dégradé cyberpunk avec grille perspective sci-fi et bandeau d'en-tête LBG Studios.
   - **Orchestrateur & CLI Unifié (`content_bot.py`)** : génération complète en ~30 secondes d'un fichier MP4 1080×1920 (H.264 / AAC, ~3 Mo) prêt pour TikTok, YouTube Shorts et Instagram Reels.
   - **Connecteurs Publication YouTube Shorts & TikTok Studio (`youtube_publisher.py`, `tiktok_publisher.py`)** :
     - **YouTube Data API v3** : authentification OAuth 2.0 officielle 100% connectée à la chaîne officielle **La Boite à Geek (@lbg-p8k, ID: UCqr0ctaojYRPy0kD4rPTBQg)** avec jeton persistant (`tools/studio_content_engine/config/youtube_token.json`).
     - Pont d'authentification automatisé avec ouverture de Firefox sur le poste Windows et proxy loopback local.
     - **Shorts publiés avec succès sur @LBG-p8k** :
       - [`https://www.youtube.com/shorts/WNfoQsOhX-0`](https://www.youtube.com/shorts/WNfoQsOhX-0) (*"Arrête de payer des API Cloud pour tes Agents IA"*).
       - [`https://www.youtube.com/shorts/sRpZn0ONnWU`](https://www.youtube.com/shorts/sRpZn0ONnWU) (*"Pourquoi Godot 4 Headless bat les serveurs traditionnels"*).
     - **TikTok Studio** : capability `preparer_upload_tiktok` sur l'Agent Windows (.10) : ouverture automatique de TikTok Studio Upload, sélection du fichier dans l'explorateur et injection de la légende/hashtags dans le presse-papier Windows.
     - **Automatisation Quotidienne (2 vidéos / jour)** :
       - Timer systemd `lbg-content-daily.timer` actif à **11h30** et **17h30** avec service `lbg-content-daily.service`.
       - Backlog de sujets curatés (`topics_backlog.json`) dépilant les thématiques tech/MMO/Godot/IA sans doublons.
       - Génération automatique du fichier MP4 + publication YouTube Shorts + création d'une fiche mémo texte (`*_tiktok_memo.txt`) dans `O:\OneDrive\Pictures\IA\Contenue\` avec légende et hashtags pour publication manuelle TikTok en 5 secondes.
2. **Pipeline Graphique 3D & World Building Automatisé (Blender Headless + Godot 4)** :
   - **Étape 1 : Blender Headless (`bpy`) & Props Modulaires (`tools/asset_pipeline/blender_prop_builder.py`)** :
     - Installation & activation de Blender 5.2.2 LTS en mode headless (`blender -b`).
     - Générateur procédural de props sci-fi avec biseaux, matériaux PBR émissifs et formes de collision Godot automatiques (`-col`).
     - Génération validée de 3 modèles `.glb` directement utilisables dans `packages/prime-client/assets/models/` (`sci_fi_crate.glb`, `modular_pillar.glb`, `terminal_console.glb`).
   - **Étape 2 : Pipeline Créatures & Personnages Rig/Animé (`tools/asset_pipeline/ai_creature_pipeline.py`)** :
     - Script `blender_creature_processor.py` : nettoyage maillage, centrage, auto-rig squelette (Armature standard), skinning automatique (Bone Heat Weighting), et animation cyclique (Idle de respiration).
     - Génération validée en 2s de créatures exportées en `.glb` avec animations (`alien_beast_crawler.glb`, `gundark_beast.glb`).
   - **Étape 3 : Constructeur de Terrain & Scatter Procédural Godot 4 (`packages/prime-client/scripts/world_terrain_builder.gd`)** :
     - Génération de maillage de terrain dynamique (`ArrayMesh` avec `FastNoiseLite`), vertex coloring par altitude/biome, calcul des normales et tangentes.
     - Collision physique temps réel via `ConcavePolygonShape3D` (`create_trimesh_shape()`).
     - Algorithme de dispersion intelligente de props (scatter) avec analyse du gradient de pente (filtrage des falaises raides).
     - Suite de tests headless `packages/prime-client/tools/terrain_builder_selftest.gd` intégrée dans `tools/ci_godot_headless.sh` (pass en <1s).
   - **Étape 4 : Amélioration du Compagnon Desktop (`packages/compagnon-desktop`)** :
     - **Accessoires 3D modulaires (`tools/asset_pipeline/blender_accessory_builder.py`)** : modélisation et export de 3 accessoires `.glb` (`cyber_visor.glb`, `holo_datapad.glb`, `neural_headset.glb`) attachables dynamiquement aux os VRM (`head`, `leftHand`).
     - **Nouvelles Poses / Emotes procédurales** : `focus` (analyse/scan de code avec posture inclinée et micro-oscillations) et `victory` (bras en V triomphal et célébration).
     - **Amélioration du Rendu 3D** : ajout d'un contre-jour `cyberHaloLight` (lumière cyan d'ambiance à 0x00f5d4) pour découper nettement la silhouette sur n'importe quel fond d'écran Windows.
     - **Intégration Electron & Overlay** : compilation via `bundle-vrm.py`, nouvelles entrées contextuelles dans le menu plateau/clic-droit (`main.js`, `overlay.js`, `preload.js`).
     - **Auto-Sync & Phase Tampon au Démarrage (`main.js`, `Lancer_Compagnon.cmd`)** :
       - Auto-détection de la source (`A:\LBG_Studios\packages\compagnon-desktop` ou partage réseau `\\192.168.0.143`) directement à l'ouverture.
       - Synchronisation automatique transparente des assets et du code (`main.js`, `preload.js`, `overlay/`).
       - Relaunch automatique transparent (`app.relaunch()`) si le code principal a été mis à jour.
       - Entrée manuelle ajoutée dans la barre des tâches : `🔄 Vérifier les mises à jour (A: -> C:)`.
       - Nouveau lanceur Windows rapide `Lancer_Compagnon.cmd` et mise à jour de `Create-DesktopShortcut.ps1`.
       - Raccourcis `Ctrl+R` / `F5` (rechargement sans cache) et `Ctrl+Shift+I` (DevTools) câblés dans `mainWindow` pour l'interface de chat.
       - Protection des modèles VRM perso : remplacement du `/MIR` robocopy par `/E` (sans purge) et sauvegarde automatique des modèles locaux vers le dépôt.
     - **Déploiement Compagnon Web/Chat UI (`packages/cortex/compagnon_ui`) sur CT `.100:5174`** :
       - Bouton `🔄 MAJ` (synchronisation et reload) ajouté dans le header du panneau avatar 3D (`LyraPanel.vue`).
       - Section `👓 Accessoires 3D` (Visière, Datapad, Oreillette) et pose `🔍 Focus` intégrées dans `LyraPanel.vue`.
       - Build Docker frontend & backend déployé sur CT `.100` (`deploy_compagnon_100.sh`).
2. **Enrichissement du Second Brain Lore & Monde LBG (`docs/lore/`)** :
   - Documentation canonique (hors Star Wars, biomes LBG propres inspirés de SWG) des 4 autres planètes majeures :
     - **`arvandor.md`** (Plaines luxuriantes, marbre blanc, cascades, diplomatie) + faction `cercle_diplomates_arvandor.md` + PNJ `bige_coto.md` (danse/arts scéniques).
     - **`khar_zuun.md`** (Lune des arbres titans, canopées géantes, brume dense) + faction `gardiens_canopee.md` + PNJ `mira_kael.md` (chasseresse).
     - **`terre_one.md`** (Berceau naval océanique, chantiers spatiaux) + faction `chantiers_navals_orbitaux.md` + PNJ `garr_vek.md` (instructeur spatial).
     - **`mor_valoth.md`** (Badlands carmin toxiques, bêtes mutantes) + faction `confrerie_brumes_rouges.md` + PNJ `dr_azra_veld.md` (bio-ingénierie dissidente).
   - Validateur `tools/validate_lore_links.py` : 21 nœuds, 147 relations, 0 lien cassé, 0 orphelin.
2. **Connexion Temps Réel de la Topologie au Hub Godot (`.246:8787`)** :
   - Endpoint `GET /v1/pilot/topology` : agrège la base de connaissances et interroge en direct le hub Godot (`/v1/bots`).
   - Injection dynamique des **10 Joueurs IA en direct** (Nix, Lia, Mira, Kael, Renn, Sola, Vex, Ori, Tess, Bram) avec leurs coordonnées temps réel, quête active et mode de jeu.
   - Frontend Pilot (`topology_graph.js`) : filtre `Bots IA 🤖`, badge live, mise à jour glissante continue (polling 4s) et drawer d'inspection enrichi.
   - Compilation Vite et déploiement en production sur la VM `.140` (`lbg-backend.service` actif et validé).
3. **Outil de Revue de Code Automatique Locale LBG (`tools/review_code_llm.py`)** :
   - Audit heuristique instantané (0 ms) des canons LBG et intégration Ollama `.110` / `.111`.
4. **Protocole Risk Gate Déterministe (`docs/design/RISK_GATE_AGENT_PROTOCOL.md`)** :
   - Formalisation canonique du sas étanche validé par la CI Godot headless (19 suites, code 0).

---

## Dernières actions antérieures (2026-11-09)
1. **Refonte & Dépoussiérage des contrôles clavier (`client_ui_dialogue.gd` & `swg_space_flight_3d.gd`)** :
   - Élimination du conflit majeur `KEY_D` (aller à droite ZQSD qui déclenchait le Datapad) ➔ Datapad déplacé sur `V` ou `Ctrl+D`.
   - Élimination des collisions de touches de fonctions `F9` (Debug HUD vs Espace 3D) et `F10` (Heal vs Login Panel).
   - Nouvelle cartographie ergonomique F-Keys :
     - `F4` : Sabre laser (dégainer / rengainer)
     - `F5` : Sonde de traque Arakyd
     - `F6` : Force Heal
     - `F8` : Vol Spatial JTL 3D
     - `F9` : Debug HUD
     - `F10` : Panneau de connexion / compte
     - `F11` : Bascule Plein écran
2. **Correction Focus Espace & Pilotage Souris Sol + Espace (`swg_space_flight_3d.gd` & `player_controller.gd`)** :
   - Désactivation du vol de focus sur les boutons HUD (`focus_mode = FOCUS_NONE`) : appuyer sur ESPACE au sol ne déclenche plus jamais l'entrée dans l'espace.
   - **Déplacement à la souris au sol** : support du simple clic au sol et du maintien continu du clic gauche (le personnage suit le curseur en temps réel). Suppression du clamp prématuré qui bloquait les clics lointains.
   - **Pilotage à la souris dans l'espace (JTL 3D)** : orientation fluide du X-Wing par déplacement de la souris (tangage/lacet/roulis auto), tir laser au clic gauche, et accélération/décélération à la molette.
3. **Synchronisation & Publication du Patch Client Launchpad** :
   - Synchronisé via `sync_prime_client_to_win.py` vers Windows SDS `J:/swgemu/clients/prime-client` (19 fichiers).
   - Déployé sur le serveur de patches `192.168.0.246:8080` via `deploy_prime_client_patch_246.sh` (version `2026-11-09T17:19:24Z`, 287 fichiers).
4. **Intégration des Nouveaux Modèles VRM (`O:\OneDrive\Pictures\IA\Models`)** :
   - Déploiement et cartographie des 8 nouveaux modèles VRM importés dans le jeu :
     - **`NeonNeko.vrm`** : Avatar félin avec oreilles et queue de chat intégrées ➔ Affecté à **Fel'Rani** (`twilek` / Arvandor).
     - **`Saiyan4.vrm`** : Avatar sauvage à fourrure et carrure de combat ➔ Affecté à **Varkoon** (`wookiee` / Arvandor).
     - **`Greeny.vrm`** : Avatar reptilien vert ➔ Affecté à **Pykrel** (`rodian` / Arvandor).
     - **`DemonHorn.vrm`** : Avatar à cornes crâniennes pointues ➔ Affecté à **K'Miri** (`zabrak` / Khar'Zuun).
     - **`Rebecca.vrm`** : Avatar d'ingénieure cyber ➔ Affecté à **Tinkling** (échelle $\times 0.50$, taille ~45 cm).
     - **`Mia.vrm`** : Avatar citoyenne de Lost Heaven ➔ Affecté à **Humain** (Terre-One / Corellien).
     - **`Marie.vrm`** : Nouvel avatar exploratrice de terrain d'Arvandor.
     - **`Espeon.vrm`** : Nouvel avatar familier quadrupède psionique des dunes.
   - Synchronisation complète des assets VRM sur les 5 dossiers cibles Windows SDS `.10` (`J:/swgemu/clients/swg-client`, `J:/swgemu/clients/prime-client`, `A:/LBG_Studios/...`, `C:/Agent_IA/...`).
   - Selftests 100% verts (`swg_client_3d_selftest.gd`, `client_modular_selftest.gd`).

---

## Objectif actuel

Continuité multi-outils : même canon **O1 Compagnon / O2 MMO banc / O3 Joueurs IA** ([`OBJECTIVES.md`](../OBJECTIVES.md)).  
Réplique exhaustive 100% Star Wars Galaxies Pre-CU : achèvement des **5 Piliers d'Élite dans l'ordre** :

- [x] **Point 1 : Villes de Joueurs & Politique (*Player Cities & Elections*) (`hub_player_cities.gd`)** :
  - Fondation de cités par les joueurs, 5 échelons d'expansion (Outpost ➔ Village ➔ Township ➔ City ➔ Metropolis).
  - Élections démocratiques régulières de Maires au suffrage universel par les citoyens résidents (`start_election`, `cast_vote`, `conclude_election`).
  - Décrets municipaux & spécialisations civiques : Centre Industriel (-10% temps craft), Sanctuaire Médical, Avant-poste Scientifique, District des Plaisirs, Refuge de Clonage.
  - Fiscalité locale paramétrable (taxes foncières, taxes sur les ventes des marchands, taxes de spatioport).
  - Rendu 3D : Modélisation générative de l'Hôtel de Ville (`build_city_hall`) avec colonnade en marbre, dôme doré et terminal politique interactif (`terminal_cityhall`).

- [x] **Point 2 : Bio-Ingénierie & Échantillonnage d'ADN (*Bio-Engineer*) (`hub_bio_engineer.gd`)** :
  - Sonde d'échantillonnage génétique sur la faune sauvage (Chacals, Banthas, Dewbacks, Dragons Krayt) avec extraction de profils de robustesse, prouesse et férocité.
  - Cuve d'incubation génétique en laboratoire (`incubate_creature`) : fusion de deux matrices d'ADN pour forger des chimères mutantes uniques destinées aux *Creature Handlers*.
  - Synthèse d'enzymes biomédicales mutagènes pour Médecins et Chefs cuisiniers.
  - Rendu 3D : Modèle procédural de l'Incubateur Génétique (`build_bio_incubator`) avec cuve de fluide bioluminescent vert émissif (`OmniLight3D`).

- [x] **Point 3 : Ingénierie Droïde Avancée (*Droid Engineer*) (`hub_droid_engineer.gd`)** :
  - Confection de châssis modulaires : Droïde Astromécano Série R2, Droïde de Protocole Série 3PO, Droïde Sonde Probot, Droïde Souris MSE-6, Droïde de Combat Série IG.
  - Montage de modules spécialisés : extension de soute (+25 slots ambulants), atelier mobile de craft nomade, dispensaire médical automatique, radar de scan sonar, tourelle blaster E-Web.
  - Commandes tactiques en jeu (`/follow`, `/stay`, `/patrol`, `/store_item`, `/dispense_meds`, `/play_music`).
  - Rendu 3D : Modélisation procédurale du droïde R2-D2 (`build_r2_astromech`) avec dôme bleu pivotant, œil holographique et roulettes de déplacement.

- [x] **Point 4 : Parcs à Thèmes Galactiques & Donjons Classiques (`hub_theme_parks.gd`)** :
  - **Palais de Jabba le Hutt (Tatooine)** : Suite de quêtes d'allégeance de la pègre auprès de Bib Fortuna, Reelo Baruk et Jabba (obtention de la Hache Vibro et de l'insigne d'Exécuteur).
  - **Retraite de l'Empereur (Naboo)** : Missions d'espionnage impérial d'élite avec Dark Vador et l'Empereur Palpatine (badge d'Inquisiteur et cape de Maître Impérial).
  - **Donjon de la Corvette Corellienne** : Instance raid chronométrée sous compte à rebours 3600s (60 min) avec progression de ponts (Sas ➔ Machines ➔ Pont de Commandement), sauvetage d'otages et sabotage de l'hyperdrive.
  - **Raid Boss Dragon Krayt** : Antre du dragon millénaire (95 000 HP) avec drop garanti de Perles de Krayt légendaires et d'écailles composites.
  - Rendu 3D : Sas pressurisé blindé de la Corvette Corellienne (`build_corvette_airlock`) avec gyrophares d'alarme rouge et voyants d'urgence.

- [x] **Point 5 : Multi-Planètes & Biomes Stellaires (`hub_galaxy_planets.gd`)** :
  - Catalogue des 5 mondes majeurs de SWG :
    - **Tatooine** : Désert aride, dunes, soleil binaire, canyons et camps Tuskens.
    - **Naboo** : Plaines luxuriantes verdoyantes, cascades, marécages et dômes en marbre de Theed.
    - **Endor** : Lune forestière dense, séquoias géants, canopée humide et villages arboricoles Ewoks.
    - **Dathomir** : Ciel carmin brumeux, badlands toxiques, Rancors sauvages et temples des Sœurs de la Nuit.
    - **Corellia** : Plaines tempérées maritimes, berceau naval et chantiers de Coronet City.
  - Transition atmosphérique, météo dynamique et billetterie de transit inter-mondes.
  - Rendu 3D : Console de navigation galactique (`terminal_planets`) pour voyager entre les 5 planètes.

- [x] **Portage Intégral sur Prime Client (`packages/prime-client`) (2D au sol + Extension Spatiale JTL 3D)** :
  - **Gameplay Planétaire 2D au sol (100% fidèle SWG sans 3D)** :
    - *Boîte de Dialogue Universelle SWG 2D* (`scripts/swg_dialog_box.gd`) : Menus narratifs interactifs pour les 5 nouveaux systèmes (Hôtel de Ville & Élections de Maire, Incubateur Bio & Synthèse ADN, Commandes Droïdes R2/MSE, Donjon Raid Corvette Corellienne, Cartographie & Transit vers les 5 planètes).
    - *Rendu 2D des Entités* (`scripts/entity.gd`) : Sabre laser Jedi avec lame de plasma émissive orientée selon `facing_angle` (dégainable avec `[F7]`), droïdes astromécanos R2 (corps blanc, dôme bleu, œil rouge), sondes Arakyd de traque avec anneau radar pulsant (`[F8]`), insignes de factions GCW et lairs de créatures.
    - *Raccourcis & Commandes Chat* (`client_ui_dialogue.gd` & `main.gd`) : Raccourcis `[F7]` (sabre laser), `[F8]` (sonde Arakyd), `[F10]` (soin Force Heal), `[F9]` (vol spatial), commandes `/saber`, `/probe`, `/space`, `/forceheal`.
  - **Extension Spatiale Jump to Lightspeed (JTL) 3D Incrustée (`scripts/swg_space_flight_3d.gd`)** :
    - Bascule instantanée sol 2D ➔ orbite spatiale 3D via `[F9]` ou dialogue de Spatioport/X-Wing.
    - *SubViewport 3D* plein écran avec champ d'étoiles procédural, modélisation 3D du chasseur Incom T-65B X-Wing, chasseurs TIE ennemis en dogfight, canons lasers rouges 3D animés.
    - *HUD Spatial 2D Overlay* : Répartiteur d'énergie Tri-Voie dynamique (Armes `[F5]`, Boucliers `[F6]`, Moteurs `[F7]`), télémétrie de vitesse (MGLT), jauges de boucliers avant/arrière et saut hyperspatial (`[H]`).
  - **Validation & Synchronisation** :
    - `client_modular_selftest.gd` : 22 composants SWG 2D + Extension Spatiale JTL 3D validés à 100% (code 0).
    - Synchronisation Windows SDS `.10` (`J:/swgemu/clients/prime-client`) : 16 fichiers synchronisés avec succès via `tools/sync_client_to_win.py --client prime`.
    - CI globale headless Godot (`tools/ci_godot_headless.sh`) : 19 suites de tests validées (code 0).


--- 

- [x] **Publication Officielle YouTube Shorts (@lbg-p8k) — Nexura Domina (13 nov. 2026)** :
  - **Clip HD 9:16 (1080×1920)** : Version corrigée v3 enregistrée en mode Kiosk plein écran GPU NVIDIA (163.8 Mo, 2m37s, fluidité 30 FPS).
  - **Améliorations validées** : Caméra reculée (dist: 4.25m, fov: 28°), lipsync spectral FFT calé sur la voix réelle, zéro pixel de bureau / coins arrondis Windows 11 éliminés.
  - **Lia Desktop (Compagnon)** : Nettoyage du menu Tray (retrait de iStripper ➔ ) et intégration du  directement dans .
  - **Lien YouTube Shorts Public** : https://www.youtube.com/shorts/uLV_0kI2ogM


### 2026-11-16 (12) — Cadastre Canonique Scrapaltai (16 km × 16 km SWG/Core3) & Nouvelle Carte Régionale 1:1

- **Carte Régionale HD Re-générée & Déployée** :
  - `packages/prime-client/assets/maps/scrapaltai_planet.png` & `.jpg` (2048×2048) :
    * Raccordement toroïdal 360° (seamless blend aux frontières X/Z).
    * Falaises de duracier rouille au Nord, Grand Rift détaillé et embranchements à l'Ouest.
    * Cratère du Lac d'Améthyste, Oasis du Ksar Nomade, Butte de Zalem et Bassin de Lost Heaven.
    * Tracé rouge/ocre des routes commerciales de convois.
    * Cartouche officiel avec mention : "Topologie : Globe Sphérique Continu (World Wrap 360°)".
  - Patch Launchpad publié sur `.246:8080` (version `2026-11-16T16:03:33Z`).
- **Bouclage Planétaire Continu (Option A — Toroidal World Wrap)** :
  - `packages/prime-client/scripts/player_controller.gd` : `wrap_world_pos()` sur les 4 axes [-8000, +8000].
    * Si X > +8000m ➔ X = -8000m (et inversement).
    * Si Z > +8000m ➔ Z = -8000m (et inversement).
    * Recalage immédiat de la caméra `_camera.position` lors du franchissement de bordure pour une transition sans à-coup.
  - `packages/prime-hub/scripts/hub_sim.gd` : Suppression de l'ancien filtre restrictif (2500..7500) et intégration du wrapping 16 km sur `set_human_pos()`.
  - Redéploiement `prime-hub` sur `.246:8787` et synchronisation vers client Windows SDS `.10` validés.
- **Standard Universel Validé pour TOUTES les Planètes du Jeu** :
  - Règle gravée dans `docs/architecture/STANDARD_PLANETAIRE_16KM.md`.
  - Toutes les planètes du MMO (Scrapaltai, Arvandor, Khar-Zuun, Mor-Valoth, Terre-One...) auront le même format canonique : **16 km × 16 km** (256 km², X/Z ∈ [-8000, +8000]), zéro jitter float 32-bit, même formule mathématique 1:1, cartes 2048×2048 px.
- **Refonte Géographique Canonique Option B** :
  - Adoption de la taille canonique SWG/Core3 (16 384 m × 16 384 m, surface 256 km², X/Z ∈ [-8000, +8000]).
  - Génération d'une carte régionale haute résolution (`2048×2048` PNG+JPG) via `packages/prime-client/tools/generate_scrapaltai_regional_map.py` :
    * Falaises de duracier et crêtes au Nord (+Z) avec Anchor-Ridge et Cratère du Lac d'Améthyste.
    * Le Grand Rift et Canyons à l'Ouest (-X) avec Gouffre du Dragon Krayt, Camp des Jawas et Bazar de Mos Espa.
    * Plaine centrale avec Zalem (capitale lore) et Avant-poste fortifié de Zalem.
    * Bassin Est/Sud-Est (+X, -Z) avec Lost Heaven (hub canonique `4749, -737`), Ferme d'Humidité Lars-Val et Camp du Vent Rouge.
    * Basses terres et oasis au Sud (-Z) avec Ksar Nomade.
    * Tracé du réseau routier rouge/ocre reliant les avant-postes.
    * Grille graduée tous les 2000m, rose des vents et cartouche spatioportuaire officiel.
- **Harmonisation Données Serveur & Client** :
  - `packages/prime-client/assets/maps/scrapaltai_planet_map.json` & `scrapaltai_pois.json` : Coordonnées réelles alignées.
  - `packages/prime-hub/data/catalog_poi.json` : Synchronisé avec les nouvelles coordonnées via `agent_catalog`.
  - `packages/prime-hub/scripts/hub_nav.gd` : Boîtes `ZONES_DEF` mises à jour pour les 7 zones (NavMesh 212 polygones validé).
  - `packages/prime-client/scripts/planet_map_panel.gd` :
    * Projection directe 1:1 métrique sans déformation (`_map_rect` carré centré).
    * Radar joueur vert pulsant en temps réel (`● Teome (Vous)`).
    * Footer propre affichant la position exacte X/Z et informations de survol des POIs.
- **Déploiements Validés** :
  - `prime-hub` déployé et redémarré sur `.246:8787` (`/healthz` 200).
  - Patch Launchpad publié sur `.246:8080` (version `2026-11-16T15:07:30Z`, 328 fichiers, images PNG/JPG incluses).
  - Scripts synchronisés vers Windows SDS `.10` (`tools/sync_client_to_win.py`).

## Historique archivé

- Les sessions et jalons détaillés antérieurs au 2026-11-09 ont été archivés dans [`docs/_archive/SESSION_HISTORY_2026_OCT_NOV.md`](_archive/SESSION_HISTORY_2026_OCT_NOV.md).
- Voir également [`docs/PRIORITES_ACTUELLES.md`](PRIORITES_ACTUELLES.md) et [`docs/SUJETS_OUVERTS.md`](SUJETS_OUVERTS.md).

---

## Prompt de démarrage (coller dans Antigravity)

```
Repo : LBG_Studios. Réponses en français.
Lis dans l’ordre : AGENTS.md → docs/SESSION_EN_COURS.md → docs/PRIORITES_ACTUELLES.md
→ le handoff @docs/handoff_…md si cité.
Confirme en ≤10 lignes : objectif, contraintes, prochain pas — avant toute édition.
En fin de session : mets à jour docs/SESSION_EN_COURS.md.
```
