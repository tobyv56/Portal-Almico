# Portal Álmico

Portal Álmico es una aplicación web desarrollada para mostrar talleres, terapias y secciones informativas, además de permitir la reserva de turnos y la administración del contenido del sitio.

## Funcionalidades principales

- Visualización de talleres disponibles
- Información sobre distintas secciones y terapias
- Reserva de turnos
- Control de horarios disponibles
- Panel de administración
- Creación y eliminación de talleres
- Creación de secciones con imágenes
- Gestión de reservas
- Integración con Google Calendar
- Limpieza automática de reservas antiguas

## Tecnologías utilizadas

- Python
- FastAPI
- Jinja2
- PostgreSQL
- Bootstrap
- JavaScript
- Cloudinary
- Google Calendar API
- APScheduler
- Render

## Estructura general

El proyecto está organizado mediante routers de FastAPI para separar las distintas responsabilidades:

```text
routers/
├── paginas.py
├── talleres.py
├── secciones.py
├── reservas.py
├── usuarios.py
└── google_calendar.py
