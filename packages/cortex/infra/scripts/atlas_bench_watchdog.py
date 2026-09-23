#!/usr/bin/env python3
"""Atlas — bench stabilise, retry KO uniquement, alerte ops (Slack + Element)."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent
_BENCH_SPEC = importlib.util.spec_from_file_location(
    "run_local_llm_bench",
    _SCRIPT_DIR / "run_local_llm_bench.py",
)
if _BENCH_SPEC is None or _BENCH_SPEC.loader is None:
    raise RuntimeError("impossible de charger run_local_llm_bench.py")
_bench = importlib.util.module_from_spec(_BENCH_SPEC)
_BENCH_SPEC.loader.exec_module(_bench)


def truthy(raw: str) -> bool:
    return raw.strip().lower() in ("1", "true", "yes", "on")


def count_oks(lots: list[dict[str, Any]]) -> tuple[int, int]:
    oks = 0
    total = 0
    for lot in lots:
        total += int(lot.get("prompt_count") or 0)
        oks += int(lot.get("oks") or 0)
    return oks, total


def recalc_lot(lot: dict[str, Any]) -> None:
    results = lot.get("results") if isinstance(lot.get("results"), list) else []
    lot["oks"] = sum(1 for r in results if isinstance(r, dict) and r.get("ok"))
    lot["prompt_count"] = len(results)
    lot["fails"] = lot["prompt_count"] - lot["oks"]


def apply_retry_results(lots: list[dict[str, Any]], retry_report: dict[str, Any]) -> list[str]:
    """Fusionne les retries OK dans les lots d'origine."""
    recovered: list[str] = []
    retry_results = retry_report.get("results") if isinstance(retry_report.get("results"), list) else []
    by_id: dict[str, dict[str, Any]] = {}
    for r in retry_results:
        if isinstance(r, dict) and r.get("ok") and r.get("id"):
            by_id[str(r["id"])] = r
    for lot in lots:
        results = lot.get("results")
        if not isinstance(results, list):
            continue
        for i, row in enumerate(results):
            if not isinstance(row, dict) or row.get("ok"):
                continue
            pid = str(row.get("id") or "")
            new = by_id.get(pid)
            if new:
                merged = {**row, **new, "retry": True}
                results[i] = merged
                recovered.append(pid)
        recalc_lot(lot)
    return recovered


