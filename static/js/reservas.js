document.addEventListener("DOMContentLoaded", () => {
    const selectorFacilitadora = document.querySelector(
        'select[name="facilitadora"]'
    );

    selectorFacilitadora.addEventListener(
    "change",
    actualizarHorariosDisponibles
    );

    const inputFecha = document.getElementById(
        "fecha-seleccionada"
    );

    const inputHorario = document.getElementById(
        "horario-seleccionado"
    );

    const botonesHorario = document.querySelectorAll(
        ".horario"
    );

    configurarCalendario();
    configurarHorarios();
    mostrarMensaje();

    selectorFacilitadora.addEventListener(
        "change",
        actualizarHorariosDisponibles
    );


    function configurarCalendario() {
        const calendario = document.querySelector(
            "#calendario-fijo"
        );

        if (!calendario || !inputFecha) {
            return;
        }

        flatpickr(calendario, {
            inline: true,
            minDate: "today",
            dateFormat: "Y-m-d",

            locale: {
                firstDayOfWeek: 1,

                weekdays: {
                    shorthand: [
                        "Do", "Lu", "Ma", "Mi", "Ju", "Vi", "Sa"
                    ],

                    longhand: [
                        "Domingo",
                        "Lunes",
                        "Martes",
                        "Miércoles",
                        "Jueves",
                        "Viernes",
                        "Sábado"
                    ]
                },

                months: {
                    shorthand: [
                        "Ene", "Feb", "Mar", "Abr",
                        "May", "Jun", "Jul", "Ago",
                        "Sep", "Oct", "Nov", "Dic"
                    ],

                    longhand: [
                        "Enero",
                        "Febrero",
                        "Marzo",
                        "Abril",
                        "Mayo",
                        "Junio",
                        "Julio",
                        "Agosto",
                        "Septiembre",
                        "Octubre",
                        "Noviembre",
                        "Diciembre"
                    ]
                }
            },

            onChange: function (selectedDates, dateStr) {
                inputFecha.value = dateStr;

                // Limpiamos el horario anterior
                inputHorario.value = "";

                botonesHorario.forEach((boton) => {
                    boton.classList.remove("activo");
                });

                // Acá consultamos los horarios ocupados
                actualizarHorariosDisponibles();
            }
        });
    }


    function configurarHorarios() {
        botonesHorario.forEach((boton) => {
            boton.addEventListener("click", () => {
                if (boton.disabled) {
                    return;
                }

                botonesHorario.forEach((otroBoton) => {
                    otroBoton.classList.remove("activo");
                });

                boton.classList.add("activo");

                inputHorario.value = boton.dataset.horario;

                console.log(
                    "Horario seleccionado:",
                    inputHorario.value
                );
            });
        });
    }


    async function actualizarHorariosDisponibles() {
        const facilitadora = selectorFacilitadora.value;
        const fecha = inputFecha.value;

        // Limpiamos el horario previamente seleccionado
        inputHorario.value = "";

        botonesHorario.forEach((boton) => {
            boton.classList.remove("activo");
        });

        if (!facilitadora || !fecha) {
            botonesHorario.forEach((boton) => {
                boton.disabled = false;
                boton.title = "";
                boton.classList.remove("btn-secondary");
                boton.classList.add("btn-principal");
            });

            return;
        }

        try {
            const parametros = new URLSearchParams({
                facilitadora: facilitadora,
                fecha: fecha
            });

            const respuesta = await fetch(
                `/reservas/horarios-ocupados?${parametros}`
            );

            if (!respuesta.ok) {
                throw new Error(
                    "No se pudieron consultar los horarios"
                );
            }

            const datos = await respuesta.json();

            console.log(
                "Horarios ocupados:",
                datos.horarios
            );

            botonesHorario.forEach((boton) => {
                const horario = boton.dataset.horario;

                const estaOcupado =
                    datos.horarios.includes(horario);

                boton.disabled = estaOcupado;

                boton.title = estaOcupado
                    ? "Este horario ya está reservado"
                    : "";

                boton.classList.toggle(
                    "btn-secondary",
                    estaOcupado
                );

                boton.classList.toggle(
                    "btn-principal",
                    !estaOcupado
                );
            });

        } catch (error) {
            console.error(
                "Error consultando horarios:",
                error
            );
        }
    }


   function mostrarMensaje() {
    const mensaje = document.body.dataset.mensaje;
    const tipo = document.body.dataset.tipo;

    if (!mensaje) {
        return;
    }

    Swal.fire({
        icon: tipo || "info",
        title: mensaje,
        confirmButtonText: "Aceptar",
        confirmButtonColor: "#b4936d",
        background: "#fdfaf5",
        color: "#4a3f35"
    });

    window.history.replaceState(
        {},
        document.title,
        window.location.pathname
    );
}
});
