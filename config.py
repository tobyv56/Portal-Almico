import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from routers.paginas import router as paginas_router
from routers.talleres import router as talleres_router
from routers.usuarios import router as usuarios_router
from routers.reservas import router as reservas_router

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env", override=True)

app = FastAPI()


SESSION_SECRET = os.getenv("GOOGLE_SESSION_SECRET")

if not SESSION_SECRET:
    raise RuntimeError("Falta SESSION_SECRET en el archivo .env")


app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site="lax",
    https_only=False
)

app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static"
)

app.include_router(paginas_router)
app.include_router(talleres_router)
app.include_router(usuarios_router)
app.include_router(reservas_router)



    
    




