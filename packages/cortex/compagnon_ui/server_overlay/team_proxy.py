"""Proxy HTTP Orch UI (LBG_IA) → Cortex Pilot (.140)."""

from __future__ import annotations

import logging
import re
import time
from typing import Any

import httpx

from src.http_timeouts import httpx_timeout
from src.services.campus_recall import campus_snapshot_from_mission_data
from src.services.team_routing import extract_team_mentions, strip_team_prefix
from src.settings import get_settings

# Overlay monorepo : même dossier ; runtime Orch greffe aussi sous src.services.
try:
    from infra_lan_intent import (  # type: ignore
        wants_infra_lan_brief as _wants_infra_lan_brief_core,
        wants_infra_lan_mission as _wants_infra_lan_mission_core,
    )
except ImportError:  # pragma: no cover — greffe Orch
    from src.services.infra_lan_intent import (  # type: ignore
        wants_infra_lan_brief as _wants_infra_lan_brief_core,
        wants_infra_lan_mission as _wants_infra_lan_mission_core,
    )

logger = logging.getLogger("lbg.team_proxy")

_L2_APPROVAL_RE = re.compile(
    r"(?i)\b("
    r"l2|hitl|approbation|approbations|validation\s+humaine|"
    r"token\s+team|en\s+attente\s+d.?approbation|valider\s+team"
    r")\b"
)


async def _attach_pending_l2_async(out: dict[str, Any], reply: str) -> dict[str, Any]:
    try:
        from src.services.team_actions import list_pending_approvals

        pending = await list_pending_approvals(limit=10)
    except Exception:
        logger.debug("pending approvals attach skipped", exc_info=True)
        out["content"] = reply
        out["response"] = reply
        return out
    if not pending.get("approval"):
        out["content"] = reply
        out["response"] = reply
        return out
    n = pending.get("count") or 0
    out["approval"] = pending["approval"]
    suffix = (
        f"\n\n**Approbations L2 en attente** : {n} — cartes ci-dessous, "
        "Pilot `#/team/office` ou `#/team/fleet`."
    )
    out["content"] = reply.rstrip() + suffix
    out["response"] = out["content"]
    return out


_STATUS_RE = re.compile(
    r"(?i)\b(status|état|etat|santé|sante|health)\b.{0,50}\b("
    r"orchestrateur|campus|systemd|ops|team|pilot|jobs"
    r")\b|"
    r"\b(jobs systemd|agents ops|ops disponibles)\b|"
    r"\b(compte\s+rendu|actions?\s+en\s+cours|que\s+fait|que\s+font).{0,80}\b("
    r"team|équipe|equipe|campus|agents?"
    r")\b|"
    r"\b(team|équipe|equipe)\b.{0,40}\b(status|état|etat|en\s+cours|compte\s+rendu)\b"
)
_MISSION_RE = re.compile(
    r"(?i)\b(mission|propose|spawn|automatiser|planif|créer|creer)\b"
)
_DISK_WARN_PCT = 80

_MULTI_MISSION_HINT_RE = re.compile(
    r"(?i)\b("
    r"max\s*\d+\s*t[aâ]ches?|"
    r"pas\s+de\s+double|"
    r"audit\s+utile|"
    r"triage|"
    r"smoke\s+lan|"
    r"healthz"
    r")\b"
)


def is_multi_role_campus_mission(text: str) -> bool:
    """Mission Campus multi-agents — ne pas réduire à un brief Infra/Prime."""
    body = text or ""
    mentions = extract_team_mentions(body)
    if len(mentions) >= 2:
        return True
    low = body.lower()
    if not _MISSION_RE.search(low):
        return False
    # Ex. « team: mission … @argus … ; @hephaistos … » déjà couvert par ≥2.
    # Sinon : mission + contrainte multi-rôle + au moins un @Team.
    if mentions and _MULTI_MISSION_HINT_RE.search(low):
        return True
    return False


