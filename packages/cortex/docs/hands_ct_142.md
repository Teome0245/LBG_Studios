# Mains Team — CT `.142` (`lbg-hands`) — **ARCHIVÉ**

**Statut** : **détruit** 2026-10-02 (NUC `.200`, CTID 142).  
**Rôle absorbé par** Omarchy **`.143:5005`** — [`migration_hands_142_to_143.md`](../../../docs/migration_hands_142_to_143.md) · [`omarchy_vm_143.md`](omarchy_vm_143.md).

IP **`.142` libérée**. Alias historiques `hands` / `ct-142` / `lbg-hands` pointent vers `.143`.

---

## Historique (référence)

Créé 2026-08-18 — LXC Ubuntu 24.04 sur NUC `.200`, `linux_agent` `:6001`, inbox `/var/lib/lbg-hands/inbox`.  
Cutover Phase 3 (2026-10-01) : agent stoppé ; trafic → `.143`.  
Phase 4 (2026-10-02) : `pct destroy 142 --purge`.

Le contenu ci-dessous est **figé** (spéc d’origine).

### Placement d’origine

| | Choix |
|--|--------|
| Hyperviseur | `.200` (NUC) |
| IP / CTID | `192.168.0.142` / 142 |
| Hostname | `lbg-hands` |
| RAM / disque | 4 Go / 20 Go |
| Service | `lbg-linux-agent.service` `:6001` |

### Rôles (avant migration)

```
Team .140
  ├─ .141  lbg-executor     pull  /v1/team/wsl/*
  ├─ .142  lbg-hands        push  linux_agent:6001   ← détruit
  └─ .143  lbg-omarchy      push  linux_agent:5005   ← canon actuel (mains + éditeur)
```
