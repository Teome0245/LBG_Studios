"""
test_physical_presence.py — Tests de détection de présence physique via Freebox.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_OVERLAY = Path(__file__).resolve().parents[1]
if str(_OVERLAY) not in sys.path:
    sys.path.insert(0, str(_OVERLAY))

import physical_presence as pp  # noqa: E402


class PhysicalPresenceTests(unittest.TestCase):
    def test_wants_physical_presence_positive(self) -> None:
        positive_prompts = [
            "suis-je au bureau ?",
            "suis-je là ?",
            "est-ce que je suis chez moi ?",
            "présence physique",
            "qui est au bureau ?",
            "détection de présence",
            "téléphones connectés",
            "wifi freebox",
            "statut freebox",
            "nest mini connecté ?",
            "es-tu au courant que je suis là ?",
            "tu peux me dire quoi sur ma présence, l'écosystème Wi-Fi/LAN ou le Nest Mini ?",
            "ma présence",
        ]
        for p in positive_prompts:
            self.assertTrue(pp.wants_physical_presence(p), f"Should match: {p}")

    def test_wants_physical_presence_negative(self) -> None:
        negative_prompts = [
            "bonjour",
            "raconte-moi une histoire",
            "status cortex",
            "quelle heure est-il à Lost Heaven ?",
            "qui es-tu ?",
        ]
        for p in negative_prompts:
            self.assertFalse(pp.wants_physical_presence(p), f"Should NOT match: {p}")

    def test_get_physical_presence_mock_detected(self) -> None:
        fake_fb_data = {
            "ok": True,
            "box_model": "Freebox v7 (r1)",
            "lan_hosts": [
                {
                    "name": "Sds-Phone",
                    "mac": "6a:42:38:e9:4c:09",
                    "active": True,
                    "reachable": True,
                    "ipv4": ["192.168.0.204"],
                    "vendor": "Google",
                },
                {
                    "name": "PC-SDESHARCHES",
                    "mac": "04:7c:16:cd:98:a5",
                    "active": True,
                    "reachable": True,
                    "ipv4": ["192.168.0.10"],
                    "vendor": "Micro-Star",
                },
                {
                    "name": "Google-Nest-Mini",
                    "mac": "d4:f5:47:16:23:64",
                    "active": True,
                    "reachable": True,
                    "ipv4": ["192.168.0.75"],
                },
            ],
        }

        mock_fb = MagicMock()
        mock_fb.freebox_configured.return_value = True
        mock_fb.probe_freebox.return_value = fake_fb_data

        with patch.object(pp, "_get_freebox_client", return_value=mock_fb):
            res = pp.get_physical_presence(force_refresh=True)
            self.assertTrue(res["ok"])
            self.assertTrue(res["teome_present"])
            self.assertEqual(len(res["active_devices"]), 2)
            self.assertTrue(res["nest_mini_active"])
            self.assertEqual(res["total_active_lan"], 3)

            report = pp.format_physical_presence_causerie(res)
            self.assertIn("au bureau", report)
            self.assertIn("Sds-Phone", report)
            self.assertIn("PC-SDESHARCHES", report)
            self.assertIn("Google Nest Mini", report)

    def test_get_physical_presence_mock_absent(self) -> None:
        fake_fb_data = {
            "ok": True,
            "box_model": "Freebox v7 (r1)",
            "lan_hosts": [
                {
                    "name": "Nintendo Switch",
                    "mac": "ec:c4:0d:bf:7e:bf",
                    "active": True,
                    "reachable": True,
                    "ipv4": ["192.168.0.210"],
                },
            ],
        }

        mock_fb = MagicMock()
        mock_fb.freebox_configured.return_value = True
        mock_fb.probe_freebox.return_value = fake_fb_data

        with patch.object(pp, "_get_freebox_client", return_value=mock_fb):
            res = pp.get_physical_presence(force_refresh=True)
            self.assertTrue(res["ok"])
            self.assertFalse(res["teome_present"])
            self.assertEqual(len(res["active_devices"]), 0)

            report = pp.format_physical_presence_causerie(res)
            self.assertIn("absent", report.lower())


if __name__ == "__main__":
    unittest.main()
