"""Tests unitaires pour la Capability Forge (P4)."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

_OVERLAY = Path(__file__).resolve().parents[1]
if str(_OVERLAY) not in sys.path:
    sys.path.insert(0, str(_OVERLAY))

import capability_forge as cf  # noqa: E402


class CapabilityForgeTests(unittest.TestCase):
    def test_ast_safety_clean_code(self) -> None:
        safe_code = """
import sys
import os
from pathlib import Path

def main():
    print("Execution safe")
    return 0

if __name__ == "__main__":
    sys.exit(main())
"""
        errors = cf.check_ast_safety(safe_code)
        self.assertEqual(errors, [])

    def test_ast_safety_forbidden_calls(self) -> None:
        forbidden = [
            "eval('2 + 2')",
            "exec('import sys')",
            "compile('pass', '', 'exec')",
            "__import__('socket')",
        ]
        for snippet in forbidden:
            with self.subTest(snippet=snippet):
                errors = cf.check_ast_safety(snippet)
                self.assertTrue(len(errors) > 0, f"Aurait dû échouer sur : {snippet}")
                self.assertTrue(any("interdit" in e for e in errors))

    def test_ast_safety_forbidden_imports(self) -> None:
        snippets = [
            "import socket",
            "from ctypes import CDLL",
            "import pty",
        ]
        for snippet in snippets:
            with self.subTest(snippet=snippet):
                errors = cf.check_ast_safety(snippet)
                self.assertTrue(len(errors) > 0)
                self.assertTrue(any("Import interdit" in e for e in errors))

    def test_ast_safety_shell_true(self) -> None:
        bad_subprocess = "import subprocess\nsubprocess.run('ls', shell=True)"
        errors = cf.check_ast_safety(bad_subprocess)
        self.assertTrue(any("shell=True est strictement interdit" in e for e in errors))

    def test_evaluate_risk_level_determinism(self) -> None:
        # Code avec unlink ou mot clé delete -> high imposé
        delete_code = "from pathlib import Path\nPath('/tmp/test').unlink()"
        self.assertEqual(cf.evaluate_risk_level("clean_tmp", delete_code, user_risk="low"), "high")

        # Code sans écriture ni suppression -> garde low
        read_code = "print('hello')"
        self.assertEqual(cf.evaluate_risk_level("read_only", read_code, user_risk="low"), "low")

    def test_write_skill_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir) / "test_skill"
            spec = cf.CapabilityCodeSpec(
                name="disk_space_check",
                description="Contrôle de l'espace disque disponible",
                python_code="print('Disque OK')",
                risk_level="low",
                allowed_roots=["/tmp"],
                timeout_s=10,
            )
            md_path, py_path = cf.write_skill_package(base_dir=base_dir, spec=spec)
            self.assertTrue(md_path.is_file())
            self.assertTrue(py_path.is_file())

            content_md = md_path.read_text(encoding="utf-8")
            self.assertIn("name: disk_space_check", content_md)
            self.assertIn("risk_level: low", content_md)

    def test_run_capability_forge_cycle_and_adoption(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            staging_p = Path(tmpdir) / "staging"
            skills_p = Path(tmpdir) / "skills"

            with patch.dict(
                os.environ,
                {
                    "LBG_CAPABILITY_FORGE_STAGING_DIR": str(staging_p),
                    "LBG_SKILLS_LEARNED_DIR": str(skills_p),
                },
            ):
                code = """
import sys

def main():
    if "--help" in sys.argv:
        print("Usage: python3 run.py")
        return 0
    print("Exécution réussie")
    return 0

if __name__ == "__main__":
    sys.exit(main())
"""
                spec = cf.CapabilityCodeSpec(
                    name="lan_ping_probe",
                    description="Sonde ping locale",
                    python_code=code,
                    risk_level="low",
                    allowed_roots=[],
                )
                res = cf.run_capability_forge_cycle(spec, spawn_l2=False)
                self.assertTrue(res["ok"])
                self.assertTrue(res["sandbox_test"]["ok"])
                manifest_p = Path(res["manifest_path"])
                self.assertTrue(manifest_p.is_file())

                # Adoption L2
                adopt_res = cf.adopt_capability_from_staging(manifest_p)
                self.assertTrue(adopt_res["ok"])
                installed_p = Path(adopt_res["installed_path"])
                self.assertTrue((installed_p / "SKILL.md").is_file())
                self.assertTrue((installed_p / "run.py").is_file())


if __name__ == "__main__":
    unittest.main()
