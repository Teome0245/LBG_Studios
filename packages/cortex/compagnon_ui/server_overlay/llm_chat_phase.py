from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

from src.services.history import get_history
from src.services.logger import log_request
from src.services.intent_learning import learn_new_intent
from src.services.capability_generator import generate_capability_code
from src.services.agents import init_agents
from src.services.router_prompts import (
    colleague_open_reply,
    extract_program_name,
    is_lab_profile,
    short_social_reply,
    soften_media_hard_refuse,
)
from src.services.routing_availability import (
    build_model_index_from_monitor,
    filter_task_models,
    resolve_effective_fallback,
)
from src.observability import log_exception_throttled


async def _maybe_attach_plan_submit(
    result: dict,
    *,
    prompt: str,
    short_ctx: list,
    lab_mode: bool,
) -> dict:
    """D6.5 — persiste le plan markdown en mission Campus si soumettre au studio."""
    try:
        from src.services.plan_submit import attach_team_plan_if_needed

        out = await attach_team_plan_if_needed(
            result, prompt=prompt, short_ctx=short_ctx, lab=lab_mode
        )
        return out if isinstance(out, dict) else result
    except Exception as e:
        logging.getLogger("lbg.router.plan_submit").warning(
            "plan_submit attach failed (best-effort): %s", e
        )
        return result


