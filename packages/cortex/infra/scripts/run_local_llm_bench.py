#!/usr/bin/env python3
"""Runner minimal de bench local LLM via API OpenAI-compatible."""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any

import httpx


def load_prompts(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    prompts = data.get("prompts")
    if not isinstance(prompts, list):
        raise ValueError("champ prompts invalide")
    return [p for p in prompts if isinstance(p, dict)]


def chat_completions_url(base_url: str) -> str:
    b = base_url.rstrip("/")
    if b.endswith("/v1"):
        return f"{b}/chat/completions"
    return f"{b}/v1/chat/completions"


def model_for_category(category: str, explicit_model: str | None = None) -> str:
    if explicit_model:
        return explicit_model
    cat = (category or "").strip().lower()
    if cat == "routage_agentique":
        return os.environ.get("LBG_REASON_MODEL_ROUTER", "").strip() or "gemma4:e2b"
    if cat == "json_actions_structurees":
        return os.environ.get("LBG_REASON_MODEL_JSON", "").strip() or "gemma4:e2b"
    if cat == "code":
        return os.environ.get("LBG_REASON_MODEL_CODE", "").strip() or "huihui_ai/Qwen3.8-abliterated:27b"
    if cat == "raisonnement":
        return (
            os.environ.get("LBG_REASON_MODEL_PM", "").strip()
            or os.environ.get("LBG_REASON_LOCAL_MODEL", "").strip()
            or "huihui_ai/Qwen3.8-abliterated:27b"
        )
    return os.environ.get("LBG_REASON_LOCAL_MODEL", "").strip() or "gemma4:e2b"


def filter_prompts(
    prompts: list[dict[str, Any]],
    *,
    categories: set[str] | None,
    ids: set[str] | None,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for p in prompts:
        cat = str(p.get("category") or "").strip().lower()
        pid = str(p.get("id") or "").strip()
        if categories and cat not in categories:
            continue
        if ids and pid not in ids:
            continue
        out.append(p)
    return out


def call_chat(
    base_url: str,
    model: str,
    instruction: str,
    *,
    timeout_s: float,
    max_tokens: int,
) -> dict[str, Any]:
    url = chat_completions_url(base_url)
    payload: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": instruction}],
        "temperature": 0,
    }
    if max_tokens > 0:
        payload["max_tokens"] = max_tokens
    started = time.perf_counter()
    with httpx.Client(timeout=httpx.Timeout(timeout_s)) as client:
        response = client.post(url, json=payload)
        latency_s = round(time.perf_counter() - started, 3)
        response.raise_for_status()
        data = response.json()
    choices = data.get("choices") if isinstance(data, dict) else None
    if not isinstance(choices, list) or not choices:
        raise ValueError("reponse chat invalide")
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    content = ""
    if isinstance(message, dict):
        content = str(message.get("content") or "")
        # Gemma4 « thinking » : content vide mais reasoning présent
        if not content.strip():
            reasoning = message.get("reasoning") or message.get("reasoning_content")
            if isinstance(reasoning, str) and reasoning.strip():
                content = reasoning.strip()
    return {"latency_s": latency_s, "content": content, "raw": data}


def execute_bench(
    base_url: str,
    prompt_path: Path,
    *,
    model: str = "",
    categories: set[str] | None = None,
    ids: set[str] | None = None,
    timeout_s: float = 180.0,
    max_tokens: int = 320,
    pause_s: float = 8.0,
) -> dict[str, Any]:
    prompts = filter_prompts(load_prompts(prompt_path), categories=categories, ids=ids)
    if not prompts:
        return {"ok": False, "error": "aucun prompt apres filtre", "prompt_count": 0, "oks": 0, "fails": 0, "results": []}

    results: list[dict[str, Any]] = []
    for i, prompt in enumerate(prompts):
        if i > 0 and pause_s > 0:
            time.sleep(pause_s)
        category = str(prompt.get("category") or "")
        resolved_model = model_for_category(category, model or None)
        item = {
            "id": prompt.get("id"),
            "category": category,
            "title": prompt.get("title"),
            "model": resolved_model,
            "max_tokens": max_tokens,
        }
        try:
            res = call_chat(
                base_url,
                resolved_model,
                str(prompt.get("instruction") or ""),
                timeout_s=timeout_s,
                max_tokens=max_tokens,
            )
            item.update({"ok": True, **res})
        except Exception as exc:  # pragma: no cover
            item.update({"ok": False, "error": str(exc)})
        results.append(item)

    oks = sum(1 for r in results if r.get("ok"))
    return {
        "ok": True,
        "model": model or "per-category",
        "base_url": base_url,
        "prompt_count": len(prompts),
        "oks": oks,
        "fails": len(prompts) - oks,
        "max_tokens": max_tokens,
        "timeout_s": timeout_s,
        "pause_s": pause_s,
        "categories_filter": sorted(categories) if categories else None,
        "ids_filter": sorted(ids) if ids else None,
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Bench local LLM a partir d'un corpus JSON")
    parser.add_argument("--base-url", required=True, help="endpoint Ollama (ex. http://192.168.0.110:11434)")
    parser.add_argument("--model", default="", help="forcer un modele pour tous les prompts du lot")
    parser.add_argument(
        "--prompts",
        default="docs/local_llm_bench_prompts.json",
        help="chemin vers le corpus de prompts",
    )
    parser.add_argument(
        "--output",
        default="tmp/local_llm_bench/latest.json",
        help="chemin du rapport JSON",
    )
    parser.add_argument("--timeout", type=float, default=180.0, help="timeout par prompt (s)")
    parser.add_argument("--max-tokens", type=int, default=320, help="plafond de generation")
    parser.add_argument("--pause-s", type=float, default=8.0, help="pause entre prompts")
    parser.add_argument(
        "--categories",
        default="",
        help="filtre categories comma-separe (ex. routage_agentique,json_actions_structurees)",
    )
    parser.add_argument("--ids", default="", help="filtre ids comma-separe")
    args = parser.parse_args()

    prompt_path = Path(args.prompts)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cat_filter: set[str] | None = None
    if args.categories.strip():
        cat_filter = {c.strip().lower() for c in args.categories.split(",") if c.strip()}
    id_filter: set[str] | None = None
    if args.ids.strip():
        id_filter = {i.strip() for i in args.ids.split(",") if i.strip()}

    report = execute_bench(
        args.base_url,
        prompt_path,
        model=args.model,
        categories=cat_filter,
        ids=id_filter,
        timeout_s=args.timeout,
        max_tokens=args.max_tokens,
        pause_s=args.pause_s,
    )
    if report.get("error") == "aucun prompt apres filtre":
        print(json.dumps({"ok": False, "error": report["error"]}, ensure_ascii=False))
        return 2

    oks = int(report.get("oks") or 0)
    prompts_count = int(report.get("prompt_count") or 0)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": True,
                "output": str(output_path),
                "prompt_count": prompts_count,
                "oks": oks,
                "fails": prompts_count - oks,
            },
            ensure_ascii=False,
        )
    )
    return 0 if oks == prompts_count else 1


if __name__ == "__main__":
    raise SystemExit(main())