def wants_infra_lan_brief(text: str) -> bool:
    """True si la demande vise RAM/disk LAN / Proxmox (pas healthz).

    Prime / .246 seuls (hébergement MMO, mémoire agent) → False.
    """
    if is_multi_role_campus_mission(text):
        return False
    return _wants_infra_lan_brief_core(text)


def wants_infra_lan_mission(text: str) -> bool:
    """Spawn Campus seulement si action ops — pas une lecture seule disk/RAM."""
    return _wants_infra_lan_mission_core(
        text,
        team_mentions=extract_team_mentions(text or ""),
        multi_role_campus=is_multi_role_campus_mission(text),
    )


def _parse_max_tasks(text: str, default: int = 6) -> int:
    m = re.search(r"(?i)max\s*(\d+)\s*t[aâ]ches?", text or "")
    if not m:
        return default
    try:
        return max(1, min(12, int(m.group(1))))
    except ValueError:
        return default


def _format_encounter(output: dict[str, Any], routed_to: Any) -> str | None:
    enc = output.get("encounter")
    if not isinstance(enc, dict):
        enc = output.get("encounter_state") if isinstance(output.get("encounter_state"), dict) else None
    if not isinstance(enc, dict):
        return None
    narrative = enc.get("narrative")
    opponent = enc.get("opponent") or "adversaire"
    status = enc.get("status") or "?"
    hp = enc.get("hp") if isinstance(enc.get("hp"), dict) else {}
    suggested = enc.get("suggested_actions") if isinstance(enc.get("suggested_actions"), list) else []
    lines = [
        f"**Réponse jeu (combat)** — routé vers `{routed_to or 'agent.combat'}` "
        "(pas une action remédiation Studio).",
    ]
    if isinstance(narrative, str) and narrative.strip():
        lines.append(narrative.strip())
    else:
        lines.append(f"Affrontement vs {opponent} — statut **{status}**.")
    if hp:
        lines.append(
            f"- PV : joueur {hp.get('player', '?')} / adversaire {hp.get('opponent', '?')}"
        )
    if suggested:
        lines.append("- Actions suggérées : " + ", ".join(str(x) for x in suggested[:6]))
    lines.append(
        "\nPour la remédiation infra Studio, utilise `@héphaïstos` / "
        "`team: mission … remédiation` ou Pilot `#/jobs` (pas `@remediate` seul via Team route)."
    )
    return "\n".join(lines)


def _format_status_dict(status: dict[str, Any], routed_to: Any) -> str | None:
    summary = status.get("summary") or status.get("message")
    if isinstance(summary, str) and summary.strip():
        return summary.strip()
    # team_status / infra probes sans champ summary
    by_status = status.get("by_status")
    if isinstance(by_status, dict) and by_status:
        parts = [f"{k}={v}" for k, v in list(by_status.items())[:8]]
        return (
            f"**Team status** (`{routed_to or 'agent.team_status'}`) — "
            + ", ".join(parts)
            + f" · queued={status.get('queued_count', '?')} running={status.get('running_count', '?')}"
        )
    probes = status.get("probes")
    if isinstance(probes, list) and probes:
        ok = status.get("ok_count")
        total = status.get("total") or len(probes)
        return f"**Infra sondes** — OK {ok}/{total} (`{routed_to or 'agent.infra_status'}`)."
    return None