async def run_llm_chat_phase(
    router: Any,
    *,
    prompt: str,
    profile: str,
    mode: str,
    task: str | None,
    model: str | None,
    agent: str | None,
    conversation_id: str,
    memory: dict,
    short_ctx: list,
    _auto_retry: bool,
) -> dict:
    """
    Phases 4–5 du dispatch : construction messages, sélection providers, fallback, log et contexte.
    """
    logger = logging.getLogger("lbg.router.dispatch")

    # A1 — journal de contexte (blocs injectés, sans secrets)
    journal_blocks: list[dict[str, Any]] = []

    is_infra_ops = False
    try:
        from src.services.router_prompts import _INFRA_OPS_RE
        is_infra_ops = bool(_INFRA_OPS_RE.search(prompt or ""))
    except Exception:
        is_infra_ops = False

    def _journal_short_circuit(source: str, out: Any) -> Any:
        try:
            from src.services.context_journal import attach_context_journal, make_block
        except ImportError:
            try:
                from context_journal import attach_context_journal, make_block  # type: ignore
            except ImportError:
                return out
        return attach_context_journal(
            out,
            [
                make_block(
                    "short_circuit",
                    label="Réponse courte",
                    summary=source,
                    chars=0,
                    meta={"source": source},
                )
            ],
        )

    def _attach_journal(out: Any) -> Any:
        try:
            from src.services.context_journal import attach_context_journal
        except ImportError:
            try:
                from context_journal import attach_context_journal  # type: ignore
            except ImportError:
                return out
        return attach_context_journal(out, journal_blocks)

    # Petites phrases sociales : réponse fixe (évite hang LLM).
    # D6.5 : short_ctx passé — go-ahead sticky / livrable ne short-circuite pas.
    fixed = short_social_reply(prompt, short_ctx=short_ctx)
    if fixed is not None:
        out = router.normalize_llm(fixed, "short_social", "local", latency=0.0)
        if isinstance(out, dict):
            out["source"] = "short_social"
            out["model"] = "short_social"
            out["model_used"] = "short_social"
        return _journal_short_circuit("short_social", out)

    # A2 — « discutons comme collègues » sans sujet → avis net (pas questionnaire)
    colleague = colleague_open_reply(prompt)
    if colleague is not None:
        out = router.normalize_llm(colleague, "colleague_open", "local", latency=0.0)
        if isinstance(out, dict):
            out["source"] = "colleague_open"
            out["model"] = "colleague_open"
            out["model_used"] = "colleague_open"
        return _journal_short_circuit("colleague_open", out)

    # D6.5 — « retour quand la Team a traité » : ack suivi, pas bible Agir
    try:
        from src.services.mission_watch_intent import (
            mission_watch_ack_reply,
            wants_mission_watch_notify,
        )

        if wants_mission_watch_notify(prompt):
            watch_out = router.normalize_llm(
                mission_watch_ack_reply(prompt),
                "mission_watch",
                "local",
                latency=0.0,
            )
            if isinstance(watch_out, dict):
                watch_out["source"] = "mission_watch"
                watch_out["model"] = "mission_watch"
                watch_out["model_used"] = "mission_watch"
                watch_out["mission_watch"] = {"notify": True}
            return _journal_short_circuit("mission_watch", watch_out)
    except Exception as e:
        logging.getLogger("lbg.router.mission_watch").warning(
            "mission_watch short-circuit failed: %s", e
        )

    chat_profile = profile
    lab_mode = is_lab_profile(profile)

    # Suivi plan d'évolutions — CR bloqués / à relancer / réalisés
    try:
        from src.services.plan_suivi import (
            attach_plan_suivi_if_needed,
            wants_plan_suivi,
        )

        if lab_mode and wants_plan_suivi(prompt):
            seed = router.normalize_llm(
                "suivi plan",
                "plan_suivi",
                "local",
                latency=0.0,
            )
            if isinstance(seed, dict):
                return _journal_short_circuit(
                    "plan_suivi",
                    await attach_plan_suivi_if_needed(
                        seed, prompt=prompt, lab=lab_mode
                    ),
                )
    except Exception as e:
        logging.getLogger("lbg.router.plan_suivi").warning(
            "plan_suivi short-circuit failed: %s", e
        )

    # Phase C2 — retour terrain présence → causerie (fetch hub, pas dump ops)
    try:
        from src.services.presence_report import (
            attach_presence_report_if_needed,
            wants_presence_report,
        )

        if lab_mode and wants_presence_report(prompt):
            seed = router.normalize_llm(
                "retour présence",
                "presence_report",
                "local",
                latency=0.0,
            )
            if isinstance(seed, dict):
                return _journal_short_circuit(
                    "presence_report",
                    await attach_presence_report_if_needed(
                        seed, prompt=prompt, lab=lab_mode
                    ),
                )
    except Exception as e:
        logging.getLogger("lbg.router.presence_report").warning(
            "presence_report short-circuit failed: %s", e
        )

    # Phase C1 — brief présence hub : markdown + Campus borné
    # wants_presence_brief exclut déjà la causerie design T5 (zone sans teste/brief/smoke)
    try:
        from src.services.presence_brief import (
            attach_presence_brief_if_needed,
            wants_presence_brief,
        )

        if lab_mode and wants_presence_brief(prompt):
            seed = router.normalize_llm(
                "brief présence",
                "presence_brief",
                "local",
                latency=0.0,
            )
            if isinstance(seed, dict):
                return _journal_short_circuit(
                    "presence_brief",
                    await attach_presence_brief_if_needed(
                        seed, prompt=prompt, lab=lab_mode
                    ),
                )
    except Exception as e:
        logging.getLogger("lbg.router.presence_brief").warning(
            "presence_brief short-circuit failed: %s", e
        )

    # Plan 3.1 — flux direct d'événements monde (Live World Stream hub :8787)
    try:
        from src.services.world_stream import (
            attach_world_stream_if_needed,
            wants_world_stream,
        )

        if lab_mode and wants_world_stream(prompt):
            seed = router.normalize_llm(
                "live world stream",
                "world_stream",
                "local",
                latency=0.0,
            )
            if isinstance(seed, dict):
                return _journal_short_circuit(
                    "world_stream",
                    await attach_world_stream_if_needed(
                        seed, prompt=prompt, lab=lab_mode
                    ),
                )
    except Exception as e:
        logging.getLogger("lbg.router.world_stream").warning(
            "world_stream short-circuit failed: %s", e
        )

    # Plan 3.2 — convergence mémoire relationnelle jeu ↔ bureau (:8787)
    try:
        from src.services.relation_memory import (
            attach_relation_memory_if_needed,
            wants_relation_memory,
        )

        if lab_mode and wants_relation_memory(prompt):
            seed = router.normalize_llm(
                "mémoire relationnelle",
                "relation_memory",
                "local",
                latency=0.0,
            )
            if isinstance(seed, dict):
                return _journal_short_circuit(
                    "relation_memory",
                    await attach_relation_memory_if_needed(
                        seed, prompt=prompt, lab=lab_mode, player="Teome"
                    ),
                )
    except Exception as e:
        logging.getLogger("lbg.router.relation_memory").warning(
            "relation_memory short-circuit failed: %s", e
        )

    # D6.5 — « soumets ce plan au studio » : réutilise le plan du fil, skip LLM
    # (évite 502 timeout LLM+Pilot quand le livrable est déjà là).
    try:
        from src.services.plan_submit import (
            extract_plan_from_ctx,
            wants_submit_existing_plan,
        )

        if lab_mode and wants_submit_existing_plan(prompt, short_ctx):
            prior = extract_plan_from_ctx(short_ctx)
            if prior:
                seed = router.normalize_llm(
                    prior,
                    "plan_submit_reuse",
                    "local",
                    latency=0.0,
                )
                if isinstance(seed, dict):
                    seed["source"] = "plan_submit"
                    seed["model"] = "plan_submit_reuse"
                    seed["model_used"] = "plan_submit_reuse"
                    return _journal_short_circuit(
                        "plan_submit",
                        await _maybe_attach_plan_submit(
                            seed, prompt=prompt, short_ctx=short_ctx, lab_mode=lab_mode
                        ),
                    )
    except Exception as e:
        logging.getLogger("lbg.router.plan_submit").warning(
            "plan_submit reuse short-circuit failed: %s", e
        )
    lyra_tone_extra = ""
    eng = getattr(router.lyra, "engine_v2", None)
    if eng is not None and profile != "test" and not lab_mode:
        try:
            snap = await eng.get_snapshot()
            router.lyra.gauges = dict(snap.gauges)
            if snap.derived.get("lyra_temperature_hal_active"):
                chat_profile = "hal"
            nudge = snap.derived.get("energy_user_nudge")
            if isinstance(nudge, str) and nudge.strip():
                lyra_tone_extra = "\n" + nudge.strip()
        except Exception:
            log_exception_throttled(
                logging.getLogger("lbg.router.lyra_snapshot"),
                router._exc_throttler,
                "lyra_snapshot",
                "Lyra snapshot failed (best-effort)",
            )

    if lab_mode:
        # Forcer le prompt LAB même si l'UI envoie profile=compagnon + LBG_COMPAGNON_LAB=1
        chat_profile = "compagnon_lab"
        # Mémoire stable coupée (anti-invention + taille) ; fil conversation conservé (D6.1)
        memory = {}
        try:
            from src.services.router_prompts import lab_short_ctx_cap

            _cap = lab_short_ctx_cap()
        except Exception:
            _cap = 6
        if short_ctx and _cap > 0 and len(short_ctx) > _cap:
            short_ctx = list(short_ctx)[-_cap:]
        elif _cap == 0:
            short_ctx = []

    # D6.2/D6 combo : LAB causerie sticky (fil) → prompt court ; sinon ops
    try:
        from src.services.router_prompts import resolve_lab_system_prompt, wants_lab_causerie_prompt

        lab_causerie = bool(lab_mode and wants_lab_causerie_prompt(prompt, short_ctx=short_ctx))
        if lab_mode:
            base_profile = resolve_lab_system_prompt(prompt, short_ctx=short_ctx)
        else:
            base_profile = router.PROFILES.get(chat_profile, router.PROFILES["chaleureux"])
    except Exception:
        lab_causerie = False
        base_profile = router.PROFILES.get(chat_profile, router.PROFILES["chaleureux"])

    # Nudge média (légal + Agir) — le 2B oublie sinon le system long
    try:
        from src.services.router_prompts import media_lab_action_nudge

        media_nudge = media_lab_action_nudge(prompt, lab=lab_mode)
    except Exception:
        media_nudge = ""

    # Nudge causerie — avance le fil + anti-invention
    try:
        from src.services.router_prompts import causerie_lab_nudge

        causerie_nudge = causerie_lab_nudge(prompt, lab=lab_mode, short_ctx=short_ctx)
    except TypeError:
        try:
            from src.services.router_prompts import causerie_lab_nudge

            causerie_nudge = causerie_lab_nudge(prompt, lab=lab_mode)
        except Exception:
            causerie_nudge = ""
    except Exception:
        causerie_nudge = ""

    # D6.5 — livrable plan (anti-méta) ; prioritaire sur le nudge causerie générique
    try:
        from src.services.router_prompts import plan_delivery_nudge

        plan_nudge = plan_delivery_nudge(prompt, lab=lab_mode, short_ctx=short_ctx)
        if plan_nudge:
            causerie_nudge = plan_nudge
    except Exception:
        pass

    # Couche Character (worldview + dials + ego soft) — best-effort
    # Causerie : dials + ego seulement, pas le mur worldview/ops catchphrases
    character_extra = ""
    try:
        from src.services.character_layer import character_enabled, format_character_block

        if character_enabled() and chat_profile in (
            "compagnon",
            "compagnon_lab",
            "lab",
            "jarvis",
            "mother",
            "kit",
            "mec_chill",
            "chill",
            "philo",
        ):
            block = format_character_block(
                lab=lab_mode,
                prompt=prompt,
                causerie=lab_causerie,
                journal=journal_blocks,
            )
            if block:
                character_extra = "\n\n" + block
    except Exception:
        character_extra = ""

    if profile == "test" or lab_mode:
        # LAB : short_ctx porte le fil ; history global resterait redondant / bruyant
        system_prompt = base_profile + media_nudge + causerie_nudge + character_extra
        history = []
    else:
        system_prompt = (
            base_profile
            + "\n"
            + router.lyra.get_style_modifier()
            + lyra_tone_extra
            + media_nudge
            + causerie_nudge
            + character_extra
        )
        history = await get_history(limit=1)

    # A1 — fil court + mémoire stable (métadonnées seulement)
    try:
        from src.services.context_journal import make_block as _cj_block
    except ImportError:
        try:
            from context_journal import make_block as _cj_block  # type: ignore
        except ImportError:
            _cj_block = None  # type: ignore

    if _cj_block and short_ctx:
        journal_blocks.append(
            _cj_block(
                "short_ctx",
                label="Fil court",
                summary=f"{len(short_ctx)} tour{'s' if len(short_ctx) != 1 else ''}",
                chars=sum(len(str(i.get("content") or "")) for i in short_ctx if isinstance(i, dict)),
                meta={"turns": len(short_ctx)},
            )
        )
    if _cj_block and memory:
        journal_blocks.append(
            _cj_block(
                "memory",
                label="Mémoire stable",
                summary="présent",
                chars=len(json.dumps(memory, ensure_ascii=False)),
            )
        )

    # Ancrage soft : injecter faits Ollama si la question touche au LAN LLM
    try:
        from src.services.lan_llm_grounding import (
            format_audit_grounding,
            load_lan_llm_audit,
            wants_lan_llm_context,
        )
        from src.settings import get_settings

        if wants_lan_llm_context(prompt) and not is_infra_ops:
            audit = await load_lan_llm_audit(settings=get_settings())
            lan_block = format_audit_grounding(audit)
            system_prompt = system_prompt + "\n\n" + lan_block
            if _cj_block and lan_block:
                journal_blocks.append(
                    _cj_block(
                        "lan_llm",
                        label="LAN LLM",
                        summary="audit Ollama",
                        chars=len(lan_block),
                    )
                )
    except Exception:
        log_exception_throttled(
            logging.getLogger("lbg.router.lan_grounding"),
            router._exc_throttler,
            "lan_llm_grounding",
            "LAN LLM grounding inject failed (best-effort)",
        )

    # P1 — Self slim (conscience studio / memory_refs) dans le prompt
    try:
        from src.services.companion_self_grounding import (
            format_self_grounding,
            load_self_status,
            wants_self_memory_context,
        )

        # D6.2 causerie : pas d'ancrage Self (bruit ops / leçons) — le fil suffit
        if not lab_causerie:
            self_payload = await load_self_status()
            if self_payload is not None:
                need_full = (wants_self_memory_context(prompt) or not lab_mode) and not is_infra_ops
                block = format_self_grounding(self_payload, compact=not need_full)
                if block:
                    system_prompt = system_prompt + "\n\n" + block
                    if _cj_block:
                        journal_blocks.append(
                            _cj_block(
                                "self_grounding",
                                label="Self",
                                summary="compact" if not need_full else "complet",
                                chars=len(block),
                                meta={"compact": not need_full},
                            )
                        )
    except Exception:
        log_exception_throttled(
            logging.getLogger("lbg.router.self_grounding"),
            router._exc_throttler,
            "companion_self_grounding",
            "Self grounding inject failed (best-effort)",
        )

    # A3 — Studio Brain court (LAB ops uniquement — pas causerie ni infra ciblée couverte par _OPS_TRUTH)
    try:
        from src.services.studio_brain import format_studio_brain_block

        if lab_mode and (not lab_causerie) and (not is_infra_ops):
            brain = format_studio_brain_block()
            if brain:
                system_prompt = system_prompt + "\n\n" + brain
                if _cj_block:
                    journal_blocks.append(
                        _cj_block(
                            "studio_brain",
                            label="Studio Brain",
                            summary="faits + leçons",
                            chars=len(brain),
                        )
                    )
    except Exception:
        log_exception_throttled(
            logging.getLogger("lbg.router.studio_brain"),
            router._exc_throttler,
            "studio_brain",
            "Studio Brain inject failed (best-effort)",
        )

    # P2 — REGISTRE-lite (hosts / Prime / incarnations) si la question touche l'écosystème (hors infra ciblée couverte par _OPS_TRUTH)
    try:
        from src.services.ecosystem_grounding import (
            format_ecosystem_grounding,
            wants_ecosystem_context,
        )

        if (not lab_causerie) and (not is_infra_ops) and wants_ecosystem_context(prompt):
            eco = format_ecosystem_grounding()
            if eco:
                system_prompt = system_prompt + "\n\n" + eco
                if _cj_block:
                    journal_blocks.append(
                        _cj_block(
                            "ecosystem",
                            label="Écosystème",
                            summary="REGISTRE-lite",
                            chars=len(eco),
                        )
                    )
    except Exception:
        log_exception_throttled(
            logging.getLogger("lbg.router.ecosystem_grounding"),
            router._exc_throttler,
            "ecosystem_grounding",
            "Ecosystem grounding inject failed (best-effort)",
        )

    # P3 — RAG (leçons / expériences / knowledge / philo) si LBG_RAG_ENABLED + indices mémoire ou profil chill (hors infra ops ciblée)
    try:
        from src.services.rag_grounding import load_rag_block

        is_chill_profile = chat_profile in ("mec_chill", "chill", "philo")
        if ((not lab_causerie) and (not is_infra_ops)) or is_chill_profile:
            rag_block = await load_rag_block(prompt, profile=chat_profile, force=is_chill_profile)
            if rag_block:
                system_prompt = system_prompt + "\n\n" + rag_block
                if _cj_block:
                    journal_blocks.append(
                        _cj_block(
                            "rag",
                            label="RAG",
                            summary="philosophie / leçons" if is_chill_profile else "leçons / knowledge",
                            chars=len(rag_block),
                        )
                    )
    except Exception:
        log_exception_throttled(
            logging.getLogger("lbg.router.rag_grounding"),
            router._exc_throttler,
            "rag_grounding",
            "RAG grounding inject failed (best-effort)",
        )

    context_messages = []
    for item in short_ctx:
        context_messages.append({"role": item["role"], "content": item["content"]})

    for item in history:
        context_messages.append({"role": "user", "content": item["prompt"]})
        context_messages.append({"role": "assistant", "content": item["response"]})

    messages = [
        {
            "role": "system",
            "content": system_prompt
            + (
                ("\n\nContexte long-terme (mémoire stable):\n" + json.dumps(memory, ensure_ascii=False))
                if memory
                else ""
            ),
        },
        *context_messages,
        {
            "role": "user",
            "content": prompt,
        },
    ]

    detected = task or router.detect_task(prompt)
    task_models = list(router.routing["tasks"].get(detected, {}).get("models", []))

    ctx = getattr(router, "app_context", None)
    llm_monitor = ctx.llm_monitor if ctx is not None else None
    if llm_monitor is None:
        llm_monitor = getattr(router, "llm_monitor", None)

    latest = None
    model_index = None
    if llm_monitor is not None:
        try:
            latest = await llm_monitor.get_latest()
            model_index = build_model_index_from_monitor(latest)
            task_models = filter_task_models(
                task_models,
                latest_monitor=latest,
                model_index=model_index,
            )
        except Exception:
            log_exception_throttled(
                logging.getLogger("lbg.router.llm_monitor"),
                router._exc_throttler,
                "llm_monitor_get_latest",
                "LLM monitor get_latest failed (best-effort)",
            )

    sorted_models = router.health.sort_providers(task_models)
    if latest is not None:
        try:
            sorted_models = router.health.sort_providers_with_monitor(task_models, latest)
        except Exception:
            log_exception_throttled(
                logging.getLogger("lbg.router.llm_monitor"),
                router._exc_throttler,
                "llm_monitor_sort",
                "LLM monitor sort failed (best-effort)",
            )

    # Méta route L1/L2 (alignée reason_route_matrix) — stampée sur la réponse finale
    route_meta: dict[str, Any] = {}

    if lab_mode:
        # LAB : local only — fast/router (.111) ; causerie e2b ; média/Agir = 12b (.110)
        from src.services.router_prompts import (
            lab_preferred_model,
            lab_route_profile,
            lab_route_tier,
            wants_lab_quality_route,
            _MEDIA_CUE_RE,
            _QUALITY_ROUTE_RE,
            _INFRA_OPS_RE,
        )

        is_chill_profile = chat_profile in ("mec_chill", "chill", "philo")
        quality = wants_lab_quality_route(prompt) or is_chill_profile
        preferred = lab_preferred_model(prompt, profile=chat_profile)
        route_profile = lab_route_profile(prompt, profile=chat_profile)
        # Causerie sticky : forcer modèle chat qualité si causerie ordinaire hors chill
        if lab_causerie and not is_chill_profile:
            from src.services.router_prompts import lab_chat_quality_model

            preferred = lab_chat_quality_model()
            quality = True
            route_profile = "dialogue"
        elif is_chill_profile:
            quality = True
            route_profile = "chill"
        before = list(sorted_models)
        local_only = [e for e in sorted_models if e.get("provider") == "local"]
        if not any(e.get("name") == preferred for e in local_only):
            local_only = [{"provider": "local", "name": preferred}, *local_only]
        head = [e for e in local_only if e.get("name") == preferred]
        tail = [e for e in local_only if e.get("name") != preferred]

        needs_heavy = bool(
            _MEDIA_CUE_RE.search(prompt or "")
            or _QUALITY_ROUTE_RE.search(prompt or "")
            or _INFRA_OPS_RE.search(prompt or "")
            or is_chill_profile
            or "e4b" in (preferred or "").lower()
            or "14b" in (preferred or "").lower()
            or "coder" in (preferred or "").lower()
            or "12b" in (preferred or "").lower()
        )
        route_meta = {
            "route_profile": route_profile,
            "route_tier": lab_route_tier(route_profile) if not needs_heavy else "heavy",
            "route_preferred": preferred,
        }

        def _is_heavy(name: str) -> bool:
            n = (name or "").lower()
            # e2b reste light (.111) — pas de forçage heavy
            return any(x in n for x in (":9b", ":12b", "12b-qat", ":e4b", "e4b", "14b", "coder"))

        if needs_heavy:
            # Code / Infra / Média / Agir / Chill : 14b / E4b-qat (.110) puis 12b puis 9b
            allow_h = {
                preferred,
                "huihui_ai/qwen2.5-coder-abliterate:14b",
                "huihui_ai/gemma-4-abliterated:E4b-qat",
                "huihui_ai/gemma-4-abliterated:12b",
                "huihui_ai/gemma-4-abliterated:12b-qat",
                "huihui_ai/qwen3.5-abliterated:9b",
            }
            tail = [e for e in tail if e.get("name") in allow_h][:2]
            sorted_models = (head + tail) or local_only[:1]
            # Secours ultime light .111 si les nœuds heavy .110 ne répondent pas
            light_backup = {"provider": "local", "name": "huihui_ai/qwen3.5-abliterated:2B"}
            if not any(e.get("name") == light_backup["name"] for e in sorted_models):
                sorted_models.append(light_backup)
        else:
            # Causerie / social / général : UNIQUEMENT light .111 (évite hang 12b CPU)
            light_ok = {
                preferred,
                "huihui_ai/gemma-4-abliterated:e2b",
                "huihui_ai/qwen3.5-abliterated:2B",
                "huihui_ai/qwen3.5-abliterated:0.8B",
                "llama3.2:3b",
                "qwen2.5:3b",
            }
            tail = [e for e in tail if e.get("name") in light_ok and not _is_heavy(str(e.get("name") or ""))][:3]
            head = [e for e in head if not _is_heavy(str(e.get("name") or ""))] or [
                {"provider": "local", "name": "huihui_ai/qwen3.5-abliterated:2B"}
            ]
            sorted_models = (head + tail) or [{"provider": "local", "name": "huihui_ai/qwen3.5-abliterated:2B"}]

        logger.info(
            "LAB mode: local-only cascade profile=%s preferred=%s quality=%s heavy=%s (from %s → %s)",
            route_profile,
            preferred,
            quality,
            needs_heavy,
            [(e.get("provider"), e.get("name")) for e in before],
            [(e.get("provider"), e.get("name")) for e in sorted_models],
        )
    else:
        # Hors LAB : option local-only (évite Groq censuré) via env
        no_cloud = (os.getenv("LBG_COMPAGNON_LOCAL_ONLY") or "").strip().lower() in (
            "1",
            "true",
            "yes",
            "on",
        )
        if no_cloud:
            sorted_models = [e for e in sorted_models if e.get("provider") == "local"]
            logger.info(
                "LOCAL_ONLY: stripped cloud providers → %s",
                [(e.get("provider"), e.get("name")) for e in sorted_models],
            )

    if model:
        selected_model = model
    elif agent and agent in router.agents:
        selected_model = router.agents[agent].preferred_model
    else:
        selected_model = router.local_llm.default_model

    if mode == "local":
        try:
            vr = await router.validation.validate_local_model(selected_model, local_llm=router.local_llm)
            if not vr.ok and vr.issue:
                return router.normalize_agent(
                    {"content": vr.issue.message, "details": vr.issue.details},
                    action="validation_error",
                    latency=0.0,
                )
        except Exception:
            log_exception_throttled(
                logging.getLogger("lbg.router.local_model_validation"),
                router._exc_throttler,
                "validate_local_model",
                "Local model validation failed (best-effort)",
            )
        raw = await router.local_llm.generate(
            prompt,
            model=selected_model,
        )
        local_out = router.normalize_llm(raw, selected_model, "local", latency=0.0)
        if isinstance(local_out, dict):
            local_out = await _maybe_attach_plan_submit(
                local_out, prompt=prompt, short_ctx=short_ctx, lab_mode=lab_mode
            )
            if route_meta:
                local_out.update(route_meta)
            raw_val = local_out.get("raw")
            is_err = bool(local_out.get("error") or (isinstance(raw_val, dict) and raw_val.get("error")))
            c = str(local_out.get("content") or "").strip()
            if is_err or not c or c.startswith("{'model_used':") or c.startswith('{"model_used":'):
                clean_msg = (
                    "Désolé, les serveurs d'inférence locaux (.110 / .111) sont actuellement indisponibles ou occupés. "
                    "Impossible de générer la réponse complète pour le moment."
                )
                local_out["content"] = clean_msg
                local_out["response"] = clean_msg
            return _attach_journal(local_out)
        return _attach_journal(local_out)

    result = None

    for entry in sorted_models:
        provider = entry["provider"]
        model_name = entry["name"]
        generator = router.GENERATOR.get(provider)

        if not generator:
            continue

        logger.debug("Essai provider: %s / %s", provider, model_name)

        start = time.monotonic()
        try:
            raw = await generator(messages, model_name)
        except Exception as e:
            logger.warning("Provider exception: %s %s", provider, e)
            router.health.record_error(provider)
            router.lyra.update_on_error()
            continue
        latency = time.monotonic() - start

        if isinstance(raw, dict) and raw.get("error"):
            logger.warning(
                "Provider KO: %s msg=%s",
                provider,
                raw.get("message") if isinstance(raw, dict) else None,
            )
            router.health.record_error(provider)
            router.lyra.update_on_error()
            continue

        if isinstance(raw, dict) and raw.get("content") and not _auto_retry:
            content_str = str(raw.get("content") or "")
            try:
                from src.services.router_prompts import reshape_media_lab_reply, lab_env_enabled

                # Force reshape dès que LAB env est on (même si profile UI = compagnon)
                reshaped = reshape_media_lab_reply(
                    prompt, content_str, lab=bool(lab_mode or lab_env_enabled())
                )
                if reshaped:
                    logger.info("Media LAB reply reshaped → canonical (anti-dérive 2B)")
                    raw = {**raw, "content": reshaped}
                    content_str = reshaped
            except Exception:
                pass
            if not lab_mode:
                softened = soften_media_hard_refuse(prompt, content_str)
                if softened:
                    logger.info("Media hard-refuse softened (garde + pistes legales)")
                    raw = {**raw, "content": softened}
                    content_str = softened
            try:
                from src.services.character_layer import reshape_blacklist

                cleaned = reshape_blacklist(content_str)
                if cleaned:
                    logger.info("Character blacklist reshape (anti langage IA générique)")
                    raw = {**raw, "content": cleaned}
                    content_str = cleaned
            except Exception:
                pass
            txt = str(raw["content"]).lower()
            if (not lab_mode) and any(
                p in txt
                for p in [
                    "je ne peux pas",
                    "je n'ai pas accès",
                    "je ne suis pas autorisé",
                    "en tant qu'ia",
                    "je ne peux pas exécuter",
                ]
            ):
                logger.info("Auto-upgrade: réponse LLM inutile -> apprentissage")

                new_intent = await learn_new_intent(prompt, router)
                if not new_intent:
                    return router.wrap_error("Impossible d'apprendre une nouvelle intention.")

                action = new_intent["action"]
                logger.info("Auto-upgrade: nouvelle action apprise: %s", action)

                router.agents = init_agents()
                await router.refresh_all_capabilities()

                existing_caps = []
                for agent_obj in router.agents.values():
                    existing_caps.extend(agent_obj.capabilities)

                if action not in existing_caps:
                    program_name = extract_program_name(action)
                    generated_code = generate_capability_code(action, program_name)

                    install_result = await router.capability_installer.install(
                        action=action,
                        code=generated_code,
                        description=f"Auto-installed capability {action}",
                    )
                    logger.info(
                        "Installation agent Windows: status=%s",
                        install_result.get("status") if isinstance(install_result, dict) else None,
                    )

                    router.agents = init_agents()
                    await router.refresh_all_capabilities()

                return await router.dispatch(
                    prompt,
                    mode=mode,
                    profile=profile,
                    task=task,
                    _auto_retry=True,
                )

        result = router.normalize_llm(raw, model_name, provider, latency)
        router.health.record_success(provider, latency)
        router.lyra.update_on_success()
        break

    if not result:
        fallback = resolve_effective_fallback(
            router.routing,
            latest_monitor=latest,
            model_index=model_index,
        ) or router.routing["routing_rules"]["fallback"]
        if lab_mode:
            fallback = {
                "provider": "local",
                "name": fallback.get("name")
                or router.routing["routing_rules"]["fallback"]["name"],
            }
        fp = fallback["provider"]
        fm = fallback["name"]
        fg = router.GENERATOR.get(fp)

        logger.info("Fallback global: provider=%s model=%s lab=%s", fp, fm, lab_mode)

        raw = await fg(messages, fm)
        result = router.normalize_llm(raw, fm, fp, latency=0.0)

    if isinstance(result, dict):
        result = await _maybe_attach_plan_submit(
            result, prompt=prompt, short_ctx=short_ctx, lab_mode=lab_mode
        )
        if route_meta:
            result.update(route_meta)

        # Anti-leak dictionnaire brut si échec total des modèles locaux
        raw_val = result.get("raw")
        is_err = bool(result.get("error") or (isinstance(raw_val, dict) and raw_val.get("error")))
        c = str(result.get("content") or "").strip()
        if is_err or not c or c.startswith("{'model_used':") or c.startswith('{"model_used":'):
            clean_msg = (
                "Désolé, les serveurs d'inférence locaux (.110 / .111) sont actuellement indisponibles ou occupés. "
                "Impossible de générer la réponse complète pour le moment."
            )
            result["content"] = clean_msg
            result["response"] = clean_msg

    await log_request(
        prompt,
        result["content"],
        result["model"],
        mode,
        result["provider"],
    )

    # Persistance centralisée dans RouterIA.dispatch (conversation_memory.persist_exchange)

    return _attach_journal(result)
