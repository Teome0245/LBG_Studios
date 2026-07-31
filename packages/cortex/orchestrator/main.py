from fastapi import FastAPI

from router.v1 import router as v1_router
from api.health import router as health_router
from services import brain as svc_brain
from services import lia_autonomy as svc_lia_autonomy
from services import jobs as svc_jobs
from services import proactive as svc_proactive

app = FastAPI(title="LBG_IA_MMO Orchestrator", version="0.1.0")
app.include_router(health_router)
app.include_router(v1_router, prefix="/v1")


@app.on_event("startup")
def _startup() -> None:
    import asyncio

    svc_brain.ensure_started()
    svc_lia_autonomy.ensure_started()
    svc_jobs.ensure_started()
    svc_proactive.ensure_started()
    try:
        from team import presence as team_presence
        from team import store as team_store

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop is not None:
            team_presence.bind_loop(loop)
        tasks = team_store.list_tasks(limit=200)
        team_presence.rebuild_from_tasks(tasks)
    except Exception:
        pass


@app.on_event("startup")
async def _presence_bind_loop() -> None:
    import asyncio

    try:
        from team import presence as team_presence

        team_presence.bind_loop(asyncio.get_running_loop())

        async def _recover_loop() -> None:
            while True:
                await asyncio.sleep(30)
                try:
                    team_presence.recover_stale_failed()
                except Exception:
                    pass

        asyncio.create_task(_recover_loop())
    except Exception:
        pass

