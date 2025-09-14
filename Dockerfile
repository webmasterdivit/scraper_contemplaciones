# Dockerfile para ejecutar scrape_diegojavier.py
FROM python:3.11-slim

# Establece el directorio de trabajo
WORKDIR /app


# Copia los archivos del proyecto y requirements.txt
COPY scrape_diegojavier.py ./
COPY requirements.txt ./

# Instala las dependencias necesarias
RUN pip install --no-cache-dir -r requirements.txt

# Crea un volumen para acceder al CSV y scrap.log
VOLUME ["/app/salida"]

# Comando por defecto para ejecutar el script
CMD ["python", "scrape_diegojavier.py"]
