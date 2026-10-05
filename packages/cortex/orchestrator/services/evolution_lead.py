"""Veille d'évolution silencieuse — pistes URL → brief → mission / tâche Team.

Pas d'ouverture navigateur (≠ ``search_web_open``). Le Compagnon / Pilot
ingest une URL ; le serveur fetch le titre/extrait, classe le domaine LBG,
persiste la piste, et spawn une analyse ``evolution_veille`` (Thémis + reason_llm).
"""

from __future__ import annotations

import json
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

_UA = (
    "LBG-Studios-Cortex/1.0 (evolution_lead; +https://github.com/Teome0245/LBG_Studios)"
)

_URL_RE = re.compile(r"https?://[^\s<>\"']+", re.I)

# Domaines → axe + rôles suggérés (pour le brief LLM — PAS d'@mentions persona
# dans l'objectif mission : ça empoisonne resolve_presence_agent_id via le blob).
_DOMAIN_HINTS: list[tuple[re.Pattern[str], str, str, list[str]]] = [
    (
        re.compile(
            r"(?i)\b(map|terrain|heightmap|river|tilemap|world.?gen|godot|swg|core3|"
            r"mightofmerchants|canvas.?of.?kings|zone.?bridge)\b"
        ),
        "mmo_world",
        "création / outils de cartes & monde MMO (Prime / Godot / Core3)",
        ["pm", "dev_game", "dev_godot"],
    ),
    (
        re.compile(r"(?i)\b(voice|tts|asr|elevenlabs|voicestudio|clonage.?de.?voix|doublage)\b"),
        "voice_local",
        "voix / TTS-ASR local pour Compagnon (LAN, pas cloud ElevenLabs)",
        ["pm", "ops"],
    ),
    (
        re.compile(
            r"(?i)\b(n8n|langgraph|crewai|autogen|multi.?agent|workflow.?agent|"
            r"agentic|orchestration|rag|cag)\b"
        ),
        "agent_orchestration",
        "orchestration agents / workflows (inspiration Team Campus, pas remplacement)",
        ["pm", "qa", "ops"],
    ),
    (
        re.compile(r"(?i)\b(comfy|lora|stable.?diffusion|sprite|asset|infograph)\b"),
        "assets",
        "pipeline assets / Infographiste",
        ["pm", "dev_game"],
    ),
]


def leads_enabled() -> bool:
    raw = os.environ.get("LBG_EVOLUTION_LEADS", "1").strip().lower()
    return raw not in ("0", "false", "no", "off")


def leads_path() -> Path:
    raw = os.environ.get("LBG_EVOLUTION_LEADS_PATH", "").strip()
    if raw:
        return Path(raw)
    return Path("/var/lib/lbg/evolution/leads.jsonl")


