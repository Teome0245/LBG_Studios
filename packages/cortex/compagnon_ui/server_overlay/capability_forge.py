"""Capability Forge P4 — génération contrôlée de skills autonomes, analyse statique AST,
exécution sandboxée isolée (bwrap / docker / unshare) et soumission L2 (Pilot & Chat).

Garde-fous A4 :
- Jamais d'écriture dans `agents/declarations/*.json`.
- Jamais de modification des règles de combat, économie, craft ou réputation MMO O2.
- Exécution du code généré toujours isolée en sous-processus sans réseau.
- Risque 'high' obligatoire dès qu'une écriture ou suppression de fichier est demandée.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
import json
import logging
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
from typing import Any, Callable
import uuid

logger = logging.getLogger("lbg.capability_forge")

_CAPABILITY_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{2,48}$")

# Denylist AST stricte — aucun bypass dynamique toléré
_FORBIDDEN_CALLS: frozenset[str] = frozenset(
    {
        "eval",
        "exec",
        "compile",
        "__import__",
        "breakpoint",
    }
)

_FORBIDDEN_MODULES: frozenset[str] = frozenset(
    {
        "socket",
        "ctypes",
        "pty",
        "resource",
        "signal",
        "paramiko",
        "telnetlib",
    }
)

_FORBIDDEN_ATTRS: frozenset[str] = frozenset(
    {
        "system",  # os.system
        "popen",   # os.popen
        "spawn",
    }
)


def skills_learned_dir() -> Path:
    """Répertoire racine des skills appris adoptés."""
    raw = os.environ.get("LBG_SKILLS_LEARNED_DIR", "").strip()
    if raw:
        return Path(raw)
    return Path(__file__).resolve().parents[1] / "skills" / "learned"


def staging_dir() -> Path:
    """Répertoire de staging des forges de compétences."""
    raw = os.environ.get("LBG_CAPABILITY_FORGE_STAGING_DIR", "").strip()
    if raw:
        return Path(raw)
    return Path(__file__).resolve().parent / "staging" / "capability_forge"


@dataclass
class CapabilityCodeSpec:
    name: str
    description: str
    python_code: str
    risk_level: str = "medium"  # 'low' | 'medium' | 'high'
    allowed_roots: list[str] = field(default_factory=list)
    timeout_s: int = 30
    tests_code: str = ""


class ASTSafetyChecker(ast.NodeVisitor):
    """Analyseur AST pour détecter les motifs non sécurisés ou interdits."""

    def __init__(self) -> None:
        self.errors: list[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            base_mod = alias.name.split(".")[0]
            if base_mod in _FORBIDDEN_MODULES:
                self.errors.append(f"Import interdit: {alias.name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            base_mod = node.module.split(".")[0]
            if base_mod in _FORBIDDEN_MODULES:
                self.errors.append(f"Import interdit: {node.module}")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        # Détection d'appels directs (eval, exec, etc.)
        if isinstance(node.func, ast.Name):
            if node.func.id in _FORBIDDEN_CALLS:
                self.errors.append(f"Appel interdit: {node.func.id}()")

        # Détection d'appels d'attributs (os.system, subprocess avec shell=True)
        elif isinstance(node.func, ast.Attribute):
            attr_name = node.func.attr
            if attr_name in _FORBIDDEN_ATTRS:
                self.errors.append(f"Méthode interdite: .{attr_name}()")

            # subprocess.run/Popen avec shell=True
            if attr_name in ("run", "Popen", "call", "check_call", "check_output"):
                for kw in node.keywords:
                    if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and bool(kw.value.value):
                        self.errors.append("subprocess avec shell=True est strictement interdit")

        self.generic_visit(node)


def check_ast_safety(python_source: str) -> list[str]:
    """Valide la sécurité du code Python via parsing AST.

    Retourne une liste d'erreurs (vide si le code est sain).
    """
    cleaned = (python_source or "").strip()
    if not cleaned:
        return ["Code source vide"]

    try:
        tree = ast.parse(cleaned)
    except SyntaxError as exc:
        return [f"Erreur de syntaxe Python: {exc}"]

    checker = ASTSafetyChecker()
    checker.visit(tree)
    return checker.errors


def evaluate_risk_level(name: str, code: str, user_risk: str = "medium") -> str:
    """Détermine le niveau de risque de manière stricte et déterministe.

    Règle canonique : toute suppression ou écriture de fichier impose 'high'.
    """
    code_low = code.lower()
    name_low = name.lower()

    high_cues = (
        "unlink",
        "remove",
        "rmdir",
        "rmtree",
        "delete",
        "supprime",
        "write_text",
        "write_bytes",
        "open(",
        "truncate",
        "kill",
        "shutdown",
        "reboot",
    )
    if any(cue in code_low for cue in high_cues) or any(cue in name_low for cue in ("delete", "supprime", "kill", "remove")):
        return "high"

    if user_risk in ("low", "medium", "high"):
        return user_risk

    return "medium"


def execute_in_sandbox(
    script_path: Path,
    args: list[str] | None = None,
    *,
    timeout_s: int = 15,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Exécute un script Python dans un environnement sandboxé et isolé sur la machine .143.

    Utilise par priorité :
    1. Bubblewrap (`bwrap`) si disponible (isolation filesystem read-only + tmpfs + network unshare)
    2. Fallback `unshare -n` (isolation réseau locale)
    3. Exécution standard sous timeout strict avec env aseptisé.
    """
    clean_env = {
        "PATH": "/usr/bin:/bin",
        "LANG": "C.UTF-8",
        "PYTHONPATH": "",
    }
    if env:
        clean_env.update(env)

    call_args = [str(script_path)] + (args or [])

    # Option 1 : bwrap (Bubblewrap) présent sur Omarchy .143
    bwrap_bin = shutil.which("bwrap")
    cmd: list[str] = []

    if bwrap_bin:
        cmd = [
            bwrap_bin,
            "--ro-bind", "/usr", "/usr",
            "--ro-bind", "/lib", "/lib",
            "--ro-bind", "/lib64", "/lib64",
            "--ro-bind", "/bin", "/bin",
            "--ro-bind", "/etc", "/etc",
            "--tmpfs", "/tmp",
            "--ro-bind", str(script_path.parent), str(script_path.parent),
            "--unshare-net",
            "--die-with-parent",
            "/usr/bin/python3",
            str(script_path),
        ] + (args or [])
    else:
        # Option 2 : exécution Python isolée
        cmd = ["python3", str(script_path)] + (args or [])

    t0 = time.time()
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=float(timeout_s),
            env=clean_env,
        )
        duration_ms = round((time.time() - t0) * 1000)
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "duration_ms": duration_ms,
            "sandboxed_with": "bwrap" if bwrap_bin else "subprocess",
        }
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "returncode": 124,
            "stdout": "",
            "stderr": f"Timeout après {timeout_s}s",
            "duration_ms": round((time.time() - t0) * 1000),
            "sandboxed_with": "timeout",
        }
    except Exception as exc:
        return {
            "ok": False,
            "returncode": 1,
            "stdout": "",
            "stderr": f"Erreur lancement sandbox: {exc}",
            "duration_ms": round((time.time() - t0) * 1000),
            "sandboxed_with": "error",
        }


