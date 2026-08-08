import os

from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from googleapiclient.discovery import build


SCOPES = [
    "https://www.googleapis.com/auth/calendar"
]


def obtener_credenciales_google():

    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    refresh_token = os.getenv("GOOGLE_REFRESH_TOKEN")

    if not client_id:
        raise RuntimeError(
            "Falta GOOGLE_CLIENT_ID"
        )

    if not client_secret:
        raise RuntimeError(
            "Falta GOOGLE_CLIENT_SECRET"
        )

    if not refresh_token:
        raise RuntimeError(
            "Falta GOOGLE_REFRESH_TOKEN"
        )

    credenciales = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES
    )

    # Obtiene automáticamente un access token nuevo
    credenciales.refresh(
        GoogleRequest()
    )

    return credenciales


def crear_evento_google(reserva):

    credenciales = obtener_credenciales_google()

    servicio = build(
        "calendar",
        "v3",
        credentials=credenciales,
        cache_discovery=False
    )

    zona_horaria = ZoneInfo(
        "America/Argentina/Buenos_Aires"
    )

    # La reserva actualmente recibe strings desde Form()
    if isinstance(reserva.fecha, date):
        fecha = reserva.fecha
    else:
        fecha = date.fromisoformat(
            str(reserva.fecha)
        )

    if isinstance(reserva.horario, time):
        hora = reserva.horario
    else:
        hora = time.fromisoformat(
            str(reserva.horario)
        )

    inicio = datetime.combine(
        fecha,
        hora,
        tzinfo=zona_horaria
    )

    # Por ahora suponemos sesiones de 1 hora
    fin = inicio + timedelta(hours=1)

    evento = {
        "summary": (
            f"{reserva.seccion} - "
            f"{reserva.nyap}"
        ),

        "description": (
            f"Sesión: {reserva.seccion}\n"
            f"Facilitadora: {reserva.facilitadora}\n"
            f"Paciente: {reserva.nyap}\n"
            f"Teléfono: {reserva.telefono}\n"
            f"Email: {reserva.email}"
        ),

        "start": {
            "dateTime": inicio.isoformat(),
            "timeZone":
                "America/Argentina/Buenos_Aires"
        },

        "end": {
            "dateTime": fin.isoformat(),
            "timeZone":
                "America/Argentina/Buenos_Aires"
        }
    }

    evento_creado = (
        servicio
        .events()
        .insert(
            calendarId="primary",
            body=evento
        )
        .execute()
    )

    return evento_creado