def _extract_reply(payload: dict[str, Any]) -> str:
    result = payload.get("result")
    if isinstance(result, dict):
        routed = result.get("routed_to")
        intent = result.get("intent")
        output = result.get("output")
        if isinstance(output, dict):
            for key in ("reply", "text", "content", "message"):
                val = output.get(key)
                if isinstance(val, str) and val.strip():
                    return val.strip()
            remote = output.get("remote")
            if isinstance(remote, dict):
                for key in ("reply", "text", "content", "message", "stdout"):
                    val = remote.get(key)
                    if isinstance(val, str) and val.strip():
                        return val.strip()
            status = output.get("status")
            if isinstance(status, dict):
                formatted = _format_status_dict(status, routed)
                if formatted:
                    return formatted
            encounter_txt = _format_encounter(output, routed)
            if encounter_txt:
                return encounter_txt
            quest = output.get("quest")
            if isinstance(quest, dict):
                title = quest.get("title") or quest.get("id")
                if title:
                    return (
                        f"Routé vers quête jeu (`{routed}`) — pas Team Campus. "
                        f"Titre : {title}. Utilise `team: mission …` ou Pilot `#/team`."
                    )
            # Dernier recours structuré (évite le message « format inattendu » opaque)
            handler = output.get("handler") or output.get("agent") or output.get("capability")
            req = output.get("request_text")
            bits = [f"Pilot a répondu via `{routed or intent or '—'}`"]
            if handler:
                bits.append(f"handler={handler}")
            if isinstance(req, str) and req.strip():
                bits.append(f"texte « {req.strip()[:80]} »")
            bits.append("— pas de champ reply exploitable. Détail : Pilot `.140:8080`.")
            return " ".join(bits)
    err = payload.get("error")
    if isinstance(err, str) and err.strip():
        return f"Erreur Team Cortex : {err.strip()}"
    return "Réponse Team reçue (format inattendu). Consulte le Pilot `.140:8080` pour le détail."


def _format_campus_status(data: dict[str, Any]) -> str:
    if data.get("ok") is False:
        return f"Campus status KO : {data.get('error') or 'erreur'}"
    dec = data.get("decision") or {}
    miss = data.get("mission") or {}
    lines = [
        "**Campus Team — état réel**",
        f"- mode : {dec.get('mode') or '—'} ({dec.get('reason') or '—'})",
        f"- busy agents : {data.get('busy_agent_count', '?')}",
        f"- file (queued) : {data.get('queued_count', '?')}",
        f"- running : {data.get('running_count', '?')}",
    ]
    if miss.get("id"):
        lines.append(
            f"- mission ouverte : {miss.get('status', '?')} — "
            f"{str(miss.get('objective') or '')[:120]}"
        )
    lr = data.get("last_report") or {}
    if lr.get("outcome"):
        lines.append(f"- dernier rapport : {lr.get('outcome')} ({lr.get('acted_as') or '—'})")
    return "\n".join(lines)


def _format_campus_mission(data: dict[str, Any], objective: str) -> str:
    if data.get("ok") is False:
        return f"Mission Campus KO : {data.get('error') or 'erreur'}"
    m = data.get("mission") or {}
    created = data.get("created") or []
    act = data.get("act") or {}
    snap = campus_snapshot_from_mission_data(data, objective)
    lines = [
        "**Mission Campus lancée**",
        f"- **mission_id** : `{snap.get('mission_id') or '—'}`",
        f"- objectif : {str(m.get('objective') or objective)[:200]}",
        f"- statut : {m.get('status', '?')}",
        f"- tâches créées : {len(created)}",
    ]
    task_ids = snap.get("task_ids") or []
    if task_ids:
        lines.append("- **task_ids** :")
        for tid in task_ids:
            role = ""
            for item in created:
                if isinstance(item, dict) and str(item.get("task_id") or item.get("id") or "") == tid:
                    role = str(item.get("role") or "")
                    break
            suffix = f" ({role})" if role else ""
            lines.append(f"  - `{tid}`{suffix}")
    elif created:
        lines.append("- ids : en attente (relance `team: status` ou demande « retrouve l’id de la tâche »)")
    if act:
        lines.append(f"- conduite (act) : {act.get('outcome', '—')}")
    lines.append("\nSuivi : Pilot `#/team/office` ou `#/team`.")
    return "\n".join(lines)


