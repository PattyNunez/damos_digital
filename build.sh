#!/usr/bin/env bash
# Script que Render ejecuta en cada deploy. `set -o errexit`: si cualquier paso falla, corta
# acá — mejor un deploy que no arranca que uno a medias sirviendo con datos/estáticos viejos.
set -o errexit

# Dependencias de SISTEMA que necesita WeasyPrint para generar los PDF (informes/propuestas).
# Confirmado contra esta instalación real: WeasyPrint 66 (a diferencia de versiones viejas)
# solo necesita Pango — no todo el paquete clásico de Cairo/GDK-Pixbuf — porque reescribieron su
# propio backend de PDF. libpango-1.0-0 arrastra libglib2.0-0/libgobject-2.0-0 como dependencias
# de apt automáticamente, que es justo lo que WeasyPrint busca al arrancar.
apt-get update -y
apt-get install -y --no-install-recommends \
  libpango-1.0-0 \
  libpangoft2-1.0-0

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate
