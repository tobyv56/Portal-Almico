from fastapi import APIRouter, Request, Form,HTTPException
from fastapi.responses import HTMLResponse
from typing import Annotated

from configuracion import templates
from fastapi.responses import HTMLResponse, RedirectResponse

from configuracion import templates
from database import get_db
import traceback

router = APIRouter(
    tags=["Páginas"]
)

class Reserva:
    def __init__(self,facilitadora,seccion,fecha,horario,nyap,email,telefono):
        self.facilitadora = facilitadora
        self.seccion = seccion
        self.fecha = fecha
        self.horario = horario
        self.nyap = nyap
        self.email = email
        self.telefono = telefono

class RepositorioReserva:

    def __init__(self, cursor):
        self.cursor = cursor

    def crear_reserva(self, reserva):
        self.cursor.execute(
            """
            INSERT INTO turno (
                facilitadora,
                seccion,
                fecha,
                hora,
                nyap,
                email,
                telefono
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                reserva.facilitadora,
                reserva.seccion,
                reserva.fecha,
                reserva.horario,
                reserva.nyap,
                reserva.email,
                reserva.telefono
            )
        )

    def obtener_reservas(self):
        self.cursor.execute(
            """
            SELECT
                seccion,
                fecha,
                hora AS horario,
                nyap,
                email
            FROM turno
            ORDER BY fecha ASC, hora ASC
            """
        )

        return self.cursor.fetchall()
    
@router.post("/reservas")
def realizar_reserva(
    request: Request,
    facilitadora: Annotated[str, Form()],
    seccion: Annotated[str, Form()],
    fecha: Annotated[str, Form()],
    horario: Annotated[str, Form()],
    nyap: Annotated[str, Form()],
    telefono: Annotated[str, Form()],
    email: Annotated[str, Form()]
):
    conn = None
    cursor = None

    try:
        conn, cursor = get_db()

        repositorio_reserva = RepositorioReserva(cursor)

        reserva = Reserva(
            facilitadora,
            seccion,
            fecha,
            horario,
            nyap,
            email,
            telefono
        )

        repositorio_reserva.crear_reserva(reserva)

        conn.commit()

        return RedirectResponse(
            url=(
                "/reservas"
                "?mensaje=Turno+reservado+correctamente"
                "&tipo=success"
            ),
            status_code=303
        )

    except Exception as error:
        if conn is not None:
            conn.rollback()

        print("ERROR AL REALIZAR LA RESERVA:", repr(error))

        return RedirectResponse(
            url=(
                "/reservas"
                "?mensaje=No+se+pudo+realizar+la+reserva"
                "&tipo=error"
            ),
            status_code=303
        )

    finally:
        if cursor is not None:
            cursor.close()

        if conn is not None:
            conn.close()

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
