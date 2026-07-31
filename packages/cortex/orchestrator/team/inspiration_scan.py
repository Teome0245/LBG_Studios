"""Pont Pygmalion → Infographiste_IA (scan/classification inspiration LoRA)."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

from team.models import TeamTask


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def infographiste_ia_root() -> Path | None:
    raw = os.environ.get("LBG_INFOGRAPHISTE_IA_ROOT", "").strip()
    if raw:
        p = Path(raw)
        return p if p.is_dir() else None
    for cand in (
        _repo_root().parent.parent / "Infographiste_IA",
        Path("/home/sdesh/projects/Infographiste_IA"),
    ):
        if (cand / "orchestrator.py").is_file():
            return cand
    return None


def _dataset_dir(root: Path) -> Path:
    raw = os.environ.get("LBG_INFOGRAPHISTE_DATASET_DIR", "").strip()
    if raw:
        return Path(raw)
    return root / "dataset" / "inspiration_mmorpg"


def _classify_inline(root: Path, dataset: Path) -> dict[str, Any]:
    """Fallback sans dépendances ComfyUI (import direct style_classifier)."""
    styles_path = root / "config" / "art_styles.json"
    src = str(root / "src")
    if src not in sys.path:
        sys.path.insert(0, src)
    from infographiste_virtuel.style_classifier import scan_and_classify

    report = scan_and_classify(dataset, styles_path)
    payload = report.to_dict()
    payload["ok"] = bool(payload.get("count", 0) > 0)
    payload["kind"] = "inspiration_classify"
    payload["infographiste_ia_root"] = str(root)
    payload["mode"] = "inline"
    return payload


def run_inspiration_classify(
    *,
    sort_to: Path | None = None,
    json_out: bool = True,
) -> dict[str, Any]:
    """Lance `orchestrator.py classify` dans Infographiste_IA."""
    root = infographiste_ia_root()
    if root is None:
        return {
            "ok": False,
            "error": "Infographiste_IA introuvable — définir LBG_INFOGRAPHISTE_IA_ROOT",
        }

    dataset = _dataset_dir(root)
    if not dataset.is_dir():
        return {
            "ok": False,
            "error": f"dataset inspiration absent: {dataset}",
            "infographiste_ia_root": str(root),
        }

    cmd = [
        sys.executable,
        str(root / "orchestrator.py"),
        "classify",
        "--dataset-dir",
        str(dataset),
        "--styles",
        str(root / "config" / "art_styles.json"),
    ]
    if json_out:
        cmd.append("--json")
    if sort_to is not None:
        cmd.extend(["--sort-to", str(sort_to), "--sort-mode", "symlink"])

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=float(os.environ.get("LBG_INFOGRAPHISTE_CLASSIFY_TIMEOUT_S", "120")),
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"ok": False, "error": str(e), "infographiste_ia_root": str(root)}

    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "classify échoué").strip()
        if "ModuleNotFoundError" in err or "No module named" in err:
            try:
                return _classify_inline(root, dataset)
            except Exception as inline_exc:  # noqa: BLE001
                return {
                    "ok": False,
                    "error": f"{err[:200]} | inline: {inline_exc}",
                    "infographiste_ia_root": str(root),
                }
        return {
            "ok": False,
            "error": err[:500],
            "infographiste_ia_root": str(root),
        }

    if not json_out:
        return {"ok": True, "stdout": proc.stdout, "infographiste_ia_root": str(root)}

    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        return {
            "ok": False,
            "error": f"JSON classify invalide: {e}",
            "stdout_tail": proc.stdout[-400:],
        }

    payload["ok"] = bool(payload.get("count", 0) > 0)
    payload["kind"] = "inspiration_classify"
    payload["infographiste_ia_root"] = str(root)
    return payload


def _sorted_styles_dir(root: Path) -> Path:
    return root / "dataset" / "styles_sorted" / "styles"


def _bucket_count(style_dir: Path) -> int:
    if not style_dir.is_dir():
        return 0
    return sum(
        1
        for p in style_dir.iterdir()
        if not p.name.startswith(".") and (p.is_file() or p.is_symlink())
    )


def _wsl_ssh_base_cmd(remote_shell: str) -> str:
    host = _wsl_ssh_host()
    port = _wsl_ssh_port()
    user = _wsl_ssh_user()
    identity = _train_ssh_identity()
    return (
        f"ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new "
        f"-o ConnectTimeout=20 -i {shlex.quote(identity)} -p {port} "
        f"{user}@{host} {shlex.quote(remote_shell)}"
    )


def _run_wsl_shell(remote_shell: str, *, timeout: float) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        _wsl_ssh_base_cmd(remote_shell),
        shell=True,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _run_wsl_orchestrator(args: str, *, timeout: float) -> dict[str, Any]:
    project = _wsl_project_dir()
    # Vision sur GPU local du WSL (.10) — ne pas réutiliser OLLAMA_BASE_URL (chat → 110)
    ollama_url = os.environ.get(
        "LBG_INFOGRAPHISTE_OLLAMA_URL",
        os.environ.get("OLLAMA_VISION_BASE_URL", "http://127.0.0.1:11434"),
    )
    ollama_model = os.environ.get(
        "LBG_INFOGRAPHISTE_VISION_MODEL",
        os.environ.get("OLLAMA_VISION_MODEL", "moondream"),
    )
    ollama_timeout = os.environ.get("OLLAMA_TIMEOUT_S", "120")
    ollama_keep = os.environ.get("OLLAMA_KEEP_ALIVE", "30s")
    remote = (
        f"cd {project} && PYTHONPATH=src "
        f"OLLAMA_BASE_URL={shlex.quote(ollama_url)} "
        f"OLLAMA_VISION_MODEL={shlex.quote(ollama_model)} "
        f"OLLAMA_TIMEOUT_S={shlex.quote(ollama_timeout)} "
        f"OLLAMA_KEEP_ALIVE={shlex.quote(ollama_keep)} "
        f"python3 orchestrator.py {args}"
    )
    proc = _run_wsl_shell(remote, timeout=timeout)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        if not detail:
            detail = f"orchestrator WSL échoué (rc={proc.returncode}, stdout/stderr vides)"
        else:
            detail = f"rc={proc.returncode}: {detail}"
        return {
            "ok": False,
            "error": detail[:500],
            "mode": "wsl",
        }
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        return {
            "ok": False,
            "error": f"JSON WSL invalide: {e}",
            "stdout_tail": proc.stdout[-400:],
            "mode": "wsl",
        }
    payload["mode"] = "wsl"
    payload["infographiste_ia_root"] = project
    return payload


def count_sorted_buckets(root: Path | None = None) -> dict[str, int]:
    """Compte les symlinks par bucket dans styles_sorted/styles/."""
    ia_root = root or infographiste_ia_root()
    if ia_root is None:
        remote = (
            f"cd {_wsl_project_dir()} && python3 - <<'PY'\n"
            "import json\nfrom pathlib import Path\n"
            "styles = Path('dataset/styles_sorted/styles')\n"
            "out = {}\n"
            "if styles.is_dir():\n"
            "  for d in sorted(styles.iterdir()):\n"
            "    if d.is_dir():\n"
            "      out[d.name] = sum(1 for p in d.iterdir() if not p.name.startswith('.') and (p.is_file() or p.is_symlink()))\n"
            "print(json.dumps(out))\nPY"
        )
        try:
            proc = _run_wsl_shell(remote, timeout=60)
            if proc.returncode == 0:
                data = json.loads(proc.stdout)
                return data if isinstance(data, dict) else {}
        except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
            return {}
        return {}
    styles_dir = _sorted_styles_dir(ia_root)
    if not styles_dir.is_dir():
        return {}
    return {d.name: _bucket_count(d) for d in sorted(styles_dir.iterdir()) if d.is_dir()}


def _orchestrator_env(root: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "src")
    env.setdefault(
        "OLLAMA_BASE_URL",
        os.environ.get(
            "LBG_INFOGRAPHISTE_OLLAMA_URL",
            os.environ.get("OLLAMA_VISION_BASE_URL", "http://127.0.0.1:11434"),
        ),
    )
    env.setdefault(
        "OLLAMA_VISION_MODEL",
        os.environ.get("LBG_INFOGRAPHISTE_VISION_MODEL", "moondream"),
    )
    env.setdefault("OLLAMA_TIMEOUT_S", "120")
    env.setdefault("OLLAMA_KEEP_ALIVE", "30s")
    return env


def run_vision_classify_batch(
    *,
    limit: int = 100,
    min_confidence: float = 0.55,
) -> dict[str, Any]:
    """Lance vision-classify sur un lot d'images unclassified."""
    root = infographiste_ia_root()
    per_image = float(os.environ.get("OLLAMA_TIMEOUT_S", "240"))
    timeout = float(
        os.environ.get(
            "LBG_INFOGRAPHISTE_VISION_BATCH_TIMEOUT_S",
            str(max(3600.0, limit * per_image * 1.2)),
        )
    )
    if root is None:
        payload = _run_wsl_orchestrator(
            f"vision-classify --limit {limit} --min-confidence {min_confidence} --json",
            timeout=timeout,
        )
        payload["ok"] = bool(payload.get("scanned", 0) > 0 or payload.get("counts")) and payload.get("ok", True)
        payload["kind"] = "vision_classify_batch"
        return payload

    cmd = [
        sys.executable,
        str(root / "orchestrator.py"),
        "vision-classify",
        "--limit",
        str(limit),
        "--min-confidence",
        str(min_confidence),
        "--json",
    ]
    per_image = float(os.environ.get("OLLAMA_TIMEOUT_S", "240"))
    timeout = float(
        os.environ.get(
            "LBG_INFOGRAPHISTE_VISION_BATCH_TIMEOUT_S",
            str(max(3600.0, limit * per_image * 1.2)),
        )
    )
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=timeout,
            env=_orchestrator_env(root),
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"ok": False, "error": str(e), "infographiste_ia_root": str(root)}

    if proc.returncode != 0:
        return {
            "ok": False,
            "error": (proc.stderr or proc.stdout or "vision-classify échoué")[:500],
            "infographiste_ia_root": str(root),
        }

    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        return {
            "ok": False,
            "error": f"JSON vision invalide: {e}",
            "stdout_tail": proc.stdout[-400:],
        }

    payload["ok"] = bool(payload.get("scanned", 0) > 0 or payload.get("counts"))
    payload["kind"] = "vision_classify_batch"
    payload["infographiste_ia_root"] = str(root)
    return payload


