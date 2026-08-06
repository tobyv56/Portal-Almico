document.addEventListener("DOMContentLoaded", () => {
    const mensaje = document.body.dataset.mensaje;
    const tipo = document.body.dataset.tipo;

    if (!mensaje) {
        return;
    }

    Swal.fire({
        icon: tipo || "info",
        title: mensaje,
        text: "Email O Contrasena incorrectas.",
        confirmButtonText: "Aceptar",
        confirmButtonColor: "#b4936d",
        background: "#fdfaf5",
        color: "#4a3f35"
    }).then(() => {
        window.history.replaceState(
            {},
            document.title,
            window.location.pathname
        );
    });
});


