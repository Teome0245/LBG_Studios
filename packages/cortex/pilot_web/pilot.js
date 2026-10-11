/*
 * pilot.js — RETIRÉ (modularisation, plan d'évolutions 1.3).
 *
 * Ce monolithe historique (~8 500 lignes) n'est PLUS chargé par index.html :
 * l'entrée est `src/main.js` (modules ES). Le code a été segmenté en
 * sous-modules de moins de 1 000 lignes à la racine de `pilot_web/` :
 *
 *   - pilot_metrics.js   — métriques Prometheus, cache latence, benchmark
 *   - pilot_core.js      — base API, stockage, panneaux, santé, route
 *   - pilot_state.js     — persistance (histoire / quête / combat) + rendu
 *   - pilot_chat.js      — presets & envoi d'intention
 *   - pilot_assistant.js — assistant : préférences, historique, mémoire
 *   - pilot_views.js     — rendus DOM de l'assistant (badges, panneaux)
 *   - pilot_actions.js   — actions conversationnelles (propose/route/execute)
 *   - pilot_orch.js      — humeur orchestrateur, LBGIA, avatars
 *   - pilot_office.js    — bureau Team (présence, carte, snapshot/WS)
 *   - pilot_team.js      — Team virtuelle (création, plan, run, approbation)
 *   - pilot_cards.js     — composants carte/chips (zones, ponts out-game)
 *   - pilot_jobs.js / pilot_router.js / pilot_pm.js / pilot_lyra.js /
 *     pilot_desktop.js / pilot_init.js
 *
 * Les chunks exécutés sont générés par `tools/gen_chunks.mjs` → `src/chunks/`.
 * Le contenu précédent reste disponible dans l'historique git.
 */

export {};