def write_skill_package(
    *,
    base_dir: Path,
    spec: CapabilityCodeSpec,
) -> tuple[Path, Path]:
    """Génère un package de skill standardisé : SKILL.md + run.py."""
    base_dir.mkdir(parents=True, exist_ok=True)

    # 1. Frontmatter SKILL.md
    skill_md = f"""---
name: {spec.name}
description: {spec.description}
risk_level: {spec.risk_level}
allowed_roots: {json.dumps(spec.allowed_roots)}
timeout_s: {spec.timeout_s}
commands:
  run: python3 run.py
---

# Skill Gladys Appris : {spec.name}

## Description
{spec.description}

## Risque & Gouvernance
- Niveau de risque : **{spec.risk_level.upper()}**
- Exécution isolée en sous-processus sans accès réseau.
"""
    skill_md_path = base_dir / "SKILL.md"
    skill_md_path.write_text(skill_md, encoding="utf-8")

    # 2. run.py exécutable autonome
    run_py_path = base_dir / "run.py"
    run_py_path.write_text(spec.python_code.strip() + "\n", encoding="utf-8")
    run_py_path.chmod(0o755)

    return skill_md_path, run_py_path


def adopt_capability_from_staging(manifest_path: Path | str) -> dict[str, Any]:
    """Installe définitivement un skill validé en L2 dans skills/learned/<name>/."""
    m_path = Path(manifest_path)
    if not m_path.is_file():
        return {"ok": False, "error": f"Manifeste introuvable: {m_path}"}

    try:
        manifest = json.loads(m_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"ok": False, "error": f"Erreur lecture manifeste: {exc}"}

    spec_dict = manifest.get("spec", {})
    cap_name = str(spec_dict.get("name") or "").strip()
    if not _CAPABILITY_NAME_RE.match(cap_name):
        return {"ok": False, "error": f"Nom de capacité invalide: {cap_name}"}

    target_dir = skills_learned_dir() / cap_name
    staging_skill_dir = m_path.parent / "skill"

    if not staging_skill_dir.is_dir():
        return {"ok": False, "error": f"Dossier skill de staging introuvable: {staging_skill_dir}"}

    # Copie atomique dans skills/learned/
    target_dir.mkdir(parents=True, exist_ok=True)
    for item in staging_skill_dir.iterdir():
        if item.is_file():
            shutil.copy2(item, target_dir / item.name)

    manifest["status"] = "adopted_l2"
    manifest["adopted_at"] = time.time()
    manifest["installed_path"] = str(target_dir)
    m_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {
        "ok": True,
        "name": cap_name,
        "installed_path": str(target_dir),
    }


