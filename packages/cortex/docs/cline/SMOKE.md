# Smoke Cline ↔ Ollama LBG

Depuis le poste qui héberge VS Code / Cursor (même LAN que 110 / 111).

## 1. Tags

```bash
curl -sS http://192.168.0.110:11434/api/tags | python3 -c 'import sys,json; print([m["name"] for m in json.load(sys.stdin).get("models",[])])'
curl -sS http://192.168.0.111:11434/api/tags | python3 -c 'import sys,json; print([m["name"] for m in json.load(sys.stdin).get("models",[])])'
```

Attendu (sous-ensemble) :

- 110 : `huihui_ai/gemma-4-abliterated:12b-qat` **et** alias `…:12b` (`ollama cp …:12b-qat …:12b`), `…:e2b`, `huihui_ai/qwen3.5-abliterated:9b` (+ optionnel `lbg-cline-plan:9b`)
- 111 : `huihui_ai/qwen3.5-abliterated:0.8B`, `huihui_ai/qwen3.5-abliterated:2B`

Si `api/show` renvoie *model not found* pour `:12b` : recréer l’alias avant Cline Act.

## 2. Chat OpenAI-compat

```bash
curl -sS http://192.168.0.110:11434/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"huihui_ai/gemma-4-abliterated:12b","messages":[{"role":"user","content":"ping: réponds OK"}],"max_tokens":16,"stream":false}'

curl -sS -m 120 http://192.168.0.110:11434/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"huihui_ai/qwen3.5-abliterated:9b","messages":[{"role":"user","content":"ping: réponds OK"}],"max_tokens":16,"stream":false}'

curl -sS http://192.168.0.111:11434/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"huihui_ai/qwen3.5-abliterated:0.8B","messages":[{"role":"user","content":"ping: réponds OK"}],"max_tokens":16,"stream":false}'
```

## 3. Cline UI

1. Act = `providers.act-110-gemma12b.json` (alias historique `providers.act-110-qwen27b.json`)
2. Plan = `providers.plan-110-9b.json` (défaut) · triage only = `plan-111-fast.json` / `plan-111-clean.json`
3. Features → **Use Compact Prompt** ON · **Plan/Act separate models** ON

Voir `../cline_local_llm.md` et `../sans_cursor.md`.
