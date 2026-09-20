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
    extract_program_name,
    is_lab_profile,
    soften_media_hard_refuse,
)
from src.services.routing_availability import (
    build_model_index_from_monitor,
    filter_task_models,
    resolve_effective_fallback,
)
from src.observability import log_exception_throttled


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

    chat_profile = profile
    lab_mode = is_lab_profile(profile)
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
        # Prompt court : éviter les timeouts Ollama (mémoire / historique gonflent le contexte)
        memory = {}
        short_ctx = []

    base_profile = router.PROFILES.get(chat_profile, router.PROFILES["chaleureux"])

    if profile == "test" or lab_mode:
        system_prompt = base_profile
        history = []
    else:
        system_prompt = base_profile + "\n" + router.lyra.get_style_modifier() + lyra_tone_extra
        history = await get_history(limit=1)

    # Ancrage soft : injecter faits Ollama si la question touche au LAN LLM
    try:
        from src.services.lan_llm_grounding import (
            format_audit_grounding,
            load_lan_llm_audit,
            wants_lan_llm_context,
        )
        from src.settings import get_settings

        if wants_lan_llm_context(prompt):
            audit = await load_lan_llm_audit(settings=get_settings())
            system_prompt = system_prompt + "\n\n" + format_audit_grounding(audit)
    except Exception:
        log_exception_throttled(
            logging.getLogger("lbg.router.lan_grounding"),
            router._exc_throttler,
            "lan_llm_grounding",
            "LAN LLM grounding inject failed (best-effort)",
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
            "content": f"Réponds uniquement en français. Voici ma question : {prompt}",
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

    if lab_mode:
        # LAB : un seul modèle uncensored — éviter double timeout abliterated→gemma
        preferred = (
            os.getenv("LBG_COMPAGNON_LAB_MODEL", "").strip()
            or "huihui_ai/qwen3.5-abliterated:2B"
        )
        before = list(sorted_models)
        only = [e for e in sorted_models if e.get("provider") == "local" and e.get("name") == preferred]
        if not only:
            only = [e for e in sorted_models if e.get("provider") == "local"][:1]
        sorted_models = only
        logger.info(
            "LAB mode: local-only single model %s (from %s → %s)",
            preferred,
            [(e.get("provider"), e.get("name")) for e in before],
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
        return router.normalize_llm(raw, selected_model, "local", latency=0.0)

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
            if not lab_mode:
                softened = soften_media_hard_refuse(prompt, str(raw.get("content") or ""))
                if softened:
                    logger.info("Media hard-refuse softened (garde + pistes legales)")
                    raw = {**raw, "content": softened}
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

    await log_request(
        prompt,
        result["content"],
        result["model"],
        mode,
        result["provider"],
    )

    # Persistance centralisée dans RouterIA.dispatch (conversation_memory.persist_exchange)

    return result
