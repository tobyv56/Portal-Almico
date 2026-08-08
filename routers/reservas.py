from fastapi import APIRouter, Request, Form,HTTPException
from fastapi.responses import HTMLResponse
from typing import Annotated

from configuracion import templates
from fastapi.responses import HTMLResponse, RedirectResponse

from configuracion import templates
from database import get_db
import traceback

from datetime import date
from routers.google_calendar import crear_evento_google

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

    def obtener_horarios_ocupados(self, facilitadora, fecha):
        self.cursor.execute(
        """
        SELECT TO_CHAR(hora, 'HH24:MI') AS horario
        FROM turno
        WHERE facilitadora = %s
          AND fecha = %s
        """,
        (facilitadora, fecha)
        )

        filas = self.cursor.fetchall()

        return [
            fila["horario"]
            for fila in filas
        ]

    def horario_esta_ocupado(
    self,
    facilitadora,
    fecha,
    horario
    ):
        self.cursor.execute(
        """
        SELECT 1
        FROM turno
        WHERE facilitadora = %s
          AND fecha = %s
          AND hora = %s
        LIMIT 1
        """,
        (
            facilitadora,
            fecha,
            horario
        )
    )

        return self.cursor.fetchone() is not None
    
@router.post("/reservas")
def realizar_reserva(
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

    facilitadora = facilitadora.strip()
    seccion = seccion.strip()
    fecha = fecha.strip()
    horario = horario.strip()
    nyap = nyap.strip()
    email = email.strip().lower()

    telefono_normalizado = (
        telefono
        .strip()
        .replace(" ", "")
        .replace("-", "")
    )

    # Validaciones
    if not all([
        facilitadora,
        seccion,
        fecha,
        horario,
        nyap,
        telefono_normalizado,
        email
    ]):
        return RedirectResponse(
            "/reservas?mensaje=Completa+todos+los+campos&tipo=warning",
            status_code=303
        )

    if not telefono_normalizado.isdigit():
        return RedirectResponse(
            "/reservas?mensaje=El+telefono+no+es+valido&tipo=warning",
            status_code=303
        )

    try:
        conn, cursor = get_db()

        repositorio_reserva = RepositorioReserva(cursor)

        # Verificar horario ocupado
        if repositorio_reserva.horario_esta_ocupado(
            facilitadora,
            fecha,
            horario
        ):
            return RedirectResponse(
                (
                    "/reservas"
                    "?mensaje=Ese+horario+ya+fue+reservado"
                    "&tipo=warning"
                ),
                status_code=303
            )

        # Crear reserva
        reserva = Reserva(
            facilitadora=facilitadora,
            seccion=seccion,
            fecha=fecha,
            horario=horario,
            nyap=nyap,
            email=email,
            telefono=telefono_normalizado
        )

        repositorio_reserva.crear_reserva(reserva)

        # Primero aseguramos la reserva en nuestra BD
        conn.commit()

        # Después intentamos Google Calendar
        try:
            evento_google = crear_evento_google(reserva)

            print(
                "EVENTO GOOGLE CREADO:",
                evento_google["id"]
            )

        except Exception as error_google:
            print(
                "ERROR GOOGLE CALENDAR:",
                repr(error_google)
            )

            return RedirectResponse(
                url=(
                    "/reservas"
                    "?mensaje=El+turno+se+guardo+pero+"
                    "no+se+pudo+agendar+en+Calendar"
                    "&tipo=warning"
                ),
                status_code=303
            )

        # Si BD y Google salieron bien
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

        print(
            "ERROR AL REALIZAR LA RESERVA:",
            repr(error)
        )

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

@router.get("/reservas/horarios-ocupados")
def mostrar_horarios_ocupados(
    facilitadora: str,
    fecha: str
):
    conn = None
    cursor = None

    try:
        conn, cursor = get_db()

        repositorio = RepositorioReserva(cursor)

        horarios = repositorio.obtener_horarios_ocupados(
            facilitadora,
            fecha
        )

        return {
            "horarios": horarios
        }

    finally:
        if cursor is not None:
            cursor.close()

        if conn is not None:
            conn.close()
