## Contrat M11 ↔ M12 (source of truth)

> Rédigé pour handoff Hermès ↔ Iris ↔ Dédale. Schémas : `docs/schemas/lbg-ws/`.

### Session

| Champ | Type | Description |
|-------|------|-------------|
| `session_token` | string (opaque, ≥32) | Émis par `lbg_gateway` après `login` OK ; requis sur WS `lbg-ws/2` |
| `ws_url` | string URL | Ex. `ws://192.168.0.140:8765/lbg-ws/2` (LAN) ; renvoyé avec `enter_zone` |
| `your_character_id` | integer | `obj_id` Core3 du perso contrôlé ; ancre `zone_state` |

### Messages client → gateway (`client.zone_command_v2` / `client.login`)

| `type` | Champs | Effet |
|--------|--------|-------|
| `login` | `username`, `password` | Auth SQL compte Prime → `session_token` + `characters[]` |
| `select_character` | `character_id` | Attache session au perso ; policy `kick_other` si déjà en ligne |
| `enter_zone` | `zone` | Spawn / attach ZoneServer → `ws_url` + `your_character_id` |

### Erreurs (gateway → client)

| Code | Quand |
|------|-------|
| `auth_failed` | mauvais user/pass ou compte inexistant |
| `character_in_use` | perso déjà attaché et policy = `reject` |
| `session_expired` | token invalide / TTL dépassé |
| `zone_unavailable` | ZoneServer / bridge down |

### Policy session

`LBG_ZONE_SESSION_POLICY=kick_other` (défaut recommandé) : une nouvelle `select_character` déconnecte l’autre session (retail ou Godot). Alternative : `reject` → `character_in_use`.

Références : [`core3_zone_bridge_spec.md`](core3_zone_bridge_spec.md) §2 · [`client.zone_command_v2.schema.json`](schemas/lbg-ws/client.zone_command_v2.schema.json) · [`client.login.schema.json`](schemas/lbg-ws/client.login.schema.json)
