"""
Plan autonomie Team — réduire la dépendance à Cursor Cloud Agent.

Réponse ancrée pour questions stratégiques « faire plus sans Cursor » / plan Team.
Ne doit PAS capturer un plan lore / game design « à soumettre au bureau/Team »,
ni une correction du type « pas un plan Cursor/LAN ».
"""

from __future__ import annotations

import re

# Signaux explicites Cursor / autonomie ops (pas un simple « préparer un plan »)
_AUTONOMY_TRIGGERS = (
    "sans soliciter cursor",
    "sans solliciter cursor",
    "moins de cursor",
    "réduire cursor",
    "reduire cursor",
    "dépendance cursor",
    "dependance cursor",
    "plan avec la team",
    "plan avec la Team",
    "sans cursor cloud",
    "cursor qui traite",
    "cursor pour developer",
    "cursor pour développer",
    "faire plus sans",
    "équipe virtuelle",
    "equipe virtuelle",
    "team campus",
    "missions campus",
)

# Lore / game design — handoff Team ≠ plan autonomie infra
_GAME_LORE_RE = re.compile(
    r"(?i)\b("
    r"scrapaltai|lost\s+heaven|"
    r"faction|factions|"
    r"\blore\b|gameplay|game\s*design|"
    r"\bpnj\b|\bpoi\b|villes?|"
    r"zone\s+d['\u2019 ]?entra[iî]nement|"
    r"qu[êe]tes?|bestiaire|personas?|incarnation"
    r")\b"
)

# Mentions Cursor/LAN niées (« pas un plan Cursor/LAN ») — à ignorer comme signal
_NEGATED_CURSOR_RE = re.compile(
    r"(?i)("
    r"pas\s+(?:un\s+)?plan\s+cursor(?:\s*/\s*lan)?|"
    r"pas\s+(?:de\s+|un\s+)?cursor(?:\s*/\s*lan)?|"
    r"pas\s+(?:le\s+|un\s+)?plan\s+(?:infra|lan|ops)|"
    r"pas\s+.{0,40}\bcursor\b|"
    r"sans\s+(?:le\s+)?plan\s+(?:cursor|infra|lan)|"
    r"mauvais\s+livrable"
    r")"
)

_CURSOR_AUTONOMY_SIGNAL_RE = re.compile(
    r"(?i)\b("
    r"cursor|autonom(?:ie|e)|moins\s+de\s+cursor|"
    r"sans\s+sol+icit|d[ée]pendance\s+cursor|"
    r"team\s+campus|missions?\s+campus|"
    r"[ée]quipe\s+virtuelle|smoke|deploy|orch\b"
    r")\b"
)


def _has_cursor_autonomy_signal(text: str) -> bool:
    """True si signal Cursor/autonomie réel (hors négations « pas un plan Cursor »)."""
    scrubbed = _NEGATED_CURSOR_RE.sub(" ", text or "")
    return bool(_CURSOR_AUTONOMY_SIGNAL_RE.search(scrubbed))


def wants_team_autonomy_plan(prompt: str) -> bool:
    """Plan stratégique Team / autonomie — pas lore jeu ni handoff bureau générique."""
    low = (prompt or "").lower()
    if not low.strip():
        return False

    # Plan game/lore « soumettre au bureau/Team » → laisser le LLM + plan_submit
    if _GAME_LORE_RE.search(low) and not _has_cursor_autonomy_signal(low):
        return False

    if any(t.lower() in low for t in _AUTONOMY_TRIGGERS):
        return True

    # « autonomie » seul trop large ; exiger co-occurrence team/campus/cursor/orch
    if re.search(r"(?i)\bautonom", low) and re.search(
        r"(?i)\b(cursor|team|campus|orch|lan)\b", low
    ):
        if not _GAME_LORE_RE.search(low) or _has_cursor_autonomy_signal(low):
            return True

    # plan/roadmap + team/campus : uniquement si signal Cursor/autonomie/ops
    if re.search(
        r"(?i)\b(plan|roadmap|stratégie|strategie)\b.{0,60}\b(team|campus|orch)\b",
        low,
    ) and _has_cursor_autonomy_signal(low):
        return True

    if re.search(
        r"(?i)\bcursor\b.{0,80}\b(team|campus|orch|backend|réflexion|reflexion)\b",
        low,
    ) and re.search(r"(?i)\b(plan|prépar|prepar|moins|sans|autonom)\w*", low):
        # Négation « pas … Cursor » déjà filtrée via scrub dans le 2e chemin ; ici
        # on refuse si toute mention cursor est niée.
        if not _has_cursor_autonomy_signal(low):
            return False
        return True
    return False


def format_team_autonomy_plan() -> str:
    """Markdown plan Local / Team / Cursor — avec lignes recollables."""
    return """## Plan autonomie — moins de Cursor, plus de Team + LAN

**Constat** : aujourd’hui Cursor Cloud Agent couvre surtout le **code repo** (branches, PR, patches multi-fichiers). Le cockpit Orch peut déjà faire beaucoup **en local/LAN** sans Cursor — il faut le router correctement et déléguer le volume à la **Team Campus (.140)**.

### Qui fait quoi (cible)

| Besoin | Canal | Pas Cursor si… |
|--------|--------|----------------|
| Status / smoke / deploy LAN | `team:` + tool_loop | sondes HTTP, scripts existants |
| Audit Ollama .110/.111 | réflexion `audit` | lecture catalogue + pull hints |
| Diagnostic cockpit | `tools` (P2) | team_status + audit + catalogue |
| Wiring caps agents vides | Team `ops` + linux_core | missions spawn documentées |
| Refactor / PR / multi-fichiers | `cursor:` | **seul cas Cursor obligatoire** |

### Phases proposées (avec la Team)

**Phase A — Orch (CT100, sans token Cursor)**
1. Étendre la boucle outils : smokes, `cursor/health` .140, gaps catalogue
2. Affiner la réflexion : plan/stratégie → ce document ou `team:`, jamais registre agents
3. Post-action : suggestions recollables (déjà en place)

**Phase B — Team Campus (.140)**
1. Mission spawn : smokes LAN quotidiens (`spawn_team_qa_smoke_job` — déjà documenté)
2. Mission : câbler `devops*` / caps vides (linux_core comme proxy)
3. Follow-ups `campus/act` après chaque diagnostic Orch

**Phase C — Réserver Cursor**
- Branches features, correctifs cross-package, ADR/docs lourds
- Tout le reste : Groq/Ollama light + Team + outils LAN

### Prochaines actions (recolle dans le chat)

- `team: propose une mission Campus pour automatiser smokes LAN et réduire les appels Cursor`
- `team: status orchestrateur, jobs systemd campus, et agents ops disponibles`
- `fais un diagnostic complet LAN`
- `liste les agents avec 0 caps et propose qui doit les câbler`

### Mission Team à lancer (depuis poste avec SSH .140)

```bash
# Exemple — à adapter via Pilot / campus
bash packages/cortex/infra/scripts/spawn_team_qa_smoke_job.sh
```

_Doc : `packages/cortex/docs/handoff_equipe_virtuelle_2026-07-10.md` · ADR bus plan `0019-team-plan-llm-bus.md`_
""".strip()
