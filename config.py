from fastapi import FastAPI, Form, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import Annotated
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import uuid
import shutil
from datetime import date, time
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=True)

import cloudinary
import cloudinary.uploader

CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUD_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUD_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

print("Cloud name cargado:", bool(CLOUD_NAME))
print("API key cargada:", bool(CLOUD_API_KEY))
print("API secret cargado:", bool(CLOUD_API_SECRET))

cloudinary.config(
    cloud_name=CLOUD_NAME,
    api_key=CLOUD_API_KEY,
    api_secret=CLOUD_API_SECRET,
    secure=True
)

DATABASE_URL = os.getenv("DATABASE_URL")
def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    return conn, cursor

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

scheduler = BackgroundScheduler()

def eliminar_talleres_viejos():
    print("Limpiando talleres...")

    conn, cursor = get_db()

    cursor.execute("""
        DELETE FROM curso
        WHERE (fecha + hora) < CURRENT_TIMESTAMP;
    """)

    print(f"Eliminados: {cursor.rowcount}")

    conn.commit()

    cursor.close()
    conn.close()

scheduler.add_job(
    eliminar_talleres_viejos,
    "cron",
    minute=0,
    hour=0)

scheduler.start()

@app.get("/reservas") 
async def mostrar_reservas(request: Request):
    return templates.TemplateResponse( 
            request=request,
            name="reservas.html",
            context={"request": request})

@app.get("/", response_class=HTMLResponse) 
async def mostrar_inicio(request: Request):
    conn, cursor = get_db()
    
    cursor.execute("""SELECT nombrecurso,fecha,hora,imagen FROM curso
                      WHERE fecha >= CURRENT_DATE
                      ORDER BY fecha ASC
                      LIMIT 3""")
    
    cursos = cursor.fetchall()
    cursor.close()
    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"cursos": cursos}
    )

@app.get("/cursos", response_class=HTMLResponse)
def mostrar_cursos(
    request: Request,
    mensaje: str | None = None,
    tipo: str | None = None
):
    conn, cursor = get_db()

    try:
        cursor.execute("""
            SELECT nombrecurso, fecha, hora, descripcion, imagen
            FROM curso
            ORDER BY fecha ASC, hora ASC
        """)

        talleres = cursor.fetchall()

        return templates.TemplateResponse(
            request=request,
            name="cursos.html",
            context={
                "talleres": talleres,
                "mensaje": mensaje,
                "tipo": tipo
            }
        )

    except Exception as error:
        print("ERROR EN GET /cursos:", repr(error))
        raise

    finally:
        cursor.close()
        conn.close()

@app.post("/cursos/eliminacion", response_class=HTMLResponse)
def eliminar_taller(
    nombreTaller: Annotated[str,Form()]
):

    conn, cursor = get_db()

    try:
        cursor.execute(
                    """
                    DELETE FROM curso
                    where nombreCurso = %s
                    """,
                    (nombreTaller,)
                )

        if cursor.rowcount == 0:
            conn.rollback()

            return RedirectResponse(
                url="/cursos?mensaje=Taller no encontrado&tipo=warning",
                status_code=303
            )

        conn.commit()

        return RedirectResponse(
            url="/cursos?mensaje=Taller eliminado correctamente&tipo=success",
            status_code=303
        )

    except Exception as error:
        conn.rollback()
        print("Error al eliminar el taller:", error)

        return RedirectResponse(
            url="/cursos?mensaje=No se pudo eliminar el taller&tipo=error",
            status_code=303
        )

    finally:
        cursor.close()
        conn.close()

