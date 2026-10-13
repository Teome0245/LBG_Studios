"""Veille évolution LBG — analyse de pistes (TikTok/docs/repos) via reason_llm.

Sans onglet navigateur. Livrable : tableau par piste + top 3 actions.
Routage : context ``evolution_veille`` / mots-clés « veille évolution ».
"""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any

from team.models import TeamTask
from team.reason_llm import complete_reason, reason_llm_enabled, reason_local_model

_LAST: dict[str, Any] = {}

_VERDICTS = frozenset({"utilisable", "inspiration", "non_pertinent"})

_SYSTEM = """Tu es Thémis (PM Studio LBG). Analyse des pistes de veille.
Ancres : Cortex/Team/Campus (pas de 2e OS), greffe périphérique (ADR 0020 DSH), Laya=intents System1, voix=TTS/ASR local.
Français. UN seul JSON (pas de markdown). Verdict ∈ utilisable|inspiration|non_pertinent.
{
  "summary": "1-2 phrases",
  "leads": [{"index":1,"title":"…","domain":"…","feasibility":"court","integration":"où brancher","pros":["…"],"cons":["…"],"verdict":"inspiration","plan":"L1/L2 ou null"}],
  "top_3_actions": [{"title":"…","owner_role":"pm|ops|dev_game","autonomy":"L1|L2","why":"…"}]
}
Max 12 leads, 3 actions. Texte court.
"""


