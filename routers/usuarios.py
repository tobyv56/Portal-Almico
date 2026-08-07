from fastapi import APIRouter, Request, Form,HTTPException
from fastapi.responses import HTMLResponse
from typing import Annotated

from configuracion import templates
from fastapi.responses import HTMLResponse, RedirectResponse
from routers.reservas import RepositorioReserva

from configuracion import templates
from database import get_db
import traceback

from routers.seguridad import (
    hashear_contrasena,
    verificar_contrasena
)

router = APIRouter(
    prefix="/admin",
    tags=["Administracion"]
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
                nyap AS nombre_apellido,
                email,
                contrasena,
                numTelefono AS telefono,
                rol
            FROM usuario
            WHERE LOWER(TRIM(email)) = %s
            LIMIT 1
            """,
            (email.strip().lower(),)
        )

        return self.cursor.fetchone()

    def buscar_por_id(self, idusuario):
        self.cursor.execute(
            """
            SELECT
                idusuario,
                nyap AS nombre_apellido,
                email,
                contrasena,
                numTelefono AS telefono,
                rol
            FROM usuario
            WHERE idusuario = %s
            LIMIT 1
            """,
            (idusuario,)
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
            DELETE FROM usuario
            WHERE email = %s
            """,
            (usuario.email,)
        )

        return self.cursor.rowcount > 0

def obtener_usuario_actual(request: Request) -> Usuario:

    print("SESIÓN AL CREAR TALLER:", dict(request.session))

    idusuario = request.session.get("idusuario")

    print("ID LEÍDO DE LA SESIÓN:", idusuario)

    if idusuario is None:
        raise HTTPException(
            status_code=401,
            detail="Debes iniciar sesión"
        )

    conn = None
    cursor = None

    try:
        conn, cursor = get_db()

        repositorio_usuario = RepositorioUsuario(cursor)

        fila_usuario = repositorio_usuario.buscar_por_id(
            idusuario
        )

        print("FILA BUSCADA POR ID:", fila_usuario)

        if fila_usuario is None:
            request.session.clear()

            raise HTTPException(
                status_code=401,
                detail="El usuario de la sesión no existe"
            )

        rol = fila_usuario["rol"].strip().lower()

        usuario_actual = Usuario(
            nombre_apellido=fila_usuario["nombre_apellido"],
            email=fila_usuario["email"],
            contrasena=fila_usuario["contrasena"],
            telefono=fila_usuario["telefono"],
            rol=rol
        )

        print("EMAIL RECUPERADO:", usuario_actual.email)
        print("ROL RECUPERADO:", repr(usuario_actual.rol))
        print("PERMISOS:", usuario_actual.tiene_permisos())

        return usuario_actual

    finally:
        if cursor is not None:
            cursor.close()

        if conn is not None:
            conn.close()

@router.get("/registro",response_class=HTMLResponse)
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

@router.get("/login",response_class=HTMLResponse)
def mostrar_login( request: Request,
                   mensaje: str | None = None,
                   tipo: str | None = None):
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

        repositorio_usuario = RepositorioUsuario(cursor)

        email_normalizado = email.strip().lower()

        admin_encontrado = repositorio_usuario.buscar_por_email(
            email_normalizado
        )

        if admin_encontrado is None:
            return RedirectResponse(
                url=(
                    "/admin/login"
                    "?mensaje=Credenciales+incorrectas"
                    "&tipo=warning"
                ),
                status_code=303
            )

        contrasena_correcta = verificar_contrasena(
            contrasena,
            admin_encontrado["contrasena"]
        )

        rol = admin_encontrado["rol"].strip().lower()

        # Solo puede entrar una cuenta administradora
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

        request.session.clear()

        request.session["idusuario"] = admin_encontrado["idusuario"]
        request.session["rol"] = "admin"

        return RedirectResponse(
            url="/admin/",
            status_code=303
        )

    except Exception as error:
        print("ERROR LOGIN ADMIN:", repr(error))

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

@router.get("/", response_class=HTMLResponse)
def mostrar_panel_admin(
    request: Request,
    mensaje: str | None = None,
    tipo: str | None = None
):
    idusuario = request.session.get("idusuario")
    rol = request.session.get("rol")

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

        repositorio_reserva = RepositorioReserva(cursor)
        reservas = repositorio_reserva.obtener_reservas()

        cursor.execute(
            """
            SELECT email, nyap
            FROM usuario
            ORDER BY nyap
            """
        )

        usuarios = cursor.fetchall()

        print("RESERVAS ENCONTRADAS:", reservas)

        return templates.TemplateResponse(
            request=request,
            name="admin.html",
            context={
                "reservas": reservas,
                "usuarios": usuarios,
                "mensaje": mensaje,
                "tipo": tipo
            }
        )

    except Exception as error:
        print("ERROR AL MOSTRAR EL PANEL:", repr(error))
        raise

    finally:
        if cursor is not None:
            cursor.close()

        if conn is not None:
            conn.close()
    

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

@router.get("/admin", response_class=HTMLResponse)
def mostrar_administracion(
    request: Request,
    mensaje: str | None = None,
    tipo: str | None = None
):
    conn, cursor = get_db()

    try:
        cursor.execute("""
            SELECT email, nyap
            FROM usuario
            ORDER BY nyap
        """)

        usuarios = cursor.fetchall()

        print("USUARIOS ENCONTRADOS:", usuarios)

        return templates.TemplateResponse(
            request=request,
            name="admin.html",
            context={
                "usuarios": usuarios,
                "mensaje": mensaje,
                "tipo": tipo
            }
        )

    finally:
        cursor.close()
        conn.close()

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

