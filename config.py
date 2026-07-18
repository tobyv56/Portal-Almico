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

DATABASE_URL = 'postgresql://neondb_owner:npg_3xjveYGCoKZ2@ep-autumn-water-aduckv3c-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'

def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    return conn, cursor

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

scheduler = BackgroundScheduler()

def eliminar_talleres_viejos():
    conn, cursor = get_db()
    
    cursor.execute("""
                    DELETE FROM curso
                    WHERE (fecha + hora) < NOW();
                    """)
    
    conn.commit()
    cursor.close()
    conn.close()

scheduler.add_job(
    eliminar_talleres_viejos,
    "cron",
    hour=0,
    minute=0)

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
async def mostrar_cursos(request: Request):
    conn, cursor = get_db()
    
    cursor.execute("""SELECT nombrecurso,fecha,hora,descripcion,imagen FROM curso
                      WHERE fecha >= CURRENT_DATE
                      ORDER BY fecha ASC
                      LIMIT 6""")
    
    talleres = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return templates.TemplateResponse(
        request=request, 
        name="cursos.html",
        context={
            "request": request,
            "talleres" : talleres
        }
    )

@app.post("/cursos/creacion", response_class=HTMLResponse)

async def creacion_cursos(
    nombreTaller: Annotated[str, Form()],
    fecha: Annotated[date, Form()],
    hora: Annotated[time, Form()],
    descripcion: Annotated[str, Form()],
    archivo: UploadFile = File(...)
):
    ruta_carpeta = os.path.join("static", "imagenes")
    os.makedirs(ruta_carpeta, exist_ok=True)
    
    await archivo.seek(0)
    nombre_imagen = f"{uuid.uuid4()}_{archivo.filename}"
    ruta_archivo = os.path.join(ruta_carpeta, nombre_imagen)
    
    conn, cursor = get_db() # Usamos la función para evitar conexiones caídas
   
    try:
        with open(ruta_archivo, "wb") as buffer:
            shutil.copyfileobj(archivo.file, buffer)
            
        query = "INSERT INTO curso (nombrecurso, fecha, hora, descripcion, imagen) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (nombreTaller, fecha, hora, descripcion, nombre_imagen))
        conn.commit()
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

    return RedirectResponse(url="/cursos", status_code=303)

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