@app.post("/cursos/creacion", response_class=HTMLResponse)
def crear_taller(
    request: Request,
    nombrecurso: Annotated[str, Form()],
    fecha: Annotated[str, Form()],
    hora: Annotated[str, Form()],
    descripcion: Annotated[str, Form()],
    imagen: Annotated[UploadFile, File()]
):
    conn, cursor = get_db()

    try:
        resultado = cloudinary.uploader.upload(
            imagen.file,
            folder="portal-almico/cursos",
            resource_type="image"
        )

        url_imagen = resultado["secure_url"]

        cursor.execute(
            """
            INSERT INTO curso
                (nombrecurso, fecha, hora, descripcion, imagen)
            VALUES
                (%s, %s, %s, %s, %s)
            """,
            (
                nombrecurso,
                fecha,
                hora,
                descripcion,
                url_imagen
            )
        )

        conn.commit()

        return RedirectResponse(
            url="/cursos",
            status_code=303
        )

    except Exception as error:
        conn.rollback()

        print("Error al crear el taller:", error)

        return RedirectResponse(
            url="/cursos/creacion",
            status_code=303
        )

    finally:
        cursor.close()
        conn.close()

@app.get("/presentacion") 
async def mostrar_presentacion(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="quienes-somos.html",
        context={"request": request})

@app.get("/ubicacion") 
async def mostrar_ubicacion(request: Request):
    return templates.TemplateResponse(request=request,
                                      name="ubicacion.html", 
                                      context={"request": request})

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/registro", response_class=HTMLResponse)
def proceso_turno(
    request: Request,
    nombre: Annotated[str, Form()] = None,
    numTelefono: Annotated[str, Form()] = None,
    email: Annotated[str, Form()] = None,
    profesor: Annotated[str, Form()] = None,
    actividad: Annotated[str, Form()] = None,
    fecha: Annotated[str | None, Form()] = None,
    horario: Annotated[str | None, Form()] = None,
):
    # validacion horario
    if not horario:
        return templates.TemplateResponse(
            request=request,
            name="reservas.html",
            context={
                "request": request,
                "mensaje": "seleccione el horario.",
                "tipo": "error"
            }
    )
    
    # validacion fecha
    if not fecha:
        return templates.TemplateResponse(
            request=request,
            name="reservas.html",
            context={
                "request": request,
                "mensaje": "seleccione la fecha.",
                "tipo": "error"
            }
    )

    # validacion profesor 
    if not profesor:
        return templates.TemplateResponse(
            request=request,
            name="reservas.html",
            context={
                "request": request,
                "mensaje": "seleccione el profesor/a.",
                "tipo": "error"
            }
    )

    # validacion actividad
    if not actividad:
        return templates.TemplateResponse(
            request=request,
            name="reservas.html",
            context={
                "request": request,
                "mensaje": "seleccione la actividad.",
                "tipo": "error"
            }
    )

    # Validación del nombre
    if not nombre or not nombre.strip():
        return templates.TemplateResponse(
            request=request,
            name="reservas.html",
            context={
                "request": request,
                "mensaje": "El nombre no puede estar vacío.",
                "tipo": "error"
            }
    )

    # Validación del teléfono
    
    if not numTelefono or not numTelefono.strip():
        return templates.TemplateResponse(
            request=request,
            name="reservas.html",
            context={
                "request": request,
                "mensaje": "El número de teléfono no puede estar vacío.",
                "tipo": "warning"
            }
        )
    
    if not numTelefono.isdigit() or len(numTelefono) != 10:
        return templates.TemplateResponse(
            request=request,
            name="reservas.html",
            context={
                "request": request,
                "mensaje": "El número de teléfono es inválido.",
                "tipo": "warning"
            }
        )
    
    # Validación del email
    
    if not email or not email.strip():
        return templates.TemplateResponse(
            request=request,
            name="reservas.html",
            context={
                "request": request,
                "mensaje": "El correo no puede estar vacío.",
                "tipo": "warning"
            }
        )
    
    if "@gmail.com" not in email and "@hotmail.com" not in email:
        return templates.TemplateResponse(
            request=request,
            name="reservas.html",
            context={
                "request": request,
                "mensaje": "El email es inválido.",
                "tipo": "error"
            }
        )

    return templates.TemplateResponse(
        request=request,
        name="reservas.html",
        context={
            "request": request,
            "mensaje": f"¡Genial {nombre}! Tu turno fue registrado correctamente.",
            "tipo": "success"
        }
    )

    
    



