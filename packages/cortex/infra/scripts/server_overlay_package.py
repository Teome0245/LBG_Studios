#!/usr/bin/env python3
"""Packaging atomique du sous-package ``server_overlay`` (ticket plan 5.1).

Le Compagnon sur CT ``.100`` est surchargé par un ensemble de modules Python
(``packages/cortex/compagnon_ui/server_overlay``). Historiquement le déploiement
faisait 29 ``rsync`` fichier-par-fichier (pas de versioning, rollback complexe).

Cet outil construit **un** artefact versionné et le déploie **atomiquement** :

  build     → tarball + ``MANIFEST.sha256`` + ``VERSION`` (checksum de version)
  verify    → vérifie le sha256 du tarball puis de chaque fichier du manifest
  apply     → sauvegarde les cibles, applique chaque fichier (rename atomique),
              écrit le marqueur de version (rollback possible)
  rollback  → restaure la sauvegarde précédente
  status    → lit le marqueur de version d'une racine de déploiement

Bibliothèque standard uniquement (aucune dépendance), utilisable telle quelle
sur ``.100``.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
DEFAULT_OVERLAY = HERE.parents[1] / "compagnon_ui" / "server_overlay"
DEFAULT_MAP = DEFAULT_OVERLAY / "overlay.map"
DEFAULT_PYPROJECT = DEFAULT_OVERLAY / "pyproject.toml"
MANIFEST_NAME = "MANIFEST.sha256"
VERSION_NAME = "VERSION"
DEFAULT_MARKER_NAME = ".server_overlay_version"
BACKUP_INDEX = "backup_index.json"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_package_version(pyproject: Path) -> str:
    text = pyproject.read_text(encoding="utf-8")
    m = re.search(r'^\s*version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not m:
        raise SystemExit(f"version introuvable dans {pyproject}")
    return m.group(1)


def git_sha(overlay_dir: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(overlay_dir), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return (out.stdout or "").strip() if out.returncode == 0 else ""


def read_map(map_path: Path) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    seen: set[str] = set()
    for raw in map_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            raise SystemExit(f"ligne overlay.map invalide: {raw!r}")
        src, dest = parts[0], parts[1]
        if dest in seen:
            continue
        seen.add(dest)
        entries.append((src, dest))
    if not entries:
        raise SystemExit(f"overlay.map vide: {map_path}")
    return entries


def _collect(overlay_dir: Path, map_path: Path) -> tuple[dict[str, bytes], list[str]]:
    files: dict[str, bytes] = {}
    order: list[str] = []
    for src_rel, dest_rel in read_map(map_path):
        src = (overlay_dir / src_rel).resolve()
        if not src.is_file():
            raise SystemExit(f"source manquante pour le packaging: {src}")
        files[dest_rel] = src.read_bytes()
        order.append(dest_rel)
    return files, order


def compute_package_sha(files: dict[str, bytes]) -> str:
    lines = [f"{_sha256_bytes(files[d])}  {d}" for d in sorted(files)]
    return _sha256_bytes(("\n".join(lines) + "\n").encode("utf-8"))


def build(
    overlay_dir: Path,
    map_path: Path,
    out_dir: Path,
    *,
    pyproject: Path | None = None,
) -> dict[str, Any]:
    files, order = _collect(overlay_dir, map_path)
    pkg_version = read_package_version(pyproject or (overlay_dir / "pyproject.toml"))
    gsha = git_sha(overlay_dir)
    version = f"{pkg_version}+{gsha}" if gsha else pkg_version
    package_sha = compute_package_sha(files)

    out_dir.mkdir(parents=True, exist_ok=True)
    tarball = out_dir / f"server_overlay-{version}.tar.gz"
    manifest_lines = [f"{_sha256_bytes(files[d])}  {d}" for d in order]
    version_doc = {
        "name": "lbg-compagnon-server-overlay",
        "version": version,
        "package_sha": package_sha,
        "git_sha": gsha,
        "files": len(files),
        "generated_ts": time.time(),
    }

    manifest_bytes = ("\n".join(manifest_lines) + "\n").encode("utf-8")
    version_bytes = (json.dumps(version_doc, ensure_ascii=False, indent=2) + "\n").encode("utf-8")

    with tarfile.open(tarball, "w:gz") as tar:
        for dest in order:
            data = files[dest]
            info = tarfile.TarInfo(name=f"overlay/{dest}")
            info.size = len(data)
            info.mtime = int(time.time())
            info.mode = 0o644
            tar.addfile(info, io.BytesIO(data))
        for name, payload in ((MANIFEST_NAME, manifest_bytes), (VERSION_NAME, version_bytes)):
            info = tarfile.TarInfo(name=name)
            info.size = len(payload)
            info.mtime = int(time.time())
            info.mode = 0o644
            tar.addfile(info, io.BytesIO(payload))

    tar_sha = sha256_file(tarball)
    sha_file = tarball.with_suffix(tarball.suffix + ".sha256")
    sha_file.write_text(f"{tar_sha}  {tarball.name}\n", encoding="utf-8")

    return {
        "ok": True,
        "action": "build",
        "version": version,
        "package_sha": package_sha,
        "git_sha": gsha,
        "files": len(files),
        "tarball": str(tarball),
        "tarball_sha256": tar_sha,
        "sha256_file": str(sha_file),
        "manifest": manifest_lines,
    }


def _read_version_doc(tar: tarfile.TarFile) -> dict[str, Any]:
    try:
        member = tar.extractfile(VERSION_NAME)
    except KeyError:
        raise SystemExit(f"{VERSION_NAME} absent du paquet")
    if member is None:
        raise SystemExit(f"{VERSION_NAME} illisible")
    return json.loads(member.read().decode("utf-8"))


def verify(tarball: Path, expected_sha: str | None = None) -> dict[str, Any]:
    if not tarball.is_file():
        raise SystemExit(f"tarball introuvable: {tarball}")
    tar_sha = sha256_file(tarball)
    if expected_sha and tar_sha != expected_sha.strip():
        raise SystemExit(f"checksum tarball invalide: {tar_sha} != {expected_sha}")
    checked = 0
    with tarfile.open(tarball, "r:gz") as tar:
        doc = _read_version_doc(tar)
        manifest = tar.extractfile(MANIFEST_NAME)
        if manifest is None:
            raise SystemExit(f"{MANIFEST_NAME} absent du paquet")
        for line in manifest.read().decode("utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            sha, dest = line.split(None, 1)
            dest = dest.strip()
            member = tar.extractfile(f"overlay/{dest}")
            if member is None:
                raise SystemExit(f"fichier absent du paquet: {dest}")
            got = _sha256_bytes(member.read())
            if got != sha:
                raise SystemExit(f"checksum invalide pour {dest}: {got} != {sha}")
            checked += 1
    return {
        "ok": True,
        "action": "verify",
        "tarball": str(tarball),
        "tarball_sha256": tar_sha,
        "version": doc.get("version"),
        "package_sha": doc.get("package_sha"),
        "files_verified": checked,
    }


def _extract(tarball: Path, dest_dir: Path) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(tarball, "r:gz") as tar:
        tar.extractall(dest_dir)


def apply(  # noqa: A001 - nom d'action CLI
    tarball: Path,
    root: Path,
    backup_dir: Path,
    *,
    marker: Path | None = None,
    expected_sha: str | None = None,
) -> dict[str, Any]:
    info = verify(tarball, expected_sha)
    root = root.resolve()
    backup_dir.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".overlay_stage.", dir=str(backup_dir)))
    marker = marker or (root / DEFAULT_MARKER_NAME)

    try:
        _extract(tarball, staging)
        manifest = (staging / MANIFEST_NAME).read_text(encoding="utf-8")
        version_doc = json.loads((staging / VERSION_NAME).read_text(encoding="utf-8"))

        # 1) Sauvegarde des cibles existantes + marqueur précédent.
        ts = time.strftime("%Y%m%d%H%M%S")
        backup_tar = backup_dir / f"overlay_backup-{ts}.tar.gz"
        index: list[dict[str, Any]] = []
        with tarfile.open(backup_tar, "w:gz") as btar:
            for line in manifest.splitlines():
                if not line.strip():
                    continue
                dest = line.split(None, 1)[1].strip()
                target = root / dest
                entry = {"dest": dest, "existed": target.is_file()}
                if entry["existed"]:
                    btar.add(str(target), arcname=dest)
                index.append(entry)
            prev_marker = {"existed": marker.is_file()}
            if prev_marker["existed"]:
                btar.add(str(marker), arcname=DEFAULT_MARKER_NAME)
            (backup_dir / BACKUP_INDEX).write_text(
                json.dumps(
                    {
                        "ts": ts,
                        "source_package_sha": version_doc.get("package_sha"),
                        "files": index,
                        "marker": prev_marker,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

        # 2) Application atomique : copie temporaire puis rename par fichier.
        applied: list[str] = []
        for line in manifest.splitlines():
            if not line.strip():
                continue
            _sha, dest = line.split(None, 1)
            dest = dest.strip()
            src = staging / "overlay" / dest
            target = root / dest
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp = target.parent / f".{target.name}.{os.getpid()}.tmp"
            shutil.copyfile(src, tmp)
            os.replace(tmp, target)
            applied.append(dest)

        # 3) Marqueur de version déployée (checksum de version).
        marker.parent.mkdir(parents=True, exist_ok=True)
        deployed = dict(version_doc)
        deployed["applied_ts"] = time.time()
        deployed["backup_tarball"] = str(backup_tar)
        marker.write_text(
            json.dumps(deployed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        return {
            "ok": True,
            "action": "apply",
            "version": version_doc.get("version"),
            "package_sha": version_doc.get("package_sha"),
            "tarball_sha256": info["tarball_sha256"],
            "files_applied": len(applied),
            "root": str(root),
            "marker": str(marker),
            "backup_tarball": str(backup_tar),
        }
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def rollback(root: Path, backup_tar: Path, *, marker: Path | None = None) -> dict[str, Any]:
    root = root.resolve()
    marker = marker or (root / DEFAULT_MARKER_NAME)
    if not backup_tar.is_file():
        raise SystemExit(f"sauvegarde introuvable: {backup_tar}")
    restored = 0
    removed = 0
    tmp = Path(tempfile.mkdtemp(prefix=".overlay_rollback."))
    try:
        _extract(backup_tar, tmp)
        index_path = backup_tar.parent / BACKUP_INDEX
        for member in sorted(tmp.rglob("*")):
            if not member.is_file():
                continue
            rel = member.relative_to(tmp)
            if str(rel) == DEFAULT_MARKER_NAME:
                tmp_marker = member
                continue
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(member, root / rel)
            restored += 1
        # Fichiers créés par le déploiement et inexistants avant → supprimés.
        if index_path.is_file():
            idx = json.loads(index_path.read_text(encoding="utf-8"))
            for entry in idx.get("files") or []:
                if not entry.get("existed") and (root / entry["dest"]).is_file():
                    (root / entry["dest"]).unlink()
                    removed += 1
            if not (idx.get("marker") or {}).get("existed"):
                marker.unlink(missing_ok=True)
        if (tmp / DEFAULT_MARKER_NAME).is_file():
            os.replace(tmp / DEFAULT_MARKER_NAME, marker)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return {
        "ok": True,
        "action": "rollback",
        "root": str(root),
        "restored": restored,
        "removed": removed,
        "backup_tarball": str(backup_tar),
    }


def status(root: Path, *, marker: Path | None = None) -> dict[str, Any]:
    marker = marker or (root.resolve() / DEFAULT_MARKER_NAME)
    if not marker.is_file():
        return {"ok": False, "action": "status", "root": str(root), "marker": str(marker), "error": "no_marker"}
    doc = json.loads(marker.read_text(encoding="utf-8"))
    return {"ok": True, "action": "status", "root": str(root), "marker": str(marker), **doc}


def _latest_backup(backup_dir: Path) -> Path:
    candidates = sorted(backup_dir.glob("overlay_backup-*.tar.gz"))
    if not candidates:
        raise SystemExit(f"aucune sauvegarde dans {backup_dir}")
    return candidates[-1]


def _emit(payload: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="sortie JSON sur une ligne")
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="construit le paquet versionné")
    b.add_argument("--overlay-dir", type=Path, default=DEFAULT_OVERLAY)
    b.add_argument("--map", type=Path, default=DEFAULT_MAP)
    b.add_argument("--out", type=Path, default=Path("dist/server_overlay"))

    v = sub.add_parser("verify", help="vérifie tarball + manifest")
    v.add_argument("--tarball", type=Path, required=True)
    v.add_argument("--sha256", default="")

    a = sub.add_parser("apply", help="applique atomiquement le paquet")
    a.add_argument("--tarball", type=Path, required=True)
    a.add_argument("--root", type=Path, required=True)
    a.add_argument("--backup-dir", type=Path, required=True)
    a.add_argument("--marker", type=Path, default=None)
    a.add_argument("--sha256", default="")

    r = sub.add_parser("rollback", help="restaure la sauvegarde précédente")
    r.add_argument("--root", type=Path, required=True)
    r.add_argument("--backup-tar", type=Path, default=None)
    r.add_argument("--backup-dir", type=Path, default=None)
    r.add_argument("--marker", type=Path, default=None)

    s = sub.add_parser("status", help="lit le marqueur de version déployée")
    s.add_argument("--root", type=Path, required=True)
    s.add_argument("--marker", type=Path, default=None)

    args = ap.parse_args(argv)
    try:
        if args.cmd == "build":
            payload = build(args.overlay_dir.resolve(), args.map.resolve(), args.out.resolve())
        elif args.cmd == "verify":
            payload = verify(args.tarball.resolve(), args.sha256 or None)
        elif args.cmd == "apply":
            payload = apply(
                args.tarball.resolve(),
                args.root,
                args.backup_dir,
                marker=args.marker,
                expected_sha=args.sha256 or None,
            )
        elif args.cmd == "rollback":
            backup_tar = args.backup_tar
            if backup_tar is None:
                if args.backup_dir is None:
                    raise SystemExit("--backup-tar ou --backup-dir requis")
                backup_tar = _latest_backup(args.backup_dir)
            payload = rollback(args.root, backup_tar, marker=args.marker)
        else:  # status
            payload = status(args.root, marker=args.marker)
    except SystemExit:
        raise
    except Exception as e:  # noqa: BLE001 - CLI: erreur → JSON + code 1
        print(json.dumps({"ok": False, "action": args.cmd, "error": str(e)}, ensure_ascii=False))
        return 1
    _emit(payload, args.json)
    return 0 if payload.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
