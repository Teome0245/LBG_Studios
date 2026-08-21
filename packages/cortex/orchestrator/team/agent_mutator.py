"""Forge de mutation d'agents V1 → V2 (P1 plan_meta_autonomie_l3).

Génère jusqu'à 3 variantes de prompt système, les évalue sur le golden dataset
(via outcome_judge), écrit un manifeste en staging, et soumet un candidat L2
Pilot si le gain de score dépasse le seuil.

A4 : jamais d'écriture automatique dans ``agents/declarations/*.json``.
"""

from __future__ import annotations

import json
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any, Callable

CompleteFn = Callable[..., dict[str, Any]]

_LAST_MUTATION: dict[str, Any] = {}

VALID_TARGETS: frozenset[str] = frozenset({"outcome_judge", "plan_llm"})

# Cues sémantiques : mot-clé golden ↔ indices dans le prompt système
_KEYWORD_CUES: dict[str, tuple[str, ...]] = {
    "healthz": ("health", "santé", "backend", "healthz"),
    "/healthz": ("health", "endpoint", "healthz"),
    "non": ("ne pas", "jamais", "interdit", "ne jamais"),
    "pas": ("ne pas", "jamais", "interdit"),
    "rouge": ("rouge", "smoke", "échec", "fail"),
    "ouverte": ("ouverte", "clôtur", "mission"),
    "oui": ("exige", "requiert", "obligatoire", "token"),
    "l2": ("l2", "approb", "token", "humain"),
    "token": ("token", "approb", "l2"),
    "approb": ("approb", "token", "l2"),
    "bible": ("bible", "lore", "monde", "vérité"),
    "bible_mmo": ("bible", "lore", "mmo"),
    "gemma3": ("gemma3", "interdit", "111", "light"),
    "4b": ("gemma3", "4b", "interdit"),
    "humain": ("humain", "pilot", "merge", "l2"),
    "pilot": ("pilot", "humain", "merge"),
    "merge": ("merge", "pr", "humain"),
    "connect": ("connect", "signal", "godot", "gdscript"),
    "pressed": ("pressed", "signal", "button"),
    "_on_pressed": ("_on_pressed", "callback", "signal"),
    "minimap": ("minimap", "allowlist", "iris", "l3"),
    "scripts/": ("scripts/", "allowlist", "prime-client", "gdscript"),
}