def _heuristic_analysis(leads: list[dict[str, Any]]) -> dict[str, Any]:
    """Fallback sans LLM — règles domaine / mots-clés Studio (livrable toujours)."""
    out_leads: list[dict[str, Any]] = []
    for lead in leads:
        title = str(lead.get("title") or "")
        desc = str(lead.get("description") or "")
        domain = str(lead.get("domain") or "general_studio")
        blob = f"{title} {desc} {domain}".lower()
        verdict = "inspiration"
        feasibility = "À évaluer sur extraits limités."
        integration = "Docs / inspiration Team — pas d'intégration immédiate."
        pros: list[str] = []
        cons: list[str] = ["extrait court / signal faible"]
        plan: str | None = None

        if "cag" in blob or "cache-augmented" in blob or "cache augmented" in blob:
            verdict = "inspiration"
            feasibility = "Proche cache dialogue Compagnon (TTL)."
            integration = "Hot docs / cache contexte court Compagnon."
            pros = ["latence"]
            cons = ["ne remplace pas RAG docs"]
            plan = "L1 : revue cache dialogue vs CAG"
        elif any(k in blob for k in ("agentic rag", "agentic", "orchestration")) and "rag" in blob:
            verdict = "inspiration"
            feasibility = "Mappe sur Team/Campus existant (OS agentique LAN)."
            integration = "Mémoire Compagnon + outils Team — pas de framework externe."
            pros = ["aligné lbg_agentic_os"]
            cons = ["risque doublon CrewAI/Dify"]
            plan = "L1 : doc mapping Agentic RAG → bus Team"
        elif "deepseek" in blob or "harness" in blob or "dsh" in blob:
            verdict = "utilisable"
            feasibility = "ADR 0020 déjà proposé (périphérie .10)."
            integration = "Spike Ollama 110 sur poste .10 ; pas 140."
            pros = ["MIT", "Ollama natif"]
            cons = ["preview", "doublon Cursor Cloud"]
            plan = "L2 : spike DSH .10 puis go/no-go dsh_headless"
        elif "voice" in blob or "tts" in blob or "asr" in blob or "eleven" in blob:
            verdict = "utilisable"
            feasibility = "Axe voice_local Compagnon déjà posé."
            integration = "TTS/ASR LAN Compagnon / dialogue."
            pros = ["local", "privacy"]
            cons = ["ops GPU/CPU"]
            plan = "L2 : spike VoiceStudio (ou équivalent) LAN"
        elif "laya" in blob:
            verdict = "inspiration"
            feasibility = "Distinguer marketing vs Laya System One (intents .111)."
            integration = "Flag LBG_ORCHESTRATOR_INTENT_LAYA — pas un chat LLM."
            pros = ["latence intents"]
            cons = ["confusion produit"]
            plan = "L1 : mesurer latence route + clarifier checkpoint"
        elif "medhic" in blob or "claude" in blob:
            verdict = "inspiration"
            feasibility = "UI/agent local exploratoire .10."
            integration = "Comparer Compagnon + ADR 0020 — pas greffe 140."
            pros = ["UX Claude-like"]
            cons = ["maintenance tierce"]
            plan = "L2 : spike .10 si utile après DSH"
        elif "geekshop" in blob or "bgm" in blob or "conseils" in blob or "abonne" in blob:
            verdict = "non_pertinent"
            feasibility = "Pas de brique technique exploitable."
            integration = "—"
            pros = []
            cons = ["bruit / tip générique"]
            plan = None
        elif domain == "mmo_world":
            verdict = "inspiration"
            feasibility = "Outils monde — sous O2 Godot/Core3."
            integration = "prime-client / Infographiste selon nature."
            pros = ["aligné O2"]
            cons = ["priorité O1 Studio"]
            plan = "L1 : classer sous PLAN_MMO_O2 si concret"

        out_leads.append(
            {
                "index": int(lead.get("index") or (len(out_leads) + 1)),
                "title": title[:160] or f"Piste {len(out_leads)+1}",
                "domain": domain[:80],
                "feasibility": feasibility,
                "integration": integration,
                "pros": pros,
                "cons": cons,
                "verdict": verdict,
                "plan": plan,
            }
        )

    # Top 3 depuis verdicts utilisable puis inspiration avec plan
    ranked = sorted(
        out_leads,
        key=lambda r: (0 if r["verdict"] == "utilisable" else 1 if r["verdict"] == "inspiration" and r.get("plan") else 2),
    )
    actions: list[dict[str, str]] = []
    for row in ranked:
        if not row.get("plan"):
            continue
        owner = "ops" if "voice" in row["domain"] else ("dev_game" if "deepseek" in row["title"].lower() or "harness" in row["title"].lower() else "pm")
        actions.append(
            {
                "title": (row.get("plan") or row["title"])[:160],
                "owner_role": owner,
                "autonomy": "L2" if row["verdict"] == "utilisable" else "L1",
                "why": f"{row['title']} → {row['verdict']}",
            }
        )
        if len(actions) >= 3:
            break
    if not actions:
        actions = [
            {
                "title": "Relancer veille avec extraits plus riches",
                "owner_role": "pm",
                "autonomy": "L1",
                "why": "signal faible sur le batch",
            }
        ]
    usable = sum(1 for r in out_leads if r["verdict"] == "utilisable")
    insp = sum(1 for r in out_leads if r["verdict"] == "inspiration")
    return {
        "summary": (
            f"Analyse heuristique Studio ({len(out_leads)} pistes) — "
            f"{usable} utilisable(s), {insp} inspiration, "
            f"{len(out_leads)-usable-insp} non pertinent(s). LLM indisponible ou timeout."
        ),
        "leads": out_leads,
        "top_3_actions": actions[:3],
        "parse_ok": True,
        "heuristic": True,
        "input_lead_count": len(leads),
    }


def last_veille() -> dict[str, Any]:
    return dict(_LAST)


def resolve_evolution_veille_workflow(task: TeamTask) -> bool:
    ctx = task.context if isinstance(task.context, dict) else {}
    if ctx.get("evolution_veille") or ctx.get("veille_batch") or ctx.get("veille_leads"):
        return True
    text = (task.objective or "").lower()
    keys = (
        "evolution_veille",
        "veille évolution",
        "veille evolution",
        "veille lbg",
        "pistes tiktok",
        "faisabilité pour l'écosystème",
        "faisabilite pour l'ecosysteme",
        "faisabilité lbg",
        "faisabilite lbg",
    )
    return any(k in text for k in keys)


def _extract_json(text: str) -> dict[str, Any] | None:
    raw = (text or "").strip()
    if not raw:
        return None
    m = re.search(r"```(?:json)?\s*(.*?)```", raw, re.DOTALL | re.IGNORECASE)
    if m:
        raw = m.group(1).strip()
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        pass
    start, end = raw.find("{"), raw.rfind("}")
    if start >= 0 and end > start:
        try:
            data = json.loads(raw[start : end + 1])
            return data if isinstance(data, dict) else None
        except json.JSONDecodeError:
            return None
    return None


