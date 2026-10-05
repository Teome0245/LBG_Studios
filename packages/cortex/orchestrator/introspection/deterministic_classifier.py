import re

from introspection.status_intent import classify_status_intent, is_operational_status_query


class DeterministicIntentClassifier:
    """
    Classifieur déterministe (baseline) destiné à être remplacé/augmenté par des modèles.
    """

    # Action DevOps explicite — avant infra_status (sinon « devops/selfcheck » tombe en statut factuel).
    _DEVOPS_ACTION_RE = re.compile(
        r"\b("
        r"sonde\s+devops|probe\s+devops|devops\s+probe|"
        r"selfcheck|diagnostic\s+infra\s+selfcheck|"
        r"healthz\s+(backend|orchestrator)|"
        r"fais\s+(une\s+)?sonde(\s+devops)?|"
        r"lance\s+(un\s+)?selfcheck"
        r")\b",
        re.IGNORECASE,
    )

    def classify(self, text: str) -> tuple[str, float]:
        t = text.strip().lower()
        if not t:
            return ("unknown", 0.0)

        if self._DEVOPS_ACTION_RE.search(t):
            return ("devops_probe", 0.78)

        status_intent, status_conf = classify_status_intent(text)
        if status_intent != "unknown":
            return (status_intent, status_conf)

        if re.search(
            r"\b(chef de projet|product owner|état d'avancement|statut du projet|point d'avancement|"
            r"plan de route|roadmap|vision produit)\b",
            t,
        ):
            return ("project_pm", 0.78)
        if re.search(
            r"\b(jalon|milestone)\b.*\b(projet|produit|mmo|release)\b|"
            r"\b(projet|produit|mmo)\b.*\b(jalon|milestone)\b",
            t,
        ):
            return ("project_pm", 0.74)
        if re.search(r"\b(opengame|prototype\s+jeu|prototype\s+game|mini-jeu|mini\s+jeu)\b", t):
            return ("prototype_game", 0.7)
        if re.search(r"\b(quest|quête|mission|tâche|tache|travail|travaux)\b", t):
            if not is_operational_status_query(text):
                return ("quest_request", 0.75)
        if re.search(r"\b(parler|dialogue|discuter)\b", t):
            return ("npc_dialogue", 0.7)
        if re.search(r"\b(combat|attaquer|taper)\b", t):
            return ("combat_action", 0.7)
        if re.search(r"\bdevops\b", t):
            return ("devops_probe", 0.72)
        return ("unknown", 0.4)
