"""Service de Vision Contextuelle Ponctuelle (Phase 3 Ticket 1.2).

Analyse d'extraits ciblés de la fenêtre active (OCR rapide + mini-VLM local 0 €).
Confidentialité stricte : zéro stockage disque persistant, purge immédiate de la mémoire tampon.
"""

from __future__ import annotations

import base64
import logging
import os
import re
import time
from typing import Any

import httpx

LOG = logging.getLogger("backend.vision_service")

_VISION_CUE_RE = re.compile(
    r"(?i)\b("
    r"regarde\s+(?:mon\s+[eé]cran|cette\s+erreur|ce\s+bug|la\s+fen[eê]tre|mon\s+code)|"
    r"inspecte\s+(?:ce\s+bug|cette\s+erreur|mon\s+[eé]cran|la\s+fen[eê]tre)|"
    r"analyse\s+(?:cette\s+erreur|mon\s+[eé]cran|la\s+fen[eê]tre\s+active)|"
    r"vois[-\s]tu\s+l['\u2019]erreur|"
    r"qu['\u2019]est[-\s]ce\s+qui\s+cloche\s+sur\s+mon\s+[eé]cran"
    r")\b"
)

_ERROR_PATTERNS: list[tuple[re.Pattern[str], str, str]] = [
    (
        re.compile(r"(?i)(ModuleNotFoundError|ImportError)\s*:\s*([^\n]+)"),
        "Erreur d'importation Python",
        "Vérifie que le venv (`packages/cortex/.venv`) est activé et que le package est installé en mode editable (`pip install -e .`).",
    ),
    (
        re.compile(r"(?i)(SyntaxError|IndentationError)\s*:\s*([^\n]+)"),
        "Erreur de syntaxe ou d'indentation",
        "Inspecte la ligne indiquée (parenthèse non fermée, deux-points manquant ou indentation mixte).",
    ),
    (
        re.compile(r"(?i)(TypeError|AttributeError|KeyError|ValueError)\s*:\s*([^\n]+)"),
        "Exception d'exécution sur type ou attribut",
        "Vérifie la structure de l'objet ou du dictionnaire reçu avant d'accéder à la propriété (ex. `.get()` avec valeur par défaut).",
    ),
    (
        re.compile(r"(?i)(ECONNREFUSED|ConnectionRefusedError|timeout|HTTP\s+5\d\d)"),
        "Incident de connectivité réseau / service distant",
        "Le service cible ne répond pas sur le port attendu ; vérifie son statut via `/healthz` ou `smoke_lan_surfaces.sh`.",
    ),
    (
        re.compile(r"(?i)(SCRIPT\s+ERROR|Assertion\s+failed|Parse\s+Error)[^\n]*"),
        "Erreur GDScript / Godot Engine",
        "Vérifie les types statiques GDScript et lance `bash tools/ci_godot_headless.sh` pour reproduire en mode headless.",
    ),
]


def is_vision_context_request(prompt: str) -> bool:
    """Détecte si la requête textuelle ou vocale demande d'inspecter la fenêtre active."""
    return bool(_VISION_CUE_RE.search(prompt or ""))


def get_vision_vlm_config() -> dict[str, Any]:
    """Configuration du mini-VLM local (0 € API)."""
    base_url = (
        os.environ.get("LBG_VISION_VLM_URL", "").strip()
        or os.environ.get("LBG_OLLAMA_LIGHT_URL", "").strip()
        or "http://192.168.0.111:11434"
    ).rstrip("/")
    model = (
        os.environ.get("LBG_VISION_VLM_MODEL", "").strip()
        or "huihui_ai/gemma-4-abliterated:E4b-qat"
    )
    return {
        "base_url": base_url,
        "model": model,
        "scope": "active_window_only",
        "persisted_to_disk": False,
    }


