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

    client_id = os.getenv(
        "GOOGLE_CLIENT_ID"
    )

    client_secret = os.getenv(
        "GOOGLE_CLIENT_SECRET"
    )

    refresh_token = os.getenv(
        "REFRESH_TOKEN"
    )

    credenciales = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES
    )

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

    if isinstance(reserva.fecha, date):
        fecha_reserva = reserva.fecha
    else:
        fecha_reserva = date.fromisoformat(
            str(reserva.fecha)
        )

    if isinstance(reserva.horario, time):
        hora_reserva = reserva.horario
    else:
        hora_reserva = time.fromisoformat(
            str(reserva.horario)
        )

    inicio = datetime.combine(
        fecha_reserva,
        hora_reserva,
        tzinfo=zona_horaria
    )

    fin = inicio + timedelta(
        hours=1
    )

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
