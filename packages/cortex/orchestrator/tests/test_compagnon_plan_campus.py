"""Plan Compagnon → Campus : pas de QA smoke / bug générique ; objectif non tronqué."""

from __future__ import annotations

from team import campus_conductor, roles as team_roles


_PLAN_MD = """## Objectif
Créer une répartition évolutive des factions sur Scrapaltai et introduire deux nouveaux
Points d'Intérêt (POI) pour y placer des PNJ représentant ces factions.

## Phases
* **Phase 1 : Définition des Factions et des POI**
* **Phase 2 : Implémentation des PNJ**
* **Phase 3 : Ajustement de l'Évolution**

## Prochaine action concrète
Soumettre ce plan au bureau/Team pour validation.
"""


def _objective() -> str:
    return (
        "Plan studio Compagnon — exécuter / découper (game design / lore / contenu monde). "
        "Demande humaine : répartition des factions sur scrapaltai, deux villes (POI), PNJ. "
        "Owners : Hermès (ordo), Iris, Chœur, Dédale. Contre-pouvoir L2 inchangé.\n\n"
        f"--- PLAN COMPAGNON ---\n{_PLAN_MD}"
    )


def test_plan_from_compagnon_scrapaltai_no_smoke_qa() -> None:
    props = team_roles.plan_from_objective(_objective(), actor_id="u:test")
    roles = [str(p.get("role")) for p in props]
    objs = [str(p.get("objective") or "").lower() for p in props]

    assert "pm" in roles
    assert "dev_game" in roles
    assert "player_ia" in roles
    assert "qa" not in roles
    assert not any("smoke lan" in o for o in objs)
    assert not any("bug gameplay" in o for o in objs)
    assert any("faction" in o for o in objs)
    assert all((p.get("context") or {}).get("compagnon_plan") for p in props)


def test_legacy_boilerplate_still_poisonous_without_marker() -> None:
    """Sans marqueur PLAN COMPAGNON, l'ancien préambule peut encore matcher smoke — attendu."""
    poisoned = (
        "Hermès (PM) + Team : exécuter. Argus (smokes). présence MMO. scrapaltai factions"
    )
    props = team_roles.plan_from_objective(poisoned, actor_id="u:test")
    roles = [str(p.get("role")) for p in props]
    # Au moins un signal smoke/mmo encore possible hors chemin Compagnon
    assert "qa" in roles or "dev_game" in roles


def test_start_mission_keeps_plan_body_in_context(monkeypatch) -> None:
    monkeypatch.setenv("LBG_TEAM_CAMPUS_CONDUCTOR", "0")
    obj = _objective()
    assert len(obj) > 200
    out = campus_conductor.start_mission(
        obj, dry_run=True, auto_act=False, max_tasks=6
    )
    assert out.get("ok") is True
    created = out.get("created") or []
    assert created
    # Contexte mission : plus de coupe à 200
    ctx_obj = str((created[0].get("context") or {}).get("_campus_mission_objective") or "")
    assert "--- PLAN COMPAGNON ---" in ctx_obj
    assert "Phase 1" in ctx_obj or "factions" in ctx_obj.lower()
    # Objectif tâche PM : plan présent
    pm = next(c for c in created if c.get("role") == "pm")
    assert "PLAN COMPAGNON" in str(pm.get("objective") or "") or "faction" in str(
        pm.get("objective") or ""
    ).lower()
