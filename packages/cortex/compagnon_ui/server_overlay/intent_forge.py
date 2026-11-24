"""Intent Forge P1 & P2 — journal des intentions non reconnues, validation déterministe
d'IntentSpec, cycle de clustering/staging (P2) et adoption sécurisée L2 (Pilot & Chat).
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import logging
import os
from pathlib import Path
import re
import time
from typing import Any, Callable
import uuid

logger = logging.getLogger("lbg.intent_forge")

# Limites de sécurité
MAX_PATTERN_LEN = 200
MAX_KEYWORDS = 8
_NESTED_QUANT_RE = re.compile(r"\([^)]*[+*][^)]*\)\s*[+*{]")
_ACTION_RE = re.compile(r"^[a-z][a-z0-9_]{2,48}$")


def misses_path() -> Path:
    """Retourne le chemin du fichier journal des intentions manquées."""
    raw = os.environ.get("LBG_INTENT_MISSES_PATH", "").strip()
    if raw:
        return Path(raw)
    return Path(__file__).resolve().parent / "data" / "intent_misses.jsonl"


def misses_enabled() -> bool:
    """Vérifie si la journalisation des misses est activée."""
    return os.environ.get("LBG_INTENT_MISSES", "1").strip().lower() in ("1", "true", "yes", "on")


def record_intent_miss(prompt: str, *, conversation_id: str = "", path: Path | None = None) -> bool:
    """Enregistre un prompt non reconnu dans le journal des misses.

    Ne lève jamais d'exception. Tronque à 500 caractères.
    """
    if not misses_enabled():
        return False

    cleaned = (prompt or "").strip()
    if not cleaned:
        return False

    target_path = path or misses_path()
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": time.time(),
            "prompt": cleaned[:500],
            "conversation_id": str(conversation_id or ""),
        }
        with open(target_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return True
    except OSError:
        return False


def load_intent_misses(path: Path | None = None, limit: int = 500) -> list[dict[str, Any]]:
    """Lit les dernières `limit` lignes valides du journal des misses."""
    target_path = path or misses_path()
    if not target_path.is_file():
        return []

    results: list[dict[str, Any]] = []
    try:
        with open(target_path, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if not line_str:
                    continue
                try:
                    data = json.loads(line_str)
                    if isinstance(data, dict):
                        results.append(data)
                except json.JSONDecodeError:
                    continue
    except OSError:
        return []

    return results[-limit:] if limit > 0 else results


@dataclass
class IntentSpec:
    action: str
    label: str
    keywords: list[str]
    target_capability: str
    examples_pos: list[str]
    examples_neg: list[str] = field(default_factory=list)
    params_schema: dict[str, Any] = field(default_factory=dict)


def intent_spec_from_dict(data: dict[str, Any]) -> tuple[IntentSpec | None, list[str]]:
    """Valide et convertit un dictionnaire brut en IntentSpec."""
    if not isinstance(data, dict):
        return None, ["Les données doivent être un dictionnaire"]

    errors: list[str] = []
    for field_name in ("action", "label", "target_capability"):
        val = data.get(field_name)
        if not isinstance(val, str) or not val.strip():
            errors.append(f"Champ obligatoire manquant ou invalide: {field_name}")

    keywords = data.get("keywords")
    if not isinstance(keywords, list) or not all(isinstance(k, str) for k in keywords):
        errors.append("Champ 'keywords' doit être une liste de chaînes")

    examples_pos = data.get("examples_pos")
    if not isinstance(examples_pos, list) or not all(isinstance(e, str) for e in examples_pos):
        errors.append("Champ 'examples_pos' doit être une liste de chaînes")

    examples_neg = data.get("examples_neg", [])
    if not isinstance(examples_neg, list) or not all(isinstance(e, str) for e in examples_neg):
        errors.append("Champ 'examples_neg' doit être une liste de chaînes")

    params_schema = data.get("params_schema", {})
    if not isinstance(params_schema, dict):
        errors.append("Champ 'params_schema' doit être un dictionnaire")

    if errors:
        return None, errors

    spec = IntentSpec(
        action=str(data["action"]).strip(),
        label=str(data["label"]).strip(),
        keywords=[str(k).strip() for k in keywords if str(k).strip()],
        target_capability=str(data["target_capability"]).strip(),
        examples_pos=[str(e).strip() for e in examples_pos if str(e).strip()],
        examples_neg=[str(e).strip() for e in examples_neg if str(e).strip()],
        params_schema=params_schema,
    )
    return spec, []


def check_regex_safe(pattern: str) -> str | None:
    """Vérifie qu'une expression régulière est sûre (anti-ReDoS, compilation)."""
    p = (pattern or "").strip()
    if not p:
        return "pattern vide"

    if len(p) > MAX_PATTERN_LEN:
        return f"pattern trop long (> {MAX_PATTERN_LEN})"

    # Détection de quantificateurs imbriqués dangereux (ex: (a+)+)
    if _NESTED_QUANT_RE.search(p):
        return "quantificateur imbriqué (ReDoS)"

    # Interdiction des backreferences coûteuses
    if re.search(r"\\[1-9]", p):
        return "backreference interdite"

    try:
        re.compile(p)
    except re.error as exc:
        return f"regex invalide: {exc}"

    return None