def run_prepare_styles_sorted(*, min_images: int = 20) -> dict[str, Any]:
    """Prépare kohya_train_by_style depuis styles_sorted."""
    root = infographiste_ia_root()
    if root is None:
        payload = _run_wsl_orchestrator(
            f"prepare-styles --from-sorted dataset/styles_sorted --min-images {min_images} --json",
            timeout=float(os.environ.get("LBG_INFOGRAPHISTE_PREPARE_TIMEOUT_S", "600")),
        )
        prepared = payload.get("styles") if isinstance(payload.get("styles"), dict) else {}
        payload["ok"] = any(v.get("ok") for v in prepared.values() if isinstance(v, dict))
        payload["kind"] = "prepare_styles_sorted"
        return payload

    sorted_root = root / "dataset" / "styles_sorted"
    cmd = [
        sys.executable,
        str(root / "orchestrator.py"),
        "prepare-styles",
        "--from-sorted",
        str(sorted_root),
        "--min-images",
        str(min_images),
        "--json",
    ]
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=float(os.environ.get("LBG_INFOGRAPHISTE_PREPARE_TIMEOUT_S", "600")),
            env=_orchestrator_env(root),
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"ok": False, "error": str(e), "infographiste_ia_root": str(root)}

    if proc.returncode != 0:
        return {
            "ok": False,
            "error": (proc.stderr or proc.stdout or "prepare-styles échoué")[:500],
            "infographiste_ia_root": str(root),
        }

    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        return {
            "ok": False,
            "error": f"JSON prepare invalide: {e}",
            "stdout_tail": proc.stdout[-400:],
        }

    prepared = payload.get("styles") if isinstance(payload.get("styles"), dict) else {}
    payload["ok"] = any(v.get("ok") for v in prepared.values() if isinstance(v, dict))
    payload["kind"] = "prepare_styles_sorted"
    payload["infographiste_ia_root"] = str(root)
    return payload


