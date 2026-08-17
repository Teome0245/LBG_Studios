#!/usr/bin/env python3
"""Micro-bench heavy Ollama .110 : gemma4:26b vs qwen3.8:27b (CPU, court)."""
from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from typing import Any, Callable

MODELS = ("gemma4:26b", "qwen3.8:27b")


@dataclass
class RunResult:
    model: str
    task: str
    ok: bool
    score: float
    total_s: float
    eval_count: int
    tokens_per_s: float
    load_s: float
    detail: str
    preview: str


def _strip_fence(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```(?:\w+)?\n?", "", t)
        t = re.sub(r"\n?```$", "", t)
    return t.strip()


def _json_ok(text: str) -> bool:
    try:
        m = re.search(r"\{[\s\S]*\}", _strip_fence(text))
        if not m:
            return False
        d = json.loads(m.group(0))
        return (
            isinstance(d, dict)
            and {"action", "host", "checks", "risk"} <= set(d.keys())
            and isinstance(d["checks"], list)
            and len(d["checks"]) == 3
            and d["risk"] in ("low", "medium", "high")
            and "110" in str(d["host"])
        )
    except (json.JSONDecodeError, TypeError, KeyError):
        return False


def _code_ok(text: str) -> bool:
    t = _strip_fence(text)
    if "def clamp" not in t:
        return False
    # no off-by-one on the success path
    if re.search(r"return\s+x\s*\+\s*1", t):
        return False
    return bool(re.search(r"return\s+x\b", t))


TASKS: list[dict[str, Any]] = [
    {
        "id": "code_fix",
        "weight": 1.2,
        "prompt": (
            "Corrige le bug off-by-one. Réponds UNIQUEMENT avec la fonction Python complète.\n"
            "def clamp(x, lo, hi):\n"
            "    if x < lo: return lo\n"
            "    if x > hi: return hi\n"
            "    return x + 1\n"
        ),
        "check": _code_ok,
        "predict": 90,
    },
    {
        "id": "json_agent",
        "weight": 1.3,
        "prompt": (
            "Réponds UNIQUEMENT JSON (pas de markdown) clés exactes: "
            "action (string), host (IP), checks (3 strings), risk (low|medium|high). "
            "Contexte: audit Ollama 192.168.0.110 (tags, ps, free RAM)."
        ),
        "check": _json_ok,
        "predict": 100,
    },
    {
        "id": "reason_steps",
        "weight": 1.0,
        "prompt": (
            "CT Proxmox 24 Go RAM, modèle 18 Go déjà chargé. "
            "Peut-on charger un second modèle 18 Go sans swap ? "
            "Réponds d'abord par NON ou OUI, puis une phrase courte."
        ),
        "check": lambda t: bool(re.search(r"\bNON\b", t, re.I)),
        "predict": 40,
    },
]


def post(base: str, path: str, body: dict[str, Any], timeout: float) -> dict[str, Any]:
    req = urllib.request.Request(
        f"{base.rstrip('/')}{path}",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def unload(base: str, model: str) -> None:
    try:
        post(base, "/api/generate", {"model": model, "prompt": "", "keep_alive": 0}, 60.0)
    except Exception as exc:  # noqa: BLE001
        print(f"  warn unload {model}: {exc}", flush=True)


def has_model(base: str, model: str) -> bool:
    tags = json.loads(urllib.request.urlopen(f"{base.rstrip('/')}/api/tags", timeout=30).read())
    names = {m.get("name") for m in tags.get("models") or []}
    return any(model == n or n.startswith(model + ":") for n in names)


def generate(base: str, model: str, prompt: str, predict: int, timeout: float) -> tuple[dict[str, Any], float]:
    t0 = time.perf_counter()
    data = post(
        base,
        "/api/generate",
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "think": False,  # sinon les tokens thinking vident la réponse utile
            "keep_alive": "10m",
            "options": {
                "num_ctx": 2048,
                "num_predict": predict,
                "temperature": 0.1,
            },
        },
        timeout,
    )
    return data, time.perf_counter() - t0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://192.168.0.110:11434")
    ap.add_argument("--models", nargs="+", default=list(MODELS))
    ap.add_argument("--timeout", type=float, default=900.0)  # CPU ~0.1–0.3 tok/s
    args = ap.parse_args()
    base = args.base

    missing = [m for m in args.models if not has_model(base, m)]
    if missing:
        print(json.dumps({"ok": False, "error": "models_missing", "missing": missing}))
        return 2

    results: list[RunResult] = []
    for model in args.models:
        print(f"\n=== {model} ===", flush=True)
        for other in args.models:
            unload(base, other)
        time.sleep(2)

        # warmup court
        try:
            generate(base, model, "Réponds uniquement: OK", 8, args.timeout)
            print("  warmup ok", flush=True)
        except Exception as exc:  # noqa: BLE001
            print(f"  warmup FAIL: {exc}", flush=True)

        for task in TASKS:
            print(f"  task {task['id']} ...", flush=True)
            try:
                data, wall = generate(base, model, task["prompt"], int(task["predict"]), args.timeout)
                text = (data.get("response") or "").strip()
                eval_count = int(data.get("eval_count") or 0)
                eval_ns = int(data.get("eval_duration") or 0)
                load_s = int(data.get("load_duration") or 0) / 1e9
                tps = (eval_count / (eval_ns / 1e9)) if eval_ns > 0 else 0.0
                ok = bool(task["check"](text))
                quality = 1.0 if ok else 0.15
                score = (quality * float(task["weight"])) / max(wall, 0.5)
                rr = RunResult(
                    model=model,
                    task=task["id"],
                    ok=ok,
                    score=round(score, 4),
                    total_s=round(wall, 2),
                    eval_count=eval_count,
                    tokens_per_s=round(tps, 2),
                    load_s=round(load_s, 2),
                    detail="pass" if ok else "fail",
                    preview=text[:240].replace("\n", "\\n"),
                )
            except Exception as exc:  # noqa: BLE001
                rr = RunResult(
                    model=model,
                    task=task["id"],
                    ok=False,
                    score=0.0,
                    total_s=0.0,
                    eval_count=0,
                    tokens_per_s=0.0,
                    load_s=0.0,
                    detail=f"error:{type(exc).__name__}:{exc}",
                    preview="",
                )
            results.append(rr)
            print(
                f"    ok={rr.ok} {rr.total_s}s tps={rr.tokens_per_s} load={rr.load_s}s "
                f"score={rr.score} detail={rr.detail} | {rr.preview[:140]}",
                flush=True,
            )

        unload(base, model)

    summary = []
    for model in args.models:
        rows = [r for r in results if r.model == model]
        passes = sum(1 for r in rows if r.ok)
        total_s = sum(r.total_s for r in rows)
        mean_tps = sum(r.tokens_per_s for r in rows) / max(len(rows), 1)
        eff = sum(r.score for r in rows)
        errors = sum(1 for r in rows if r.detail.startswith("error:"))
        summary.append(
            {
                "model": model,
                "passes": passes,
                "tasks": len(rows),
                "errors": errors,
                "total_s": round(total_s, 2),
                "mean_tokens_per_s": round(mean_tps, 2),
                "efficiency_score": round(eff, 4),
            }
        )
    summary.sort(key=lambda x: (-x["passes"], -x["efficiency_score"], x["total_s"]))
    out = {
        "ok": True,
        "base": base,
        "results": [asdict(r) for r in results],
        "summary": summary,
        "winner": summary[0]["model"] if summary else None,
        "criterion": "max passes, then efficiency_score (quality*weight/latency), then lower total_s",
    }
    print("\n=== SUMMARY ===", flush=True)
    print(json.dumps(out, ensure_ascii=False, indent=2), flush=True)
    path = "/tmp/bench_heavy_110_result.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"wrote {path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
