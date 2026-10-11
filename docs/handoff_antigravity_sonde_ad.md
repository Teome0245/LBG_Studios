# Handoff Antigravity — Sonde AD qui revient en boucle (Compagnon)

**Statut** : **RÉSOLU / CLÔTURÉ (2026-10-11)**  
**Date initiale** : 2026-09-17  
**Décision d'architecture validée** : **Absence d'Active Directory actée dans l'écosystème.**  
- Neutralisation définitive du faux positif `ad_agent_down`.  
- Recadrage de la sonde sur le véritable agent Windows desktop (`192.168.0.10:5005`, poste Teome).  
- Libellés mis à jour : « Sonde agent desktop » (sans mention d'AD).  
**Repo** : `LBG_Studios`  
**Surface** : Compagnon `http://192.168.0.100:5174/` · toast « Je vois `autonomous_nudge` »  
**Priorité** : O1 Studio — initiatives proactives stabilisées et signaux alignés sur le réel.

---

## Prompt à coller dans Antigravity

```
Tu travailles dans LBG_Studios (O1 Studio / packages/cortex).
Objectif : corriger la boucle « Sonde AD » du Compagnon :5174 qui revient à chaque fois,
sans casser Agir ni l’autonomie bornée (jamais d’auto-exec).

## Symptôme (prod LAN, 2026-09-17)
Sur http://192.168.0.100:5174/ le toast InitiativeToast affiche en boucle :
  Titre : Je vois `autonomous_nudge`
  Message : « Je vois l’agent AD injoignable — je peux lancer une sonde (dry-run). »
  Boutons : Sonde AD (dry-run) · Ouvrir Pilot Jobs
Même après Ignorer / Expliquer / Agir, ça revient.

## Preuves live (ne pas inventer)
GET http://192.168.0.100:5174/api/pilot/orchestrator/proactive/status →
{
  enabled: true,
  tension: 1.0,
  curiosite: 1.0,
  silence_seconds_est: ~3900,
  auto_jobs_spawned: 78,
  last_job_id: "<uuid changeant>",
  last_action: { kind: "autonomous_nudge", mode: "autonome",
    message: "Relance proactive : tension élevée…" },
  infra_signals: {
    orchestrator_reachable: true,
    ad_agent_reachable: false,   // ← FAUX POSITIF
    ad_agent_down: true,         // ← FAUX POSITIF
    mmo_sidecar_reachable: true
  }
}
Depuis le LAN WSL :
  TCP 192.168.0.10:5005  → OPEN   (vrai agent Windows / AD desktop)
  TCP 192.168.0.143:5005 → OPEN   (linux agent Omarchy)
  TCP 192.168.0.100:5005 → (cible sondée) → down

## Cause racine (2 bugs couplés)

### Bug A — mauvaise cible TCP pour « agent AD »
Fichier : packages/cortex/orchestrator/services/proactive.py → `_infra_signals()`
```python
ad_url = os.environ.get("AGENT_WINDOWS_SRV_AD_URL", "http://192.168.0.100:5005")
ad_host = …  # → .100
ad_agent_ok = _tcp_open(ad_host, 5005)
```
Env actuel (`lbg.env.example`) :
- `AGENT_WINDOWS_URL="http://192.168.0.10:5005"` ← **vrai agent desktop** (open)
- `AGENT_WINDOWS_SRV_AD_URL="http://192.168.0.100:5005"` ← **cible legacy / morte** (down)

Le toast parle d’« agent AD » mais sonde l’URL AD (`.100`), pas le poste `.10`.
Donc `ad_agent_down=true` en permanence → message sticky « AD injoignable ».

Canon attendu (à trancher dans le fix) :
- Santé « poste Teome / desktop » = **AGENT_WINDOWS_URL → .10:5005**
- Cible `ad` / serveur-AD : soit corriger l’IP réelle, soit ne plus l’utiliser comme signal d’initiative Compagnon
- (optionnel) linux agent : **192.168.0.143:5005**
Voir docs/REGISTRE.md · desktop_targets.py · windows_agent.

### Bug B — fingerprint d’initiative ≠ message affiché
Fichier : packages/cortex/compagnon_ui/src/lib/initiativeQuota.js

`fingerprintFromStatus(status)` priorité :
  1) last_job_id → `job:<id>`
  2) last_action → `act:kind|msg`
  3) sinon infra:ad_agent_down / orch_down

`messageFromStatus` / `agirIntentsFromStatus` priorité :
  1) ad_agent_down → message « AD injoignable » + intent probe_ad
  2) orch down / tension / etc.

Effet : chaque nouveau `last_job_id` (auto_jobs_spawned élevé, tick proactive)
crée un **nouvel id** de quota → `canShowInitiative` laisse passer → toast revient,
mais le **texte** reste toujours la sonde AD (signal infra sticky faux-positif).
Quota actuel : max 3/h, minInterval 600s, prune 1h, localStorage `lbg_compagnon_initiative_quota_v1`.
Ignorer = dismiss UI seulement (ne snooze pas le signal).

Poll client : useInitiative.js → /api/pilot/orchestrator/proactive/status toutes les 60s.

## Correctifs attendus (ordre)

1) **Corriger la cible AD**
   - Défaut `AGENT_WINDOWS_SRV_AD_URL` → `http://192.168.0.10:5005` (ou var dédiée LBG_DESKTOP_AGENT_URL).
   - Aligner `lbg.env.example` + runtime `.140` /etc/lbg-ia-mmo.env (sans committer secrets).
   - Vérifier que `_infra_signals().ad_agent_reachable` passe à true quand `.10:5005` est up.
   - Option : distinguer `desktop_agent` (.10) vs `ad_dc` si un vrai contrôleur AD existe ailleurs — ne pas mélanger les labels.

2) **Stabiliser le quota d’initiatives**
   - Fingerprint doit être **stable pour un même signal utilisateur** :
     ex. si on affiche probe_ad, id = `infra:ad_agent_down` (pas job:uuid).
   - Ou : fingerprint = hash(intents primaires / message kind), pas last_job_id volatile.
   - Après Ignorer : snooze explicite du fingerprint (ex. 2–6 h) en plus du quota horaire.
   - Après Agir dry-run/réel réussi sur ce signal : snooze plus long tant que le signal n’a pas changé (edge rising only).
   - Ne pas re-proposer la même intent si `ad_agent_down` sticky sans transition false→true.

