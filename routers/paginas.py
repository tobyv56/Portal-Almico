from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from configuracion import templates
from database import get_db

router = APIRouter(
    tags=["Páginas"]
)

def contexto_sesion(request: Request):
    id_usuario = request.session.get("idusuario")
    rol_usuario = request.session.get("rol")

    return {
        "idusuario": id_usuario,
        "rol_usuario": rol_usuario,
        "usuario_logueado": id_usuario is not None,
        "es_admin": rol_usuario == "admin"
    }


@router.get("/", response_class=HTMLResponse)
def mostrar_login(
    request: Request,
    mensaje: str | None = None,
    tipo: str | None = None
):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "mensaje": mensaje,
            "tipo": tipo
        }
    )

@router.get("/inicio", response_class=HTMLResponse)
def mostrar_inicio(request: Request):

    id_usuario = request.session.get("idusuario")

    if id_usuario is None:
        return RedirectResponse(
            url="/?mensaje=Debes+iniciar+sesion&tipo=warning",
            status_code=303
        )

    conn, cursor = get_db()

    try:
        cursor.execute(
            """
            SELECT
                nombrecurso,
                mes,
                descripcion,
                imagen
            FROM curso
            ORDER BY idcurso DESC
            LIMIT 3
            """
        )

        talleres = cursor.fetchall()

        rol_usuario = request.session.get("rol")

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "idusuario": id_usuario,
                "rol_usuario": rol_usuario,
                "es_admin": rol_usuario == "admin",
                "talleres": talleres
            }
        )

    except Exception as error:
        print("ERROR AL OBTENER TALLERES:", repr(error))
        raise

    finally:
        cursor.close()
        conn.close()


@router.get("/presentacion", response_class=HTMLResponse)
def mostrar_presentacion(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="quienes-somos.html",
        context={
            **contexto_sesion(request)
        }
    )


@router.get("/ubicacion", response_class=HTMLResponse)
def mostrar_ubicacion(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="ubicacion.html",
        context={
            **contexto_sesion(request)
        }
    )


@router.get("/health")
def health():
    return {"status": "ok"}