import asyncio
from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator

from fastapi import FastAPI

from router.v1 import router as v1_router
from api.health import router as health_router
from services import brain as svc_brain
from services import lia_autonomy as svc_lia_autonomy
from services import jobs as svc_jobs
try:
    from services import proactive as svc_proactive
except ImportError:
    svc_proactive = None  # type: ignore[assignment]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    svc_brain.ensure_started()
    svc_lia_autonomy.ensure_started()
    svc_jobs.ensure_started()
    if svc_proactive is not None:
        svc_proactive.ensure_started()

    try:
        from team import presence as team_presence
        from team import store as team_store

        loop = asyncio.get_running_loop()
        team_presence.bind_loop(loop)
        tasks = team_store.list_tasks(limit=200)
        team_presence.rebuild_from_tasks(tasks)

        async def _recover_loop() -> None:
            while True:
                await asyncio.sleep(30)
                try:
                    team_presence.recover_stale_failed()
                    team_presence.reconcile_with_store()
                except Exception:
                    pass

        asyncio.create_task(_recover_loop())
    except Exception:
        pass

    logger = logging.getLogger("lbg.llm_model_probe")

    async def _probe_cycle() -> None:
        await asyncio.sleep(5)  # laisser le temps au startup
        while True:
            try:
                from team.llm_model_probe import auto_fix_env

                summary = auto_fix_env()
                if summary.get("patched"):
                    logger.warning("LLM model auto-fix applied: %s", summary["changes"])
                else:
                    logger.debug("LLM model probe OK — no changes needed")
            except Exception as exc:
                logger.debug("LLM model probe error: %s", exc)
            await asyncio.sleep(600)  # 10 min

    asyncio.create_task(_probe_cycle())

    yield


app = FastAPI(title="LBG_IA_MMO Orchestrator", version="0.1.0", lifespan=lifespan)
app.include_router(health_router)
app.include_router(v1_router, prefix="/v1")
