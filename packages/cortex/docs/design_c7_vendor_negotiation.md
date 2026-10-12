# Design C7 — Négociation marchand bornée (1 vendor)

**Ticket** : Boîte §14 **C7** · Epitome  
**Date** : 2026-10-06 · **Owner** : Dédale / Iris  
**Statut** : **live prime-hub** `:8787` (2026-10-07) — **pas** LLM libre sur prix · **pas** Core3  
**Canon** : [`AGENT_SKILL_MMO.md`](AGENT_SKILL_MMO.md) (`trade/offer`) · Bible V40–V54

---

## Objectif

Un vendor hub accepte une **offre bornée** : delta prix + delta réputation, clampés. Pas de marchandage prose libre.

Done MVP : stub JSON + **`POST /v1/trade/offer`** + suggestions dialogue Jax (client hotbar coups).

---

## Choix vendor MVP

| Champ | Valeur |
|-------|--------|
| PNJ | **Jax Moro** — `npc:core3_barman_jax` |
| Lieu | La Perle de Scrapaltai (cantina) |
| Raison | Déjà `role: vendor` registry · ancré LH · boucle tip / boisson existante |

Hors scope v1 : `npc:merchant` fantasy_stub · relief Sira/Torrik · marché plein inventaire.

---

## Contrat `trade/offer` (stub)

```json
{
  "action": "trade/offer",
  "vendor_id": "npc:core3_barman_jax",
  "sku_id": "drink:cactus_noir",
  "list_price": 25,
  "offer_price": 20,
  "reputation": 10
}
```

### Règles bornées (data)

| Règle | Clamp |
|-------|-------|
| `price_delta_pct` | ±15 % du `list_price` |
| `reputation_delta` | −5 … +5 par offre acceptée |
| Rejet | offre hors bornes → `reject` + raison typée, **sans** LLM |
| Accept | `commit.flags` : `trade_sku`, `price_paid`, `reputation_delta` |

Réputation basse (`< 0`) resserre le max discount (ex. ±8 %). Pas d’invention de SKU hors liste stub.

---

## Data stub

[`vendor_negotiation_jax.json`](../content/world/vendor_negotiation_jax.json)

---

## Fichiers futurs (hors Vague C stub)

| Couche | Fichier / surface |
|--------|-------------------|
| Agent | handler `trade/offer` sidecar `:8791` (C11 tick mutation) |
| Dialogue | move `kind: trade` → utterance + action (C1) |
| Godot | panneau offre prix (pas carte libre) |

---

## Hors scope

- Core3 `vendor_buy` / `vendor_sell` live 246
- LLM qui fixe un prix
- Multi-vendors / stock dynamique
