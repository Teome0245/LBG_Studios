"""Feature Proposer — idéation produit → RFC staging → branche auto-evolution/* → L2.

P2 plan_meta_autonomie_l3. Miroir du pattern agent_mutator (staging + revue L2).

A4 :
- pas d'écriture Core3 / declarations /
- pas de git push / merge auto
- OpenGame = sandbox only (note RFC, pas d'exec auto)
- Cursor PR = hors cycle (opt-in humain)
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any

_LAST_PROPOSAL: dict[str, Any] = {}

# Seeds alignées Boîte à idées / Bible (pas de vérité nouvelle sans revue).
_SEED_IDEAS: tuple[dict[str, str], ...] = (
    {
        "id": "seed_craft_social_loop",
        "title": "Boucle craft ↔ social hub Lost Heaven",
        "summary": (
            "Renforcer la boucle compétences → schémas → ressources → craft → économie "
            "au hub Lost Heaven (V2), sans privilégier le combat (V34)."
        ),
        "owner_hint": "dedale",
        "source": "boite:§1",
    },
    {
        "id": "seed_tone_patchwork",
        "title": "Ancrage tone patchwork Lost Heaven",
        "summary": (
            "Appliquer le tone « Patchwork. Récup’. Élégante désolation. » "
            "aux dialogues / POI (pas de magie surface, jargon technique léger)."
        ),
        "owner_hint": "choeur",
        "source": "boite:§2",
    },
    {
        "id": "seed_hub_quest_short",
        "title": "Quête courte hub (starport → cantina)",
        "summary": (
            "Prototype quête courte Lost Heaven : starport → La Perle de Scrapaltai, "
            "PNJ registry-only, sans Tatooine / fantasy gelée."
        ),
        "owner_hint": "iris",
        "source": "boite:§4+bible:V11-V13",
    },
    {
        "id": "seed_m10_novice_vitrine",
        "title": "Vitrine M10 novices craft (hors combat)",
        "summary": (
            "Étendre la vitrine M10 des novices craft/social ; combat Poing/Visée hors UI courte (V34)."
        ),
        "owner_hint": "dedale",
        "source": "bible:V30-V34",
    },
    {
        "id": "seed_studio_judge_dashboard",
        "title": "Dashboard Miroir Team (scores judge / leçons)",
        "summary": (
            "Surface Pilot : historique last_judge / last_mutation / lessons_count "
            "pour le sprint d'évolution (O1 Studio)."
        ),
        "owner_hint": "argus",
        "source": "plan_meta_autonomie_l3",
    },
)

_FORBIDDEN_LORE: tuple[str, ...] = (
    "tatooine",
    "mos eisley",
    "jedi",
    "empire",
    "hutt",
    "lightsaber",
    "magie",
    "magic",
    "loup-garou",
    "pomme rouge",
)

_REQUIRED_LORE_CUES: tuple[str, ...] = (
    "scrapaltai",
    "lost heaven",
    "craft",
    "pre-cu",
    "precu",
    "bible",
)


def proposer_enabled() -> bool:
    return os.environ.get("LBG_TEAM_FEATURE_PROPOSER", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def git_enabled() -> bool:
    return os.environ.get("LBG_FEATURE_PROPOSER_GIT", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def staging_base() -> Path:
    raw = os.environ.get("LBG_FEATURE_PROPOSER_STAGING_DIR", "").strip()
    if raw:
        return Path(raw)
    return Path(__file__).resolve().parent / "staging" / "feature_proposer"


def repo_root() -> Path:
    raw = os.environ.get("LBG_STUDIOS_ROOT", "").strip()
    if raw:
        return Path(raw)
    # packages/cortex/orchestrator/team → LBG_Studios
    return Path(__file__).resolve().parents[4]


def bible_path() -> Path:
    raw = os.environ.get("LBG_BIBLE_MMO_PATH", "").strip()
    if raw:
        return Path(raw)
    return repo_root() / "docs" / "world" / "BIBLE_MMO.md"


def boite_path() -> Path:
    raw = os.environ.get("LBG_BOITE_IDEES_PATH", "").strip()
    if raw:
        return Path(raw)
    return repo_root() / "docs" / "world" / "BOITE_IDEES_GAMEPLAY.md"


def last_proposal_trace() -> dict[str, Any]:
    return dict(_LAST_PROPOSAL) if _LAST_PROPOSAL else {}


def _set_last(trace: dict[str, Any]) -> None:
    global _LAST_PROPOSAL
    _LAST_PROPOSAL = dict(trace)


def meta_status() -> dict[str, object]:
    return {
        "enabled": proposer_enabled(),
        "staging_dir": str(staging_base()),
        "git_enabled": git_enabled(),
        "bible_exists": bible_path().is_file(),
        "boite_exists": boite_path().is_file(),
        "last_proposal": last_proposal_trace(),
    }


def slugify(title: str) -> str:
    s = (title or "").lower().strip()
    repl = {
        "é": "e",
        "è": "e",
        "ê": "e",
        "à": "a",
        "ù": "u",
        "ô": "o",
        "î": "i",
        "ç": "c",
        "’": "",
        "'": "",
    }
    for a, b in repl.items():
        s = s.replace(a, b)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return (s or "feature")[:48]


def collect_signals(*, limit: int = 12) -> list[dict[str, Any]]:
    """Agrège opportunités sprint + seeds Boîte/Bible + leçons PM/dev."""
    out: list[dict[str, Any]] = []
    seen: set[str] = set()

    def _add(item: dict[str, Any]) -> None:
        iid = str(item.get("id") or "")
        if not iid or iid in seen:
            return
        seen.add(iid)
        out.append(item)

    # 1) Sprint opportunités (si dernier sprint en mémoire)
    try:
        from team import evolution_sprint_workflow as evo

        sprint = evo.last_sprint() or {}
        for opp in sprint.get("opportunities") or []:
            if not isinstance(opp, dict):
                continue
            if opp.get("spawn") is False:
                continue
            summary = str(opp.get("summary") or opp.get("gap") or "").strip()
            if not summary:
                continue
            track = str(opp.get("track") or "sprint")
            _add(
                {
                    "id": f"sprint_{track}_{slugify(summary)[:24]}",
                    "title": summary[:80],
                    "summary": summary,
                    "owner_hint": str(opp.get("owner") or "pm"),
                    "source": f"sprint:{track}",
                    "lore_relevant": False,
                }
            )
    except Exception:
        pass

    # 2) Seeds canon
    for seed in _SEED_IDEAS:
        item = dict(seed)
        item["lore_relevant"] = item.get("owner_hint") in ("choeur", "dedale", "iris")
        _add(item)

    # 3) Leçons → opportunités d'amélioration Studio
    try:
        from team import lessons_learned

        for lesson in lessons_learned.list_lessons(role="pm", limit=6):
            pat = str(lesson.get("pattern") or "").strip()
            if not pat:
                continue
            lid = str(lesson.get("id") or uuid.uuid4().hex[:8])
            _add(
                {
                    "id": f"lesson_{lid}",
                    "title": f"Capitaliser leçon: {pat[:60]}",
                    "summary": pat,
                    "owner_hint": str(lesson.get("agent_role") or "pm"),
                    "source": "lessons_learned",
                    "lore_relevant": False,
                }
            )
    except Exception:
        pass

    cap = max(1, min(int(limit), 30))
    return out[:cap]


def pick_idea(
    signals: list[dict[str, Any]] | None = None,
    *,
    idea_id: str = "",
) -> dict[str, Any]:
    items = signals if signals is not None else collect_signals()
    if not items:
        raise RuntimeError("aucun signal Feature Proposer")
    want = (idea_id or "").strip()
    if want:
        for it in items:
            if str(it.get("id")) == want:
                return dict(it)
        raise ValueError(f"idée inconnue: {want}")
    # Préférer une idée lore/Studio seed stable
    for it in items:
        if str(it.get("id") or "").startswith("seed_"):
            return dict(it)
    return dict(items[0])


def bible_check_stub(text: str) -> dict[str, Any]:
    """Vérifie présence Bible + absences mots interdits + présence d'ancres lore."""
    path = bible_path()
    blob = (text or "").lower()
    exists = path.is_file()
    forbidden_hits = [w for w in _FORBIDDEN_LORE if w in blob]
    cue_hits = [w for w in _REQUIRED_LORE_CUES if w in blob]
    # Studio-only ideas may skip lore cues
    lore_ok = exists and not forbidden_hits
    warnings: list[str] = []
    if not exists:
        warnings.append("BIBLE_MMO.md introuvable")
    if forbidden_hits:
        warnings.append(f"termes interdits: {forbidden_hits}")
    if exists and not cue_hits and "studio" not in blob and "pilot" not in blob and "team" not in blob:
        warnings.append("peu d'ancres lore (Scrapaltai / Lost Heaven / craft)")
    return {
        "ok": lore_ok,
        "bible_path": str(path),
        "bible_exists": exists,
        "forbidden_hits": forbidden_hits,
        "lore_cues": cue_hits,
        "warnings": warnings,
    }