3) **Calmer le moteur proactive (si besoin)**
   - Fichiers : orchestrator/services/proactive.py + hybrid_proactive_agent/engine.py
   - tension/curiosite à 1.0 + silence élevé + autonomous_nudge en boucle alimente last_action / jobs.
   - Ne pas casser L1 ; juste éviter que chaque tick crée un fingerprint toastable.

4) **Tests**
   - Unit : initiativeQuota fingerprint stable quand ad_agent_down sticky + last_job_id change.
   - Unit / integration : _infra_signals avec mock TCP .10 up → ad_agent_down absent.
   - Manuel : :5174 — Ignorer → pas de retour immédiat ; Agir Sonde AD → carte Dry-run ; après fix env, toast AD disparaît si agent up.

## Contraintes projet
- Monorepo LBG_Studios uniquement ; pas de feature dans LBG_IA_MMORPG / new_mmo.
- Compagnon = :5174 (compagnon_ui) ; Pilot = .140:8080 cockpit ops.
- Jamais d’auto-exec desktop ; Agir = proposal → dry-run → réel + token.
- Deploy UI : bash packages/cortex/infra/scripts/deploy_compagnon_100.sh
- Réponses / commits en français OK ; pas de secrets dans git (lbg.env).

## Fichiers clés
- packages/cortex/orchestrator/services/proactive.py (_infra_signals, get_status)
- packages/cortex/compagnon_ui/src/lib/initiativeQuota.js
- packages/cortex/compagnon_ui/src/composables/useInitiative.js
- packages/cortex/compagnon_ui/src/components/InitiativeToast.vue
- packages/cortex/infra/secrets/lbg.env.example (pas lbg.env)
- docs/FOCUS_COMPAGNON.md · docs/handoff_antigravity_sonde_ad.md (ce fichier)

## Déjà livré (ne pas refaire) — session 2026-09-17
- PilotageBar + PilotagePalette Ctrl+K + ActivityEncart + suites ActionCard
- Initiatives Agir-ready (intents), Desktop Pet Electron, Session 0 agent Windows scripts
- Deploy :5174 OK ; Agir desktop (vghd/notepad) fonctionne via worker .10

## Critère de done
1. Avec agent .10:5005 up, infra_signals.ad_agent_down !== true
2. Toast « Sonde AD » ne revient pas à chaque poll / chaque nouveau last_job_id
3. Ignorer snooze réellement le signal
4. Tests verts sur le fingerprint + doc courte mise à jour dans FOCUS_COMPAGNON.md
```

---

## Notes ops (humain)

| Check | Commande / URL |
|-------|----------------|
| Status proactive | `curl -s http://192.168.0.100:5174/api/pilot/orchestrator/proactive/status \| jq .infra_signals` |
| Agent desktop | `Test-NetConnection 192.168.0.10 -Port 5005` (Windows) ou TCP depuis WSL |
| Quota client | DevTools → Application → Local Storage → `lbg_compagnon_initiative_quota_v1` |
| Env orch | Sur `.140` : `grep AGENT_WINDOWS /etc/lbg-ia-mmo.env` |

**Workaround immédiat** (sans code) : dans DevTools, supprimer la clé quota **ne résout pas** le retour ; plutôt fixer `AGENT_WINDOWS_SRV_AD_URL=http://192.168.0.10:5005` côté orchestrateur et redémarrer le service, **ou** Ignorer + attendre le prune 1 h (insuffisant tant que `last_job_id` change).
