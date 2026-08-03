import psycopg2
from psycopg2.extras import RealDictCursor
from configuracion import DATABASE_URL

def get_db():
    conexion = psycopg2.connect(
        DATABASE_URL
    )

    cursor = conexion.cursor(
        cursor_factory=RealDictCursor
    )

    return conexion, cursor