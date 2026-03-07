from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from typing import Annotated
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/reservas") 
async def mostrar_reservas(request: Request):
    return templates.TemplateResponse("reservas.html", {"request": request})

@app.get("/") 
async def mostrar_inicio(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/cursos") 
async def mostrar_cursos(request: Request):
    return templates.TemplateResponse("cursos.html", {"request": request})

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
    

    
