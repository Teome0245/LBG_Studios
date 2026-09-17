# Handoff Antigravity — Visuel & polish Compagnon

**Date** : 2026-09-17  
**Repo** : `LBG_Studios` · `main` (après `d7cbc90` ou plus récent)  
**Surface** : Compagnon `http://192.168.0.100:5174/` · sources `packages/cortex/compagnon_ui`  
**Optionnel** : overlay Electron `packages/compagnon-desktop` (cohérence visuelle avatar)  
**Priorité** : O1 Studio — *feeling* compagnon (Jarvis / présence), pas un dashboard ops.

---

## Prompt à coller dans Antigravity

```
Tu travailles dans LBG_Studios (O1 Studio).
Objectif : améliorer le VISUEL et le polish UX du Compagnon (:5174),
avec des améliorations concrètes (micro-interactions, hiérarchie, présence),
sans casser Agir / pilotage / initiatives, et sans transformer l’UI en cockpit Pilot.

## Pari produit (non négociable)
Les 30 premières secondes doivent sentir un COMPAGNON, pas un hub technique.
Réf. : docs/FOCUS_COMPAGNON.md
Canon : chat produit = http://192.168.0.100:5174/
Pilot (.140:8080) reste le cockpit ops — ne pas le cloner ici.

## État actuel (baseline)
Stack : Vue 3 + Vite + Tailwind v4 (src/style.css @import "tailwindcss") + fonts Inter/Outfit.
Thème : dark slate + accent teal/emerald + fond image glass.
Éléments déjà livrés (ne pas supprimer) :
- ChatFlow / ChatHeader / ChatInput
- PilotageBar + PilotagePalette (Ctrl+K) + ActivityEncart (style Cursor)
- ActionCard Dry-run/Réel + InitiativeToast
- LyraWidget / FaceRig (présence, fallback CSS si sheets foireuses)
- Banner cutover Pilot (masquable)

Douleurs visuelles observées (screenshot Teome 2026-09-17) :
1. Trop d’éléments techniques en premier plan (gauges CPU/RAM, CT100-PROD, chrome ops)
   → le chat ne « respire » pas assez comme un compagnon.
2. Palette teal/emerald + slate générique AI-dashboard ; peu de personnalité de marque LBG.
3. Toast initiative + input + pilotage + avatar = zones qui se chevauchent / concurrence visuelle.
4. ActivityEncart / PilotageBar utiles mais encore « collés » au chrome technique, pas intégrés
   dans une composition unique.
5. Messages / réflexion / tool logs denses (look ops) — OK en détail, à adoucir en surface.
6. FaceRig / Lyra : présence OK mais parfois collage slideshow / mood object — rester robuste.
7. Tailwind content/source incomplets : beaucoup de .vue nouveaux (Pilotage*, Activity*, etc.)
   peuvent manquer dans @source de style.css / tailwind.config → styles incomplets au build.
   Vérifier et ajouter les chemins manquants.

## Direction visuelle demandée
Une présence studio chaude / crédible, type assistant de bureau (Jarvis light), pas SaaS purple.

À FAIRE :
- Une composition claire : zone chat dominante ; chrome secondaire discret.
- Brand « Compagnon / LBG » lisible sans crier (header / empty state).
- Typo expressive déjà amorcée (Outfit titres) — l’affirmer ; éviter de retomber sur Inter partout.
- Atmosphère : garder le fond image ou le raffiner (overlay gradient plus doux, vignette),
  pas un fond plat unique.
- Motion utile (2–3) : apparition message, pulse « en cours » activité, entrée toast — pas de glow spam.
- Hiérarchie : persona / statut en ligne > metrics ops (metrics derrière toggle déjà existant —
  s’assurer qu’elles restent secondaires / repliées par défaut).
- Harmoniser PilotageBar + Ctrl+K + ActivityEncart + ActionCard (même langage de boutons,
  espacements, coins, accents).
- Toast initiative : moins « alerte monitoring », plus « je te propose » ; ne pas masquer Agir.
- Empty state / premier message : invitation à parler ou Ctrl+K, pas une liste de panneaux.
- Responsive : input + toast + avatar OK sur largeur ~1280 et ~900.

À ÉVITER (règles design projet) :
- Thème purple-on-white / purple-indigo gradient générique AI
- Warm cream + serif terracotta broadsheet
- Cards partout (surtout pas dans un éventuel hero) ; cards seulement pour interaction
  (ActionCard, toast, palette OK)
- Pills rounded-full en grappes, multi-shadow, glow néon excessif, emojis décoratifs
- Dark mode « cyberpunk » saturé ; rester studio discret
- Ne pas transformer :5174 en clone de Pilot (Team office, jobs dense, etc.)

## Améliorations fonctionnelles légères (bonus, si le temps)
Autorisées seulement si elles renforcent le feeling compagnon :
- Empty state avec 2–3 suggestions cliquables (ask / Agir) branchées sur PilotageBar intents
- Indicateur « Compagnon écoute / agit » lié à useActivity (déjà là) — plus visible, moins technique
- Cohérence light theme (ThemeToggle) si cassé / laid — sinon ignorer
- Overlay Electron (compagnon-desktop) : aligner couleurs / bulle avec le toast web
  (optionnel, second)

INTERDIT dans ce ticket :
- Refonte backend / Agir protocol / auto-exec
- Fix sonde AD (autre handoff : docs/handoff_antigravity_sonde_ad.md) — ne pas mélanger sauf
  snooze UI cosmétique du toast
- Nouvelles deps lourdes (pas de lib UI entière type shadcn mass import)
- Modifier Pilot web (.140) sauf lien / deep-link déjà en place
- Committer secrets (lbg.env)

## Fichiers clés
- packages/cortex/compagnon_ui/src/style.css          (tokens, fond, glass)
- packages/cortex/compagnon_ui/src/components/ChatFlow.vue
- packages/cortex/compagnon_ui/src/components/ChatHeader.vue
- packages/cortex/compagnon_ui/src/components/ChatInput.vue
- packages/cortex/compagnon_ui/src/components/PilotageBar.vue
- packages/cortex/compagnon_ui/src/components/PilotagePalette.vue
- packages/cortex/compagnon_ui/src/components/ActivityEncart.vue
- packages/cortex/compagnon_ui/src/components/ActionCard.vue
- packages/cortex/compagnon_ui/src/components/InitiativeToast.vue
- packages/cortex/compagnon_ui/src/components/LyraWidget.vue
- packages/cortex/compagnon_ui/src/pages/HomePage.vue
- packages/cortex/compagnon_ui/index.html
- packages/cortex/compagnon_ui/tailwind.config.js
- Deploy : bash packages/cortex/infra/scripts/deploy_compagnon_100.sh [--smoke]

## Méthode de travail
1. Audit rapide (lire les fichiers ci-dessus + screenshot mental : chat + toast + input).
2. Plan court (5–8 bullets) avant gros CSS.
3. Tokens CSS dans :root (accent, glass, radius, spacing) — une direction claire.
4. Passer @source / content Tailwind pour tous les composants utilisés.
5. Polish composants un par un (header → flow → input/pilotage → toast → activity).
6. Build local ou deploy_compagnon_100.sh --smoke ; vérifier http://192.168.0.100:5174/
7. Doc courte : 5 lignes dans docs/FOCUS_COMPAGNON.md (§ Visuel) + captures si possible.
8. Commit + push main (message feat(o1): polish visuel Compagnon …) — pas de secrets.

## Critères de done
1. Au premier viewport, on lit « Compagnon » / présence, pas un dashboard métriques.
2. Pilotage + Agir restent évidents (barre / Ctrl+K / bouton Agir).
3. Toast initiative ne domine pas toute la composition ; z-index / position OK vs input.
4. ActivityEncart lisible, style Cursor mais intégré (pas un bloc alien).
5. Pas de régression Agir dry-run / proposal.
6. Deploy :5174 OK (smoke chat + agir notepad ou équivalent).
7. Diff principalement compagnon_ui (+ desktop overlay si touché) ; doc FOCUS à jour.
```

---

## Notes pour Teome

| | |
|--|--|
| Prompt prêt à coller | section ci-dessus |
| Autre handoff ouvert | [`handoff_antigravity_sonde_ad.md`](handoff_antigravity_sonde_ad.md) (bug sonde) — **ticket séparé** |
| Deploy après travail Antigravity | `bash packages/cortex/infra/scripts/deploy_compagnon_100.sh --smoke` |

Si Antigravity n’a qu’un créneau : prioriser **hiérarchie + tokens + toast/input/pilotage** avant FaceRig/Electron.