def render_rfc_markdown(
    *,
    idea: dict[str, Any],
    bible: dict[str, Any],
    branch_info: dict[str, Any],
) -> str:
    slug = slugify(str(idea.get("title") or idea.get("id") or "feature"))
    lines = [
        f"# RFC — {idea.get('title')}",
        "",
        f"**Slug** : `auto-evolution/{slug}`  ",
        f"**Source** : `{idea.get('source')}`  ",
        f"**Owner hint** : `{idea.get('owner_hint')}`  ",
        f"**Date** : {time.strftime('%Y-%m-%d')}  ",
        "",
        "## Résumé",
        "",
        str(idea.get("summary") or "").strip(),
        "",
        "## Alignement Bible MMO",
        "",
        f"- Bible présente : `{bible.get('bible_exists')}`",
        f"- Check OK : `{bible.get('ok')}`",
        f"- Cues lore : {', '.join(bible.get('lore_cues') or []) or '—'}",
        f"- Warnings : {', '.join(bible.get('warnings') or []) or 'aucun'}",
        "",
        "## Plan d'implémentation (proposé)",
        "",
        "1. Thémis — valider le brief (ce RFC).",
        "2. Dédale / Iris — proto borné (OpenGame sandbox **ou** allowlist Iris).",
        "3. Argus — smokes owner / LAN pertinents.",
        "4. Chœur — conformité Bible si contenu jeu.",
        "5. Pilot L2 — approve / merge humain (pas d'auto-merge).",
        "",
        "## Branche Git",
        "",
        f"- Nom : `{branch_info.get('branch') or f'auto-evolution/{slug}'}`",
        f"- Créée : `{branch_info.get('created')}`",
        f"- Dry-run : `{branch_info.get('dry_run')}`",
        f"- Raison : {branch_info.get('reason') or '—'}",
        "",
        "## Garde-fous A4",
        "",
        "- Pas d'écriture Core3 / `agents/declarations/` auto",
        "- Pas de `git push` / merge auto",
        "- OpenGame = sandbox ADR 0003 uniquement",
        "- Cursor Cloud PR = opt-in humain séparé",
        "",
        "## Critères d'acceptation",
        "",
        "- [ ] RFC relu dans Pilot (tâche L2)",
        "- [ ] Smoke / check_local pertinents verts",
        "- [ ] Bible respectée (pas de termes gelés)",
        "- [ ] Merge humain sur branche `auto-evolution/*`",
        "",
    ]
    return "\n".join(lines)


