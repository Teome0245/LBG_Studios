"""Mémoire agent Compagnon — synthèse read-only Self + leçons (sans LLM, ≠ RAM VM).

P5 : après recall, extraire **1** ``evolution_seed`` scorée (Jobs L2 / LAN / mails…)
proposée via STUDIO (Team L1 / En parler / Ignorer) — jamais auto-promue sans choix humain.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from lbg_agents.factual_status_common import fetch_json, orchestrator_base, status_result

RECALL_SCHEMA_VERSION = 1

# Thèmes prioritaires pour scorer une seed (P5)
_THEME_WEIGHTS: tuple[tuple[tuple[str, ...], str, float], ...] = (
    (("job", "l2", "waiting_approval", "approval", "hitl"), "jobs_l2", 0.92),
    (("réseau", "reseau", "lan", "inventaire", "freebox", "apparu", "disparu"), "lan", 0.88),
    (("mail", "imap", "inbox", "courriel"), "mail", 0.84),
    (("selfcheck", "healthz", "infra", "sonde", "disk", "disque"), "infra", 0.78),
    (("compagnon", "agir", "studio", "spontané", "spontan"), "compagnon", 0.72),
)


def _lessons_json_candidates() -> list[Path]:
    out: list[Path] = []
    env = os.environ.get("LBG_TEAM_LESSONS_PATH", "").strip()
    if env:
        out.append(Path(env))
    # Runtime 140
    out.append(Path("/opt/LBG_IA_MMO/knowledge/lessons_learned.json"))
    out.append(Path("/var/lib/lbg/knowledge/lessons_learned.json"))
    # Monorepo (dev)
    here = Path(__file__).resolve()
    for parent in here.parents:
        cand = parent / "knowledge" / "lessons_learned.json"
        if cand not in out:
            out.append(cand)
        # packages/cortex/knowledge
        cand2 = parent / "packages" / "cortex" / "knowledge" / "lessons_learned.json"
        if cand2 not in out:
            out.append(cand2)
    return out


def load_recent_lessons(*, limit: int = 5) -> tuple[list[dict[str, Any]], int, str | None]:
    """Retourne (leçons récentes, total, path ou None)."""
    cap = max(1, min(int(limit), 20))
    # Préférer l'API Team si dispo (même process orch)
    try:
        from team import lessons_learned as ll  # type: ignore

        if ll.lessons_enabled():
            total = ll.lessons_count()
            # list_lessons coupe au début — on veut les plus récentes
            doc = ll.load_lessons_doc()
            items = [x for x in (doc.get("lessons") or []) if isinstance(x, dict)]
            recent = list(reversed(items[-cap:]))
            path = str(ll.lessons_path())
            return recent, total, path
    except Exception:
        pass

    for path in _lessons_json_candidates():
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        items = [x for x in (data.get("lessons") or []) if isinstance(x, dict)]
        recent = list(reversed(items[-cap:]))
        return recent, len(items), str(path)
    return [], 0, None


def _fetch_self() -> dict[str, Any] | None:
    payload = fetch_json(
        f"{orchestrator_base()}/v1/self/status?ensure_goals=0",
        timeout=3.0,
    )
    return payload if isinstance(payload, dict) else None


def _pct(drives: dict[str, Any], key: str) -> str:
    try:
        v = float(drives.get(key))
        if v <= 1.0:
            return f"{int(round(v * 100))}%"
        return f"{int(round(v))}%"
    except (TypeError, ValueError):
        return "—"


def _lesson_blob(lesson: dict[str, Any]) -> str:
    parts = [
        str(lesson.get("pattern") or ""),
        str(lesson.get("summary") or ""),
        str(lesson.get("do_not_repeat") or ""),
        str(lesson.get("agent_role") or ""),
        str(lesson.get("id") or ""),
    ]
    return " ".join(parts).lower()


def score_lesson_for_evolution(lesson: dict[str, Any]) -> tuple[float, str]:
    """Retourne (score 0–1, theme_id)."""
    if not isinstance(lesson, dict):
        return 0.0, "none"
    blob = _lesson_blob(lesson)
    if len(blob.strip()) < 8:
        return 0.0, "none"
    best_theme = "general"
    best = 0.55
    for needles, theme, weight in _THEME_WEIGHTS:
        hit = False
        for n in needles:
            # frontières de mot (évite « relance » → « lan »)
            if re.search(rf"(?<![a-z0-9_]){re.escape(n)}(?![a-z0-9_])", blob):
                hit = True
                break
        if hit and weight > best:
            best = weight
            best_theme = theme
    # Légère boost si leçon récente porte un id / role ops/qa
    role = str(lesson.get("agent_role") or "").lower()
    if role in ("ops", "qa", "admin_infra", "pm"):
        best = min(0.98, best + 0.04)
    return round(best, 3), best_theme


def extract_evolution_seed(
    signals: dict[str, Any] | None = None,
    *,
    min_score: float = 0.55,
) -> dict[str, Any] | None:
    """Choisit **1** seed scorée depuis les leçons (pas un dump)."""
    s = signals or {}
    recent = s.get("recent_lessons") if isinstance(s.get("recent_lessons"), list) else []
    ranked: list[tuple[float, str, dict[str, Any]]] = []
    for lesson in recent:
        if not isinstance(lesson, dict):
            continue
        score, theme = score_lesson_for_evolution(lesson)
        if score < min_score:
            continue
        ranked.append((score, theme, lesson))
    if not ranked:
        # Fallback déterministe si leçons vides mais Self a des refs
        total = int(s.get("lessons_total") or 0)
        if total >= 1:
            return {
                "text": (
                    "Prioriser la veille Jobs L2 / LAN / mails à partir des leçons studio "
                    f"({total} en mémoire) — 1 micro-évolution Compagnon, pas un dump."
                )[:160],
                "score": 0.6,
                "theme": "jobs_l2",
                "from_lesson_id": None,
                "auto_promote": False,
            }
        return None
    ranked.sort(key=lambda x: (-x[0], str(x[2].get("id") or "")))
    score, theme, lesson = ranked[0]
    pattern = str(lesson.get("pattern") or lesson.get("summary") or "").strip()
    pattern = re.sub(r"\s+", " ", pattern)[:90]
    theme_label = {
        "jobs_l2": "Jobs L2",
        "lan": "LAN / inventaire",
        "mail": "mails IMAP",
        "infra": "infra / selfcheck",
        "compagnon": "Compagnon Agir",
        "general": "studio",
    }.get(theme, theme)
    text = f"Évolution : renforcer la veille « {theme_label} » — {pattern or 'ancre leçon studio'}"
    return {
        "text": text[:160],
        "score": score,
        "theme": theme,
        "from_lesson_id": str(lesson.get("id") or "")[:48] or None,
        "auto_promote": False,
    }


def build_studio_offer(seed: dict[str, Any] | None) -> dict[str, Any] | None:
    """Offre STUDIO : Team L1 / En parler / Ignorer (jamais auto-Réel)."""
    if not isinstance(seed, dict):
        return None
    text = str(seed.get("text") or "").strip()
    if len(text) < 12:
        return None
    return {
        "offer": True,
        "id": f"memory:evo:{seed.get('from_lesson_id') or seed.get('theme') or 'seed'}"[:64],
        "kind": "evolution_from_memory",
        "offerType": "studio",
        "message": (
            f"Seed d’évolution (score {float(seed.get('score') or 0):.2f}) : « {text[:120]} ». "
            "Team L1, en parler, ou ignorer ?"
        ),
        "evolution_seed": text,
        "evolution_score": float(seed.get("score") or 0),
        "theme": seed.get("theme"),
        "auto_promote": False,
        "intents": [
            {
                "id": "team_l1",
                "label": "Team L1",
                "hint": "qa · lecture seule",
                "teamSpawn": True,
                "teamRole": "qa",
                "teamObjective": (
                    f"Explorer cette idée d'évolution Compagnon (5 lignes, pas de merge, L1) : {text[:140]}"
                ),
            },
            {
                "id": "discuss",
                "label": "En parler",
                "hint": "discuss",
                "sourceText": f"parle-moi de cette idée d'évolution : {text[:120]}",
            },
            {
                "id": "ignore",
                "label": "Ignorer",
                "hint": "dismiss",
                "dismiss": True,
            },
        ],
    }


def _lesson_line(lesson: dict[str, Any]) -> str:
    lid = str(lesson.get("id") or "?")[:28]
    role = str(lesson.get("agent_role") or "any").strip() or "any"
    pattern = str(lesson.get("pattern") or lesson.get("summary") or "").strip()
    if not pattern:
        pattern = str(lesson.get("do_not_repeat") or "").strip()
    pattern = pattern.replace("\n", " ")[:120]
    return f"- `{lid}` ({role}) — {pattern or '(sans résumé)'}"


def collect_memory_signals(*, context: dict[str, Any] | None = None) -> dict[str, Any]:
    del context  # réservé notes futures
    self_raw = _fetch_self()
    state: dict[str, Any] = {}
    enabled = None
    if isinstance(self_raw, dict):
        enabled = self_raw.get("enabled")
        st = self_raw.get("state")
        if isinstance(st, dict):
            state = st

    identity = state.get("identity") if isinstance(state.get("identity"), dict) else {}
    drives = state.get("drives") if isinstance(state.get("drives"), dict) else {}
    intent = state.get("intent") if isinstance(state.get("intent"), dict) else {}
    refs = state.get("memory_refs") if isinstance(state.get("memory_refs"), dict) else {}
    will = state.get("pending_will") if isinstance(state.get("pending_will"), list) else []
    goals = state.get("goals") if isinstance(state.get("goals"), list) else []
    goals_n = state.get("goals_active_count")
    if goals_n is None:
        goals_n = len(
            [
                g
                for g in goals
                if isinstance(g, dict)
                and str(g.get("status") or "").lower() in ("active", "pending", "open")
            ]
        )

    recent, lessons_total, lessons_path = load_recent_lessons(limit=5)
    # Prefer Self refs count when file offline but Self has count
    if lessons_total == 0 and isinstance(refs.get("lessons_count"), int):
        lessons_total = int(refs["lessons_count"])

    incarn = identity.get("incarnations") if isinstance(identity.get("incarnations"), dict) else {}
    return {
        "self_enabled": enabled,
        "identity": {
            "display_name": identity.get("display_name") or "Cortex",
            "mode": identity.get("mode") or "studio",
            "studio": incarn.get("studio") or "lyra",
            "mmo": incarn.get("mmo") or "lia",
        },
        "drives": drives,
        "intent": intent,
        "pending_will_count": len(will),
        "goals_active_count": int(goals_n) if goals_n is not None else 0,
        "memory_refs": {
            "lessons_count": refs.get("lessons_count"),
            "last_lesson_id": refs.get("last_lesson_id"),
            "lessons_path": refs.get("lessons_path") or lessons_path,
        },
        "lessons_total": lessons_total,
        "lessons_path": lessons_path,
        "recent_lessons": recent,
        "self_reachable": self_raw is not None,
    }


def format_memory_recall_reply(signals: dict[str, Any] | None = None) -> str:
    s = signals or collect_memory_signals()
    ident = s.get("identity") if isinstance(s.get("identity"), dict) else {}
    drives = s.get("drives") if isinstance(s.get("drives"), dict) else {}
    intent = s.get("intent") if isinstance(s.get("intent"), dict) else {}
    refs = s.get("memory_refs") if isinstance(s.get("memory_refs"), dict) else {}
    recent = s.get("recent_lessons") if isinstance(s.get("recent_lessons"), list) else []

    lines = [
        "**Mémoire agent** (lecture seule — pas la RAM des VM).",
        "",
        f"- Identité : **{ident.get('display_name') or 'Cortex'}**"
        f" · mode `{ident.get('mode') or 'studio'}`"
        f" · incarnations studio=`{ident.get('studio')}` / mmo=`{ident.get('mmo')}`",
        f"- Intent : `{intent.get('primary') or '—'}`"
        f" · curiosité {_pct(drives, 'curiosity')}"
        f" · tension {_pct(drives, 'tension')}"
        f" · confiance {_pct(drives, 'confidence')}",
        f"- Envies pending : {s.get('pending_will_count', 0)}"
        f" · buts actifs : {s.get('goals_active_count', 0)}",
        f"- Leçons enregistrées : **{s.get('lessons_total', 0)}**"
        + (
            f" · dernier `{refs.get('last_lesson_id')}`"
            if refs.get("last_lesson_id")
            else ""
        ),
    ]
    if s.get("self_reachable") is False:
        lines.append("- ⚠ Self injoignable — synthèse partielle (fichier leçons si dispo).")
    if s.get("self_enabled") is False:
        lines.append("- Flag Self : désactivé (projection lecture seule).")

    lines.append("")
    if recent:
        lines.append(f"**Dernières leçons** ({len(recent)}) :")
        for lesson in recent:
            if isinstance(lesson, dict):
                lines.append(_lesson_line(lesson))
    else:
        lines.append("**Dernières leçons** : aucune chargée (fichier absent ou vide).")

    lines.extend(
        [
            "",
            "**Suite utile (Agir)** :",
            "1. `fais mon brief du matin` — point studio élargi",
            "2. `ouvre http://192.168.0.140:8080/#/team dans le navigateur` — Campus / leçons",
        ]
    )
    seed = s.get("evolution_seed") if isinstance(s.get("evolution_seed"), dict) else None
    if not seed:
        seed = extract_evolution_seed(s)
    if seed:
        lines.append("")
        lines.append(
            f"**STUDIO · seed** (score {float(seed.get('score') or 0):.2f}, pas d’auto-promo) :"
        )
        lines.append(f"« {seed.get('text')} »")
        lines.append("→ Team L1 · En parler · Ignorer")
    else:
        lines.append("")
        lines.append("_Aucune seed évolution extractible pour l’instant._")
    lines.append("")
    lines.append("_Mémoire agent = Self + lessons_learned. RAM/disk VM = Héphaïstos (autre intent)._")
    return "\n".join(lines)


def build_memory_recall_payload(*, context: dict[str, Any] | None = None) -> dict[str, Any]:
    signals = collect_memory_signals(context=context)
    seed = extract_evolution_seed(signals)
    if seed:
        signals = {**signals, "evolution_seed": seed}
    reply = format_memory_recall_reply(signals)
    studio = build_studio_offer(seed)
    return {
        "schema_version": RECALL_SCHEMA_VERSION,
        "kind": "memory_recall",
        "spoken_text": reply,
        "reply": reply,
        "signals": signals,
        "evolution_seed": seed,
        "studio_offer": studio,
        "auto_promote": False,
        "next_agir": [
            {"id": "morning_brief", "sourceText": "fais mon brief du matin"},
            {
                "id": "team",
                "sourceText": "ouvre http://192.168.0.140:8080/#/team dans le navigateur",
            },
            {
                "id": "ecosystem",
                "sourceText": (
                    "rappelle-moi la carte de l'écosystème LBG et le MMO sur .246"
                ),
            },
        ],
    }


def run_memory_recall(*, actor_id: str, text: str, context: dict[str, Any]) -> dict[str, Any]:
    del text
    payload = build_memory_recall_payload(context=context)
    reply = str(payload.get("reply") or "")
    return status_result(
        agent="memory_recall",
        handler="memory_recall",
        actor_id=actor_id,
        reply=reply,
        status=payload,
        source="deterministic_memory_recall",
    )
