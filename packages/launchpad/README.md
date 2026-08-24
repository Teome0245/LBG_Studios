# packages/launchpad — sources Electron

Sans `node_modules` / `dist`. Build : `npm ci && npm run build:win`.

Profil **prime** → Godot `J:\swgemu\clients\prime-client` → gateway **246**.

## Workflow Prime (Windows) — canal officiel

Les mises à jour du client **passent par le bouton « Vérifier Mises à Jour »** (serveur
`http://192.168.0.246:8080/patches/prime/`). Pas de rsync WSL → J: pour jouer.

1. **Publier** (WSL, après changements `packages/prime-client`) :
   ```bash
   bash packages/prime-client/tools/deploy_prime_client_patch_246.sh
   ```
2. Sur le PC **.10** : Launchpad → **Vérifier Mises à Jour** → attend « Prime mis à jour » ou « 0 diff ».
3. **JOUER** (ferme Godot avant le patch).

Fallback atelier uniquement : `bash packages/prime-client/tools/sync_prime_client_to_j.sh` (écrase J:, à éviter si Godot est ouvert).

## État serveur Prime (v2.1.2+)

- L’API `:8792` sur **245** ne remonte souvent que PreCu.
- Launchpad sonde aussi **`http://192.168.0.246:8765/health`** (gateway Prime).
- Profil **prime** : une seule pastille « LBG MMO Serveur Prime · 192.168.0.246 ».

Rebuild Launchpad après changement JS :
```bash
cd packages/launchpad && npm ci && npm run build:win
```
Puis recopier `dist/win-unpacked` vers `J:\swgemu\dist\` (ou votre install habituelle).
