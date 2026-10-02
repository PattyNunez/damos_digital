# Render (runtime nativo) no deja instalar paquetes de sistema (apt) — el filesystem es de
# solo lectura fuera de lo que viene pre-instalado, y Pango/Cairo/Harfbuzz no están ahí. Por
# eso este Dockerfile: WeasyPrint SÍ necesita Pango para generar los PDF (informes/propuestas),
# y la única vía soportada por Render para librerías de sistema propias es Docker.
FROM python:3.9-slim-bookworm

# Mismas 2 librerías identificadas y probadas en build.sh (flujo nativo, ahora reemplazado por
# este Dockerfile): WeasyPrint 66 ya no necesita Cairo/GDK-Pixbuf, solo Pango (que arrastra
# GLib/GObject solas como dependencias de apt).
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render detecta el puerto expuesto o usa la variable PORT — si el dashboard define su propia
# PORT, esa gana sobre este default al correr el contenedor.
ENV PORT=10000
EXPOSE 10000

# collectstatic y migrate corren al ARRANCAR el contenedor, no durante el build: las variables
# de entorno reales (DATABASE_URL, CLOUDINARY_URL, SECRET_KEY) de Render recién están
# disponibles en tiempo de ejecución. Meterlas en el build (vía ARG) dejaría secretos grabados
# en las capas de la imagen — ver docs de Render sobre "Docker secrets".
CMD python manage.py collectstatic --no-input && python manage.py migrate && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