def _style_lora_meta(root: Path, style_id: str) -> dict[str, Any]:
    styles_path = root / "config" / "art_styles.json"
    try:
        doc = json.loads(styles_path.read_text(encoding="utf-8"))
        lora_cfg = (doc.get("styles") or {}).get(style_id, {}).get("lora") or {}
    except (OSError, json.JSONDecodeError, AttributeError):
        lora_cfg = {}
    trigger = str(lora_cfg.get("trigger_word") or style_id)
    repeats = int(lora_cfg.get("repeats") or 10)
    output_name = str(lora_cfg.get("output_name") or f"{style_id}_lora.safetensors")
    kohya_folder = f"{repeats}_{trigger}"
    return {
        "trigger_word": trigger,
        "repeats": repeats,
        "output_name": output_name,
        "kohya_folder": kohya_folder,
        "lora_name": output_name.replace(".safetensors", ""),
    }


def _wsl_ssh_host() -> str:
    return (
        os.environ.get("LBG_INFOGRAPHISTE_WSL_SSH_HOST", "").strip()
        or os.environ.get("LBG_LAN_HOST_DESKTOP", "").strip()
        or "192.168.0.10"
    )


def _wsl_ssh_port() -> int:
    try:
        return int(os.environ.get("LBG_INFOGRAPHISTE_WSL_SSH_PORT", "2222"))
    except ValueError:
        return 2222