def _norm_verdict(raw: str) -> str:
    v = (raw or "").strip().lower().replace(" ", "_")
    aliases = {
        "usable": "utilisable",
        "adopt": "utilisable",
        "adopter": "utilisable",
        "utile": "utilisable",
        "inspir": "inspiration",
        "inspiration_seule": "inspiration",
        "watch": "inspiration",
        "reject": "non_pertinent",
        "rejeter": "non_pertinent",
        "non-pertinent": "non_pertinent",
        "ignore": "non_pertinent",
    }
    if v in _VERDICTS:
        return v
    for k, mapped in aliases.items():
        if k in v:
            return mapped
    return "inspiration" if v else "non_pertinent"


def _normalize_payload(data: dict[str, Any] | None, *, fallback_text: str, n_input: int) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {
            "summary": (fallback_text or "")[:600] or "Réponse non structurée",
            "leads": [],
            "top_3_actions": [],
            "parse_ok": False,
            "raw_preview": (fallback_text or "")[:800],
        }
    leads_out: list[dict[str, Any]] = []
    for i, row in enumerate((data.get("leads") or [])[:12]):
        if not isinstance(row, dict):
            continue
        pros = [str(x).strip() for x in (row.get("pros") or []) if str(x).strip()][:4]
        cons = [str(x).strip() for x in (row.get("cons") or []) if str(x).strip()][:4]
        plan = row.get("plan")
        leads_out.append(
            {
                "index": int(row.get("index") or (i + 1)),
                "title": str(row.get("title") or f"Piste {i + 1}")[:160],
                "domain": str(row.get("domain") or "")[:80],
                "feasibility": str(row.get("feasibility") or "")[:500],
                "integration": str(row.get("integration") or "")[:500],
                "pros": pros,
                "cons": cons,
                "verdict": _norm_verdict(str(row.get("verdict") or "")),
                "plan": (str(plan).strip()[:500] if plan not in (None, "", "null") else None),
            }
        )
    actions: list[dict[str, str]] = []
    for a in (data.get("top_3_actions") or [])[:3]:
        if isinstance(a, dict):
            actions.append(
                {
                    "title": str(a.get("title") or "")[:160],
                    "owner_role": str(a.get("owner_role") or "pm")[:40],
                    "autonomy": str(a.get("autonomy") or "L2")[:8],
                    "why": str(a.get("why") or "")[:400],
                }
            )
        elif isinstance(a, str) and a.strip():
            actions.append({"title": a.strip()[:160], "owner_role": "pm", "autonomy": "L2", "why": ""})
    return {
        "summary": str(data.get("summary") or "")[:800],
        "leads": leads_out,
        "top_3_actions": actions,
        "parse_ok": True,
        "input_lead_count": n_input,
    }


def _leads_from_context(ctx: dict[str, Any]) -> list[dict[str, Any]]:
    raw = ctx.get("leads") or ctx.get("veille_leads") or []
    out: list[dict[str, Any]] = []
    if isinstance(raw, list):
        for i, row in enumerate(raw[:12]):
            if isinstance(row, dict):
                out.append(
                    {
                        "index": i + 1,
                        "url": str(row.get("url") or "")[:300],
                        "title": str(row.get("title") or row.get("host") or f"Piste {i + 1}")[:160],
                        "description": str(row.get("description") or row.get("desc") or "")[:480],
                        "domain": str(row.get("domain") or "general_studio")[:80],
                        "axis": str(row.get("axis") or "")[:200],
                    }
                )
            elif isinstance(row, str) and row.strip():
                out.append(
                    {
                        "index": i + 1,
                        "url": "",
                        "title": row.strip()[:160],
                        "description": "",
                        "domain": "general_studio",
                        "axis": "",
                    }
                )
    return out


def _leads_from_objective(objective: str) -> list[dict[str, Any]]:
    """Parse listes numérotées « 1. … » dans l'objectif mission."""
    text = objective or ""
    out: list[dict[str, Any]] = []
    for m in re.finditer(
        r"(?m)^\s*(\d+)\s*[.)\-–—]\s*(.+?)(?=\n\s*\d+\s*[.)\-–—]|\nLivrable|\nTravailler|\Z)",
        text,
        re.DOTALL,
    ):
        body = re.sub(r"\s+", " ", m.group(2)).strip()[:400]
        if not body:
            continue
        out.append(
            {
                "index": int(m.group(1)),
                "url": "",
                "title": body[:160],
                "description": body,
                "domain": "general_studio",
                "axis": "",
            }
        )
    return out[:12]


