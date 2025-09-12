# README: Ejecutar scrape_diegojavier.py con Docker

Este proyecto contiene un script Python llamado `scrape_diegojavier.py` que puede ejecutarse fácilmente usando Docker.

## Requisitos previos
- Tener instalado [Docker](https://docs.docker.com/get-docker/)

## Construcción de la imagen

Desde la raíz del proyecto, ejecuta:

```bash
docker build -t scraper-contemplaciones .
```

## Ejecución del script

Para ejecutar el script dentro de un contenedor Docker:

```bash
docker run --rm scraper-contemplaciones
```

Si necesitas pasar argumentos al script, agrégalos al final del comando:

```bash
docker run --rm scraper-contemplaciones python scrape_diegojavier.py arg1 arg2
```

## Notas
- Si el script requiere archivos adicionales, agrégalos al Dockerfile o monta un volumen con `-v`.
- Si tienes un archivo `requirements.txt`, modifica el Dockerfile para instalar todas las dependencias.
