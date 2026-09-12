#!/usr/bin/env bash
# Script de construccion que ejecuta Render en cada despliegue.
# `set -o errexit` corta el deploy apenas algo falla, en vez de publicar
# una version a medio construir.
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

# Junta los archivos estaticos del admin de Django para que WhiteNoise los sirva.
python manage.py collectstatic --no-input

# Aplica las migraciones sobre la base de datos de produccion.
python manage.py migrate
