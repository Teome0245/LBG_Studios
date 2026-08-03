# Dialogue Portraits

Ce dossier contient les **portraits de dialogue** affichés dans la fenêtre type Warcraft 3.

## Arborescence attendue

```text
assets/ui/portraits/
  player_human/
    neutral.png …
  npc_guide/
  npc_bartender/
  npc_merchant/
  npc_civilian/
  npc_trainer/
```

## Notes

- Les clés doivent rester alignées avec `config/dialogue_portraits.json`
- Format conseillé : PNG (pas de `.svg` — TextureRect Godot fragile)
- Fond transparent ou neutre
- Même personnage, même costume, même lumière entre les expressions
- Interim OK : copier bartender→merchant/civilian tant que Pygmalion n’a pas généré les vrais
- Génération : `Infographiste_IA/scripts/generate_dialogue_portraits_mvp.sh` puis `deploy_dialogue_portraits_to_prime.sh` (cible LBG_Studios)