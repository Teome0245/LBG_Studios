# ADR 0028 — Clôture de veille : DeepSeek Harness et VoiceStudio LAN

**Statut** : **Accepté**  
**Date** : 2026-10-13  
**Contexte** : Évaluation des pistes L2 issues de la veille technologique (`O-VEIL-1` et `O-VEIL-2`).  
**Références** : ADR 0020 (DSH greffe périphérique), ADR 0025 (Mains de code .143), [`voice_local.md`](../voice_local.md), [`local_llm_route_matrix.md`](../local_llm_route_matrix.md).

---

## 1. DeepSeek Harness (O-VEIL-1)

### Contexte & Rappel ADR 0020
L'ADR 0020 proposait d'évaluer DeepSeek Harness (`dsh`) soit comme outil de codage exploratoire sur le poste `.10`, soit comme capability Team autonome `dsh_headless` (L2) pointant vers Ollama `.110`.

### Retours de terrain & Diagnostic chiffré
1. **Saturation CPU de `.110`** : Lors du diagnostic live O-IDE-2, nous avons mesuré que les modèles de coding/raisonnement lourds s'exécutent en RAM CPU pure (`size_vram: 0`), occasionnant des latences > 350 s par tour.
2. **Capacité existante éprouvée** : OpenCode headless (`opencode run -m opencode/big-pickle`) est déjà déployé et validé comme nominal de production pour la Team (Métis / Iris / Dédale) sur le worker `.143`. De plus, Cline CLI fournit déjà une solution de second avis 0 € API.
3. **Contrainte ops sur 140** : Le backend Python Cortex / Team refuse formellement l'introduction d'un runtime Node.js sur `.140`.

### Décision (O-VEIL-1)
- **NO-GO formel pour `dsh_headless` dans Cortex/Team** : Aucun module `dsh_agent.py` ne sera introduit dans l'orchestrateur. Cela évite un doublon fonctionnel avec OpenCode et préserve les ressources de `.110`.
- **Usage exploratoire poste `.10` uniquement** : DSH reste autorisé en local sur le poste dev (`ollama launch dsh`), sans greffe sur le bus Team ni déploiement centralisé.
- **Clôture** : Sujet `O-VEIL-1` clos.

---

## 2. VoiceStudio / Alternatives TTS/ASR LAN (O-VEIL-2)

### Contexte & Architecture existante
Le Compagnon dispose déjà d'une architecture audio hybride opérationnelle documentée dans [`voice_local.md`](../voice_local.md) :
- **Primaire (cloud 0 €)** : `Edge TTS` (`fr-FR-DeniseNeural`), qualité studio naturelle, latence quasi nulle, aucun coût API.
- **Secours local (LAN)** : `Piper` (`/opt/lbg-piper-tts` sur `.111:8098`, voix `fr_FR-siwis-medium`), ultra léger (< 200 Mo RAM), résilient et hors-ligne.
- **Intégration** : Proxy `/api/tts` sur `.100:5174`, bouton Voix opt-in dans la SPA Compagnon, FaceRig synchronisé.

### Évaluation de VoiceStudio (clonage vocal neuronal lourd)
- **Charge GPU** : VoiceStudio ou les modèles de clonage vocal neuronal récents (F5-TTS, Chatterbox, Kokoro) exigent une accélération GPU dédiée sous peine de latences inacceptables en synthèse temps réel (> 4 s pour une réplique).
- Sur le LAN LBG, le cluster VM/CT ne dispose pas de GPU libre excédentaire dédié à la voix.
- Piper assure déjà la souveraineté et l'autonomie hors-ligne avec une empreinte minimale.

### Décision (O-VEIL-2)
- **Maintien du stack nominal existant** : Le couple Edge TTS (défaut) + Piper LAN `.111:8098` (fallback) est confirmé comme la référence de production pour le Compagnon.
- **Pas de greffe de conteneur VoiceStudio lourd** sur le LAN tant qu'un GPU dédié à la voix n'est pas provisionné.
- **Clôture** : Sujet `O-VEIL-2` clos.
