document.addEventListener("DOMContentLoaded", () => {
    const mensaje = document.body.dataset.mensaje;
    const tipo = document.body.dataset.tipo;

    if (!mensaje) {
        return;
    }

    Swal.fire({
        icon: tipo || "info",
        title: mensaje,
        text: tipo === "success"
            ? "Ya podés iniciar sesión con tu nueva cuenta."
            : "",
        confirmButtonText: "Aceptar",
        confirmButtonColor: "#b4936d"
    }).then(() => {
        window.history.replaceState(
            {},
            document.title,
            window.location.pathname
        );
    });
});