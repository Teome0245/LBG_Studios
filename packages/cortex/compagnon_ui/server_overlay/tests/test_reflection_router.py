"""Tests — reflection_router heuristiques (sans Orch runtime)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

_OVERLAY = Path(__file__).resolve().parents[1]
if str(_OVERLAY) not in sys.path:
    sys.path.insert(0, str(_OVERLAY))

# Stubs imports Orch absents en test local
for mod in (
    "httpx",
    "src",
    "src.http_timeouts",
    "src.services",
    "src.services.lan_llm_grounding",
    "src.services.multi_block_dispatch",
    "src.services.team_routing",
    "src.services.desktop_dispatch",
    "src.services.cursor_agent_client",
    "src.services.team_proxy",
    "src.services.tool_loop",
    "src.services.cockpit_overview",
    "src.services.team_autonomy_plan",
    "src.services.campus_recall",
    "src.settings",
):
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()

sys.modules["src.services.lan_llm_grounding"].wants_factual_lan_answer = lambda _p: False
sys.modules["src.services.lan_llm_grounding"].wants_lan_llm_context = lambda _p: False
sys.modules["src.services.multi_block_dispatch"].is_numbered_multi_block = lambda _p: False
sys.modules["src.services.team_routing"].strip_team_prefix = lambda p: (p, False)
sys.modules["src.services.desktop_dispatch"].wants_desktop_open = lambda _p: False
sys.modules["src.services.cursor_agent_client"].strip_cursor_prefix = lambda p: (p, False)
sys.modules["src.services.team_proxy"].wants_infra_lan_brief = lambda _p: False
sys.modules["src.services.tool_loop"].tool_loop_enabled = lambda: True
sys.modules["src.services.tool_loop"].wants_tool_loop = lambda _p: False
sys.modules["src.services.cockpit_overview"].wants_cockpit_overview = lambda _p: False
sys.modules["src.services.team_autonomy_plan"].wants_team_autonomy_plan = lambda _p: False
sys.modules["src.http_timeouts"].httpx_timeout = lambda **_k: None

import reflection_router as rr  # noqa: E402


class ReflectionHeuristicTests(unittest.TestCase):
    def test_exploratory_answer(self) -> None:
        d = rr._heuristic(
            "pour le moment je voudrai Chatter, échanger, confondre pour voir jusqu'ou on peut aller"
        )
        self.assertIsNotNone(d)
        assert d is not None
        self.assertEqual(d.action, "answer")

    def test_physical_presence_heuristic(self) -> None:
        d = rr._heuristic("suis-je au bureau ?")
        self.assertIsNotNone(d)
        assert d is not None
        self.assertEqual(d.action, "answer")
        self.assertIn("présence physique", d.reason)

    def test_auto_audit_tools(self) -> None:
        d = rr._heuristic("tu pourrais faire un auto audit ?")
        self.assertIsNotNone(d)
        assert d is not None
        self.assertEqual(d.action, "tools")

    def test_studio_audit_team(self) -> None:
        d = rr._heuristic("un audit Team, studio pour avoir la base et l'état actuel")
        self.assertIsNotNone(d)
        assert d is not None
        self.assertEqual(d.action, "team")

    def test_ollama_audit(self) -> None:
        d = rr._heuristic("fais un audit Ollama .110 et .111")
        self.assertIsNotNone(d)
        assert d is not None
        self.assertEqual(d.action, "audit")

    def test_campus_concept_answer(self) -> None:
        d = rr._heuristic("pour toi, qu'est ce que le campus lbg")
        self.assertIsNotNone(d)
        assert d is not None
        self.assertEqual(d.action, "answer")

    def test_campus_ops_team(self) -> None:
        d = rr._heuristic("status campus")
        self.assertIsNotNone(d)
        assert d is not None
        self.assertEqual(d.action, "team")

    def test_design_brainstorm_answer_not_tools(self) -> None:
        """1.1 — rejeu T5 zone d'entraînement → answer, pas tools/tool_loop."""
        t5 = (
            "pour moi l'environnement jeu doit rester une zone d'entraînement "
            "des personas, pas un dump ops"
        )
        d = rr._heuristic(t5)
        self.assertIsNotNone(d)
        assert d is not None
        self.assertEqual(d.action, "answer")
    def test_avatar_dances_answer_not_team(self) -> None:
        p = "tu peux regarder pour intégré plus de danse différentes pour l'avatar ? fait travailler la team sur le sujet."
        d = rr._heuristic(p)
        self.assertIsNotNone(d)
        assert d is not None
        self.assertEqual(d.action, "answer")
        self.assertNotEqual(d.action, "team")

    def test_conversational_check_answer_not_tools(self) -> None:
        p = "et donc tu peux vérifier ?"
        d = rr._heuristic(p)
        self.assertIsNotNone(d)
        assert d is not None
        self.assertEqual(d.action, "answer")
        self.assertNotEqual(d.action, "tools")

    def test_ui_empty_bubble_answer(self) -> None:
        p = "j'ai une bulle vide dans l'interface, elle ne se remplis qu'apres que j'ai écrit une nouvelle question ..."
        d = rr._heuristic(p)
        self.assertIsNotNone(d)
        assert d is not None
        self.assertEqual(d.action, "answer")

    def test_network_analysis_real_servers_answer_not_tools(self) -> None:
        p = "ce n'est pas qu'il sont eteind, c'est qu'il n'on jamais existés. fais une analyse réseaux si besoin, pour avoir le vrais nom des serveurs."
        d = rr._heuristic(p)
        self.assertIsNotNone(d)
        assert d is not None
        self.assertEqual(d.action, "answer")
        self.assertNotEqual(d.action, "tools")

    def test_rebuttal_fake_servers_answer(self) -> None:
        p = "toujours pas de serveurs L1 et L2, mais fait le nécessaire pour ne pas \"divaguer\"."
        d = rr._heuristic(p)
        self.assertIsNotNone(d)
        assert d is not None
        self.assertEqual(d.action, "answer")
        self.assertNotEqual(d.action, "tools")

    def test_servers_dont_exist_rebuttal(self) -> None:
        p = "Serveur L1 et L2 n'existe pas et le model '.140' non plus, .140 est l'abréviation pour l'un des serveur serveur, et non un model, tu invente et divague."
        d = rr._heuristic(p)
        self.assertIsNotNone(d)
        assert d is not None
        self.assertEqual(d.action, "answer")

    def test_confirmation_cest_bien_ca_answer(self) -> None:
        phrases = (
            "c'est bien ça.",
            "c'est ça",
            "exactement",
            "tout à fait",
            "voilà",
            "ok faity",
            "vas-y",
            "oui c'est ça.",
            "oui je veux bien.",
            "oui je veux bien",
            "je veux bien",
            "oui",
            "oui vas-y",
            "oui stp",
            "volontiers",
            "avec plaisir",
            "carrément",
            "pourquoi pas",
            "d'accord",
            "ok ça marche",
            "fais ça",
        )
        for phrase in phrases:
            d = rr._heuristic(phrase)
            self.assertIsNotNone(d, f"failed on {phrase}")
            assert d is not None
            self.assertEqual(d.action, "answer", f"action not answer on {phrase}")

    def test_ask_user_downgrade_on_affirmation(self) -> None:
        d = rr._parse_llm_json('{"action":"ask_user","reason":"trop vague","clarify":"De quoi s\'agit-il ?"}', prompt="oui je veux bien.")
        self.assertIsNotNone(d)
        assert d is not None
        self.assertEqual(d.action, "answer")
        self.assertIn("downgrade", d.reason)

    def test_heuristic_short_ctx_assistant_proposal(self) -> None:
        short_ctx = [
            {"role": "user", "content": "tu peux regarder comment se comporte nos pnj ?"},
            {"role": "assistant", "content": "On pourrait lancer une requête pour voir la distribution des états ?"},
        ]
        d = rr._heuristic("oui je veux bien.", short_ctx=short_ctx)
        self.assertIsNotNone(d)
        assert d is not None
        self.assertEqual(d.action, "answer")

    def test_tools_downgrade_without_diag_keywords(self) -> None:
        d = rr._parse_llm_json('{"action":"tools","reason":"confused"}', prompt="c'est bien ça.")
        self.assertIsNotNone(d)
        assert d is not None
        self.assertEqual(d.action, "answer")
        self.assertIn("downgrade", d.reason)

    def test_contextual_followup_no_tools_on_confirmation(self) -> None:
        mem = {"last_action": '{"source":"tool_loop","action":"tools"}'}
        d = rr._contextual_followup("c'est bien ça.", mem)
        self.assertIsNone(d)

    def test_semantic_action_normalization(self) -> None:
        # Les SLM compacts (ex: lfm3) émettent parfois des verbes d'action
        d_q = rr._parse_llm_json('{"action":"question","reason":"avatar","clarify":null}')
        self.assertIsNotNone(d_q)
        assert d_q is not None
        self.assertEqual(d_q.action, "answer")

        d_d = rr._parse_llm_json('{"action":"deploy","reason":"mise à jour","clarify":null}')
        self.assertIsNotNone(d_d)
        assert d_d is not None
        self.assertEqual(d_d.action, "team")


if __name__ == "__main__":
    unittest.main()