def _build_user_prompt(task: TeamTask) -> tuple[str, int]:
    ctx = task.context if isinstance(task.context, dict) else {}
    leads = _leads_from_context(ctx)
    if not leads:
        leads = _leads_from_objective(task.objective or "")
    parts: list[str] = [
        "Mission veille LBG — produire le tableau + top 3 actions.",
        f"Objectif brut:\n{(task.objective or '')[:3500]}",
    ]
    if leads:
        parts.append("Pistes structurées:")
        for lead in leads:
            parts.append(
                f"{lead['index']}. [{lead.get('domain')}] {lead.get('title')}"
                + (f" — {lead['url']}" if lead.get("url") else "")
                + (f"\n   Extrait: {lead['description'][:320]}" if lead.get("description") else "")
                + (f"\n   Axe: {lead['axis']}" if lead.get("axis") else "")
            )
    else:
        parts.append("(Aucune piste structurée — déduis les pistes depuis l'objectif.)")
    note = ctx.get("note") or ctx.get("human_note")
    if isinstance(note, str) and note.strip():
        parts.append(f"Note humaine: {note.strip()[:400]}")
    return "\n".join(parts), len(leads)


def _human_summary(analysis: dict[str, Any]) -> str:
    leads = analysis.get("leads") or []
    actions = analysis.get("top_3_actions") or []
    lines = [
        "Thémis — veille évolution",
        "",
        str(analysis.get("summary") or "").strip() or "(pas de résumé)",
        "",
        f"Pistes analysées : {len(leads)}",
    ]
    for lead in leads:
        if not isinstance(lead, dict):
            continue
        lines.append(
            f"  · [{lead.get('verdict')}] {lead.get('title')}"
            + (f" — {lead.get('integration')[:80]}" if lead.get("integration") else "")
        )
    if actions:
        lines.append("")
        lines.append("Top actions :")
        for i, a in enumerate(actions, 1):
            if isinstance(a, dict):
                lines.append(
                    f"  {i}. [{a.get('autonomy')}/{a.get('owner_role')}] {a.get('title')}"
                )
    return "\n".join(lines)[:4000]


