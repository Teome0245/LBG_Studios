# Migration Pilot Nginx → 140

## État

| Rôle | Hôte | Port | Statut |
|------|------|------|--------|
| **Pilot LBG** | `192.168.0.140` | `:8080` | Actif |
| **Web front** | `192.168.0.100` | `:80/:3000/:5174/:8093` | **CT 100** `lbg-web-100` |
| Legacy `.112` | — | — | **VM détruite** |

Voir aussi [`migration_web_ct113.md`](migration_web_ct113.md).

## Bookmarks

1. Pilot LBG → http://192.168.0.140:8080/
2. Cockpit P03 → http://192.168.0.100:8093/pilot/#/cockpit
3. Orchestrateur UI → http://192.168.0.100:5174/
