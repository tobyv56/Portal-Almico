from typing import Annotated

from fastapi import (
    APIRouter,
    Request,
    Form,
    HTTPException
)

from fastapi.responses import (
    HTMLResponse,
    RedirectResponse
)

from configuracion import templates
from database import get_db

from modelos.usuario import Usuario
from repositorios.usuario import RepositorioUsuario

from seguridad import (
    hashear_contrasena,
    verificar_contrasena
)


router = APIRouter(
    prefix="/admin",
    tags=["Administracion"]
)


# =========================================================
# REGISTRO
# =========================================================

@router.get("/registro", response_class=HTMLResponse)
def mostrar_registro(
    request: Request,
    mensaje: str | None = None,
    tipo: str | None = None
):
    return templates.TemplateResponse(
        request=request,
        name="registro.html",
        context={
            "mensaje": mensaje,
            "tipo": tipo
        }
    )


@router.post("/registro")
def registro_usuario(
    request: Request,
    telefono: Annotated[str, Form()],
    email: Annotated[str, Form()],
    contrasena: Annotated[str, Form()],
    confirmarContrasena: Annotated[str, Form()],
    nombreApellido: Annotated[str, Form()]
):

    conn = None
    cursor = None

    try:

        # -------------------------------------------------
        # NORMALIZAR DATOS
        # -------------------------------------------------

        nombreApellido = nombreApellido.strip()
        email = email.strip().lower()
        telefono = telefono.strip()

        # -------------------------------------------------
        # VALIDAR CONTRASEÑAS
        # -------------------------------------------------

        if contrasena != confirmarContrasena:

            return RedirectResponse(
                url=(
                    "/admin/registro"
                    "?mensaje=Las+contraseñas+no+coinciden"
                    "&tipo=warning"
                ),
                status_code=303
            )

        # -------------------------------------------------
        # VALIDAR TELÉFONO
        # -------------------------------------------------

        if not telefono.isdigit() or len(telefono) != 10:

            return RedirectResponse(
                url=(
                    "/admin/registro"
                    "?mensaje=El+telefono+debe+tener+10+numeros"
                    "&tipo=warning"
                ),
                status_code=303
            )

        # -------------------------------------------------
        # CONEXIÓN
        # -------------------------------------------------

        conn, cursor = get_db()

        repositorio_usuario = RepositorioUsuario(
            cursor
        )

        # -------------------------------------------------
        # VERIFICAR EMAIL
        # -------------------------------------------------

        usuario_existente = (
            repositorio_usuario
            .buscar_por_email(email)
        )

        if usuario_existente is not None:

            return RedirectResponse(
                url=(
                    "/admin/registro"
                    "?mensaje=Ya+existe+una+cuenta+con+ese+email"
                    "&tipo=warning"
                ),
                status_code=303
            )

        # -------------------------------------------------
        # HASHEAR CONTRASEÑA
        # -------------------------------------------------

        contrasena_hasheada = (
            hashear_contrasena(contrasena)
        )

        # -------------------------------------------------
        # CREAR USUARIO
        # -------------------------------------------------

        usuario = Usuario(
            nombreApellido,
            email,
            contrasena_hasheada,
            telefono,
            rol="usuario"
        )

        repositorio_usuario.crear_usuario(
            usuario
        )

        conn.commit()

        # -------------------------------------------------
        # REGISTRO EXITOSO
        # -------------------------------------------------

        return RedirectResponse(
            url=(
                "/admin/registro"
                "?mensaje=Cuenta+creada+correctamente"
                "&tipo=success"
            ),
            status_code=303
        )

    except Exception as error:

        if conn is not None:
            conn.rollback()

        print(
            "ERROR AL REGISTRAR USUARIO:",
            repr(error)
        )

        return RedirectResponse(
            url=(
                "/admin/registro"
                "?mensaje=No+se+pudo+crear+la+cuenta"
                "&tipo=error"
            ),
            status_code=303
        )

    finally:

        if cursor is not None:
            cursor.close()

        if conn is not None:
            conn.close()


# =========================================================
# LOGIN ADMIN
# =========================================================

@router.get("/login", response_class=HTMLResponse)
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


@router.post("/login")
def iniciar_sesion_admin(
    request: Request,
    email: Annotated[str, Form()],
    contrasena: Annotated[str, Form()]
):

    conn = None
    cursor = None

    try:

        conn, cursor = get_db()

        repositorio_usuario = (
            RepositorioUsuario(cursor)
        )

        email_normalizado = (
            email.strip().lower()
        )

        admin_encontrado = (
            repositorio_usuario
            .buscar_por_email(email_normalizado)
        )

        # -------------------------------------------------
        # EMAIL NO EXISTE
        # -------------------------------------------------

        if admin_encontrado is None:

            return RedirectResponse(
                url=(
                    "/admin/login"
                    "?mensaje=Credenciales+incorrectas"
                    "&tipo=warning"
                ),
                status_code=303
            )

        # -------------------------------------------------
        # VERIFICAR CONTRASEÑA
        # -------------------------------------------------

        contrasena_correcta = (
            verificar_contrasena(
                contrasena,
                admin_encontrado["contrasena"]
            )
        )

        rol = (
            admin_encontrado["rol"]
            .strip()
            .lower()
        )

        # -------------------------------------------------
        # SOLO ADMIN
        # -------------------------------------------------

        if not contrasena_correcta or rol != "admin":

            request.session.clear()

            return RedirectResponse(
                url=(
                    "/admin/login"
                    "?mensaje=Credenciales+incorrectas"
                    "&tipo=warning"
                ),
                status_code=303
            )

        # -------------------------------------------------
        # CREAR SESIÓN
        # -------------------------------------------------

        request.session.clear()

        request.session["idusuario"] = (
            admin_encontrado["idusuario"]
        )

        request.session["rol"] = "admin"

        return RedirectResponse(
            url="/admin/",
            status_code=303
        )

    except Exception as error:

        print(
            "ERROR LOGIN ADMIN:",
            repr(error)
        )

        return RedirectResponse(
            url=(
                "/admin/login"
                "?mensaje=No+se+pudo+iniciar+sesion"
                "&tipo=error"
            ),
            status_code=303
        )

    finally:

        if cursor is not None:
            cursor.close()

        if conn is not None:
            conn.close()


# =========================================================
# PANEL ADMIN
# =========================================================

@router.get("/", response_class=HTMLResponse)
def mostrar_panel_admin(
    request: Request,
    mensaje: str | None = None,
    tipo: str | None = None
):

    idusuario = request.session.get(
        "idusuario"
    )

    rol = request.session.get(
        "rol"
    )

    # -------------------------------------------------
    # VERIFICAR SESIÓN
    # -------------------------------------------------

    if idusuario is None or rol != "admin":

        request.session.clear()

        return RedirectResponse(
            url=(
                "/admin/login"
                "?mensaje=Debes+iniciar+sesion+como+administrador"
                "&tipo=warning"
            ),
            status_code=303
        )

    conn = None
    cursor = None

    try:

        conn, cursor = get_db()

        # -------------------------------------------------
        # OBTENER USUARIOS
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                email,
                nyap
            FROM usuario
            ORDER BY nyap
            """
        )

        usuarios = cursor.fetchall()

        return templates.TemplateResponse(
            request=request,
            name="admin.html",
            context={
                "usuarios": usuarios,
                "mensaje": mensaje,
                "tipo": tipo
            }
        )

    except Exception as error:

        print(
            "ERROR AL MOSTRAR PANEL ADMIN:",
            repr(error)
        )

        raise

    finally:

        if cursor is not None:
            cursor.close()

        if conn is not None:
            conn.close()