def execute_evolution_veille_workflow(task: TeamTask, _dispatch: Any = None) -> dict[str, object]:
    """Analyse veille (reason_llm profile=pm) — silencieuse, sans navigateur."""
    started = time.time()
    global _LAST
    ctx = task.context if isinstance(task.context, dict) else {}

    if not reason_llm_enabled():
        out: dict[str, object] = {
            "kind": "evolution_veille_workflow",
            "ok": False,
            "skipped": True,
            "error": "REASON LLM désactivé ou aucune route",
            "agent_id": "studio_pm_themis",
            "human_summary": "Veille — REASON LLM indisponible",
            "browser_open": False,
            "silent": True,
        }
        _LAST = dict(out)
        return out

    user, n_input = _build_user_prompt(task)
    temp = float(os.environ.get("LBG_VEILLE_TEMPERATURE", "0.2"))
    # json (light .111) = structuré rapide. Fallback désactivable via LBG_VEILLE_REASON_FALLBACK=0.
    primary = os.environ.get("LBG_VEILLE_REASON_PROFILE", "json").strip() or "json"
    raw_fb = os.environ.get("LBG_VEILLE_REASON_FALLBACK", "0").strip().lower()
    fallback = "" if raw_fb in ("", "0", "false", "no", "off", "none") else raw_fb
    profiles = [primary]
    if fallback and fallback != primary:
        profiles.append(fallback)

    prev_timeout = os.environ.get("LBG_REASON_TIMEOUT_S")
    prev_max = os.environ.get("LBG_REASON_MAX_TOKENS")
    prev_light_fo = os.environ.get("LBG_REASON_LIGHT_FAILOVER_HEAVY")
    default_timeout = min(150, max(45, n_input * 15)) if n_input > 1 else 45
    default_max_tokens = min(2048, max(900, n_input * 180)) if n_input > 1 else 900
    os.environ["LBG_REASON_TIMEOUT_S"] = os.environ.get("LBG_VEILLE_TIMEOUT_S", str(default_timeout))
    os.environ["LBG_REASON_MAX_TOKENS"] = os.environ.get("LBG_VEILLE_MAX_TOKENS", str(default_max_tokens))
    # évite bascule 111→110 (12b) qui fait timeout sur batch 8 pistes
    os.environ["LBG_REASON_LIGHT_FAILOVER_HEAVY"] = os.environ.get(
        "LBG_VEILLE_LIGHT_FAILOVER_HEAVY", "0"
    )
    llm: dict[str, Any] = {}
    text = ""
    analysis: dict[str, Any] = {}
    profile_used = primary
    try:
        for profile in profiles:
            profile_used = profile
            llm = complete_reason(
                system=_SYSTEM,
                user=user,
                temperature=temp,
                profile=profile,
                prefer_cloud=False,
            )
            if not isinstance(llm, dict):
                llm = {"ok": False, "error": "llm_bad_type"}
            text = str(llm.get("text") or "")
            analysis = _normalize_payload(_extract_json(text), fallback_text=text, n_input=n_input)
            if llm.get("ok") and analysis.get("parse_ok") and (
                analysis.get("leads") or analysis.get("top_3_actions")
            ):
                break
    finally:
        if prev_timeout is None:
            os.environ.pop("LBG_REASON_TIMEOUT_S", None)
        else:
            os.environ["LBG_REASON_TIMEOUT_S"] = prev_timeout
        if prev_max is None:
            os.environ.pop("LBG_REASON_MAX_TOKENS", None)
        else:
            os.environ["LBG_REASON_MAX_TOKENS"] = prev_max
        if prev_light_fo is None:
            os.environ.pop("LBG_REASON_LIGHT_FAILOVER_HEAVY", None)
        else:
            os.environ["LBG_REASON_LIGHT_FAILOVER_HEAVY"] = prev_light_fo

    llm_ok = bool(isinstance(llm, dict) and llm.get("ok"))
    parse_ok = bool(analysis.get("parse_ok") and (analysis.get("leads") or analysis.get("top_3_actions")))
    used_heuristic = False
    if not parse_ok:
        # Toujours livrer un brief Team (timeout LLM fréquent sur batch 8).
        ctx_leads = _leads_from_context(ctx) or _leads_from_objective(task.objective or "")
        analysis = _heuristic_analysis(ctx_leads if ctx_leads else [{"title": (task.objective or "")[:120], "domain": "general_studio", "description": ""}])
        used_heuristic = True
        parse_ok = True
    ok = parse_ok  # heuristique = succès métier même si LLM KO
    summary = _human_summary(analysis)
    if used_heuristic:
        summary = "[heuristique]\n" + summary
    profile = profile_used
    out = {
        "kind": "evolution_veille_workflow",
        "ok": ok,
        "agent_id": "studio_pm_themis",
        "persona": "themis",
        "role": "pm",
        "autonomy": "L1",
        "capability": "evolution_veille",
        "llm_profile": profile,
        "model": llm.get("model") if isinstance(llm, dict) else reason_local_model(profile=profile),
        "tier": llm.get("tier") if isinstance(llm, dict) else None,
        "latency_ms": int((time.time() - started) * 1000),
        "analysis": analysis,
        "leads": analysis.get("leads") or [],
        "top_3_actions": analysis.get("top_3_actions") or [],
        "human_summary": summary,
        "browser_open": False,
        "silent": True,
        "context_echo": {
            "evolution_veille": True,
            "veille_batch": bool(ctx.get("veille_batch")),
            "input_leads": n_input,
            "heuristic": used_heuristic,
            "llm_ok": llm_ok,
        },
        "error": None
        if ok and not used_heuristic
        else (
            None
            if ok
            else (
                None
                if llm_ok
                else (llm.get("error") if isinstance(llm, dict) else "llm_failed")
            )
            or ("parse_failed" if not parse_ok else "veille_failed")
        ),
        "warning": (llm.get("error") if used_heuristic and isinstance(llm, dict) else None),
    }
    _LAST = {
        "ok": out["ok"],
        "leads_count": len(out["leads"]),  # type: ignore[arg-type]
        "actions_count": len(out["top_3_actions"]),  # type: ignore[arg-type]
        "summary": (analysis.get("summary") or "")[:240],
        "ts": time.time(),
    }
    return out