def format_infra_lan_brief(snapshot: dict[str, Any], *, focus: str = "") -> str:
    """Synthèse Héphaïstos depuis snapshot Cockpit (RAM/disk réels)."""
    infra = snapshot.get("infra") if isinstance(snapshot.get("infra"), list) else []
    focus_l = (focus or "").lower()
    want_front = any(
        k in focus_l for k in (".100", "192.168.0.100", "front", "web-100", "lbg-web", "compagnon")
    )
    want_prime = any(k in focus_l for k in ("prime", "246", "192.168.0.246"))
    want_disk = any(
        k in focus_l for k in ("disk", "disque", "stockage", "occupation", "proxmox", "local-lvm")
    )
    # Disk générique sans hôte nommé → garder le focus Prime (comportement historique)
    if want_disk and not want_front and not want_prime:
        want_prime = True

    lines = [
        "**Héphaïstos — point Infra LAN (Cockpit)**",
        "",
        "| Hôte | RAM | Disk | Load |",
        "|------|-----|------|------|",
    ]
    alerts: list[str] = []
    for h in infra:
        if not isinstance(h, dict):
            continue
        label = h.get("label") or h.get("server_id") or h.get("host") or "?"
        host = h.get("host") or ""
        mem = h.get("mem_used_pct")
        disk = h.get("disk_used_pct")
        load = str(h.get("load_avg") or "—").split()[0] if h.get("load_avg") else "—"
        ok = "●" if h.get("ok") else "○"
        mem_s = f"{mem}%" if mem is not None else "—"
        disk_s = f"{disk}%" if disk is not None else "—"
        mark = ""
        if isinstance(disk, (int, float)) and disk >= _DISK_WARN_PCT:
            mark = " ⚠️"
            alerts.append(f"**{label}** (`{host}`) disk **{disk}%** — seuil {_DISK_WARN_PCT}%")
        if isinstance(mem, (int, float)) and mem >= 90:
            alerts.append(f"**{label}** (`{host}`) RAM **{mem}%**")
        lines.append(f"| {ok} {label} `{host}` | {mem_s} | {disk_s}{mark} | {load} |")

    if not infra:
        lines.append("| — | snapshot vide | — | — |")

    if alerts:
        lines.extend(["", "**Alertes** :"])
        for a in alerts:
            lines.append(f"- {a}")
    elif want_prime or want_front:
        lines.append("")
        lines.append("Aucune alerte disk ≥80 % sur le snapshot courant.")

    def _append_focus(*, match_host: str, label_needles: tuple[str, ...], title: str, prime: bool) -> None:
        for h in infra:
            if not isinstance(h, dict):
                continue
            host = str(h.get("host") or "")
            label = str(h.get("label") or "").lower()
            if match_host not in host and not any(n in label for n in label_needles):
                continue
            disk = h.get("disk_used_pct")
            used = h.get("disk_used_mb")
            total = h.get("disk_total_mb")
            detail = f"{title} `{host}` — disk {disk}%"
            if used is not None and total is not None:
                detail += f" ({used}/{total} Mo)"
            lines.extend(["", f"**Focus {title}** : {detail}."])
            if isinstance(disk, (int, float)) and disk >= _DISK_WARN_PCT:
                if prime:
                    lines.append(
                        "Action : sonde Proxmox thin `local-lvm` (runbook stockage Prime) "
                        "+ nettoyage / agrandissement si pool plein."
                    )
                else:
                    lines.append(
                        "Action : Docker prune / logs / images orphelines sur le guest "
                        "(remédiation consultative L1) si disk élevé."
                    )
            break

    if want_front:
        _append_focus(
            match_host="192.168.0.100",
            label_needles=("front", "web-100", "lbg-web"),
            title="Front .100",
            prime=False,
        )
    if want_prime:
        _append_focus(
            match_host="192.168.0.246",
            label_needles=("prime",),
            title="Prime",
            prime=True,
        )

    lines.extend(
        [
            "",
            "_Source : `GET /monitor/cockpit` (P03) — pas les healthz HTTP génériques._",
        ]
    )
    return "\n".join(lines)