def _wsl_ssh_user() -> str:
    return os.environ.get("LBG_INFOGRAPHISTE_WSL_SSH_USER", "sdesh").strip() or "sdesh"


def _wsl_project_dir() -> str:
    return (
        os.environ.get("LBG_INFOGRAPHISTE_WSL_PROJECT", "").strip()
        or "/home/sdesh/projects/Infographiste_IA"
    )


def _train_ssh_identity() -> str:
    for key in ("LBG_INFOGRAPHISTE_LORA_TRAIN_SSH_IDENTITY", "LBG_SSH_IDENTITY"):
        val = os.environ.get(key, "").strip()
        if val:
            return val
    return "/home/lbg/.ssh/id_ed25519"


def lora_train_remote_enabled() -> bool:
    if os.environ.get("LBG_INFOGRAPHISTE_LORA_TRAIN_CMD", "").strip():
        return True
    flag = os.environ.get("LBG_INFOGRAPHISTE_LORA_TRAIN_REMOTE", "1").strip().lower()
    return flag in ("1", "true", "yes", "on")


def build_wsl_lora_train_cmd(style_id: str, *, deploy: bool) -> str:
    """Commande SSH depuis core 140 → WSL poste dev (portproxy 2222)."""
    host = _wsl_ssh_host()
    port = _wsl_ssh_port()
    user = _wsl_ssh_user()
    project = _wsl_project_dir()
    identity = _train_ssh_identity()
    deploy_flag = "--deploy" if deploy else ""
    remote_shell = (
        f"cd {project} && ./scripts/train_lora_by_style.sh --style {style_id} {deploy_flag}"
    ).strip()
    return (
        f"ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new "
        f"-o ConnectTimeout=20 -i {shlex.quote(identity)} -p {port} "
        f"{user}@{host} {shlex.quote(remote_shell)}"
    )


