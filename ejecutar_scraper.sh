docker run --rm -v "$(pwd)/salida:/app/salida" scraper-contemplaciones

#!/bin/bash
# Ejecuta el contenedor Docker y muestra la salida en tiempo real
echo "========== RECONSTRUYENDO IMAGEN DOCKER =========="
docker build -t scraper-contemplaciones .
build_status=$?
if [ $build_status -ne 0 ]; then
	echo "Error al construir la imagen Docker. Abortando."
	exit $build_status
fi
echo "========== INICIANDO SCRAPER =========="
docker run --rm -v "$(pwd)/salida:/app/salida" scraper-contemplaciones
status=$?
echo "=========== FIN DE LA EJECUCIÓN (exit code: $status) ==========="
exit $status
