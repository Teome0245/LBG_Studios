import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.health import router as health_router
from api.v1.router import router as v1_router
from config import get_settings
from middleware import TraceIdMiddleware

LOG = logging.getLogger("backend")


def _configure_logging() -> None:
    fmt = "%(asctime)s %(levelname)-5s %(name)s: %(message)s"
    logging.basicConfig(level=logging.INFO, format=fmt, force=True)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def resolve_pilot_static_dir(pilot_root: Path, mode: str | None = None) -> Path:
    """Répertoire servi sous ``/pilot/``.

    ``LBG_PILOT_STATIC`` :
    - ``auto`` (défaut) — ``dist/`` si ``dist/index.html`` existe, sinon sources ;
    - ``dist`` — bundle Vite (repli sources si absent) ;
    - ``source`` — ``pilot_web/`` (dev ESM / import map).
    """
    raw = (mode if mode is not None else get_settings().lbg_pilot_static).strip().lower() or "auto"
    dist = pilot_root / "dist"
    dist_ok = (dist / "index.html").is_file()
    if raw == "source":
        return pilot_root
    if raw == "dist":
        return dist if dist_ok else pilot_root
    return dist if dist_ok else pilot_root


def create_app() -> FastAPI:
    _configure_logging()

    application = FastAPI(title="LBG_IA_MMO Backend", version="0.1.0")

    application.add_middleware(TraceIdMiddleware)

    cors_origins = get_settings().cors_origins_list()
    if cors_origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    application.include_router(health_router)
    application.include_router(v1_router, prefix="/v1")

    pilot_root = Path(__file__).resolve().parent.parent / "pilot_web"
    if pilot_root.is_dir():
        pilot_dir = resolve_pilot_static_dir(pilot_root)
        LOG.info("pilot static dir=%s", pilot_dir)
        application.mount("/pilot", StaticFiles(directory=str(pilot_dir), html=True), name="pilot")

    return application


app = create_app()
