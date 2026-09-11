import os
from pathlib import Path
from contextlib import asynccontextmanager

from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from starlette.middleware.sessions import SessionMiddleware

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from routers.paginas import router as paginas_router
from routers.talleres import router as talleres_router
from routers.usuarios import router as usuarios_router
from routers.reservas import router as reservas_router
from routers.google_calendar import router as googlec_router
from routers.secciones import router as seccion_router

from routers.reservas import limpiar_reservas_viejas


BASE_DIR = Path(__file__).resolve().parent

load_dotenv(
    BASE_DIR / ".env",
    override=True
)


# -------------------------
# SCHEDULER
# -------------------------

scheduler = AsyncIOScheduler()

scheduler.add_job(
    limpiar_reservas_viejas,
    "interval",
    weeks=1
)


@asynccontextmanager
async def lifespan(app: FastAPI):

    print("INICIANDO SCHEDULER")

    scheduler.start()

    yield

    print("CERRANDO SCHEDULER")

    scheduler.shutdown()


# -------------------------
# FASTAPI
# -------------------------

app = FastAPI(
    lifespan=lifespan
)


# -------------------------
# SESSION
# -------------------------

SESSION_SECRET = os.getenv(
    "GOOGLE_SESSION_SECRET"
)

if not SESSION_SECRET:
    raise RuntimeError(
        "Falta GOOGLE_SESSION_SECRET"
    )


app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site="lax",
    https_only=False
)


# -------------------------
# STATIC
# -------------------------

app.mount(
    "/static",
    StaticFiles(
        directory=str(
            BASE_DIR / "static"
        )
    ),
    name="static"
)


# -------------------------
# ROUTERS
# -------------------------

app.include_router(
    paginas_router
)

app.include_router(
    talleres_router
)

app.include_router(
    usuarios_router
)

app.include_router(
    reservas_router
)

app.include_router(
    googlec_router
)

app.include_router(
    seccion_router
)