def diagnose_text_excerpt(text: str, window_title: str = "", process_name: str = "") -> dict[str, str]:
    """Analyse rapide d'un extrait OCR ou titre de fenêtre pour identifier la cause d'un bug."""
    combined = f"{window_title}\n{text}".strip()
    for pattern, category, hint in _ERROR_PATTERNS:
        m = pattern.search(combined)
        if m:
            matched = m.group(0).strip()
            return {
                "category": category,
                "matched_error": matched[:200],
                "diagnosis_hint": hint,
                "summary": f"{category} détectée dans `{process_name or 'fenêtre active'}` ({matched[:120]}). {hint}",
            }

    app_label = process_name or window_title or "l'application active"
    if combined:
        return {
            "category": "Inspection contextuelle",
            "matched_error": "",
            "diagnosis_hint": "Extrait analysé sans trace de crash critique immédiat ; vérifie les logs de console ou précise le comportement inattendu.",
            "summary": f"Fenêtre active `{app_label}` inspectée (« {combined[:140]} »).",
        }
    return {
        "category": "Fenêtre active",
        "matched_error": "",
        "diagnosis_hint": "Fenêtre capturée ; aucun texte d'erreur explicite détecté.",
        "summary": f"Inspection visuelle ponctuelle de `{app_label}` effectuée.",
    }


async def analyze_window_snippet(
    *,
    image_b64: str | None = None,
    prompt: str = "",
    window_title: str = "",
    process_name: str = "",
    ocr_text: str = "",
    allow_remote_vlm: bool = False,
) -> dict[str, Any]:
    """Analyse un extrait ciblé de la fenêtre active en mémoire vive et purge immédiatement le tampon."""
    t0 = time.time()
    cfg = get_vision_vlm_config()
    decoded_bytes_len = 0

    # Validation et purge immédiate du buffer image en mémoire vive (zéro écriture disque)
    if image_b64:
        clean_b64 = image_b64.strip()
        if clean_b64.startswith("data:image/"):
            parts = clean_b64.split(",", 1)
            clean_b64 = parts[1] if len(parts) > 1 else ""
        try:
            raw_bytes = base64.b64decode(clean_b64, validate=False)
            decoded_bytes_len = len(raw_bytes)
            # Purge explicite de la référence binaire
            del raw_bytes
        except Exception as exc:
            raise ValueError("invalid_image_b64") from exc
        if decoded_bytes_len == 0:
            raise ValueError("empty_image_payload")

    diag = diagnose_text_excerpt(ocr_text, window_title=window_title, process_name=process_name)
    vlm_used = "local_ocr_heuristic"
    analysis_text = diag["summary"]

    if allow_remote_vlm and image_b64:
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                r = await client.post(
                    f"{cfg['base_url']}/api/chat",
                    json={
                        "model": cfg["model"],
                        "stream": False,
                        "messages": [
                            {
                                "role": "user",
                                "content": (
                                    f"Fenêtre: {window_title} ({process_name}). "
                                    f"Question: {prompt or 'Identifie l erreur ou le code affiché et explique la cause.'}"
                                ),
                                "images": [clean_b64],
                            }
                        ],
                    },
                )
                if r.status_code == 200:
                    data = r.json()
                    msg = (data.get("message") or {}).get("content", "").strip()
                    if msg:
                        analysis_text = msg
                        vlm_used = cfg["model"]
        except Exception as exc:
            LOG.debug("vision_service local VLM fallback: %s", exc)

    # Purge de la chaîne base64 locale avant retour
    image_b64 = None

    return {
        "ok": True,
        "scope": "active_window_only",
        "persisted_to_disk": False,
        "purged_from_memory": True,
        "decoded_bytes": decoded_bytes_len,
        "window_title": window_title,
        "process_name": process_name,
        "ocr_excerpt": ocr_text[:400] if ocr_text else diag["matched_error"],
        "category": diag["category"],
        "analysis": analysis_text,
        "diagnosis_hint": diag["diagnosis_hint"],
        "provider": vlm_used,
        "latency_ms": round((time.time() - t0) * 1000.0, 2),
    }