def validate_intent_spec(
    spec: IntentSpec,
    *,
    existing_patterns: dict[str, list[str]],
    negative_corpus: list[str],
    known_capabilities: set[str],
) -> dict[str, Any]:
    """Effectue toutes les validations déterministes sur une IntentSpec."""
    errors: list[str] = []

    # a. Format action
    if not _ACTION_RE.match(spec.action):
        errors.append(f"action invalide: {spec.action!r}")

    # b. Collision nom action
    if spec.action in existing_patterns:
        errors.append(f"action déjà existante: {spec.action}")

    # c. Nombre de keywords
    if not spec.keywords or len(spec.keywords) > MAX_KEYWORDS:
        errors.append(f"nombre de keywords invalide: {len(spec.keywords)} (attendu 1..{MAX_KEYWORDS})")

    # d. Sécurité des keywords
    compiled_keywords: list[re.Pattern] = []
    regex_safe = True
    for kw in spec.keywords:
        err = check_regex_safe(kw)
        if err:
            errors.append(f"keyword {kw!r}: {err}")
            regex_safe = False
        else:
            try:
                compiled_keywords.append(re.compile(kw, re.IGNORECASE))
            except re.error:
                regex_safe = False

    # e. Exemples positifs
    if not spec.examples_pos:
        errors.append("examples_pos vide")

    # f & g. Tests de correspondances (uniquement si regex sûres)
    if regex_safe and compiled_keywords:
        # f. Chaque exemple positif doit matcher au moins un keyword
        for ex in spec.examples_pos:
            matched = any(p.search(ex) for p in compiled_keywords)
            if not matched:
                errors.append(f"exemple positif non reconnu: {ex!r}")

        # g. Aucun texte négatif ne doit matcher
        all_neg = list(spec.examples_neg) + list(negative_corpus)
        for neg in all_neg:
            matched = any(p.search(neg) for p in compiled_keywords)
            if matched:
                errors.append(f"faux positif: {neg!r}")

    # h. Collisions avec les patterns existants
    for act_name, pats in existing_patterns.items():
        for pat in pats:
            try:
                pat_re = re.compile(pat, re.IGNORECASE)
                for ex in spec.examples_pos:
                    if pat_re.search(ex):
                        errors.append(f"collision avec {act_name}")
                        break
            except re.error:
                continue

    # i. Vérification de la capability cible
    if spec.target_capability not in known_capabilities:
        errors.append(f"capability_missing:{spec.target_capability}")

    return {
        "ok": len(errors) == 0,
        "errors": errors,
    }


def default_existing_patterns() -> dict[str, list[str]]:
    """Extrait les patterns des actions canoniques existantes."""
    try:
        import pending_actions

        return {k: list(v.get("keywords") or []) for k, v in pending_actions.CANONICAL_ACTIONS.items()}
    except Exception:
        return {}


DEFAULT_NEGATIVE_CORPUS: tuple[str, ...] = (
    "bonjour",
    "salut, comment ça va ?",
    "merci beaucoup",
    "tu peux m'expliquer ce que tu fais ?",
    "raconte-moi une histoire",
    "qu'est-ce que tu penses du MMO ?",
)


# =====================================================================
# Phase 2 : Clustering, Staging, Tâche L2 & Adoption Overlay
# =====================================================================

DEFAULT_MIN_OCCURRENCES = 3


