async function checkHealth() {
    try {
        const respuesta = await fetch("/health");

        console.log(
            "Health Check Status:",
            respuesta.status
        );
    } catch (error) {
        console.warn(
            "Health check error:",
            error
        );
    }
}

// Ejecuta el health check apenas carga la página
checkHealth();

// Después lo repite cada 10 minutos
setInterval(checkHealth, 600000);