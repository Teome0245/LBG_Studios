"""Tests — validation déterministe Intent Forge P1, P2 & intégration runtime P3."""

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

import intent_forge as f  # noqa: E402


class IntentForgeTests(unittest.TestCase):
    def test_record_and_load_misses_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "misses.jsonl"
            self.assertTrue(f.record_intent_miss("lance un scan", conversation_id="c1", path=file_path))
            self.assertTrue(f.record_intent_miss("vérifie la météo", conversation_id="c2", path=file_path))

            items = f.load_intent_misses(path=file_path, limit=10)
            self.assertEqual(len(items), 2)
            self.assertEqual(items[0]["prompt"], "lance un scan")
            self.assertEqual(items[1]["conversation_id"], "c2")

    def test_empty_prompt_and_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "misses.jsonl"
            self.assertFalse(f.record_intent_miss("   ", path=file_path))
            with patch.dict(os.environ, {"LBG_INTENT_MISSES": "0"}):
                self.assertFalse(f.record_intent_miss("scan lan", path=file_path))

    def test_prompt_truncation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "misses.jsonl"
            long_prompt = "a" * 600
            self.assertTrue(f.record_intent_miss(long_prompt, path=file_path))
            items = f.load_intent_misses(path=file_path)
            self.assertEqual(len(items), 1)
            self.assertEqual(len(items[0]["prompt"]), 500)

    def test_load_corrupted_json_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "misses.jsonl"
            file_path.write_text("{\"prompt\": \"ok\"}\ncorrupted line\n{\"prompt\": \"ok2\"}\n", encoding="utf-8")
            items = f.load_intent_misses(path=file_path)
            self.assertEqual(len(items), 2)

    def test_intent_spec_from_dict_valid(self) -> None:
        raw = {
            "action": "custom_audit",
            "label": "Audit personnalisé",
            "keywords": [r"fais\s+un\s+audit"],
            "target_capability": "audit_tool",
            "examples_pos": ["fais un audit lan"],
        }
        spec, errors = f.intent_spec_from_dict(raw)
        self.assertEqual(errors, [])
        self.assertIsNotNone(spec)
        self.assertEqual(spec.action, "custom_audit")

    def test_intent_spec_from_dict_missing_fields(self) -> None:
        raw = {"action": "bad"}
        spec, errors = f.intent_spec_from_dict(raw)
        self.assertIsNone(spec)
        self.assertTrue(len(errors) > 0)

    def test_check_regex_safe(self) -> None:
        self.assertIsNone(f.check_regex_safe(r"supprime\s+le\s+fichier"))
        self.assertIn("ReDoS", str(f.check_regex_safe("(a+)+")))
        self.assertIn("backreference", str(f.check_regex_safe(r"(\w)\1")))
        self.assertIn("regex invalide", str(f.check_regex_safe("(")))
        self.assertIn("trop long", str(f.check_regex_safe("a" * 205)))

    def test_validate_intent_spec_success(self) -> None:
        spec = f.IntentSpec(
            action="custom_scan",
            label="Scan personnalisé",
            keywords=[r"lance\s+un\s+scan\s+perso"],
            target_capability="scan_tool",
            examples_pos=["lance un scan perso"],
            examples_neg=[],
        )
        res = f.validate_intent_spec(
            spec,
            existing_patterns={},
            negative_corpus=list(f.DEFAULT_NEGATIVE_CORPUS),
            known_capabilities={"scan_tool"},
        )
        self.assertTrue(res["ok"])
        self.assertEqual(res["errors"], [])

    def test_validate_capability_missing(self) -> None:
        spec = f.IntentSpec(
            action="custom_scan",
            label="Scan",
            keywords=[r"lance\s+le\s+scan"],
            target_capability="unknown_cap",
            examples_pos=["lance le scan"],
        )
        res = f.validate_intent_spec(
            spec,
            existing_patterns={},
            negative_corpus=[],
            known_capabilities={"other_cap"},
        )
        self.assertFalse(res["ok"])
        self.assertIn("capability_missing:unknown_cap", res["errors"])

    def test_validate_false_positive_on_negative_corpus(self) -> None:
        spec = f.IntentSpec(
            action="too_broad",
            label="Trop large",
            keywords=[r"bonjour"],
            target_capability="cap",
            examples_pos=["bonjour Gladys"],
        )
        res = f.validate_intent_spec(
            spec,
            existing_patterns={},
            negative_corpus=list(f.DEFAULT_NEGATIVE_CORPUS),
            known_capabilities={"cap"},
        )
        self.assertFalse(res["ok"])
        self.assertTrue(any("faux positif" in e for e in res["errors"]))

    def test_validate_collision_existing_action(self) -> None:
        spec = f.IntentSpec(
            action="new_smoke",
            label="New smoke",
            keywords=[r"smoke\s+test"],
            target_capability="cap",
            examples_pos=["lance un smoke test lan"],
        )
        existing = {"smoke_lan_quick": [r"smoke\s+test\s+lan"]}
        res = f.validate_intent_spec(
            spec,
            existing_patterns=existing,
            negative_corpus=[],
            known_capabilities={"cap"},
        )
        self.assertFalse(res["ok"])
        self.assertTrue(any("collision avec smoke_lan_quick" in e for e in res["errors"]))

    def test_validate_bad_action_name_or_exists(self) -> None:
        spec = f.IntentSpec(
            action="Bad-Name!",
            label="Bad",
            keywords=[r"test"],
            target_capability="cap",
            examples_pos=["test"],
        )
        res = f.validate_intent_spec(
            spec,
            existing_patterns={},
            negative_corpus=[],
            known_capabilities={"cap"},
        )
        self.assertFalse(res["ok"])
        self.assertTrue(any("action invalide" in e for e in res["errors"]))

    def test_validate_unmatched_positive_example(self) -> None:
        spec = f.IntentSpec(
            action="clean_cache",
            label="Clean",
            keywords=[r"vide\s+le\s+cache"],
            target_capability="cap",
            examples_pos=["nettoie tout de suite"],
        )
        res = f.validate_intent_spec(
            spec,
            existing_patterns={},
            negative_corpus=[],
            known_capabilities={"cap"},
        )
        self.assertFalse(res["ok"])
        self.assertTrue(any("exemple positif non reconnu" in e for e in res["errors"]))

    # ==================== Tests Phase 2 ====================

    def test_cluster_intent_misses_threshold(self) -> None:
        misses = [
            {"prompt": "fais un scan lan"},
            {"prompt": "fais un scan lan svp"},
            {"prompt": "fais un scan lan maintenant"},
            {"prompt": "autre question météo"},
        ]
        clusters = f.cluster_intent_misses(misses, min_count=3)
        self.assertEqual(len(clusters), 1)
        self.assertEqual(clusters[0]["count"], 3)
        self.assertEqual(len(clusters[0]["examples"]), 3)

        clusters_4 = f.cluster_intent_misses(misses, min_count=4)
        self.assertEqual(len(clusters_4), 0)

    def test_write_manifest_and_adopt_intent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            staging_p = Path(tmpdir) / "staging"
            learned_p = Path(tmpdir) / "learned_intents.json"

            with patch.dict(
                os.environ,
                {
                    "LBG_INTENT_FORGE_STAGING_DIR": str(staging_p),
                    "LBG_LEARNED_INTENTS_PATH": str(learned_p),
                },
            ):
                spec = f.IntentSpec(
                    action="scan_reseau",
                    label="Scan réseau LAN",
                    keywords=[r"scan\s+r[ée]seau"],
                    target_capability="diagnose_lan",
                    examples_pos=["scan réseau rapide"],
                )
                cluster = {"count": 3, "examples": ["scan réseau rapide"]}
                manifest_file = f.write_intent_manifest(
                    run_id="run_test_123",
                    spec=spec,
                    validation_res={"ok": True, "errors": []},
                    cluster=cluster,
                )
                self.assertTrue(manifest_file.is_file())

                res = f.adopt_intent_from_manifest(manifest_file)
                self.assertTrue(res["ok"])
                self.assertEqual(res["action"], "scan_reseau")
                self.assertTrue(learned_p.is_file())

                data = json.loads(learned_p.read_text(encoding="utf-8"))
                self.assertIn("scan_reseau", data["intents"])
                self.assertEqual(data["intents"]["scan_reseau"]["target_capability"], "diagnose_lan")

    def test_run_intent_forge_cycle(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            staging_p = Path(tmpdir) / "staging"
            learned_p = Path(tmpdir) / "learned_intents.json"

            misses = [
                {"prompt": "vérifie le ping lan"},
                {"prompt": "vérifie le ping lan s'il te plaît"},
                {"prompt": "vérifie le ping lan rapide"},
            ]
            with patch.dict(
                os.environ,
                {
                    "LBG_INTENT_FORGE_STAGING_DIR": str(staging_p),
                    "LBG_LEARNED_INTENTS_PATH": str(learned_p),
                    "LBG_INTENT_FORGE_MIN_OCCURRENCES": "3",
                },
            ):
                res = f.run_intent_forge_cycle(
                    misses=misses,
                    known_capabilities={"ping_host"},
                    spawn_l2=False,
                )
                self.assertTrue(res["ok"])
                self.assertEqual(res["clusters_found"], 1)
                self.assertEqual(len(res["proposals"]), 1)
                prop = res["proposals"][0]
                self.assertTrue(prop["valid"])
                self.assertTrue(Path(prop["manifest_path"]).is_file())

    # ==================== Tests Phase 3 ====================

    def test_match_learned_intent_and_kill_switch(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            learned_p = Path(tmpdir) / "learned_intents.json"
            learned_p.write_text(
                json.dumps(
                    {
                        "intents": {
                            "reboot_router": {
                                "action": "reboot_router",
                                "label": "Redémarrage routeur",
                                "keywords": [r"red[ée]marr(?:e|er)\s+(?:le\s+)?routeur"],
                                "target_capability": "router_tool",
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            with patch.dict(
                os.environ,
                {
                    "LBG_LEARNED_INTENTS_PATH": str(learned_p),
                    "LBG_LEARNED_INTENTS_ENABLED": "1",
                },
            ):
                m = f.match_learned_intent("peux-tu redémarrer le routeur svp ?")
                self.assertIsNotNone(m)
                self.assertEqual(m["action"], "reboot_router")

                # Test kill-switch
                with patch.dict(os.environ, {"LBG_LEARNED_INTENTS_ENABLED": "0"}):
                    m_disabled = f.match_learned_intent("peux-tu redémarrer le routeur svp ?")
                    self.assertIsNone(m_disabled)


if __name__ == "__main__":
    unittest.main()