def _mission_objective_for_infra(body_text: str) -> str:
    mentions = extract_team_mentions(body_text)
    owner = "@hephaistos" if "hephaistos" in mentions or not mentions else f"@{mentions[0]}"
    return (
        f"{owner} — point Infra LAN / Proxmox : vérifier disk Prime (.246) et pool thin "
        f"local-lvm ; remonter alertes + actions. Contexte Orch : {body_text[:240]}"
    )


_URL_RE = re.compile(r"https?://[^\s<>\"']+", re.I)
_EVOLUTION_HINT_RE = re.compile(
    r"(?i)\b("
    r"evolution|évolution|amelior|amélior|piste|idee|idée|"
    r"faisabil|integr|intégr|utilisable|inspiration|"
    r"veille|pour\s+(?:l['\u2019])?ecosysteme|pour\s+lbg|"
    r"map|carte|voix|voice|tiktok|github\.com"
    r")\b"
)


def _wants_evolution_lead(text: str) -> bool:
    """URL de piste d'amélioration → veille silencieuse (pas search_web / onglet)."""
    body = text or ""
    if not _URL_RE.search(body):
        return False
    if _EVOLUTION_HINT_RE.search(body):
        return True
    # URL seule (TikTok / GitHub / doc) collée dans le chat Team = piste par défaut
    host = ""
    m = _URL_RE.search(body)
    if m:
        try:
            from urllib.parse import urlparse

            host = (urlparse(m.group(0)).hostname or "").lower()
        except Exception:
            host = ""
    if any(h in host for h in ("tiktok.com", "github.com", "gitlab.com", "notion.so", "readthedocs")):
        return True
    # Message quasi = URL seule
    stripped = _URL_RE.sub("", body).strip()
    return len(stripped) < 40