def collect_failed_for_retry(lots: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for lot in lots:
        timeout_s = float(lot.get("timeout_s") or 180)
        max_tokens = int(lot.get("max_tokens") or 320)
        pause_s = float(lot.get("pause_s") or 12)
        for r in lot.get("results") or []:
            if not isinstance(r, dict) or r.get("ok"):
                continue
            out.append(
                {
                    "id": str(r.get("id") or ""),
                    "model": str(r.get("model") or lot.get("model") or ""),
                    "timeout_s": timeout_s,
                    "max_tokens": int(r.get("max_tokens") or max_tokens),
                    "pause_s": pause_s,
                }
            )
    return [x for x in out if x["id"] and x["model"]]


def retry_failed_prompts(
    base_url: str,
    prompt_path: Path,
    lots: list[dict[str, Any]],
    *,
    pause_between_groups_s: float,
) -> dict[str, Any]:
    failed = collect_failed_for_retry(lots)
    if not failed:
        return {"ok": True, "skipped": True, "recovered": [], "results": []}

    groups: dict[tuple[str, int, float, float], set[str]] = {}
    for item in failed:
        key = (item["model"], item["max_tokens"], item["timeout_s"], item["pause_s"])
        groups.setdefault(key, set()).add(item["id"])

    all_retry_results: list[dict[str, Any]] = []
    recovered: list[str] = []
    for (model, max_tokens, timeout_s, pause_s), idset in groups.items():
        if pause_between_groups_s > 0:
            time.sleep(pause_between_groups_s)
        report = _bench.execute_bench(
            base_url,
            prompt_path,
            model=model,
            ids=idset,
            timeout_s=timeout_s,
            max_tokens=max_tokens,
            pause_s=pause_s,
        )
        recovered.extend(apply_retry_results(lots, report))
        for r in report.get("results") or []:
            if isinstance(r, dict):
                all_retry_results.append(r)

    return {
        "ok": True,
        "recovered": sorted(set(recovered)),
        "groups": len(groups),
        "results": all_retry_results,
    }


def run_stabilized_bench(
    base_url: str,
    prompt_path: Path,
    out_dir: Path,
    stamp: str,
) -> dict[str, Any]:
    lots: list[dict[str, Any]] = []

    # Timeouts CPU-only 110 : gemma4 « thinking » ~5–15 tok/s effectifs souvent <10 tok/min.
    e2b_timeout = float(os.environ.get("LBG_ATLAS_BENCH_E2B_TIMEOUT_S", "900"))
    e2b_tokens = int(os.environ.get("LBG_ATLAS_BENCH_E2B_MAX_TOKENS", "48"))
    e2b_pause = float(os.environ.get("LBG_ATLAS_BENCH_E2B_PAUSE_S", "5"))
    e2b = _bench.execute_bench(
        base_url,
        prompt_path,
        model="gemma4:e2b",
        categories={"routage_agentique", "json_actions_structurees"},
        timeout_s=e2b_timeout,
        max_tokens=e2b_tokens,
        pause_s=e2b_pause,
    )
    e2b_path = out_dir / f"bench_e2b_{stamp}.json"
    e2b_path.write_text(json.dumps(e2b, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lots.append(e2b)

    pause_lots = float(os.environ.get("LBG_ATLAS_BENCH_PAUSE_LOTS_S", "30"))
    if pause_lots > 0:
        time.sleep(pause_lots)

    b26_timeout = float(os.environ.get("LBG_ATLAS_BENCH_26B_TIMEOUT_S", "1200"))
    b26_tokens = int(os.environ.get("LBG_ATLAS_BENCH_26B_MAX_TOKENS", "64"))
    b26_pause = float(os.environ.get("LBG_ATLAS_BENCH_26B_PAUSE_S", "10"))
    b26 = _bench.execute_bench(
        base_url,
        prompt_path,
        model="gemma4:26b",
        ids={"reason-001", "code-002"},
        timeout_s=b26_timeout,
        max_tokens=b26_tokens,
        pause_s=b26_pause,
    )
    b26_path = out_dir / f"bench_26b_{stamp}.json"
    b26_path.write_text(json.dumps(b26, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lots.append(b26)

    return {"stamp": stamp, "lots": lots, "paths": {"e2b": str(e2b_path), "26b": str(b26_path)}}


def send_element_alert(message: str) -> dict[str, Any]:
    if truthy(os.environ.get("LBG_ATLAS_BENCH_ALERT_DISABLE", "0")):
        return {"ok": True, "skipped": True, "reason": "LBG_ATLAS_BENCH_ALERT_DISABLE"}

    try:
        from lbg_agents.ops_notify import send_text
    except ImportError:
        # Fallback chemin repo (script lancé hors venv editable)
        root = Path(__file__).resolve().parents[2]
        agents_src = root / "agents" / "src"
        if agents_src.is_dir() and str(agents_src) not in sys.path:
            sys.path.insert(0, str(agents_src))
        from lbg_agents.ops_notify import send_text

    return send_text(message, channel="ops")


def format_alert_message(
    *,
    stamp: str,
    oks_before: int,
    total: int,
    oks_after: int,
    min_oks: int,
    retry_meta: dict[str, Any],
    merged_path: Path,
) -> str:
    lines = [
        "⚠️ Atlas watchdog — bench LLM local",
        "",
        f"• stamp: {stamp}",
        f"• avant retry: {oks_before}/{total} OK",
        f"• apres retry KO: {oks_after}/{total} OK",
        f"• seuil minimum: {min_oks}/{total}",
        f"• retry recupere: {', '.join(retry_meta.get('recovered') or []) or 'aucun'}",
        f"• rapport: {merged_path}",
        "",
        "Action: verifier Ollama 110, swap, OLLAMA_MAX_LOADED_MODELS=1, relancer bench stabilise.",
    ]
    return "\n".join(lines)


def run_watchdog(
    *,
    base_url: str,
    prompt_path: Path,
    out_dir: Path,
    min_oks: int,
    do_retry: bool,
    do_alert: bool,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stabilized = run_stabilized_bench(base_url, prompt_path, out_dir, stamp)
    lots = stabilized["lots"]
    oks_before, total = count_oks(lots)

    retry_meta: dict[str, Any] = {"skipped": not do_retry}
    if do_retry and oks_before < total:
        pause_retry = float(os.environ.get("LBG_ATLAS_BENCH_RETRY_PAUSE_S", "20"))
        retry_meta = retry_failed_prompts(base_url, prompt_path, lots, pause_between_groups_s=pause_retry)

    oks_after, _ = count_oks(lots)
    merged = {
        "stamp": stamp,
        "oks_before_retry": oks_before,
        "oks_after_retry": oks_after,
        "total": total,
        "min_oks": min_oks,
        "lots": lots,
        "retry": retry_meta,
    }
    merged_path = out_dir / f"bench_watchdog_{stamp}.json"
    merged_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    alert_below = oks_after < min_oks
    alert_out: dict[str, Any] = {"skipped": not do_alert or not alert_below}
    if do_alert and alert_below:
        alert_out = send_element_alert(
            format_alert_message(
                stamp=stamp,
                oks_before=oks_before,
                total=total,
                oks_after=oks_after,
                min_oks=min_oks,
                retry_meta=retry_meta,
                merged_path=merged_path,
            )
        )

    return {
        "ok": not alert_below,
        "stamp": stamp,
        "oks_before_retry": oks_before,
        "oks_after_retry": oks_after,
        "total": total,
        "min_oks": min_oks,
        "alert_below_threshold": alert_below,
        "merged_path": str(merged_path),
        "retry": retry_meta,
        "element_alert": alert_out,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Atlas bench watchdog")
    parser.add_argument("--base-url", default=os.environ.get("LBG_BENCH_OLLAMA_URL", "http://192.168.0.110:11434"))
    parser.add_argument("--prompts", default="docs/local_llm_bench_prompts.json")
    parser.add_argument("--out-dir", default="tmp/local_llm_bench")
    parser.add_argument("--min-oks", type=int, default=int(os.environ.get("LBG_ATLAS_BENCH_MIN_OKS", "3")))
    parser.add_argument("--no-retry", action="store_true")
    parser.add_argument("--no-alert", action="store_true")
    args = parser.parse_args()

    root = Path(os.environ.get("LBG_IA_MMO_ROOT", Path(__file__).resolve().parents[2]))
    prompt_path = Path(args.prompts)
    if not prompt_path.is_file():
        prompt_path = root / args.prompts
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = root / out_dir

    result = run_watchdog(
        base_url=args.base_url.rstrip("/"),
        prompt_path=prompt_path,
        out_dir=out_dir,
        min_oks=max(1, args.min_oks),
        do_retry=not args.no_retry,
        do_alert=not args.no_alert,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result.get("ok"):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
