document.addEventListener("DOMContentLoaded", () => {
    const mensaje = document.body.dataset.mensaje;
    const tipo = document.body.dataset.tipo;

    if (!mensaje) {
        return;
    }

    Swal.fire({
        icon: tipo || "info",
        title: mensaje,
        confirmButtonText: "Aceptar"
    }).then(() => {
        window.history.replaceState(
            {},
            document.title,
            "/cursos"
        );
    });
});