def extract_urls(text: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for m in _URL_RE.finditer(text or ""):
        u = m.group(0).rstrip(").,;]")
        if u not in seen:
            seen.add(u)
            found.append(u)
    return found


def _safe_host(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower()
    except Exception:
        return ""


def _fetch_meta(url: str, *, timeout_s: float = 12.0) -> dict[str, Any]:
    """Fetch HTTP silencieux — titre / description (TikTok, pages HTML)."""
    out: dict[str, Any] = {
        "url": url,
        "ok": False,
        "host": _safe_host(url),
        "title": None,
        "description": None,
        "error": None,
    }
    try:
        with httpx.Client(
            timeout=timeout_s,
            follow_redirects=True,
            headers={"User-Agent": _UA, "Accept-Language": "fr,en;q=0.8"},
        ) as client:
            r = client.get(url)
        out["status_code"] = r.status_code
        if r.status_code >= 400:
            out["error"] = f"HTTP {r.status_code}"
            return out
        text = r.text or ""
        for pat in (
            r'"desc":"((?:[^"\\]|\\.){8,500})"',
            r'"og:description"\s+content="([^"]{8,400})"',
            r'property="og:description"\s+content="([^"]{8,400})"',
            r'<meta[^>]+name="description"[^>]+content="([^"]{8,400})"',
        ):
            m = re.search(pat, text, re.I)
            if m:
                desc = _unescape_js(m.group(1))
                if desc and len(desc) > 8:
                    out["description"] = desc[:480]
                    break
        for pat in (
            r'"nickname":"((?:[^"\\]|\\.){2,80})"',
            r'property="og:title"\s+content="([^"]{3,200})"',
            r"<title>([^<]{3,200})</title>",
        ):
            m = re.search(pat, text, re.I)
            if m:
                title = _unescape_js(m.group(1)).strip()
                if title and "tiktok" not in title.lower():
                    out["title"] = title[:160]
                    break
        out["ok"] = bool(out.get("description") or out.get("title") or r.status_code < 400)
        if out["ok"] and not out.get("error"):
            out["error"] = None
        return out
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {e}"
        return out


def _unescape_js(s: str) -> str:
    try:
        return json.loads(f'"{s}"')
    except Exception:
        return (
            s.replace("\\n", " ")
            .replace("\\/", "/")
            .replace('\\"', '"')
            .replace("\\u0026", "&")
        )


def classify_domain(url: str, blob: str) -> dict[str, Any]:
    text = f"{url} {blob}"
    for rx, domain, axis, roles in _DOMAIN_HINTS:
        if rx.search(text):
            return {"domain": domain, "axis": axis, "suggested_roles": roles}
    return {
        "domain": "general_studio",
        "axis": "évolution générale Studio / Team / MMO",
        "suggested_roles": ["pm", "qa"],
    }


def build_mission_objective(
    *,
    url: str,
    meta: dict[str, Any],
    domain_info: dict[str, Any],
    note: str = "",
) -> str:
    """Objectif mission — mots-clés « Veille évolution » (pas Sprint / pas @persona)."""
    title = meta.get("title") or meta.get("host") or "piste"
    desc = (meta.get("description") or "").strip()
    note_s = (note or "").strip()
    lines = [
        "Veille évolution LBG (silencieuse : pas d'onglet navigateur).",
        f"Source : {url}",
        f"Titre / auteur : {title}",
    ]
    if desc:
        lines.append(f"Extrait : {desc[:320]}")
    if note_s:
        lines.append(f"Note humaine : {note_s[:240]}")
    lines.extend(
        [
            f"Axe : {domain_info.get('axis')}",
            "Livrable attendu (brief court) :",
            "1) faisabilité pour l'écosystème LBG (Prime / Godot / Core3 / Compagnon / Team) ;",
            "2) intégration possible (où brancher) ;",
            "3) avantages / inconvénients ;",
            "4) verdict : utilisable / inspiration seule / non pertinent ;",
            "5) si pertinent : plan d'implémentation borné (L1 sonde vs L2 RFC).",
            "Ne pas ouvrir le navigateur du poste ; travailler sur l'extrait + connaissances Studio.",
        ]
    )
    return "\n".join(lines)


def build_batch_mission_objective(
    leads: list[dict[str, Any]],
    *,
    note: str = "",
) -> str:
    lines = [
        "Veille évolution LBG batch (silencieuse, PAS d'onglet navigateur).",
        "Pour CHAQUE piste : faisabilité LBG, intégration possible, avantages/inconvénients,",
        "verdict (utilisable / inspiration / non pertinent), plan borné si oui.",
        "Pistes :",
    ]
    for i, lead in enumerate(leads[:12], 1):
        title = lead.get("title") or lead.get("host") or "piste"
        domain = lead.get("domain") or "general_studio"
        desc = (lead.get("description") or "")[:160]
        url = lead.get("url") or ""
        lines.append(f"{i}. [{domain}] {title}" + (f" — {url}" if url else ""))
        if desc:
            lines.append(f"   Extrait : {desc}")
    if note.strip():
        lines.append(f"Note humaine : {note.strip()[:240]}")
    lines.extend(
        [
            "Livrable : tableau synthèse + top 3 actions concrètes pour Compagnon / Team / MMO / infra.",
            "Travailler sur extraits + connaissances Studio ; ne pas ouvrir le navigateur du poste.",
        ]
    )
    return "\n".join(lines)


def _append_lead(record: dict[str, Any]) -> None:
    path = leads_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass


def list_leads(*, limit: int = 20) -> list[dict[str, Any]]:
    path = leads_path()
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
        if len(rows) >= max(1, limit):
            break
    return rows


def _spawn_veille_mission(
    *,
    objective: str,
    leads: list[dict[str, Any]],
    actor_id: str,
    auto_act: bool = True,
) -> dict[str, Any]:
    """Crée une mission Campus avec **une** tâche PM evolution_veille (pas smoke/ops)."""
    from team import campus_conductor
    from team import store as team_store

    if not team_store.team_enabled():
        return {"ok": False, "error": "team_disabled"}

    mission_id = str(uuid.uuid4())
    ctx: dict[str, Any] = {
        "evolution_veille": True,
        "veille_batch": len(leads) > 1,
        "presence_agent_id": "studio_pm_themis",
        "leads": leads,
        "silent": True,
        "browser_open": False,
        "_campus_mission_id": mission_id,
        "_campus_mission_objective": objective[:500],
    }
    task = team_store.create_task(
        role="pm",
        objective=objective[:4000],
        actor_id=actor_id,
        priority="high",
        approval_required=False,
        context=ctx,
    )
    mission = {
        "id": mission_id,
        "objective": objective,
        "status": "open",
        "created_ts": time.time(),
        "task_ids": [task.id],
        "dry_run": False,
        "kind": "evolution_veille",
    }
    campus_conductor._set_mission(mission)
    act_report = None
    if auto_act and campus_conductor.enabled():
        act_report = campus_conductor.act(dry_run=False, max_starts_override=2)
        mission["status"] = "driving"
        campus_conductor._set_mission(mission)
    return {
        "ok": True,
        "mission": mission,
        "created": [{"task_id": task.id, "role": "pm", "objective": objective[:200], "context": ctx}],
        "act": act_report,
    }


def ingest_lead(
    *,
    url: str | None = None,
    text: str | None = None,
    note: str = "",
    spawn_mission: bool = True,
    dry_run: bool = False,
    actor_id: str = "compagnon:evolution",
) -> dict[str, Any]:
    """Ingest URL (ou texte contenant une URL) → meta → mission veille."""
    if not leads_enabled():
        return {"ok": False, "error": "evolution_leads_disabled"}

    urls: list[str] = []
    if url and str(url).strip():
        urls.append(str(url).strip())
    urls.extend(extract_urls(text or ""))
    seen: set[str] = set()
    uniq: list[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            uniq.append(u)
    if not uniq:
        return {"ok": False, "error": "no_url"}

    if len(uniq) > 1:
        return ingest_leads_batch(
            urls=uniq,
            note=note,
            spawn_mission=spawn_mission,
            dry_run=dry_run,
            actor_id=actor_id,
        )

    primary = uniq[0]
    meta = _fetch_meta(primary)
    blob = " ".join(
        str(x)
        for x in (meta.get("title"), meta.get("description"), note, text or "")
        if x
    )
    domain_info = classify_domain(primary, blob)
    objective = build_mission_objective(
        url=primary, meta=meta, domain_info=domain_info, note=note or (text or "")
    )
    lead_row = {
        "url": primary,
        "title": meta.get("title") or meta.get("host") or "piste",
        "description": meta.get("description") or "",
        "domain": domain_info.get("domain"),
        "axis": domain_info.get("axis"),
        "host": meta.get("host"),
    }
    lead_id = uuid.uuid4().hex[:12]
    record: dict[str, Any] = {
        "id": lead_id,
        "ts": time.time(),
        "actor_id": actor_id,
        "url": primary,
        "urls": uniq[:5],
        "meta": {
            k: meta.get(k)
            for k in ("ok", "host", "title", "description", "error", "status_code")
        },
        "domain": domain_info.get("domain"),
        "axis": domain_info.get("axis"),
        "suggested_roles": domain_info.get("suggested_roles"),
        "objective_preview": objective[:500],
        "spawn_mission": bool(spawn_mission) and not dry_run,
        "silent": True,
        "browser_open": False,
    }

    mission_out: dict[str, Any] | None = None
    if spawn_mission and not dry_run:
        try:
            mission_out = _spawn_veille_mission(
                objective=objective,
                leads=[lead_row],
                actor_id=actor_id,
                auto_act=True,
            )
            if not mission_out.get("ok"):
                record["mission_error"] = mission_out.get("error") or "spawn_failed"
            else:
                mid = (mission_out.get("mission") or {}).get("id")
                record["mission"] = {
                    "ok": True,
                    "mission_id": mid,
                    "created_count": len(mission_out.get("created") or []),
                    "kind": "evolution_veille",
                }
        except Exception as e:
            record["mission_error"] = f"{type(e).__name__}: {e}"
    elif dry_run:
        record["dry_run"] = True

    _append_lead(record)
    human = _human_ack(record, meta, domain_info)
    return {
        "ok": True,
        "lead_id": lead_id,
        "silent": True,
        "browser_open": False,
        "url": primary,
        "meta": record["meta"],
        "domain": domain_info,
        "objective": objective,
        "mission": record.get("mission"),
        "mission_error": record.get("mission_error"),
        "human_summary": human,
        "raw_mission": mission_out,
    }


def ingest_leads_batch(
    *,
    urls: list[str] | None = None,
    text: str | None = None,
    note: str = "",
    spawn_mission: bool = True,
    dry_run: bool = False,
    actor_id: str = "compagnon:evolution",
) -> dict[str, Any]:
    """Ingest plusieurs URLs → une mission veille groupée (tableau + top 3)."""
    if not leads_enabled():
        return {"ok": False, "error": "evolution_leads_disabled"}

    collected: list[str] = []
    for u in urls or []:
        if u and str(u).strip():
            collected.append(str(u).strip())
    collected.extend(extract_urls(text or ""))
    seen: set[str] = set()
    uniq: list[str] = []
    for u in collected:
        if u not in seen:
            seen.add(u)
            uniq.append(u)
    if not uniq:
        return {"ok": False, "error": "no_url"}

    leads: list[dict[str, Any]] = []
    lead_ids: list[str] = []
    for primary in uniq[:12]:
        meta = _fetch_meta(primary)
        blob = " ".join(
            str(x)
            for x in (meta.get("title"), meta.get("description"), note)
            if x
        )
        domain_info = classify_domain(primary, blob)
        lead_id = uuid.uuid4().hex[:12]
        lead_ids.append(lead_id)
        lead_row = {
            "url": primary,
            "title": meta.get("title") or meta.get("host") or "piste",
            "description": meta.get("description") or "",
            "domain": domain_info.get("domain"),
            "axis": domain_info.get("axis"),
            "host": meta.get("host"),
        }
        leads.append(lead_row)
        _append_lead(
            {
                "id": lead_id,
                "ts": time.time(),
                "actor_id": actor_id,
                "url": primary,
                "meta": {
                    k: meta.get(k)
                    for k in ("ok", "host", "title", "description", "error", "status_code")
                },
                "domain": domain_info.get("domain"),
                "axis": domain_info.get("axis"),
                "batch": True,
                "silent": True,
                "browser_open": False,
            }
        )

    objective = build_batch_mission_objective(leads, note=note)
    mission_out: dict[str, Any] | None = None
    mission_rec: dict[str, Any] | None = None
    mission_error: str | None = None
    if spawn_mission and not dry_run:
        try:
            mission_out = _spawn_veille_mission(
                objective=objective,
                leads=leads,
                actor_id=actor_id,
                auto_act=True,
            )
            if not mission_out.get("ok"):
                mission_error = str(mission_out.get("error") or "spawn_failed")
            else:
                mid = (mission_out.get("mission") or {}).get("id")
                mission_rec = {
                    "ok": True,
                    "mission_id": mid,
                    "created_count": len(mission_out.get("created") or []),
                    "kind": "evolution_veille",
                }
        except Exception as e:
            mission_error = f"{type(e).__name__}: {e}"

    human_parts = [
        f"Batch veille : {len(leads)} piste(s) notée(s) en silence.",
        "Pas d'onglet navigateur ouvert.",
    ]
    if mission_rec and mission_rec.get("ok"):
        human_parts.append(
            f"Mission Team lancée (`{mission_rec.get('mission_id')}`) — analyse tableau + top 3."
        )
        human_parts.append(
            "Je te ressortirai le brief quand la Team aura livré (Pilot `#/team`)."
        )
    elif mission_error:
        human_parts.append(f"Mission non lancée : {mission_error}.")
    elif dry_run:
        human_parts.append("Dry-run : mission non spawnée.")

    return {
        "ok": True,
        "lead_ids": lead_ids,
        "count": len(leads),
        "silent": True,
        "browser_open": False,
        "leads": leads,
        "objective": objective,
        "mission": mission_rec,
        "mission_error": mission_error,
        "human_summary": " ".join(human_parts),
        "raw_mission": mission_out,
        "dry_run": bool(dry_run),
    }


def _human_ack(record: dict[str, Any], meta: dict[str, Any], domain_info: dict[str, Any]) -> str:
    title = meta.get("title") or meta.get("host") or "cette piste"
    axis = domain_info.get("axis") or "évolution Studio"
    parts = [
        f"Piste notée en silence ({title}) — axe « {axis} ».",
        "Pas d'onglet navigateur ouvert.",
    ]
    if record.get("mission") and record["mission"].get("ok") is not False:
        mid = record["mission"].get("mission_id")
        parts.append(
            f"Mission Team lancée"
            + (f" (`{mid}`)" if mid else "")
            + " : analyse faisabilité / intégration / +/- / verdict."
        )
        parts.append(
            "Je te ressortirai le brief quand la Team aura produit le livrable (Pilot `#/team`)."
        )
    elif record.get("mission_error"):
        parts.append(f"Mission non lancée : {record['mission_error']}.")
    elif record.get("dry_run"):
        parts.append("Dry-run : mission non spawnée.")
    else:
        parts.append("Piste enregistrée sans mission (spawn_mission=false).")
    return " ".join(parts)
