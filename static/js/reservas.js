document.addEventListener("DOMContentLoaded", () => {
    configurarCalendario();
    configurarHorarios();
    mostrarMensaje();
});


function configurarCalendario() {
    const calendario = document.querySelector("#calendario-fijo");
    const inputFecha = document.querySelector("#fecha-seleccionada");

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

            console.log("Fecha seleccionada:", dateStr);
        }
    });
}


function configurarHorarios() {
    const botonesHorarios = document.querySelectorAll(".horario");
    const inputHorario = document.querySelector("#horario-seleccionado");

    if (!inputHorario) {
        return;
    }

    botonesHorarios.forEach((boton) => {
        boton.addEventListener("click", () => {
            botonesHorarios.forEach((otroBoton) => {
                otroBoton.classList.remove("activo");
            });

            boton.classList.add("activo");

            inputHorario.value = boton.textContent.trim();

            console.log(
                "Horario seleccionado:",
                inputHorario.value
            );
        });
    });
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
}