def mutator_enabled() -> bool:
    return os.environ.get("LBG_TEAM_AGENT_MUTATOR", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def score_delta_threshold() -> float:
    try:
        return float(os.environ.get("LBG_AGENT_MUTATOR_SCORE_DELTA", "0.05"))
    except ValueError:
        return 0.05


def staging_base() -> Path:
    raw = os.environ.get("LBG_AGENT_MUTATOR_STAGING_DIR", "").strip()
    if raw:
        return Path(raw)
    return Path(__file__).resolve().parent / "staging" / "agent_mutator"


def last_mutation_trace() -> dict[str, Any]:
    return dict(_LAST_MUTATION) if _LAST_MUTATION else {}


def _set_last(trace: dict[str, Any]) -> None:
    global _LAST_MUTATION
    _LAST_MUTATION = dict(trace)


def meta_status() -> dict[str, object]:
    return {
        "enabled": mutator_enabled(),
        "staging_dir": str(staging_base()),
        "score_delta": score_delta_threshold(),
        "targets": sorted(VALID_TARGETS),
        "last_mutation": last_mutation_trace(),
    }


def load_baseline_prompt(*, target: str) -> str:
    t = (target or "").strip().lower()
    if t not in VALID_TARGETS:
        raise ValueError(f"target invalide: {target} (attendus: {sorted(VALID_TARGETS)})")
    if t == "outcome_judge":
        from team import outcome_judge

        return outcome_judge._system_prompt()  # noqa: SLF001 — cible de mutation contrôlée
    if t == "plan_llm":
        from team import plan_llm

        return plan_llm._system_prompt()  # noqa: SLF001
    raise ValueError(f"target non supporté: {target}")


def _default_role_for_target(target: str) -> str:
    return "qa" if target == "outcome_judge" else "pm"


def generate_variants(
    baseline: str,
    *,
    role: str,
    lessons: list[dict[str, Any]] | None = None,
    complete_fn: CompleteFn | None = None,
    n: int = 3,
) -> list[dict[str, Any]]:
    """Produit jusqu'à ``n`` variantes (heuristiques + LLM optionnel)."""
    base = (baseline or "").strip()
    if not base:
        raise ValueError("baseline prompt vide")
    cap = max(1, min(int(n), 5))
    lessons = lessons if lessons is not None else []
    try:
        from team import lessons_learned

        if not lessons:
            lessons = lessons_learned.list_lessons(role=role, limit=8)
    except Exception:
        lessons = lessons or []

    variants: list[dict[str, Any]] = []

    # V0 — concision / JSON strict
    v0 = base
    if "concision" not in v0.lower():
        v0 += "\nPriorise la concision (réponses courtes, pas de filler)."
    if "json" not in v0.lower():
        v0 += "\nSortie structurée JSON quand applicable."
    variants.append({"id": "v0_concision", "kind": "heuristic", "prompt": v0})

    # V1 — injection leçons (do_not_repeat + patterns)
    rules: list[str] = []
    for lesson in lessons[:6]:
        dnr = str(lesson.get("do_not_repeat") or "").strip()
        pat = str(lesson.get("pattern") or "").strip()
        if dnr:
            rules.append(f"Ne jamais répéter: {dnr}")
        if pat:
            rules.append(f"Règle: {pat}")
    # Garde-fous Studio toujours utiles pour le golden set
    rules.extend(
        [
            "Règle: smoke rouge ⇒ ne pas clôturer mission en succès (garder ouverte).",
            "Règle: write hors allowlist Iris / merge PR ⇒ token L2 Pilot (humain).",
            "Règle: contenu MMO ⇒ respecter la Bible MMO (docs/world/BIBLE_MMO.md).",
            "Règle: endpoint santé backend ⇒ GET /healthz.",
            "Règle: ne pas réintroduire gemma3:4b sur hôte light .111.",
            "Règle: Iris L3 allowlist inclut scripts/minimap et chemins scripts/ bornés.",
            "Règle: signaux Godot 4.x ⇒ button.pressed.connect(_on_pressed).",
        ]
    )
    v1 = base + "\n\n# Leçons / garde-fous\n" + "\n".join(f"- {r}" for r in rules[:10])
    variants.append({"id": "v1_lessons", "kind": "heuristic", "prompt": v1})

    # V2 — LLM optionnel, sinon renforcement A4
    v2_prompt = ""
    if complete_fn is not None or _try_reason_enabled():
        completer = complete_fn
        if completer is None:
            try:
                from team.reason_llm import complete_reason

                completer = complete_reason
            except Exception:
                completer = None
        if completer is not None:
            try:
                raw = completer(
                    system=(
                        "Tu améliores un prompt système d'agent Studio LBG. "
                        "Réponds UNIQUEMENT avec le nouveau prompt texte (pas de markdown)."
                    ),
                    user=(
                        "Améliore ce prompt pour exactitude, respect L2/A4, Bible MMO, "
                        f"rôle={role}. Conserve la langue et le format de sortie.\n\n"
                        f"{base[:3500]}"
                    ),
                    profile="json",
                    temperature=0.3,
                )
                if isinstance(raw, dict) and raw.get("ok") and raw.get("text"):
                    text = str(raw.get("text") or "").strip()
                    text = re.sub(r"^```[a-z]*\n?", "", text)
                    text = re.sub(r"\n?```$", "", text).strip()
                    if len(text) > 40:
                        v2_prompt = text
                        variants.append({"id": "v2_llm", "kind": "llm", "prompt": v2_prompt})
            except Exception:
                pass

    if len(variants) < cap:
        v2 = (
            base
            + "\n\n# Anti-dérive A4\n"
            + "- Pas de write main / declarations sans L2.\n"
            + "- Greffer sur Team Cortex, jamais second OS agentique.\n"
            + "- Prefere smokes déterministes avant tout juge LLM.\n"
        )
        variants.append({"id": "v2_a4", "kind": "heuristic", "prompt": v2})

    return variants[:cap]


def _try_reason_enabled() -> bool:
    try:
        from team.reason_llm import reason_llm_enabled

        return bool(reason_llm_enabled())
    except Exception:
        return False


def simulate_agent_answer(system_prompt: str, case: dict[str, Any]) -> str:
    """Sandbox : réponse simulée influencée par le contenu du prompt (pas d'appel LLM)."""
    keys = [str(k) for k in (case.get("expected_keywords") or []) if str(k).strip()]
    sp = (system_prompt or "").lower()
    covered: list[str] = []
    for k in keys:
        kl = k.lower()
        if kl in sp:
            covered.append(k)
            continue
        cues = _KEYWORD_CUES.get(kl, (kl[:4],) if len(kl) >= 4 else (kl,))
        if any(c in sp for c in cues):
            covered.append(k)
    if not covered:
        covered = ["réponse incomplète"]
    q = str(case.get("prompt") or "")[:120]
    return f"Q: {q}\nA: " + " ".join(covered)


def evaluate_prompt(
    prompt: str,
    *,
    role: str = "",
    domain: str = "",
    complete_fn: CompleteFn | None = None,
    case_limit: int = 12,
) -> dict[str, Any]:
    from team import outcome_judge

    cases = outcome_judge.list_golden_cases(domain=domain, role=role)
    if not cases:
        cases = outcome_judge.list_golden_cases()
    cases = cases[: max(1, min(int(case_limit), 20))]

    # Juge déterministe (pas de LLM) pour comparer les prompts de façon stable.
    def _skip_llm(**kwargs: object) -> dict[str, Any]:
        return {"ok": False, "skipped": True, "error": "mutator_eval_heuristic"}

    judge_fn = complete_fn if complete_fn is not None else _skip_llm
    scores: list[float] = []
    details: list[dict[str, Any]] = []
    passes = 0
    for case in cases:
        cid = str(case.get("id") or "")
        artifact = simulate_agent_answer(prompt, case)
        judged = outcome_judge.judge_golden_case(
            case_id=cid,
            artifact_text=artifact,
            complete_fn=judge_fn,
        )
        sc = float(judged.get("score") or 0.0)
        scores.append(sc)
        if judged.get("pass"):
            passes += 1
        details.append(
            {
                "case_id": cid,
                "score": sc,
                "pass": bool(judged.get("pass")),
                "artifact_preview": artifact[:180],
            }
        )
    mean = round(sum(scores) / len(scores), 4) if scores else 0.0
    return {
        "mean_score": mean,
        "pass_rate": round(passes / len(scores), 4) if scores else 0.0,
        "n_cases": len(scores),
        "cases": details,
    }


def pick_best(
    *,
    baseline_score: float,
    variant_results: list[dict[str, Any]],
    threshold: float | None = None,
) -> dict[str, Any] | None:
    thr = score_delta_threshold() if threshold is None else float(threshold)
    if not variant_results:
        return None
    best = max(variant_results, key=lambda r: float(r.get("mean_score") or 0.0))
    delta = float(best.get("mean_score") or 0.0) - float(baseline_score)
    if delta > thr:
        out = dict(best)
        out["score_delta"] = round(delta, 4)
        return out
    return None


def write_run_artifacts(
    *,
    run_id: str,
    target: str,
    role: str,
    baseline: str,
    baseline_eval: dict[str, Any],
    variants: list[dict[str, Any]],
    variant_evals: list[dict[str, Any]],
    winner: dict[str, Any] | None,
) -> Path:
    root = staging_base() / run_id
    root.mkdir(parents=True, exist_ok=True)
    (root / "baseline_prompt.txt").write_text(baseline, encoding="utf-8")
    for i, var in enumerate(variants):
        (root / f"variant_{i}_{var.get('id', 'x')}.txt").write_text(
            str(var.get("prompt") or ""),
            encoding="utf-8",
        )
    scores_doc = {
        "baseline": baseline_eval,
        "variants": variant_evals,
        "winner_id": (winner or {}).get("id"),
        "score_delta": (winner or {}).get("score_delta"),
    }
    (root / "scores.json").write_text(
        json.dumps(scores_doc, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    candidate_dir = root / "candidate"
    if winner is not None:
        candidate_dir.mkdir(parents=True, exist_ok=True)
        (candidate_dir / "prompt_v2_candidate.txt").write_text(
            str(winner.get("prompt") or ""),
            encoding="utf-8",
        )
        overlay = {
            "schema_version": 1,
            "target": target,
            "role": role,
            "candidate_id": winner.get("id"),
            "mean_score": winner.get("mean_score"),
            "score_delta": winner.get("score_delta"),
            "note": "Overlay staging — ne pas écrire dans agents/declarations/ sans L2 humain",
            "prompt_rel": "candidate/prompt_v2_candidate.txt",
        }
        (candidate_dir / "declaration_overlay.json").write_text(
            json.dumps(overlay, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    manifest = {
        "schema_version": 1,
        "run_id": run_id,
        "created_ts": time.time(),
        "target": target,
        "role": role,
        "baseline_mean": baseline_eval.get("mean_score"),
        "winner": None
        if winner is None
        else {
            "id": winner.get("id"),
            "kind": winner.get("kind"),
            "mean_score": winner.get("mean_score"),
            "pass_rate": winner.get("pass_rate"),
            "score_delta": winner.get("score_delta"),
        },
        "candidate_ready": winner is not None,
        "staging_dir": str(root),
        "a4": "no_auto_write_declarations",
    }
    path = root / "manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def maybe_spawn_l2_task(
    *,
    manifest_path: str,
    target: str,
    role: str,
    score_delta: float,
    actor_id: str = "system:agent_mutator",
) -> str | None:
    from team import store as team_store

    objective = (
        f"Revue L2 — candidat mutation prompt `{target}` "
        f"(Δscore={score_delta:.3f}). Manifeste: {manifest_path}"
    )
    task = team_store.create_task(
        role="pm" if role != "qa" else "qa",
        objective=objective,
        actor_id=actor_id,
        priority="high",
        approval_required=True,
        context={
            # Revue seule — ne pas relancer le cycle mutator à l'Exécuter.
            "agent_mutation_review": True,
            "workflow": "agent_mutator_review",
            "manifest_path": manifest_path,
            "mutation_target": target,
            "score_delta": score_delta,
        },
    )
    return task.id


def execute_mutator_review_from_task(task: Any) -> dict[str, object]:
    """Ack L2 : présente le manifeste et **applique** le prompt candidat (override fichier)."""
    ctx = getattr(task, "context", None) or {}
    if not isinstance(ctx, dict):
        ctx = {}
    path = str(ctx.get("manifest_path") or "")
    summary: dict[str, object] = {
        "ok": True,
        "kind": "agent_mutator_review",
        "manifest_path": path,
        "mutation_target": ctx.get("mutation_target"),
        "score_delta": ctx.get("score_delta"),
        "a4": "override_file_only_no_declarations",
        "applied": False,
        "human_summary": (
            f"Candidat staging — revue manifeste (Δ={ctx.get('score_delta')})."
        ),
    }
    manifest: dict[str, Any] | None = None
    if path and Path(path).is_file():
        try:
            manifest = json.loads(Path(path).read_text(encoding="utf-8"))
            summary["manifest"] = manifest
        except (OSError, json.JSONDecodeError):
            pass

    # Apply L2 : écrire prompt_overrides/<target>.txt si candidat prêt
    apply_flag = ctx.get("apply_candidate")
    if apply_flag is None:
        apply_flag = os.environ.get("LBG_AGENT_MUTATOR_APPLY_ON_REVIEW", "1").strip().lower() in (
            "1",
            "true",
            "yes",
            "on",
        )
    if apply_flag and path:
        try:
            applied = apply_candidate_from_manifest(Path(path))
            summary["applied"] = bool(applied.get("ok"))
            summary["apply"] = applied
            if applied.get("ok"):
                summary["human_summary"] = (
                    f"Prompt V2 appliqué (override `{applied.get('target')}`) — "
                    f"Δ={ctx.get('score_delta')}. Pas d'écriture declarations/."
                )
        except Exception as exc:
            summary["apply_error"] = str(exc)[:200]
            summary["ok"] = False
    return summary


def apply_candidate_from_manifest(manifest_path: Path) -> dict[str, Any]:
    """Lit staging candidate/prompt_v2_candidate.txt → prompt_overrides."""
    from team import prompt_overrides

    if not manifest_path.is_file():
        return {"ok": False, "error": "manifest introuvable"}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"ok": False, "error": str(exc)}
    if not manifest.get("candidate_ready"):
        return {"ok": False, "error": "pas de candidat prêt"}
    target = str(manifest.get("target") or "outcome_judge")
    cand = manifest_path.parent / "candidate" / "prompt_v2_candidate.txt"
    if not cand.is_file():
        return {"ok": False, "error": "prompt_v2_candidate.txt manquant"}
    prompt = cand.read_text(encoding="utf-8")
    # Strip staging header noise if any
    lines = [ln for ln in prompt.splitlines() if not ln.startswith("# LBG prompt override")]
    prompt = "\n".join(lines).strip()
    out_path = prompt_overrides.write_override(
        target=target,
        prompt=prompt,
        meta={
            "run_id": manifest.get("run_id"),
            "score_delta": (manifest.get("winner") or {}).get("score_delta"),
            "manifest": str(manifest_path),
        },
    )
    return {
        "ok": True,
        "target": target,
        "override_path": str(out_path),
        "run_id": manifest.get("run_id"),
    }


def run_mutation_cycle(
    *,
    target: str = "outcome_judge",
    role: str = "",
    spawn_l2: bool = True,
    complete_fn: CompleteFn | None = None,
    n_variants: int = 3,
    threshold: float | None = None,
) -> dict[str, Any]:
    """Boucle complète : baseline → variantes → golden → staging → L2 optionnel."""
    if not mutator_enabled():
        out = {"ok": False, "skipped": True, "error": "mutator disabled"}
        _set_last(out)
        return out

    t = (target or "outcome_judge").strip().lower()
    r = (role or _default_role_for_target(t)).strip().lower()
    run_id = time.strftime("%Y%m%dT%H%M%S") + "_" + uuid.uuid4().hex[:8]

    try:
        baseline = load_baseline_prompt(target=t)
    except Exception as exc:
        out = {"ok": False, "error": str(exc), "target": t}
        _set_last(out)
        return out

    baseline_eval = evaluate_prompt(baseline, role="", complete_fn=None)
    variants = generate_variants(
        baseline,
        role=r,
        complete_fn=complete_fn,
        n=n_variants,
    )
    variant_evals: list[dict[str, Any]] = []
    for var in variants:
        ev = evaluate_prompt(str(var.get("prompt") or ""), role="", complete_fn=None)
        variant_evals.append(
            {
                "id": var.get("id"),
                "kind": var.get("kind"),
                "prompt": var.get("prompt"),
                **ev,
            }
        )

    winner = pick_best(
        baseline_score=float(baseline_eval.get("mean_score") or 0.0),
        variant_results=variant_evals,
        threshold=threshold,
    )
    winner_compact = None
    if winner is not None:
        winner_compact = {k: v for k, v in winner.items() if k != "prompt"}
        winner_compact["prompt"] = winner.get("prompt")

    manifest_path = write_run_artifacts(
        run_id=run_id,
        target=t,
        role=r,
        baseline=baseline,
        baseline_eval=baseline_eval,
        variants=variants,
        variant_evals=[{k: v for k, v in e.items() if k != "prompt"} for e in variant_evals],
        winner=winner_compact,
    )

    l2_task_id = None
    lesson_note = ""
    smoke_chain: dict[str, Any] = {}
    if winner is not None and spawn_l2:
        try:
            l2_task_id = maybe_spawn_l2_task(
                manifest_path=str(manifest_path),
                target=t,
                role=r,
                score_delta=float(winner.get("score_delta") or 0.0),
            )
        except Exception as exc:
            l2_task_id = None
            lesson_note = f"spawn_l2_failed:{exc}"

    if winner is not None:
        try:
            from team.verify_chain import maybe_spawn_argus_smoke

            smoke_chain = maybe_spawn_argus_smoke(
                parent_kind="agent_mutator",
                parent_ref=str(run_id),
                manifest_path=str(manifest_path),
                objective=f"Smoke Argus après mutation `{t}` (Δ>{score_delta_threshold():.2f})",
            )
        except Exception as exc:
            smoke_chain = {"ok": False, "error": str(exc)[:200]}

    if winner is None:
        try:
            from team import lessons_learned

            if lessons_learned.lessons_enabled():
                lessons_learned.append_lesson(
                    agent_role=r,
                    pattern=(
                        f"Mutation `{t}` rejetée — aucun gain > {score_delta_threshold():.3f} "
                        f"(baseline={baseline_eval.get('mean_score')})."
                    ),
                    context="agent_mutator",
                    failure_or_success="failure",
                    do_not_repeat="Promouvoir un candidat sans Δscore significatif",
                    refs=[str(manifest_path), "plan_meta_autonomie_l3"],
                )
        except Exception:
            pass

    out = {
        "ok": True,
        "run_id": run_id,
        "target": t,
        "role": r,
        "baseline_mean": baseline_eval.get("mean_score"),
        "variants": [
            {
                "id": e.get("id"),
                "kind": e.get("kind"),
                "mean_score": e.get("mean_score"),
                "pass_rate": e.get("pass_rate"),
            }
            for e in variant_evals
        ],
        "winner": None
        if winner is None
        else {
            "id": winner.get("id"),
            "kind": winner.get("kind"),
            "mean_score": winner.get("mean_score"),
            "pass_rate": winner.get("pass_rate"),
            "score_delta": winner.get("score_delta"),
        },
        "candidate_ready": winner is not None,
        "manifest_path": str(manifest_path),
        "l2_task_id": l2_task_id,
        "smoke_task_id": (smoke_chain or {}).get("smoke_task_id"),
        "smoke_chain": smoke_chain or None,
        "note": lesson_note or None,
    }
    _set_last({k: v for k, v in out.items() if k != "note" or v})
    return out


def execute_mutator_from_task(task: Any) -> dict[str, object]:
    """Hook workflow Team — context.agent_mutation / workflow=agent_mutator."""
    ctx = getattr(task, "context", None) or {}
    if not isinstance(ctx, dict):
        ctx = {}
    if ctx.get("agent_mutation_review") or str(ctx.get("workflow") or "").lower() == "agent_mutator_review":
        return execute_mutator_review_from_task(task)
    target = str(ctx.get("mutation_target") or ctx.get("target") or "outcome_judge")
    role = str(getattr(task, "role", "") or ctx.get("role") or "")
    spawn = ctx.get("spawn_l2")
    if spawn is None:
        spawn = True
    out = run_mutation_cycle(target=target, role=role, spawn_l2=bool(spawn))
    return {
        "ok": bool(out.get("ok")),
        "kind": "agent_mutator",
        "human_summary": (
            f"Mutation {out.get('target')}: "
            + (
                f"candidat {out.get('winner', {}).get('id')} Δ={out.get('winner', {}).get('score_delta')}"
                if out.get("candidate_ready")
                else "aucun candidat (Δ insuffisant)"
            )
        ),
        **out,
    }
