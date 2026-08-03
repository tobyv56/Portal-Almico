from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from configuracion import templates
from database import get_db

router = APIRouter(
    tags=["Páginas"]
)

class Reserva:
    def __init__(self,facilitadora,seccion,fecha,horario,usuario):
        self.facilitadora = facilitadora
        self.seccion = seccion
        self.fecha = fecha
        self.horario = horario
        self.usuario = usuario

class RepositorioReserva:
    def __init__(self,cursor):
        self.cursor = cursor

    def crear_reserva(self, reserva):
        self.cursor.execute(
        """
        INSERT INTO reserva (
            facilitadora,
            seccion,
            fecha,
            horario,
            idusuario
        )
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            reserva.facilitadora,
            reserva.seccion,
            reserva.fecha,
            reserva.horario,
            reserva.usuario.idusuario
        )
    )

@router.get("/reservas", response_class=HTMLResponse)
def mostrar_reserva(
    request: Request,
    mensaje: str | None = None,
    tipo: str | None = None
):
    return templates.TemplateResponse(
            request=request,
            name="reservas.html",
            context={
                "mensaje": mensaje,
                "tipo": tipo
            }
        )