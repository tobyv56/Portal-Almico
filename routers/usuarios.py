from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from typing import Annotated

from configuracion import templates
from fastapi.responses import HTMLResponse, RedirectResponse

from configuracion import templates
from database import get_db
import traceback

from routers.seguridad import (
    hashear_contrasena,
    verificar_contrasena
)

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios"]
)

class Usuario:

    def __init__(
        self,
        nombre_apellido,
        email,
        contrasena,
        telefono,
        rol="usuario"
    ):
        self.nombre_apellido = nombre_apellido
        self.email = email
        self.contrasena = contrasena
        self.telefono = telefono
        self.rol = rol

    def tiene_permisos(self):
        return self.rol == "admin"


class Admin(Usuario):

    def __init__(
        self,
        nombre_apellido,
        email,
        contrasena,
        telefono
    ):
        super().__init__(
            nombre_apellido,
            email,
            contrasena,
            telefono,
            rol="admin"
        )

    def agregar_taller(self, taller, repositorio):
        repositorio.creacion_taller(taller)

    def eliminar_taller(self, nombre_taller, repositorio):
        return repositorio.eliminacion_taller(
            nombre_taller
        )


class RepositorioUsuario:

    def __init__(self, cursor):
        self.cursor = cursor

    def buscar_por_email(self, email):
        self.cursor.execute(
            """
            SELECT
                idusuario,
                nyap,
                email,
                contrasena,
                numTelefono,
                rol
            FROM usuario
            WHERE LOWER(TRIM(email)) = %s
            LIMIT 1
            """,
            (email,)
        )

        return self.cursor.fetchone()

    def buscar_rol(self,email):
        self.cursor.execute(
            """
            SELECT 
                rol
            FROM usuario
            WHERE email = %s
            """,
            (email,)
        )

        return self.cursor.fetchone()
    
    def crear_usuario(self, usuario):
        self.cursor.execute(
            """
            INSERT INTO usuario (
                nyap,
                email,
                contrasena,
                numTelefono,
                rol
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                usuario.nombre_apellido,
                usuario.email,
                usuario.contrasena,
                usuario.telefono,
                usuario.rol
            )
        )

    def eliminar_usuario(self, usuario):
        self.cursor.execute(
            """
            DELETE FROM usuarios
            WHERE email = %s
            """,
            (usuario.email,)
        )

        return self.cursor.rowcount > 0


@router.get(
    "/registro",
    response_class=HTMLResponse
)
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
def iniciar_sesion(
    request: Request,
    email: Annotated[str, Form()],
    contrasena: Annotated[str, Form()]
):
    conn, cursor = get_db()

    try:
        repositorio_usuario = RepositorioUsuario(cursor)

        email_normalizado = email.strip().lower()

        usuario_encontrado = repositorio_usuario.buscar_por_email(
            email_normalizado
        )

        if usuario_encontrado is None:
            return RedirectResponse(
                url="/?mensaje=Email+o+contraseña+incorrectos&tipo=warning",
                status_code=303
            )

        contrasena_correcta = verificar_contrasena(
            contrasena,
            usuario_encontrado["contrasena"]
        )

        if not contrasena_correcta:
            return RedirectResponse(
                url="/?mensaje=Email+o+contraseña+incorrectos&tipo=warning",
                status_code=303
            )

        rol_usuario = usuario_encontrado["rol"].strip().lower()

        if rol_usuario not in ("usuario", "admin"):
            request.session.clear()

            return RedirectResponse(
                url="/?mensaje=Rol+de+usuario+invalido&tipo=error",
                status_code=303
            )

        if rol_usuario == "admin":
            return templates.TemplateResponse(
                    request=request,
                    name="admin.html",
                    context={
                        "mensaje": mensaje,
                        "tipo": tipo
                    }
            )

        request.session["idusuario"] = usuario_encontrado["idusuario"]
        request.session["rol"] = rol_usuario

        return RedirectResponse(
            url="/inicio",
            status_code=303
        )

    except Exception as error:
        print("ERROR REAL DEL LOGIN:", repr(error))
        traceback.print_exc()
        raise

    finally:
        cursor.close()
        conn.close()

@router.get("/",response_class=HTMLResponse)
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
            })

@router.get("/registroUsuario",response_class=HTMLResponse)
def mostrar_registro( request: Request,
    mensaje: str | None = None,
    tipo: str | None = None):
    return templates.TemplateResponse(
        request=request,
        name="registro.html",
        context={
            "mensaje": mensaje,
            "tipo": tipo
        }
    )

@router.get("/admin",response_class=HTMLResponse)
def mostrar_administracion(request: Request,
                           mensaje: str | None = None,
                           tipo: str | None = None):
    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "mensaje": mensaje,
            "tipo": tipo
        }
    )

@router.post("/registro", response_class=HTMLResponse)
def registro_usuario(
    request: Request,
    telefono: Annotated[str, Form()], 
    email: Annotated[str, Form()],
    contrasena: Annotated[str, Form()],
    confirmarContrasena: Annotated[str, Form()], 
    nombreApellido: Annotated[str, Form()]
):

    conn, cursor = get_db()

    if contrasena != confirmarContrasena:
        return RedirectResponse(
            url=(
                "/usuarios/registro"
                "?mensaje=Las+contraseñas+no+coinciden"
                "&tipo=warning"
            ),
            status_code=303
        )

    if not telefono.isdigit() or len(telefono) != 10:
        return RedirectResponse(
            url=(
                "/usuarios/registro"
                "?mensaje=El+telefono+debe+tener+10+numeros"
                "&tipo=warning"
            ),
            status_code=303
        )

    try: 
        repositorioUsuario = RepositorioUsuario(cursor)

        email_normalizado = email.strip().lower()
        contrasena_hasheada = hashear_contrasena(contrasena)

        usuario_existente = repositorioUsuario.buscar_por_email(email_normalizado)

        if usuario_existente is not None:

           return RedirectResponse(
               url=(
                   "/usuarios/registro"
                   "?mensaje=Ya+existe+una+cuenta+con+ese+email"
                   "&tipo=warning"
                ),
               status_code=303
           )

        usuario = Usuario(nombreApellido,email,contrasena_hasheada,telefono,rol="usuario")

        repositorioUsuario.crear_usuario(usuario)
        conn.commit()

        return RedirectResponse(
        url=(
        "/usuarios/registro"
        "?mensaje=Cuenta+creada+correctamente"
        "&tipo=success"
        ),
        status_code=303
        )

    except Exception as error:
        conn.rollback()

        print(
            "Error al registrar usuario:",
            repr(error)
        )

        return RedirectResponse(
            url=(
                "/usuarios/registro"
                "?mensaje=No+se+pudo+crear+la+cuenta"
                "&tipo=error"
            ),
            status_code=303
        )

    finally:
        cursor.close()
        conn.close()

@router.get("/administracion", response_class=HTMLResponse)
def mostrar_administracion(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="administracion.html",
        context={}
    )

