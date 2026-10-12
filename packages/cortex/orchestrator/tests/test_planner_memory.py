"""Planner : supervision mémoire VM."""

from __future__ import annotations

from services.planner import plan_deterministic, _objective_is_vm_memory_supervision


def test_plan_memory_supervision() -> None:
    o = (
        "Supervise la mémoire des VM 246 Prime, 245 PreCU et 110 Ollama : "
        "charge, libération, compare et signale les seuils critiques"
    )
    plan = plan_deterministic(o, {"_planner": "deterministic"})
    assert len(plan.steps) == 2
    assert plan.steps[0].capability == "devops_probe"
    assert plan.steps[0].action.get("kind") == "vm_memory_probe"
    assert plan.steps[1].capability == "npc_dialogue"


def test_agent_memory_not_vm_supervision() -> None:
    o = (
        "renforce ta mémoire et ta conscience de l'écosystème sur le MMO .246"
    ).lower()
    assert not _objective_is_vm_memory_supervision(o)
