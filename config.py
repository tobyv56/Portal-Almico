from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from typing import Annotated
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import unicodedata
from datetime import date, time
from fastapi.responses import RedirectResponse
from fastapi import UploadFile, File

#bdd

DATABASE_URL ='postgresql://neondb_owner:npg_3xjveYGCoKZ2@ep-autumn-water-aduckv3c-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor(cursor_factory=RealDictCursor)

def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    return conn, cursor

#conexion pagina
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/reservas") 
async def mostrar_reservas(request: Request):
    return templates.TemplateResponse("reservas.html", {"request": request})

@app.get("/", response_class=HTMLResponse) 
async def mostrar_inicio(request: Request):

    conn, cursor = get_db()
    
    cursor.execute("""SELECT nombrecurso,fecha,hora,descripcion FROM curso
                      WHERE fecha >= CURRENT_DATE
                      ORDER BY fecha ASC
                      LIMIT 3""")
    
    cursos = cursor.fetchall()

    cursor.close()
    conn.close()

    return templates.TemplateResponse( 
    "index.html", {
        "request" : request,
        "cursos" : cursos
    }
    )

#cursos
@app.get("/cursos") 
async def mostrar_cursos(request: Request):
    return templates.TemplateResponse("cursos.html", {"request": request})

@app.post("/cursos/creacion", response_class=HTMLResponse)
async def creacion_cursos(nombreTaller: Annotated[str, Form()],
                          fecha: Annotated[date, Form()],
                          hora: Annotated[time, Form()],
                          descripcion: Annotated[str, Form()],
                          archivo: UploadFile = File(...)):
    
    query = f"INSERT INTO curso (nombrecurso,fecha,hora,descripcion) VALUES (%s,%s,%s,%s)"

    ruta_carpeta = "static/imagenes"
    os.makedirs(ruta_carpeta, exist_ok=True) 
    
    
    cursor.execute(query,(nombreTaller,fecha,hora,descripcion))
    conn.commit()

    return RedirectResponse(url="/cursos", status_code=303)

#TODO REVISAR UPLODEAD IMAGEN

@app.get("/presentacion") 
async def mostrar_presentacion(request: Request):
    return templates.TemplateResponse("quienes-somos.html", {"request": request})

@app.get("/ubicacion") 
async def mostrar_ubicacion(request: Request):
    return templates.TemplateResponse("ubicacion.html", {"request": request})

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/registro", response_class=HTMLResponse)
def proceso_turno(nombre: Annotated[str, Form()], 
    numTelefono: Annotated[str, Form()], 
    email: Annotated[str, Form()],
    request: Request
):
    if not nombre.strip():
        return templates.TemplateResponse("reservas.html", {
            "request": request,
            "mensaje": "Nombre inválido: no puede estar vacío"
        })
        
    if len(numTelefono) != 10:
        return templates.TemplateResponse("reservas.html", {
            "request": request,
            "mensaje": "numero de telefono invalido"
        })

    if "@gmail.com" not in email and "@hotmail.com" not in email:
        return templates.TemplateResponse("reservas.html", {
            "request": request,
            "mensaje": "email invalido"
        })
    
    return templates.TemplateResponse("reservas.html", {
        "request": request,
        "mensaje": f"¡Genial {nombre}! Turno registrado."
    })



    



    



