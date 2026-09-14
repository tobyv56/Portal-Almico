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
    tags=["Talleres"] #seccion=talleres
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

@router.get("/infoSecciones", response_class=HTMLResponse)
def mostrar_ubicacion(request: Request):

    conn, cursor = get_db()

    try:

        repositorio = RepositorioSeccion(cursor)

        secciones = repositorio.obtener_todos() #devuelve todas las secciones

        print(secciones)

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

@router.post("/creacionSeccion")
def crearSeccion(nombre: Annotated[str, Form()],
                 descripcion: Annotated[str, Form()],
                 imagen: Annotated[UploadFile, File()],
                 usuarioActual:Annotated[
                         Usuario,
                         Depends(obtener_usuario_actual) #lo convierte en un objeto tipo Usuario
                     ]):

    conn, cursor = get_db()

    if not usuarioActual.tiene_permisos(): #se dedica a ver si no es rol admin no puede crear ni eliminar secciones
        return RedirectResponse(
            url="/cursos?mensaje=No+tenes+permisos&tipo=error",
            status_code=303
        )

    repositorioSeccion = RepositorioSeccion(cursor)
    resultado = cloudinary.uploader.upload( #sube la imagen a cloudinary
                imagen.file,
                folder="portal-almico/creacionSeccion",
                resource_type="image"
            )

    #print("RESULTADO CLOUDINARY:", resultado)
    #print("URL:", resultado["secure_url"])

    seccion = Seccion( #crea el objeto Seccion
        nombre= nombre,
        descripcion= descripcion,
        imagen = resultado["secure_url"]
    )

    repositorioSeccion.crearSeccion(seccion)

    conn.commit()
    
    return RedirectResponse(
                url=(
                    "/infoSecciones"
                    "?mensaje=Seccion+creado+correctamente"
                    "&tipo=success"
                ),
                status_code=303
            )

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
    
            if not self.imagen or not self.url_imagen.strip():
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

    def crearSeccion(self,seccion):
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
    
    def eliminacion_seccion(self, nombreSeccion):
            self.cursor.execute( #elimina la seccion en la bdd
                """
                DELETE FROM seccion
                WHERE nombreseccion = %s
                """,
                (nombreSeccion,)
                )
    
            return self.cursor.rowcount > 0