def _run_git(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )


def maybe_create_local_branch(slug: str, *, dry_run: bool | None = None) -> dict[str, Any]:
    """Crée ``auto-evolution/<slug>`` en local. NEVER push / NEVER merge."""
    branch = f"auto-evolution/{slugify(slug)}"
    root = repo_root()
    force_dry = dry_run if dry_run is not None else not git_enabled()
    info: dict[str, Any] = {
        "branch": branch,
        "created": False,
        "dry_run": True,
        "reason": "",
        "repo": str(root),
    }
    if force_dry:
        info["reason"] = "git disabled or dry_run=1"
        return info
    if not (root / ".git").exists():
        info["reason"] = "pas de dépôt .git"
        return info
    # dirty ?
    st = _run_git(["status", "--porcelain"], cwd=root)
    if st.returncode != 0:
        info["reason"] = f"git status failed: {st.stderr.strip()[:200]}"
        return info
    if st.stdout.strip():
        info["reason"] = "working tree dirty — dry-run"
        return info
    # already on branch?
    cur = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=root)
    current = (cur.stdout or "").strip()
    if current == branch:
        info["created"] = False
        info["dry_run"] = False
        info["reason"] = "déjà sur la branche"
        return info
    exists = _run_git(["show-ref", "--verify", "--quiet", f"refs/heads/{branch}"], cwd=root)
    if exists.returncode == 0:
        info["dry_run"] = False
        info["reason"] = "branche déjà existante (pas de checkout auto)"
        return info
    created = _run_git(["checkout", "-b", branch], cwd=root)
    if created.returncode != 0:
        info["reason"] = f"checkout -b failed: {(created.stderr or '')[:200]}"
        return info
    info["created"] = True
    info["dry_run"] = False
    info["reason"] = "branche créée (locale, no push)"
    return info


