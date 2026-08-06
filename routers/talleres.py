from typing import Annotated
from routers.usuarios import Usuario

import cloudinary.uploader

from fastapi import (
    APIRouter,
    File,
    Form,
    Request,
    UploadFile,
    Depends,
    HTTPException
)
from fastapi.responses import HTMLResponse, RedirectResponse

from configuracion import templates
from database import get_db
from routers.usuarios import (Usuario,obtener_usuario_actual)

router = APIRouter(
    tags=["Talleres"]
)

@router.post("/cursos/eliminacion")
def eliminar_taller(
    nombreTaller: Annotated[str, Form()],
    usuarioActual:Annotated[
        Usuario,
        Depends(obtener_usuario_actual)
    ]
):

    conn, cursor = get_db()

    if not Usuario.tiene_permisos(usuarioActual):
        return RedirectResponse(
            url="/cursos?mensaje=No+tenes+permisos&tipo=error",
            status_code=303
        )

    talleres = RepositorioTalleres(cursor)

    try:
        fue_eliminado = talleres.eliminacion_taller(nombreTaller)

        if not fue_eliminado:

            conn.rollback()

            return RedirectResponse(
                url=(
                    "/cursos"
                    "?mensaje=Taller+no+encontrado"
                    "&tipo=warning"
                ),
                status_code=303
            )

        conn.commit()

        return RedirectResponse(
            url=(
                "/cursos"
                "?mensaje=Taller+eliminado+correctamente"
                "&tipo=success"
            ),
            status_code=303
        )

    except Exception as error:
        conn.rollback()

        print("Error al eliminar taller:", error)

        return RedirectResponse(
            url=(
                "/cursos"
                "?mensaje=No+se+pudo+eliminar+el+taller"
                "&tipo=error"
            ),
            status_code=303
        )

    finally:
        cursor.close()
        conn.close()

@router.get("/cursos", response_class=HTMLResponse)
def mostrar_pag_talleres(
    request: Request,
    mensaje: str | None = None,
    tipo: str | None = None
):  
    
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
                LIMIT 6
                """
            )
    
            talleres = cursor.fetchall()
    
            rol_usuario = request.session.get("rol")
    
            return templates.TemplateResponse(
                request=request,
                name="cursos.html",
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

@router.post("/cursos/creacion")
def crear_taller(
    request: Request,
    nombrecurso: Annotated[str, Form()],
    mes: Annotated[str, Form()],
    descripcion: Annotated[str, Form()],
    imagen: Annotated[UploadFile, File()],
    usuarioActual:Annotated[
            Usuario,
            Depends(obtener_usuario_actual)
        ]
):
    conn, cursor = get_db()

    print("CREAR TALLER - EMAIL:", usuarioActual.email)
    print("CREAR TALLER - ROL:", repr(usuarioActual.rol))

    if not usuarioActual.tiene_permisos():
        return RedirectResponse(
            url="/cursos?mensaje=No+tenes+permisos&tipo=error",
            status_code=303
        )

    try:

        repositorioTalleres = RepositorioTalleres(cursor)
        resultado = cloudinary.uploader.upload(
            imagen.file,
            folder="portal-almico/cursos",
            resource_type="image"
        )

        url_imagen = resultado["secure_url"]

        taller = Taller(
            nombreTaller = nombrecurso,
            mes = mes,
            descripcion = descripcion,
            url_imagen = url_imagen
        )

        repositorioTalleres.creacion_taller(taller)

        conn.commit()

        return RedirectResponse(
            url=(
                "/cursos"
                "?mensaje=Taller+creado+correctamente"
                "&tipo=success"
            ),
            status_code=303
        )

    except Exception as error:
        conn.rollback()

        print("Error al crear taller:", repr(error)) #sirve para ver el error mas explicito

        return RedirectResponse(
            url=(
                "/cursos"
                "?mensaje=No+se+pudo+crear+el+taller"
                "&tipo=error"
            ),
            status_code=303
        )

    finally:
        cursor.close()
        conn.close()
        
class Taller:

    def __init__(self, nombreTaller, mes,descripcion,url_imagen):
        self.nombreTaller = nombreTaller
        self.mes = mes 
        self.descripcion = descripcion
        self.url_imagen = url_imagen

    def validar(self):
        if not self.nombre_taller or not self.nombre_taller.strip():
            raise ValueError("El nombre del taller no puede estar vacío")

        if not self.mes or not self.mes.strip():
            raise ValueError("El mes no puede estar vacío")

        if not self.descripcion or not self.descripcion.strip():
            raise ValueError("La descripción no puede estar vacía")

        if not self.url_imagen or not self.url_imagen.strip():
            raise ValueError("La imagen no puede estar vacía")

class RepositorioTalleres:

    def __init__(self, cursor):
        self.cursor = cursor

    def obtener_todos(self):
        self.cursor.execute("""
            SELECT *
            FROM curso
            ORDER BY idcurso
        """)

        return self.cursor.fetchall()

    def creacion_taller(self,taller):
        self.cursor.execute(
                    """
                    INSERT INTO curso
                        (nombrecurso, mes, descripcion, imagen)
                    VALUES
                        (%s, %s, %s, %s)
                    """,
                    (
                        taller.nombreTaller,
                        taller.mes,
                        taller.descripcion,
                        taller.url_imagen
                    )
                )

    def eliminacion_taller(self, nombreTaller):
        self.cursor.execute(
            """
            DELETE FROM curso
            WHERE nombrecurso = %s
            """,
            (nombreTaller,)
            )

        return self.cursor.rowcount > 0

