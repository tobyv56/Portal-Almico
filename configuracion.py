# configuracion.py

import os
from pathlib import Path

import cloudinary
from dotenv import load_dotenv
from fastapi.templating import Jinja2Templates

# Carpeta principal del proyecto
BASE_DIR = Path(__file__).resolve().parent

# Carga el archivo .env cuando trabajás localmente
load_dotenv(BASE_DIR / ".env")

# Variables de entorno
DATABASE_URL = os.getenv("DATABASE_URL")

CLOUDINARY_CLOUD_NAME = os.getenv(
    "CLOUDINARY_CLOUD_NAME"
)

CLOUDINARY_API_KEY = os.getenv(
    "CLOUDINARY_API_KEY"
)

CLOUDINARY_API_SECRET = os.getenv(
    "CLOUDINARY_API_SECRET"
)

# Configuración de Cloudinary
cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
    secure=True
)

# Configuración de Jinja
templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)