def write_staging(
    *,
    slug: str,
    idea: dict[str, Any],
    rfc_md: str,
    bible: dict[str, Any],
    branch_info: dict[str, Any],
    signals_head: list[dict[str, Any]],
) -> Path:
    run_id = f"{slugify(slug)}_{time.strftime('%Y%m%dT%H%M%S')}_{uuid.uuid4().hex[:6]}"
    root = staging_base() / run_id
    root.mkdir(parents=True, exist_ok=True)
    (root / "RFC.md").write_text(rfc_md, encoding="utf-8")
    (root / "idea.json").write_text(
        json.dumps(idea, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "schema_version": 1,
        "run_id": run_id,
        "slug": slugify(slug),
        "created_ts": time.time(),
        "idea_id": idea.get("id"),
        "title": idea.get("title"),
        "branch": branch_info.get("branch"),
        "branch_created": branch_info.get("created"),
        "branch_dry_run": branch_info.get("dry_run"),
        "bible_ok": bible.get("ok"),
        "bible_warnings": bible.get("warnings") or [],
        "signals_sample": [
            {"id": s.get("id"), "title": s.get("title"), "source": s.get("source")}
            for s in signals_head[:8]
        ],
        "a4": {
            "no_core3_write": True,
            "no_declarations_mutate": True,
            "no_auto_merge": True,
            "no_git_push": True,
            "opengame": "sandbox_only_via_prototype_game",
        },
        "staging_dir": str(root),
        "rfc_rel": "RFC.md",
    }
    path = root / "manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def maybe_spawn_l2_review(
    *,
    manifest_path: str,
    slug: str,
    title: str,
    actor_id: str = "system:feature_proposer",
) -> str | None:
    from team import store as team_store

    objective = (
        f"Revue L2 — Feature proposal `{slug}` — {title[:80]}. "
        f"Manifeste: {manifest_path}"
    )
    task = team_store.create_task(
        role="pm",
        objective=objective,
        actor_id=actor_id,
        priority="high",
        approval_required=True,
        context={
            "feature_proposal_review": True,
            "workflow": "feature_proposal_review",
            "manifest_path": manifest_path,
            "proposal_slug": slug,
        },
    )
    return task.id