def run_lora_train_style(style_id: str, *, deploy: bool = False) -> dict[str, Any]:
    """Entraîne un LoRA Kohya pour un style (poste GPU Windows/WSL)."""
    root = infographiste_ia_root()
    if root is None:
        return {"ok": False, "error": "Infographiste_IA introuvable", "style_id": style_id}

    meta = _style_lora_meta(root, style_id)
    remote = lora_train_remote_enabled()
    lora_path = root / "lora" / meta["output_name"]
    if not remote and lora_path.is_file() and lora_path.stat().st_size > 0:
        return {
            "ok": True,
            "skipped": True,
            "reason": "lora_deja_present",
            "style_id": style_id,
            **meta,
            "lora_path": str(lora_path),
        }

    kohya_dir = root / "dataset" / "kohya_train_by_style" / meta["kohya_folder"] if root else None
    if root and kohya_dir and not kohya_dir.is_dir():
        return {
            "ok": False,
            "error": f"dataset Kohya absent: {kohya_dir}",
            "style_id": style_id,
            **meta,
        }
    if root is None and remote:
        pass  # train entièrement sur WSL
    elif root is None:
        return {
            "ok": False,
            "error": "Infographiste_IA introuvable et train remote désactivé",
            "style_id": style_id,
            **meta,
        }

    remote_tpl = os.environ.get("LBG_INFOGRAPHISTE_LORA_TRAIN_CMD", "").strip()
    script = root / "scripts" / "train_lora_by_style.sh"
    train_mode = "unknown"
    if remote_tpl:
        cmd = remote_tpl.format(style_id=style_id, deploy="--deploy" if deploy else "")
        shell = True
        argv: list[str] | str = cmd
        train_mode = "custom_cmd"
    elif remote:
        cmd = build_wsl_lora_train_cmd(style_id, deploy=deploy)
        shell = True
        argv = cmd
        train_mode = "wsl_ssh"
    elif script.is_file():
        cmd_list = ["bash", str(script), "--style", style_id]
        if deploy:
            cmd_list.append("--deploy")
        shell = False
        argv = cmd_list
        cmd = cmd_list
        train_mode = "local"
    else:
        return {
            "ok": False,
            "error": "train désactivé — WSL SSH ou train_lora_by_style.sh requis",
            "style_id": style_id,
            **meta,
        }

    timeout = float(os.environ.get("LBG_INFOGRAPHISTE_LORA_TRAIN_TIMEOUT_S", "14400"))
    try:
        proc = subprocess.run(
            argv,
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=shell,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"ok": False, "error": str(e), "style_id": style_id, **meta}

    if proc.returncode != 0:
        return {
            "ok": False,
            "error": (proc.stderr or proc.stdout or "train échoué")[:500],
            "style_id": style_id,
            **meta,
        }

    return {
        "ok": True,
        "style_id": style_id,
        **meta,
        "deploy": deploy,
        "train_mode": train_mode,
        "command": cmd if isinstance(cmd, str) else " ".join(cmd),
        "stdout_tail": (proc.stdout or "")[-300:],
    }


def probe_inspiration_dataset(task: TeamTask | None = None) -> dict[str, Any]:
    """Sonde L1 — inventaire + classification par style (read-only sauf sort_to explicite)."""
    ctx = task.context if task else {}
    sort = bool(ctx.get("inspiration_sort"))
    sort_to = None
    if sort:
        root = infographiste_ia_root()
        if root:
            sort_to = root / "dataset" / "styles_sorted"

    out = run_inspiration_classify(sort_to=sort_to)
    by_style = out.get("by_style") if isinstance(out.get("by_style"), dict) else {}
    unclassified = int(out.get("unclassified") or 0)
    ready = out.get("ready_for_lora") if isinstance(out.get("ready_for_lora"), list) else []

    return {
        "kind": "inspiration_probe",
        "ok": bool(out.get("ok")),
        "readiness": "pret_lora" if ready else ("partiel" if out.get("ok") else "absent"),
        "unclassified": unclassified,
        "ready_for_lora": ready,
        "by_style": by_style,
        "classify": out,
        "hint": (
            "Lancer: python orchestrator.py classify --json dans Infographiste_IA"
            if not out.get("ok")
            else None
        ),
    }
