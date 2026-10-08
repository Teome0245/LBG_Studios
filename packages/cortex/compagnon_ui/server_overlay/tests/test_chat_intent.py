"""Tests — chat_intent (identité / causerie / audit)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_OVERLAY = Path(__file__).resolve().parents[1]
if str(_OVERLAY) not in sys.path:
    sys.path.insert(0, str(_OVERLAY))

import chat_intent as ci  # noqa: E402


class ChatIntentTests(unittest.TestCase):
    def test_identity_true(self) -> None:
        for p in (
            "Bonjour, tu peux me dire quoi sur toi.",
            "dis moi quelque chose d interessant sur toi",
            "qui es-tu ?",
            "parle-moi de toi",
            "présente-toi",
            "raconte-moi quelque chose d'intéressant",
        ):
            self.assertTrue(ci.is_companion_chat(p), p)

    def test_exploratory_true(self) -> None:
        for p in (
            "pour le moment je voudrai Chatter, échanger, confondre",
            "discutons maturité et MMORPG",
            "on peut brainstormer l'écosystème LBG",
            "discutons comme entre collègues ou amis au sujet du projet",
            "ce qui me frustre c'est le manque de fluidité",
        ):
            self.assertTrue(ci.is_companion_chat(p), p)
            self.assertTrue(ci.wants_exploratory_chat(p), p)

    def test_greeting_causerie(self) -> None:
        for p in (
            "Bonjour, comment ça va aujourd'hui ?",
            "salut",
            "bien merci, et toi ?",
            "ça va ?",
        ):
            self.assertTrue(ci.is_greeting_chat(p), p)
            self.assertTrue(ci.is_companion_chat(p), p)
            self.assertTrue(ci.wants_sticky_causerie(p), p)

    def test_colleague_open_a2(self) -> None:
        import router_prompts as rp  # noqa: E402

        for p in (
            "Discutons comme collègues du projet",
            "discutons comme entre collègues",
            "on peut discuter comme collègues du projet ?",
        ):
            self.assertTrue(ci.is_colleague_open(p), p)
            reply = rp.colleague_open_reply(p)
            self.assertIsNotNone(reply, p)
            self.assertRegex(reply or "", r"(?i)avis")
            self.assertNotRegex(
                reply or "",
                r"(?i)pr[ée]occupe|t['\u2019]?am[èe]ne|quel point",
            )
        # Avec sujet / frustration → laisser le LLM (V6), pas le fixed
        self.assertFalse(
            ci.is_colleague_open(
                "Discutons comme collègues du projet — qu'est-ce qui te frustre le plus sur O1 ?"
            )
        )
        self.assertIsNone(
            rp.colleague_open_reply(
                "Discutons comme collègues — qu'est-ce qui te frustre sur O1 ?"
            )
        )

    def test_plan_delivery_intent(self) -> None:
        self.assertTrue(
            ci.wants_plan_delivery(
                "tu pourrais préparer le plan d'action pour le soumettre au studio, "
                "et commencer à travailler dessus ?"
            )
        )
        self.assertTrue(ci.is_go_ahead("allons y"))
        self.assertTrue(ci.is_go_ahead("Allons-y."))
        ctx = [
            {
                "role": "user",
                "content": "prépare le plan d'action pour le studio et commence",
            },
            {"role": "assistant", "content": "Je peux structurer…"},
        ]
        self.assertTrue(ci.has_pending_work(ctx))
        self.assertTrue(ci.wants_deliverable_turn("allons y", ctx))
        self.assertFalse(ci.wants_deliverable_turn("allons y", None))

    def test_ops_false(self) -> None:
        for p in (
            "team: status campus",
            "dis moi le status pilot",
            "qui es-tu et status team",
            "smoke lan",
            "tu pourrais faire un auto audit ?",
        ):
            self.assertFalse(ci.is_companion_chat(p), p)

    def test_causerie_lab_nudge(self) -> None:
        import router_prompts as rp  # noqa: E402

        nudge = rp.causerie_lab_nudge(
            "discutons comme entre collègues du projet", lab=True
        )
        # A2 : invite collègue → nudge C2 (avis), sinon « avance le fil »
        self.assertTrue(
            "collègue c2" in nudge.lower() or "avance le fil" in nudge.lower(),
            nudge,
        )
        self.assertIn("avis", nudge.lower())
        self.assertEqual(rp.causerie_lab_nudge("discutons", lab=False), "")
        self.assertEqual(rp.causerie_lab_nudge("smoke lan", lab=True), "")
        # Fil sticky avec sujet → nudge générique avance le fil
        sticky_nudge = rp.causerie_lab_nudge(
            "tu inventes ou tu as investigué ?",
            lab=True,
            short_ctx=[
                {"role": "user", "content": "discutons comme collègues du projet LBG"},
                {"role": "assistant", "content": "Mon avis : …"},
            ],
        )
        self.assertIn("avance le fil", sticky_nudge.lower())
        # Sticky : follow-up sans mot-clé, mais fil causerie
        ctx = [
            {"role": "user", "content": "discutons comme collègues du projet LBG"},
            {"role": "assistant", "content": "Mon avis : …"},
        ]
        self.assertTrue(
            rp.wants_lab_causerie_prompt("tu inventes ou tu as investigué ?", short_ctx=ctx)
        )
        self.assertTrue(
            rp.wants_lab_causerie_prompt(
                "tu te sens prêt pour m'aider à faire évoluer tout ça ?", short_ctx=ctx
            )
        )
        self.assertFalse(
            rp.wants_lab_causerie_prompt("team: status campus", short_ctx=ctx)
        )
        causerie = rp.resolve_lab_system_prompt(
            "discutons comme entre collègues du projet"
        )
        self.assertIn("avis", causerie.lower())
        self.assertIn("hypoth", causerie.lower())
        self.assertEqual(rp.lab_short_ctx_cap(), 6)

    def test_d65_short_social_and_plan_nudge(self) -> None:
        import router_prompts as rp  # noqa: E402

        # A1 — greeting chaud, pas ops
        greet = rp.short_social_reply("Bonjour, comment ça va aujourd'hui ?")
        self.assertIsNotNone(greet)
        self.assertNotRegex(greet or "", r"(?i)agir|dry-run|\.143|deploy")
        self.assertIn("écoute", (greet or "").lower())

        # A3 — allons-y après demande de plan → pas de short_social
        work_ctx = [
            {
                "role": "user",
                "content": "prépare le plan d'action pour le soumettre au studio",
            },
            {"role": "assistant", "content": "Je peux structurer…"},
        ]
        self.assertIsNone(rp.short_social_reply("allons y", short_ctx=work_ctx))
        # Sans contexte : short_social OK
        alone = rp.short_social_reply("allons y", short_ctx=None)
        self.assertEqual(alone, "Allons-y. Je te suis.")

        # A4 — nudge livrable
        pn = rp.plan_delivery_nudge(
            "tu pourrais préparer le plan d'action pour le soumettre au studio",
            lab=True,
        )
        self.assertIn("livrable", pn.lower())
        self.assertIn("markdown", pn.lower())
        self.assertEqual(
            rp.plan_delivery_nudge("allons y", lab=True, short_ctx=work_ctx).lower().count(
                "livrable"
            ),
            1,
        )
        self.assertEqual(rp.plan_delivery_nudge("allons y", lab=True, short_ctx=None), "")
        self.assertEqual(rp.plan_delivery_nudge("prépare un plan", lab=False), "")

    def test_openclaw_not_on_causerie_evoluer(self) -> None:
        import openclaw_markers as oc  # noqa: E402

        self.assertFalse(
            oc.prompt_has_openclaw_substrings(
                "tu te sens prêt pour m'aider à faire évoluer tout ça ?"
            )
        )
        self.assertFalse(
            oc.prompt_has_openclaw_substrings("que pense tu du rôle de Lyra ?")
        )
        self.assertTrue(oc.prompt_has_openclaw_substrings("lance openclaw repair"))
        self.assertTrue(oc.prompt_has_openclaw_substrings("auto-évolution du module"))

    def test_team_routing_campus_concept(self) -> None:
        import team_routing as tr  # noqa: E402

        self.assertFalse(
            tr.should_route_to_team(
                prompt="pour toi, qu'est ce que le campus lbg",
                intent_v2={"intent": "conversation", "confidence": 0.9},
                enabled=True,
            )
        )
        self.assertTrue(
            tr.should_route_to_team(
                prompt="status campus",
                intent_v2={"intent": "devops_request", "confidence": 0.9},
                enabled=True,
            )
        )


    def test_studio_audit(self) -> None:
        self.assertTrue(ci.wants_studio_team_audit("audit Team, studio pour l'état actuel"))
        self.assertTrue(ci.wants_broad_audit("tu pourrais faire un auto audit ?"))
        self.assertFalse(ci.wants_ollama_only_audit("audit Team studio"))
        self.assertTrue(ci.wants_ollama_only_audit("audit Ollama .110 .111"))


if __name__ == "__main__":
    unittest.main()