def run_proposal_cycle(
    *,
    idea_id: str = "",
    spawn_l2: bool = True,
    create_branch: bool = True,
    dry_run_git: bool | None = None,
) -> dict[str, Any]:
    if not proposer_enabled():
        out = {"ok": False, "skipped": True, "error": "feature proposer disabled"}
        _set_last(out)
        return out

    signals = collect_signals()
    try:
        idea = pick_idea(signals, idea_id=idea_id)
    except Exception as exc:
        out = {"ok": False, "error": str(exc)}
        _set_last(out)
        return out

    slug = slugify(str(idea.get("title") or idea.get("id") or "feature"))
    text_for_bible = f"{idea.get('title')} {idea.get('summary')}"
    bible = bible_check_stub(text_for_bible)
    # Enrich RFC text with canon anchors for lore ideas
    if idea.get("lore_relevant") and not bible.get("lore_cues"):
        idea = dict(idea)
        idea["summary"] = (
            str(idea.get("summary") or "")
            + " Ancres: Scrapaltai / Lost Heaven / craft Pre-CU (Bible MMO)."
        )
        bible = bible_check_stub(f"{idea.get('title')} {idea.get('summary')}")

    if create_branch:
        branch_info = maybe_create_local_branch(slug, dry_run=dry_run_git)
    else:
        branch_info = {
            "branch": f"auto-evolution/{slug}",
            "created": False,
            "dry_run": True,
            "reason": "create_branch=false",
        }

    rfc = render_rfc_markdown(idea=idea, bible=bible, branch_info=branch_info)
    manifest_path = write_staging(
        slug=slug,
        idea=idea,
        rfc_md=rfc,
        bible=bible,
        branch_info=branch_info,
        signals_head=signals,
    )

    l2_task_id = None
    note = ""
    smoke_chain: dict[str, Any] = {}
    if spawn_l2:
        try:
            l2_task_id = maybe_spawn_l2_review(
                manifest_path=str(manifest_path),
                slug=slug,
                title=str(idea.get("title") or slug),
            )
        except Exception as exc:
            note = f"spawn_l2_failed:{exc}"

    try:
        from team.verify_chain import maybe_spawn_argus_smoke

        smoke_chain = maybe_spawn_argus_smoke(
            parent_kind="feature_proposer",
            parent_ref=slug,
            manifest_path=str(manifest_path),
            objective=f"Smoke Argus après feature proposal `{slug}`",
        )
    except Exception as exc:
        smoke_chain = {"ok": False, "error": str(exc)[:200]}

    out: dict[str, Any] = {
        "ok": True,
        "idea_id": idea.get("id"),
        "title": idea.get("title"),
        "slug": slug,
        "manifest_path": str(manifest_path),
        "bible_ok": bible.get("ok"),
        "bible_warnings": bible.get("warnings") or [],
        "branch": branch_info,
        "l2_task_id": l2_task_id,
        "smoke_task_id": (smoke_chain or {}).get("smoke_task_id"),
        "smoke_chain": smoke_chain or None,
        "signals_count": len(signals),
        "note": note or None,
    }
    _set_last({k: v for k, v in out.items() if k != "note" or v})
    return out


def execute_proposer_review_from_task(task: Any) -> dict[str, object]:
    ctx = getattr(task, "context", None) or {}
    if not isinstance(ctx, dict):
        ctx = {}
    path = str(ctx.get("manifest_path") or "")
    summary: dict[str, object] = {
        "ok": True,
        "kind": "feature_proposal_review",
        "manifest_path": path,
        "proposal_slug": ctx.get("proposal_slug"),
        "a4": {
            "no_core3_write": True,
            "no_declarations_mutate": True,
            "no_auto_merge": True,
            "no_git_push": True,
        },
        "human_summary": (
            f"RFC feature `{ctx.get('proposal_slug')}` en staging — "
            "relire RFC.md, puis merge humain de la branche auto-evolution/*."
        ),
    }
    if path and Path(path).is_file():
        try:
            summary["manifest"] = json.loads(Path(path).read_text(encoding="utf-8"))
            rfc = Path(path).parent / "RFC.md"
            if rfc.is_file():
                summary["rfc_preview"] = rfc.read_text(encoding="utf-8")[:1200]
        except (OSError, json.JSONDecodeError):
            pass
    return summary


def execute_proposer_from_task(task: Any) -> dict[str, object]:
    ctx = getattr(task, "context", None) or {}
    if not isinstance(ctx, dict):
        ctx = {}
    wf = str(ctx.get("workflow") or "").lower()
    if ctx.get("feature_proposal_review") or wf == "feature_proposal_review":
        return execute_proposer_review_from_task(task)

    idea_id = str(ctx.get("idea_id") or ctx.get("proposal_idea_id") or "")
    spawn = ctx.get("spawn_l2")
    if spawn is None:
        spawn = True
    create_branch = ctx.get("create_branch")
    if create_branch is None:
        create_branch = True
    dry = ctx.get("dry_run_git")
    out = run_proposal_cycle(
        idea_id=idea_id,
        spawn_l2=bool(spawn),
        create_branch=bool(create_branch),
        dry_run_git=bool(dry) if dry is not None else None,
    )
    return {
        "ok": bool(out.get("ok")),
        "kind": "feature_proposer",
        "human_summary": (
            f"Feature proposal `{out.get('slug')}` — "
            + (
                f"L2 {out.get('l2_task_id')}"
                if out.get("l2_task_id")
                else "staging only"
            )
        ),
        **out,
    }