async def _post_evolution_lead(
    base: str,
    timeout: httpx.Timeout,
    *,
    text: str,
    conversation_id: str | None,
) -> dict[str, Any]:
    body = {
        "text": text,
        "spawn_mission": True,
        "dry_run": False,
        "actor_id": f"orch-ui:{(conversation_id or 'default').strip() or 'default'}",
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(f"{base}/v1/pilot/team/evolution/lead", json=body)
    if r.status_code >= 400:
        raise RuntimeError(f"evolution/lead HTTP {r.status_code}: {r.text[:200]}")
    data = r.json()
    if not isinstance(data, dict):
        raise RuntimeError("evolution/lead non-JSON")
    return data


async def _get_campus_status(base: str, timeout: httpx.Timeout) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(f"{base}/v1/pilot/team/campus/status")
    if r.status_code >= 400:
        raise RuntimeError(f"Campus status HTTP {r.status_code}")
    data = r.json()
    if not isinstance(data, dict):
        raise RuntimeError("Campus status non-JSON")
    return data


async def _post_campus_mission(
    base: str,
    timeout: httpx.Timeout,
    *,
    objective: str,
    max_tasks: int | None = None,
) -> dict[str, Any]:
    n = int(max_tasks) if max_tasks is not None else _parse_max_tasks(objective, 6)
    body = {
        "objective": objective,
        "dry_run": False,
        "auto_act": True,
        "max_tasks": max(1, min(12, n)),
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(f"{base}/v1/pilot/team/campus/mission", json=body)
    if r.status_code >= 400:
        raise RuntimeError(f"Campus mission HTTP {r.status_code}: {r.text[:200]}")
    data = r.json()
    if not isinstance(data, dict):
        raise RuntimeError("Campus mission non-JSON")
    return data


async def call_cortex_pilot_route(
    *,
    prompt: str,
    conversation_id: str | None,
) -> dict[str, Any]:
    settings = get_settings()
    base = str(settings.cortex_pilot_url or "").rstrip("/")
    if not base:
        raise RuntimeError("CORTEX_PILOT_URL non configuré")

    text, _forced = strip_team_prefix(prompt)
    actor = f"orch-ui:{(conversation_id or 'default').strip() or 'default'}"
    timeout = httpx_timeout(read=float(settings.cortex_pilot_timeout_s))
    t0 = time.perf_counter()

    body_text = (text or prompt or "").strip()
    low = body_text.lower()

    # Veille silencieuse : URL piste → fetch serveur + mission analyse (pas d'onglet)
    if _wants_evolution_lead(body_text):
        data = await _post_evolution_lead(
            base, timeout, text=body_text, conversation_id=conversation_id
        )
        latency = time.perf_counter() - t0
        reply = str(data.get("human_summary") or data.get("objective") or "Piste notée.")
        return {
            "role": "assistant",
            "content": reply,
            "response": reply,
            "source": "team",
            "model": "evolution-lead",
            "model_used": "evolution-lead",
            "provider": "cortex",
            "latency": latency,
            "trace_id": data.get("lead_id"),
            "raw": data,
            "agent_action": None,
            "campus_meta": data.get("mission"),
        }

    if _L2_APPROVAL_RE.search(low):
        from src.services.team_actions import list_pending_approvals

        pending = await list_pending_approvals(limit=10)
        latency = time.perf_counter() - t0
        n = int(pending.get("count") or 0)
        tasks = pending.get("tasks") if isinstance(pending.get("tasks"), list) else []
        if n:
            lines = [f"**{n} validation(s) L2** en attente (même liste que Pilot Fleet) :"]
            for t in tasks[:8]:
                if not isinstance(t, dict):
                    continue
                sid = str(t.get("id") or "")[:8]
                role = str(t.get("role") or "?")
                obj = str(t.get("objective") or "")[:100]
                st = str(t.get("status") or "")
                lines.append(f"- `#{sid}` **{role}** ({st}) — {obj}")
            lines.append("\nValide dans le Compagnon (cartes), Pilot `#/team/office` ou `#/team/fleet`.")
            reply = "\n".join(lines)
        else:
            reply = "Aucune approbation L2 Team en attente pour l’instant."
        out: dict[str, Any] = {
            "role": "assistant",
            "content": reply,
            "response": reply,
            "source": "team",
            "model": "team-l2-pending",
            "model_used": "team-l2-pending",
            "provider": "cortex",
            "latency": latency,
            "trace_id": None,
            "raw": pending,
            "agent_action": None,
        }
        if pending.get("approval"):
            out["approval"] = pending["approval"]
        return out

    if _STATUS_RE.search(low):
        data = await _get_campus_status(base, timeout)
        latency = time.perf_counter() - t0
        reply = _format_campus_status(data)
        out = {
            "role": "assistant",
            "content": reply,
            "response": reply,
            "source": "team",
            "model": "campus-status",
            "model_used": "campus-status",
            "provider": "cortex",
            "latency": latency,
            "trace_id": None,
            "raw": data,
            "agent_action": None,
        }
        return await _attach_pending_l2_async(out, reply)

    # Point Infra LAN / disk / Proxmox / @hephaistos — snapshot Cockpit (réel)
    if wants_infra_lan_brief(body_text):
        from src.services.cockpit_snapshot import fetch_cockpit_snapshot

        snap = await fetch_cockpit_snapshot(force=True)
        brief = format_infra_lan_brief(snap if isinstance(snap, dict) else {}, focus=body_text)
        spawn_mission = wants_infra_lan_mission(body_text)
        campus_meta = None
        mission_block = ""
        raw: dict[str, Any] = {"cockpit": snap}
        if spawn_mission:
            try:
                objective = _mission_objective_for_infra(body_text)
                data = await _post_campus_mission(base, timeout, objective=objective)
                mission_block = "\n\n" + _format_campus_mission(data, objective)
                campus_meta = campus_snapshot_from_mission_data(data, objective)
                raw["campus_mission"] = data
            except Exception as e:
                logger.warning("campus mission after infra brief failed: %s", e)
                mission_block = f"\n\n_Mission Campus non lancée : {e}_"

        latency = time.perf_counter() - t0
        reply = brief + mission_block
        out = {
            "role": "assistant",
            "content": reply,
            "response": reply,
            "source": "team",
            "model": "hephaistos-infra",
            "model_used": "hephaistos-infra",
            "provider": "cortex",
            "latency": latency,
            "trace_id": None,
            "raw": raw,
            "agent_action": None,
        }
        if campus_meta:
            out["campus_meta"] = campus_meta
            try:
                from src.services.team_actions import (
                    approval_payload_from_tasks,
                    fetch_tasks_by_ids,
                )

                task_ids = list(campus_meta.get("task_ids") or [])
                details = await fetch_tasks_by_ids(task_ids) if task_ids else []
                approval = approval_payload_from_tasks(details)
                if approval:
                    out["approval"] = approval
                    out["content"] = (
                        reply.rstrip()
                        + "\n\n**Validation L2 requise** — cartes ci-dessous ou Pilot `#/team/office`."
                    )
                    out["response"] = out["content"]
            except Exception:
                logger.debug("infra mission approval attach skipped", exc_info=True)
        return out

    if _MISSION_RE.search(low) or is_multi_role_campus_mission(body_text):
        data = await _post_campus_mission(
            base,
            timeout,
            objective=body_text,
            max_tasks=_parse_max_tasks(body_text, 6),
        )
        latency = time.perf_counter() - t0
        reply = _format_campus_mission(data, body_text)
        snap = campus_snapshot_from_mission_data(data, body_text)
        out = {
            "role": "assistant",
            "content": reply,
            "response": reply,
            "source": "team",
            "model": "campus-mission",
            "model_used": "campus-mission",
            "provider": "cortex",
            "latency": latency,
            "trace_id": None,
            "raw": data,
            "campus_meta": snap,
            "agent_action": None,
        }
        try:
            from src.services.team_actions import (
                approval_payload_from_tasks,
                fetch_tasks_by_ids,
            )

            task_ids = list(snap.get("task_ids") or [])
            details = await fetch_tasks_by_ids(task_ids) if task_ids else []
            approval = approval_payload_from_tasks(details)
            if approval:
                out["approval"] = approval
                out["content"] = (
                    reply.rstrip()
                    + "\n\n**Validation L2 requise** — utilise les cartes ci-dessous (token) ou Pilot `#/team/office`."
                )
                out["response"] = out["content"]
        except Exception:
            logger.debug("mission approval attach skipped", exc_info=True)
        return out

    body = {
        "actor_id": actor,
        "text": body_text or prompt,
        "context": {
            "source": "lbg_ia_orch_ui",
            "conversation_id": conversation_id or "default",
        },
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(f"{base}/v1/pilot/route", json=body)
    latency = time.perf_counter() - t0

    if r.status_code >= 400:
        logger.warning("cortex pilot route HTTP %s: %s", r.status_code, r.text[:300])
        raise RuntimeError(f"Pilot Cortex HTTP {r.status_code}")

    data = r.json()
    if not isinstance(data, dict):
        raise RuntimeError("réponse Pilot non-JSON")

    if data.get("ok") is False:
        raise RuntimeError(str(data.get("error") or "Pilot Cortex ok=false"))

    reply = _extract_reply(data)
    result = data.get("result") if isinstance(data.get("result"), dict) else {}
    routed = result.get("routed_to") if isinstance(result, dict) else None
    intent = result.get("intent") if isinstance(result, dict) else None

    return {
        "role": "assistant",
        "content": reply,
        "response": reply,
        "source": "team",
        "model": routed or intent or "cortex-pilot",
        "model_used": routed or intent or "cortex-pilot",
        "provider": "cortex",
        "latency": latency,
        "trace_id": data.get("trace_id"),
        "raw": data,
        "agent_action": None,
    }
