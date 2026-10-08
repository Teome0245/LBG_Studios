# Rejeu D6 feeling — 2026-10-08 (après-midi)

**Surface** : Compagnon `:5174` · modèle `lbg-compagnon-e4b-v1` / routes `short_social` · `presence_brief`  
**Objectif** : clôturer le « rejeu humain » ouvert dans [`smoke_humain_d6_2026-10-08.md`](smoke_humain_d6_2026-10-08.md) (C2 PARTIEL → gaps A1–A4).  
**Méthode** : smokes auto D6 / D6.5 + probe greeting + amorce rejeu fil (T1–T5) — proxy lab, pas un 2ᵉ fil UI manuel.

---

## Smokes auto

| Smoke | Résultat | Preuve |
|-------|----------|--------|
| D6 V6→V8 | **PASS** | `SMOKE_D6_V6V8 OK` · cid `smoke-d6-v6v8-6001d071` |
| D6.5 V9 greeting | **PASS** | `short_social` · « Salut — ça va… collègue studio » · **zéro** Agir/`.143` |
| D6.5 V10 plan | **PASS** | `presence_brief` · markdown Objectif/Phases · mission Campus `8264112d-…` |
| Présence C2 retour | **PASS** | `SMOKE_C2_PRESENCE_REPORT_OK` · Nix escort ≠ Mira greet |

## Probe / amorce fil humain

| Tour | Humain | Source | Note |
|------|--------|--------|------|
| T1 | Bonjour, comment ça va… | `short_social` | **C2 open PASS** (était FAIL le matin) |
| T2 | bien merci, et toi ? | `short_social` | **PASS** · pas de mur ops |
| T3 | Discutons comme collègues… | LLM | **PARTIEL** · bascule mode, peu d’avis concret |
| T4 | MMORPG + incarnation IA | LLM | **C1 OK** · prise de position |
| T5 | zone d’entraînement | `tool_loop` | **régression feeling** — cockpit Team / dry-run (ops leak) ; ask saturé ensuite |

Script : `tools/smoke_rejeu_humain_d6_5174.sh` (interrompu après T5 — `/api/ask` bloqué par tool_loop long).

---

## Score critères

| Critère | Matin | Rejeu PM | Commentaire |
|---------|-------|----------|-------------|
| **C1** | PASS | **PASS** | V7 + T4 |
| **C2** | PARTIEL | **PASS ouverture** · PARTIEL « collègues » | A1 OK ; A2 encore mince |
| **C4 / délivrance** | FAIL | **PASS** (V10) | Plan markdown + Campus |
| Go-ahead trap | FAIL | **PASS** (V10 / D6.5) | A3+A4 |

**Verdict** : gaps bloquants du matin (**greeting** + **plan**) = **fermés**. Residual : avis « collègues » plus franc (A2) · éviter `tool_loop` ops sur causerie zone entraînement.

---

## Références

- Fil matin : [`smoke_humain_d6_2026-10-08.md`](smoke_humain_d6_2026-10-08.md)  
- Plan présence : [`PLAN_PRESENCE_ZONE_ENTRAINEMENT.md`](PLAN_PRESENCE_ZONE_ENTRAINEMENT.md)  
- Focus D6 : [`FOCUS_COMPAGNON.md`](FOCUS_COMPAGNON.md) § D6