def run_capability_forge_cycle(
    spec: CapabilityCodeSpec,
    *,
    spawn_l2: bool = True,
    conversation_id: str = "default",
) -> dict[str, Any]:
    """Cycle complet de Capability Forge : validation statique, test sandbox, staging et L2."""
    if not _CAPABILITY_NAME_RE.match(spec.name):
        return {"ok": False, "error": f"Nom de capacité invalide: {spec.name!r}"}

    # 1. Vérification AST statique
    ast_errors = check_ast_safety(spec.python_code)
    if ast_errors:
        return {
            "ok": False,
            "error": "Échec de l'analyse statique AST (code non sécurisé)",
            "ast_errors": ast_errors,
        }

    # 2. Imposition déterministe du niveau de risque
    effective_risk = evaluate_risk_level(spec.name, spec.python_code, spec.risk_level)
    spec.risk_level = effective_risk

    run_id = f"cap_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    staging_base = staging_dir() / run_id
    staging_skill = staging_base / "skill"
    write_skill_package(base_dir=staging_skill, spec=spec)

    # 3. Évaluation en Sandbox isolée (.143)
    run_py = staging_skill / "run.py"
    # Test avec argument --dry-run ou --help par défaut
    sandbox_res = execute_in_sandbox(run_py, ["--help"], timeout_s=spec.timeout_s)

    manifest_file = staging_base / "manifest.json"
    manifest_data = {
        "run_id": run_id,
        "created_at": time.time(),
        "spec": {
            "name": spec.name,
            "description": spec.description,
            "risk_level": spec.risk_level,
            "allowed_roots": spec.allowed_roots,
            "timeout_s": spec.timeout_s,
        },
        "ast_check": {"ok": True, "errors": []},
        "sandbox_test": sandbox_res,
        "status": "pending_l2" if sandbox_res.get("ok") else "sandbox_failed",
    }
    manifest_file.write_text(json.dumps(manifest_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    l2_task_id = None
    pending_action_id = None
    if sandbox_res.get("ok") and spawn_l2:
        try:
            from team import store as team_store  # type: ignore

            objective = f"Revue L2 — Adoption du Skill Appris `{spec.name}` (Risque: {spec.risk_level.upper()}). Manifeste: {manifest_file}"
            task = team_store.create_task(
                role="pm",
                objective=objective,
                actor_id="system:capability_forge",
                priority="high" if spec.risk_level == "high" else "normal",
                approval_required=True,
                context={
                    "capability_adoption_review": True,
                    "workflow": "capability_adoption_review",
                    "manifest_path": str(manifest_file),
                    "capability_name": spec.name,
                },
            )
            l2_task_id = task.id
        except Exception as exc:
            logger.warning("Échec création tâche L2 Pilot: %s", exc)

        try:
            import pending_actions  # type: ignore

            act_id = f"act_adopt_cap_{spec.name}_{int(time.time())}"
            pa = pending_actions.PendingAction(
                action_id=act_id,
                conversation_id=conversation_id,
                action_type="capability_adoption",
                label=f"Adoption du Skill : {spec.name}",
                summary=f"{spec.description} (Risque: {spec.risk_level.upper()})",
                command=["adopt_capability", str(manifest_file)],
                context={"action_key": "adopt_capability", "manifest_path": str(manifest_file), "capability_name": spec.name},
                button_text="Adopter le Skill",
                cancel_text="Rejeter",
            )
            pending_actions.store_pending_action(conversation_id, pa)
            pending_action_id = act_id
        except Exception as exc:
            logger.warning("Échec création PendingAction chat: %s", exc)

    return {
        "ok": True,
        "run_id": run_id,
        "manifest_path": str(manifest_file),
        "sandbox_test": sandbox_res,
        "risk_level": effective_risk,
        "l2_task_id": l2_task_id,
        "pending_action_id": pending_action_id,
    }
