from typing import Annotated

import cloudinary.uploader

from fastapi import (
    APIRouter,
    File,
    Form,
    Request,
    UploadFile,
    Depends,
)
from fastapi.responses import HTMLResponse, RedirectResponse

from configuracion import templates
from database import get_db
from routers.usuarios import (Usuario,obtener_usuario_actual)

router = APIRouter(
    tags=["Secciones"] #seccion=talleres sirve para agrupar los endpoints
)

def contexto_sesion(request: Request): #devuelve el idUsuario y el rol
    id_usuario = request.session.get("idusuario")
    rol_usuario = request.session.get("rol")

    return {
        "idusuario": id_usuario,
        "rol_usuario": rol_usuario,
        "usuario_logueado": id_usuario is not None, #pregunta si es el id es null
        "es_admin": rol_usuario == "admin"
    }

@router.get("/info_secciones", response_class=HTMLResponse)
def mostrar_seccion(request: Request):

    conn, cursor = get_db()

    try:

        repositorio = RepositorioSeccion(cursor)

        secciones = repositorio.obtener_todos() #devuelve todas las secciones

        return templates.TemplateResponse(
            request=request,
            name="infoSecciones.html",
            context={
                **contexto_sesion(request), #convierte todo en context
                "secciones": secciones
            }
        )

    finally:
        cursor.close()
        conn.close()

@router.post("/creacion_seccion")
def crear_seccion(nombre: Annotated[str, Form()],
                 descripcion: Annotated[str, Form()],
                 imagen: Annotated[UploadFile, File()],
                 usuarioActual:Annotated[
                         Usuario,
                         Depends(obtener_usuario_actual) #lo convierte en un objeto tipo Usuario
                     ]):

    if not usuarioActual.tiene_permisos(): #se dedica a ver si no es rol admin no puede crear ni eliminar secciones
        return RedirectResponse(
            url="/cursos?mensaje=No+tenes+permisos&tipo=error",
            status_code=303
        )

    conn, cursor = get_db()

    #manejo de try para garantizar el control completo de la conexion
    try:

        repositorio_seccion = RepositorioSeccion(cursor)
        resultado = cloudinary.uploader.upload( #sube la imagen a cloudinary
                    imagen.file,
                    folder="portal-almico/creacionSeccion",
                    resource_type="image"
                )

        seccion.validar()
        #print("RESULTADO CLOUDINARY:", resultado)
        #print("URL:", resultado["secure_url"])

        seccion = Seccion( #crea el objeto Seccion
            nombre= nombre,
            descripcion= descripcion,
            imagen = resultado["secure_url"]
        )

        repositorio_seccion.crear_seccion(seccion)

        conn.commit()

    except Exception as error:

        print("ERROR:", repr(error)) #me tira error en los logs de la consola
        conn.rollback() #rollbackeo para que no sufra ninguna modificacion la petision

        return RedirectResponse(
        url="/info_secciones?mensaje=No+se+pudo+crear+la+seccion&tipo=error",
        status_code=303
        )

    finally:
        #cierro conexion
        cursor.close()
        conn.close()
        
    return RedirectResponse(
                url=(
                    "/info_secciones"
                    "?mensaje=Seccion+creado+correctamente"
                    "&tipo=success"
                ),
                status_code=303
            )
@router.post("/eliminar_seccion/{id_seccion}")
def eliminar_seccion(
    id_seccion: int,
    usuario_actual: Annotated[
        Usuario,
        Depends(obtener_usuario_actual)
    ]
):

    if not usuario_actual.tiene_permisos():
        return RedirectResponse(
            url="/info_secciones?mensaje=No+tenes+permisos&tipo=error",
            status_code=303
        )

    conn, cursor = get_db()

    try:
        repositorio_seccion = RepositorioSeccion(cursor)

        fue_eliminada = repositorio_seccion.eliminar_seccion(
            id_seccion
        )

        if not fue_eliminada: #pregunta si existe la seccion
            conn.rollback()

            return RedirectResponse(
                url="/info_secciones?mensaje=La+seccion+no+existe&tipo=error",
                status_code=303
            )

        conn.commit()

        return RedirectResponse(
            url="/info_secciones?mensaje=Seccion+eliminada+correctamente&tipo=success",
            status_code=303
        )

    except Exception as error:
        print("ERROR AL ELIMINAR SECCION:", repr(error))

        conn.rollback()

        return RedirectResponse(
            url="/info_secciones?mensaje=No+se+pudo+eliminar+la+seccion&tipo=error",
            status_code=303
        )

    finally:
        cursor.close()
        conn.close()

class Seccion:

    def __init__(
        self,
        nombre,
        descripcion,
        imagen
    ):
        self.nombre = nombre
        self.descripcion = descripcion
        self.imagen = imagen

    def validar(self):
            if not self.nombre or not self.nombre.strip(): 
                raise ValueError("El nombre de la seccion no puede estar vacío")
    
            if not self.descripcion or not self.descripcion.strip():
                raise ValueError("La descripción no puede estar vacía")
     
            if not self.imagen or not self.imagen.strip():
                raise ValueError("La imagen no puede estar vacía")

class RepositorioSeccion:

    def __init__(self, cursor):
            self.cursor = cursor
    
    def obtener_todos(self):
            self.cursor.execute(""" #devuelve todas las secciones
                SELECT *
                FROM seccion
                ORDER BY idseccion
            """)
    
            return self.cursor.fetchall()

    def crear_seccion(self,seccion):
            self.cursor.execute( #crea la seccion en la bdd
                        """
                        INSERT INTO seccion
                            (nombreseccion, descripcion, imagen)
                        VALUES
                            (%s, %s, %s)
                        """,
                        (
                            seccion.nombre,
                            seccion.descripcion,
                            seccion.imagen
                        )
                    )
    
    def eliminar_seccion(self, id_seccion):
        self.cursor.execute(
        """
        DELETE FROM seccion
        WHERE idseccion = %s
        """,
        (id_seccion,)
        )

        return self.cursor.rowcount > 0
