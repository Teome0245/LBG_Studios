# Migration web front → CT `.100`

## Canonique

- **IP web** : `192.168.0.100` — **CTID 100** (`lbg-web-100`)
- **Ollama heavy** : `192.168.0.110` — **CTID 110** (`ollama-110`)
- VM legacy `.112` / ancien VMID 110 QEMU : **détruite**

| Usage | URL |
|-------|-----|
| Cockpit P03 | http://192.168.0.100:8093/pilot/#/cockpit |
| Orchestrateur UI | http://192.168.0.100:5174/ |
| API orchestrateur | http://192.168.0.100:3000/ |
| Traefik | http://192.168.0.100/ |
| MCP front | http://192.168.0.100:8766/healthz |
| Pilot LBG | http://192.168.0.140:8080/ |

## Alignement CTID = dernier octet IP

| Avant | Après |
|-------|--------|
| CT 113 → `.100` | **CT 100** / `.100` |
| CT 109 → `.110` | **CT 110** / `.110` |
