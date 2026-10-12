from introspection.deterministic_classifier import DeterministicIntentClassifier


def test_classifier_detects_quest_keywords_task_work() -> None:
    c = DeterministicIntentClassifier()
    for text in (
        "J'ai une tache pour toi",
        "J'ai une tâche pour toi",
        "Du travail pour moi ?",
        "Des travaux à faire ?",
    ):
        intent, conf = c.classify(text)
        assert intent == "quest_request"
        assert 0.0 <= conf <= 1.0


def test_classifier_detects_devops_probe() -> None:
    c = DeterministicIntentClassifier()
    for text in (
        "sonde devops stp",
        "fais un diagnostic infra selfcheck LAN",
        "lance un selfcheck",
    ):
        intent, conf = c.classify(text)
        assert intent == "devops_probe", text
        assert conf >= 0.72


def test_classifier_detects_project_pm_action() -> None:
    c = DeterministicIntentClassifier()
    for text in (
        "point d'avancement du projet",
        "fais un brief pm sur le plan de route",
        "consulte la roadmap et les jalons",
    ):
        intent, conf = c.classify(text)
        assert intent == "project_pm", text
        assert conf >= 0.72


def test_classifier_status_infra_still_wins_without_action() -> None:
    c = DeterministicIntentClassifier()
    intent, _ = c.classify("où en est l'infra et les healthz orchestrateur ?")
    assert intent == "infra_status"


def test_classifier_detects_opengame_prototype() -> None:
    c = DeterministicIntentClassifier()
    intent, conf = c.classify("prépare un prototype jeu avec OpenGame")
    assert intent == "prototype_game"
    assert 0.0 <= conf <= 1.0

