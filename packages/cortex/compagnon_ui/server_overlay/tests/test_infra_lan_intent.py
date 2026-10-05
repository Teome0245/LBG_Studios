"""Tests — désambiguïsation Infra LAN vs mémoire agent / MMO .246."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_OVERLAY = Path(__file__).resolve().parents[1]
if str(_OVERLAY) not in sys.path:
    sys.path.insert(0, str(_OVERLAY))

import infra_lan_intent as ili  # noqa: E402


class InfraLanIntentTests(unittest.TestCase):
    def test_mmo_memory_on_246_is_not_infra_brief(self) -> None:
        text = (
            "le MMO dans lequel tu pourras t'incarner, hébergé sur .246, "
            "c'est là qu'il faut renforcer la mémoire et ta conscience "
            "de l'écosystème lbg."
        )
        self.assertFalse(ili.wants_infra_lan_brief(text))
        self.assertTrue(ili.is_agent_memory_or_mmo_product(text))

    def test_prime_host_alone_is_not_infra(self) -> None:
        self.assertFalse(ili.wants_infra_lan_brief("travaille sur le MMO Prime .246"))
        self.assertFalse(ili.wants_infra_lan_brief("le serveur 246 héberge le monde"))

    def test_disk_on_246_still_infra(self) -> None:
        self.assertTrue(ili.wants_infra_lan_brief("occupation disque sur .246"))
        self.assertTrue(ili.wants_infra_lan_brief("point sur le disk Prime"))
        self.assertTrue(ili.wants_infra_lan_brief("état RAM du serveur 246"))

    def test_hephaistos_and_proxmox_still_infra(self) -> None:
        self.assertTrue(ili.wants_infra_lan_brief("@hephaistos point infra LAN"))
        self.assertTrue(ili.wants_infra_lan_brief("état proxmox cluster"))

    def test_agent_memory_with_disk_word_still_infra(self) -> None:
        # Signal storage fort gagne même si « conscience » apparaît.
        self.assertTrue(
            ili.wants_infra_lan_brief(
                "conscience du disque : occupation disk sur Prime 246"
            )
        )

    def test_mission_spawn_on_disk_alert(self) -> None:
        self.assertTrue(
            ili.wants_infra_lan_mission(
                "mission : surveille le disque .246",
                team_mentions=[],
            )
        )
        self.assertFalse(
            ili.wants_infra_lan_mission(
                "montre occupation disque .100",
                team_mentions=[],
            )
        )


if __name__ == "__main__":
    unittest.main()
