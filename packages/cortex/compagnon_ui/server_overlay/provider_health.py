import time
from collections import defaultdict
from typing import Any


class ProviderHealth:
    """Santé providers — ne réordonne plus par latence (sinon Groq écrase le local)."""

    def __init__(self):
        self.stats = defaultdict(lambda: {
            "success": 0,
            "errors": 0,
            "latency": 1.0  # valeur par défaut
        })

    def record_success(self, provider: str, latency: float):
        self.stats[provider]["success"] += 1
        self.stats[provider]["latency"] = latency

    def record_error(self, provider: str):
        self.stats[provider]["errors"] += 1

    def score(self, provider: str) -> float:
        s = self.stats[provider]["success"]
        e = self.stats[provider]["errors"]
        l = self.stats[provider]["latency"]
        return (s * 2) - (e * 3) + (1 / (l + 0.001))

    def sort_providers(self, models: list):
        """Conserve l'ordre routing.json ; ne dépriorise que les providers en erreur nette."""
        def _key(m: dict) -> tuple:
            p = str(m.get("provider") or "")
            st = self.stats[p]
            # Erreurs > succès → en queue (failover). Sinon ordre configuré (stable sort).
            error_heavy = 1 if st["errors"] > st["success"] else 0
            return (error_heavy,)

        return sorted(models, key=_key)

    def sort_providers_with_monitor(
        self,
        models: list,
        latest_monitor: dict[str, Any] | None,
    ) -> list:
        """
        Ordre configuré (+ dépriorisation erreurs), puis recule les providers ``down``.
        """
        base = self.sort_providers(models)
        if not latest_monitor:
            return base
        down = {
            p
            for p, st in latest_monitor.items()
            if isinstance(st, dict) and st.get("status") == "down"
        }
        # Alias monitor : local → ollama_heavy
        if "ollama_heavy" in down:
            down.add("local")
        if not down:
            return base
        return [m for m in base if m.get("provider") not in down] + [
            m for m in base if m.get("provider") in down
        ]
