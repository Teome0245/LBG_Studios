"""Tests unitaires pour pending_actions (cocréation Antigravity / Gladys)."""

from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path

_OVERLAY = Path(__file__).resolve().parents[1]
if str(_OVERLAY) not in sys.path:
    sys.path.insert(0, str(_OVERLAY))

import pending_actions as pa


class PendingActionsTests(unittest.IsolatedAsyncioTestCase):
    def test_is_confirmation_affirmative(self) -> None:
        positives = [
            "oui",
            "OUI",
            "oui s'il te plaît",
            "oui vas-y",
            "ok",
            "OK",
            "ok vas-y",
            "go",
            "GO",
            "vas-y",
            "vas y",
            "fais-le",
            "fais le",
            "lance",
            "exécute",
            "execute",
            "déclenche",
            "declenche",
            "je confirme",
            "confirme",
            "d'accord",
            "d accord",
            "roule",
            "affirmatif",
        ]
        for p in positives:
            with self.subTest(prompt=p):
                self.assertTrue(pa.is_confirmation_affirmative(p), f"Devrait être reconnu comme affirmatif: {p}")

        negatives = [
            "non",
            "pas du tout",
            "comment ça va ?",
            "fais un diagnostic complet",
            "pourquoi ?",
            "oui mais attends",
        ]
        for n in negatives:
            with self.subTest(prompt=n):
                self.assertFalse(pa.is_confirmation_affirmative(n), f"Ne devrait PAS être reconnu comme affirmatif simple: {n}")

    def test_is_confirmation_negative(self) -> None:
        negatives = ["non", "NON", "nan", "annule", "annuler", "stop", "laisse tomber", "pas maintenant"]
        for n in negatives:
            with self.subTest(prompt=n):
                self.assertTrue(pa.is_confirmation_negative(n), f"Devrait être reconnu comme négatif: {n}")

    def test_extract_pending_action_dns(self) -> None:
        assistant_text = (
            "On peut déployer un serveur DNS AdGuard Home via le script officiel :\n"
            "`packages/cortex/infra/scripts/create_lbg_dns_ct_proxmox.sh`.\n\n"
            "Cela provisionnera un conteneur LXC Ubuntu 24.01 (CT 153) sur l'hyperviseur .201 "
            "avec l'IP statique 192.168.0.53. Veux-tu que je déclenche cette mise en service ?"
        )
        action = pa.extract_pending_action_from_assistant_message(assistant_text, "conv_123")
        self.assertIsNotNone(action)
        self.assertEqual(action.conversation_id, "conv_123")
        self.assertIn("AdGuard", action.label)
        self.assertEqual(action.context.get("action_key"), "dns_adguard_deploy")

    def test_extract_pending_action_no_question(self) -> None:
        # Sans point d'interrogation ni formule interrogative, pas d'action en attente
        text = "Voici les informations sur le serveur DNS AdGuard."
        action = pa.extract_pending_action_from_assistant_message(text, "conv_123")
        self.assertIsNone(action)

    def test_store_and_get_pending_action(self) -> None:
        action = pa.PendingAction(
            action_id="act_test_1",
            conversation_id="conv_abc",
            action_type="script",
            label="Action de test",
            summary="Test résumé",
            command=["echo", "test"],
        )
        pa.store_pending_action("conv_abc", action)
        retrieved = pa.get_pending_action("conv_abc")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.action_id, "act_test_1")

        pa.clear_pending_action("conv_abc")
        self.assertIsNone(pa.get_pending_action("conv_abc"))

    def test_pending_action_expired(self) -> None:
        action = pa.PendingAction(
            action_id="act_expired",
            conversation_id="conv_exp",
            action_type="script",
            label="Action expirée",
            summary="Test",
            command=["echo", "test"],
            created_at=100.0,
        )
        pa.store_pending_action("conv_exp", action)
        # 1000s plus tard
        self.assertTrue(action.is_expired(now=1500.0))
        # get_pending_action doit purger et renvoyer None
        retrieved = pa.get_pending_action("conv_exp")
        # En temps réel actuel time.time() > 100 + 900
        self.assertIsNone(retrieved)

    async def test_execute_pending_action_success(self) -> None:
        action = pa.PendingAction(
            action_id="act_echo",
            conversation_id="conv_echo",
            action_type="script",
            label="Commande Echo Test",
            summary="Affiche un message",
            command=["echo", "http://192.168.0.53:3000/ - Service DNS en ligne"],
        )
        res = await pa.execute_pending_action(action)
        self.assertTrue(res.get("ok"))
        self.assertIn("exécuté avec succès", res.get("content", ""))
        self.assertIn("192.168.0.53:3000", res.get("content", ""))
        self.assertEqual(len(res.get("timeline", [])), 2)


if __name__ == "__main__":
    unittest.main()
