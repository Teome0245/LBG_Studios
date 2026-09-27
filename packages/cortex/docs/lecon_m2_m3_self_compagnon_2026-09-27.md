# Leçon — M2 Self→Compagnon + M3 Team L1 (2026-09-27)

**Commit** : `1afd3aa` · **Surfaces** : orch `.140` · Compagnon `:5174` · Pilot Team  
**Statut** : livré + smoke LAN (proxy, bandeau, spawn Team, Ollama Plan/Act)

---

## Ce qui a marché

1. **Proxy slim** `GET /v1/pilot/orchestrator/self/status?ensure_goals=0` — évite le dump des milliers de goals done ; Compagnon reste fluide.
2. **Bandeau Self** (`SelfPresenceStrip`) — présence continue (intent + jauges) sans dépendre du toast.
3. **Toast Self** seulement sur signaux forts : `pending_will` → curiosité ≥ 0.85 → social ≥ 0.85 → tension ≥ 0.75.
4. **Priorité proactive** : `jobs:idle` / silence d’abord ; Self en secours. À curiosité 0.75 le bandeau suffit — pas de faux positif `self:curiosity`.
5. **Team L1 depuis toast** (`teamSpawn.js`) : `POST /api/pilot/team/tasks` + run + mémoire équipe ; contre-pouvoir Agir inchangé dans `ActionCard`.

## Pièges / à retenir

| Sujet | Leçon |
|-------|--------|
| Inventaire Ollama `.110` | Tag réel = `gemma-4-abliterated:12b-qat` ; la matrice / Cline attendent `:12b`. **Alias** `ollama cp …:12b-qat …:12b` obligatoire sinon Act Cline KO. Premier chat après `cp` peut prendre ~3–4 min CPU. |
| Plan 9b | Réponses « thinking » peuvent vider `content` si `max_tokens` trop bas — juger le HTTP 200 + usage, pas seulement le texte. |
| Cline UI `.143` | Extension `saoudrizwan.claude-dev` présente ; smoke réseau = tags + chat OpenAI-compat ; config UI Plan=`providers.plan-110-9b` / Act=`providers.act-110-gemma12b`. |
| Quota toast | Self ne remplace pas idle : snooze / silence prolongé → on voit surtout `jobs:idle`. |

## Boucle validée

```text
Self (.140) → proxy Pilot → bandeau Compagnon
                ↘ toast (si seuil) → Team L1 spawn  ou  Agir (dry-run → review)
```

## Suite maturité

- [x] M2 / M3 code + deploy  
- [x] Smoke tags + chat Plan 9b / Act 12b (via alias) depuis LAN  
- [ ] Un aller-retour UI Cline Plan→Act sur un micro-patch (manuel opérateur)  
- O2 jeu seulement quand la checklist `ecosystem_dev_143.md` est verte