def min_occurrences_threshold() -> int:
    """Seuil de répétition pour regrouper des misses (défaut arbitré : 3)."""
    try:
        return max(1, int(os.environ.get("LBG_INTENT_FORGE_MIN_OCCURRENCES", str(DEFAULT_MIN_OCCURRENCES))))
    except ValueError:
        return DEFAULT_MIN_OCCURRENCES


def staging_dir() -> Path:
    """Dossier de staging des manifestes Intent Forge."""
    raw = os.environ.get("LBG_INTENT_FORGE_STAGING_DIR", "").strip()
    if raw:
        return Path(raw)
    return Path(__file__).resolve().parent / "staging" / "intent_forge"


def learned_intents_path() -> Path:
    """Chemin du fichier JSON persistant des intentions adoptées."""
    raw = os.environ.get("LBG_LEARNED_INTENTS_PATH", "").strip()
    if raw:
        return Path(raw)
    return Path(__file__).resolve().parent / "data" / "learned_intents.json"


def learned_intents_enabled() -> bool:
    """Kill-switch global pour l'activation des intentions apprises au runtime."""
    return os.environ.get("LBG_LEARNED_INTENTS_ENABLED", "1").strip().lower() in ("1", "true", "yes", "on")


def load_learned_intents() -> dict[str, dict[str, Any]]:
    """Charge les intentions apprises et validées depuis learned_intents.json.

    Respecte le kill-switch LBG_LEARNED_INTENTS_ENABLED=0.
    """
    if not learned_intents_enabled():
        return {}

    target = learned_intents_path()
    if not target.is_file():
        return {}

    try:
        data = json.loads(target.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "intents" in data and isinstance(data["intents"], dict):
            return data["intents"]
    except Exception as exc:
        logger.warning("Erreur lecture learned_intents.json: %s", exc)

    return {}


def match_learned_intent(text: str) -> dict[str, Any] | None:
    """Cherche si un texte utilisateur matche une intention apprise L2.

    Retourne la spec de l'intention matchée ou None.
    Toujours appelé en second plan APRÈS les intentions canoniques codées en dur.
    """
    intents = load_learned_intents()
    if not intents:
        return None

    cleaned = (text or "").strip()
    if not cleaned:
        return None

    for action_key, spec in intents.items():
        keywords = spec.get("keywords") or []
        for kw in keywords:
            try:
                if re.search(kw, cleaned, re.IGNORECASE):
                    return spec
            except re.error:
                continue

    return None


def cluster_intent_misses(
    misses: list[dict[str, Any]],
    *,
    min_count: int | None = None,
) -> list[dict[str, Any]]:
    """Regroupe les prompts similaires (mots significatifs partagés).

    Retourne les clusters ayant au moins `min_count` occurrences.
    """
    threshold = min_count if min_count is not None else min_occurrences_threshold()
    # Mots vides ignorés pour le regroupement
    stopwords = {"un", "une", "le", "la", "les", "des", "du", "de", "ce", "cet", "cette", "svp", "stp", "s'il", "te", "plaît", "maintenant", "vite", "stp"}

    # Liste de clusters : [{"tokens": set(...), "examples": [...]}]
    clusters: list[dict[str, Any]] = []

    for m in misses:
        prompt = str(m.get("prompt") or "").strip()
        if not prompt:
            continue
        cleaned = re.sub(r"[^\w\s]", " ", prompt.lower())
        tokens = {t for t in cleaned.split() if len(t) > 2 and t not in stopwords}
        if not tokens:
            tokens = {t for t in cleaned.split() if len(t) > 1}

        # Chercher un cluster existant avec forte similarité (Jaccard ou intersection >= 2)
        matched_cluster = None
        for c in clusters:
            inter = tokens.intersection(c["tokens"])
            if (len(inter) >= 2) or (len(tokens) == 1 and inter == tokens):
                matched_cluster = c
                break

        if matched_cluster:
            matched_cluster["examples"].append(prompt)
            matched_cluster["tokens"].update(tokens)
        else:
            clusters.append({"tokens": set(tokens), "examples": [prompt]})

    out: list[dict[str, Any]] = []
    for c in clusters:
        items = c["examples"]
        if len(items) >= threshold:
            unique_examples = list(dict.fromkeys(items))
            key = " ".join(sorted(list(c["tokens"])[:4]))
            out.append(
                {
                    "cluster_key": key,
                    "count": len(items),
                    "examples": unique_examples,
                }
            )
    return sorted(out, key=lambda x: x["count"], reverse=True)


def write_intent_manifest(
    *,
    run_id: str,
    spec: IntentSpec,
    validation_res: dict[str, Any],
    cluster: dict[str, Any],
) -> Path:
    """Écrit le manifeste de staging pour revue L2."""
    base = staging_dir() / run_id
    base.mkdir(parents=True, exist_ok=True)
    manifest = {
        "run_id": run_id,
        "created_at": time.time(),
        "spec": {
            "action": spec.action,
            "label": spec.label,
            "keywords": spec.keywords,
            "target_capability": spec.target_capability,
            "examples_pos": spec.examples_pos,
            "examples_neg": spec.examples_neg,
            "params_schema": spec.params_schema,
        },
        "validation": validation_res,
        "cluster": cluster,
        "status": "pending_l2" if validation_res.get("ok") else "rejected_validation",
    }
    manifest_file = base / "manifest.json"
    manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest_file


def maybe_spawn_intent_l2_task(
    *,
    manifest_path: str,
    action: str,
    label: str,
    count: int,
) -> str | None:
    """Crée une tâche L2 d'adoption dans Pilot via team_store."""
    try:
        from team import store as team_store  # type: ignore

        objective = f"Revue L2 — Adoption d'intention `{action}` ({label}) vue {count} fois. Manifeste: {manifest_path}"
        task = team_store.create_task(
            role="pm",
            objective=objective,
            actor_id="system:intent_forge",
            priority="normal",
            approval_required=True,
            context={
                "intent_adoption_review": True,
                "workflow": "intent_adoption_review",
                "manifest_path": str(manifest_path),
                "action": action,
            },
        )
        return task.id
    except Exception as exc:
        logger.warning("Échec création tâche L2 Pilot: %s", exc)
        return None


def create_intent_pending_action(
    *,
    spec: IntentSpec,
    manifest_path: str,
    conversation_id: str = "default",
) -> Any:
    """Crée une PendingAction pour confirmation en chat ('oui / go')."""
    try:
        import pending_actions  # type: ignore

        act_id = f"act_adopt_intent_{spec.action}_{int(time.time())}"
        summary = (
            f"Adopter l'intention `{spec.action}` ({spec.label}) ciblant la capacité `{spec.target_capability}`. "
            f"Déclencheurs : {', '.join(spec.keywords[:3])}"
        )
        action = pending_actions.PendingAction(
            action_id=act_id,
            conversation_id=conversation_id,
            action_type="intent_adoption",
            label=f"Adoption de l'intention : {spec.label}",
            summary=summary,
            command=["adopt_intent", str(manifest_path)],
            context={
                "action_key": "adopt_intent",
                "manifest_path": str(manifest_path),
                "action": spec.action,
            },
            button_text="Adopter l'intention",
            cancel_text="Ignorer",
        )
        pending_actions.store_pending_action(conversation_id, action)
        return action
    except Exception as exc:
        logger.warning("Échec création PendingAction chat: %s", exc)
        return None


def adopt_intent_from_manifest(manifest_path: Path | str) -> dict[str, Any]:
    """Applique l'adoption L2 d'une intention : écrit dans learned_intents.json."""
    m_path = Path(manifest_path)
    if not m_path.is_file():
        return {"ok": False, "error": f"Manifeste introuvable: {m_path}"}

    try:
        manifest = json.loads(m_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"ok": False, "error": f"Erreur lecture manifeste: {exc}"}

    spec_dict = manifest.get("spec")
    spec, errors = intent_spec_from_dict(spec_dict)
    if not spec:
        return {"ok": False, "error": f"Spec invalide: {errors}"}

    target_file = learned_intents_path()
    target_file.parent.mkdir(parents=True, exist_ok=True)

    current_data: dict[str, Any] = {"intents": {}}
    if target_file.is_file():
        try:
            loaded = json.loads(target_file.read_text(encoding="utf-8"))
            if isinstance(loaded, dict) and "intents" in loaded:
                current_data = loaded
        except Exception:
            current_data = {"intents": {}}

    intents = current_data.setdefault("intents", {})
    intents[spec.action] = {
        "action": spec.action,
        "label": spec.label,
        "keywords": spec.keywords,
        "target_capability": spec.target_capability,
        "examples_pos": spec.examples_pos,
        "examples_neg": spec.examples_neg,
        "params_schema": spec.params_schema,
        "adopted_at": time.time(),
        "run_id": manifest.get("run_id"),
    }

    tmp_file = target_file.with_suffix(target_file.suffix + ".tmp")
    tmp_file.write_text(json.dumps(current_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp_file.replace(target_file)

    manifest["status"] = "adopted_l2"
    manifest["adopted_at"] = time.time()
    m_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {
        "ok": True,
        "action": spec.action,
        "learned_intents_path": str(target_file),
    }


def run_intent_forge_cycle(
    *,
    misses: list[dict[str, Any]] | None = None,
    propose_fn: Callable[[dict[str, Any]], dict[str, Any] | None] | None = None,
    known_capabilities: set[str] | None = None,
    conversation_id: str = "default",
    spawn_l2: bool = True,
) -> dict[str, Any]:
    """Cycle complet de l'Intent Forge (nocturne ou déclenché)."""
    raw_misses = misses if misses is not None else load_intent_misses(limit=1000)
    clusters = cluster_intent_misses(raw_misses)
    if not clusters:
        return {"ok": True, "clusters_found": 0, "proposals": []}

    caps = known_capabilities if known_capabilities is not None else {"audit_tool", "diagnose_lan", "ping_host"}
    existing = default_existing_patterns()
    proposals: list[dict[str, Any]] = []

    for cluster in clusters:
        # Génération de la proposition d'intention (via propose_fn ou fallback heuristique)
        proposed_dict = None
        if propose_fn:
            try:
                proposed_dict = propose_fn(cluster)
            except Exception as e:
                logger.warning("Échec propose_fn: %s", e)

        if not proposed_dict:
            # Fallback heuristique standard si LLM indisponible
            main_example = cluster["examples"][0]
            # Mots bruts (conservant les accents pour la regex)
            raw_words = [w for w in re.sub(r"[^\w\s]", "", main_example.lower()).split() if len(w) > 2]
            # Normalisation ASCII sans accents strictement pour le nom d'action technique
            ascii_example = (
                main_example.lower()
                .replace("é", "e")
                .replace("è", "e")
                .replace("ê", "e")
                .replace("à", "a")
                .replace("ù", "u")
                .replace("ç", "c")
            )
            ascii_words = [w for w in re.sub(r"[^a-z0-9\s]", "", ascii_example).split() if len(w) > 2]
            action_name = f"learned_{'_'.join(ascii_words[:2])}" if ascii_words else f"learned_{int(time.time())}"

            # Regex basée sur les mots réels avec accents
            kw = rf"{re.escape(raw_words[0])}.*{re.escape(raw_words[1])}" if len(raw_words) >= 2 else r"action\s+inconnue"
            proposed_dict = {
                "action": action_name[:40],
                "label": f"Action apprise : {main_example[:30]}",
                "keywords": [kw],
                "target_capability": list(caps)[0] if caps else "default_cap",
                "examples_pos": cluster["examples"][:3],
                "examples_neg": [],
            }

        spec, errs = intent_spec_from_dict(proposed_dict)
        if not spec:
            continue

        val_res = validate_intent_spec(
            spec,
            existing_patterns=existing,
            negative_corpus=list(DEFAULT_NEGATIVE_CORPUS),
            known_capabilities=caps,
        )

        run_id = f"intent_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        manifest_p = write_intent_manifest(
            run_id=run_id,
            spec=spec,
            validation_res=val_res,
            cluster=cluster,
        )

        l2_task_id = None
        pending_action_id = None
        if val_res.get("ok") and spawn_l2:
            l2_task_id = maybe_spawn_intent_l2_task(
                manifest_path=str(manifest_p),
                action=spec.action,
                label=spec.label,
                count=cluster["count"],
            )
            pa = create_intent_pending_action(
                spec=spec,
                manifest_path=str(manifest_p),
                conversation_id=conversation_id,
            )
            if pa:
                pending_action_id = getattr(pa, "action_id", None)

        proposals.append(
            {
                "action": spec.action,
                "label": spec.label,
                "valid": val_res.get("ok"),
                "validation_errors": val_res.get("errors", []),
                "manifest_path": str(manifest_p),
                "l2_task_id": l2_task_id,
                "pending_action_id": pending_action_id,
            }
        )

    return {
        "ok": True,
        "clusters_found": len(clusters),
        "proposals": proposals,
    }
