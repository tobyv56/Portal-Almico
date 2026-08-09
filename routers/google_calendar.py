import os

from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from googleapiclient.discovery import build


router = APIRouter(
    prefix="/admin/google",
    tags=["Google Calendar"]
)


SCOPES = [
    "https://www.googleapis.com/auth/calendar"
]


# ---------------------------------------------------------
# CREAR FLUJO OAUTH
# ---------------------------------------------------------

def crear_flow():
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")

    if not client_id:
        raise RuntimeError("Falta GOOGLE_CLIENT_ID")

    if not client_secret:
        raise RuntimeError("Falta GOOGLE_CLIENT_SECRET")

    if not redirect_uri:
        raise RuntimeError("Falta GOOGLE_REDIRECT_URI")

    return Flow.from_client_config(
        {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        },
        scopes=SCOPES,
        redirect_uri=redirect_uri,
        autogenerate_code_verifier=True
    )

# ---------------------------------------------------------
# CONECTAR GOOGLE CALENDAR
# GET /admin/google/conectar
# ---------------------------------------------------------

@router.get("/conectar")
def conectar_google(request: Request):

    flow = crear_flow()

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )

    # Guardamos estos datos para poder validar el callback.
    request.session["google_oauth_state"] = state

    request.session[
        "google_code_verifier"
    ] = flow.code_verifier

    return RedirectResponse(
        authorization_url
    )


# ---------------------------------------------------------
# CALLBACK DE GOOGLE
# GET /admin/google/callback
# ---------------------------------------------------------

@router.get("/callback")
def google_callback(
    request: Request,
    code: str,
    state: str
):

    state_guardado = request.session.get(
        "google_oauth_state"
    )

    code_verifier = request.session.get(
        "google_code_verifier"
    )

    if not state_guardado:
        return RedirectResponse(
            (
                "/admin/"
                "?mensaje=La+sesion+OAuth+expiro"
                "&tipo=error"
            ),
            status_code=303
        )

    if state != state_guardado:
        request.session.pop(
            "google_oauth_state",
            None
        )

        request.session.pop(
            "google_code_verifier",
            None
        )

        return RedirectResponse(
            (
                "/admin/"
                "?mensaje=Error+de+seguridad+OAuth"
                "&tipo=error"
            ),
            status_code=303
        )

    try:

        flow = crear_flow()

        # Tiene que ser el mismo verifier usado al iniciar OAuth.
        flow.code_verifier = code_verifier

        flow.fetch_token(
            code=code
        )

        credenciales = flow.credentials

        # NO imprimir el token real.
        print(
            "GOOGLE CONECTADO:",
            credenciales.refresh_token is not None
        )

        # Limpiamos datos temporales de OAuth.
        request.session.pop(
            "google_oauth_state",
            None
        )

        request.session.pop(
            "google_code_verifier",
            None
        )

        return RedirectResponse(
            (
                "/admin/"
                "?mensaje=Google+Calendar+conectado"
                "&tipo=success"
            ),
            status_code=303
        )

    except Exception as error:

        print(
            "ERROR CALLBACK GOOGLE:",
            repr(error)
        )

        return RedirectResponse(
            (
                "/admin/"
                "?mensaje=No+se+pudo+conectar+Google+Calendar"
                "&tipo=error"
            ),
            status_code=303
        )


# ---------------------------------------------------------
# CREDENCIALES PARA CREAR EVENTOS
# ---------------------------------------------------------

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
            "Falta REFRESH_TOKEN"
        )

    credenciales = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=(
            "https://oauth2.googleapis.com/token"
        ),
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES
    )

    credenciales.refresh(
        GoogleRequest()
    )

    return credenciales


# ---------------------------------------------------------
# CREAR EVENTO
# ---------------------------------------------------------

def crear_evento_google(reserva):

    credenciales = (
        obtener_credenciales_google()
    )

    servicio = build(
        "calendar",
        "v3",
        credentials=credenciales,
        cache_discovery=False
    )

    zona_horaria = ZoneInfo(
        "America/Argentina/Buenos_Aires"
    )

    # Fecha
    if isinstance(reserva.fecha, date):

        fecha_reserva = reserva.fecha

    else:

        fecha_reserva = date.fromisoformat(
            str(reserva.fecha)
        )

    # Hora
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

    # Por ahora cada sesión dura una hora.
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
            f"Facilitadora: "
            f"{reserva.facilitadora}\n"
            f"Paciente: {reserva.nyap}\n"
            f"Teléfono: {reserva.telefono}\n"
            f"Email: {reserva.email}"
        ),

        "start": {
            "dateTime":
                inicio.isoformat(),

            "timeZone":
                "America/Argentina/Buenos_Aires"
        },

        "end": {
            "dateTime":
                fin.isoformat(),

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
