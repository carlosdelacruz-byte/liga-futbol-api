#!/usr/bin/env bash
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --no-input

python manage.py migrate

if [[ -n "$DJANGO_SUPERUSER_USERNAME" ]]; then
  python manage.py createsuperuser --noinput || true
  python manage.py shell -c "
from usuarios.models import UsuarioModel
UsuarioModel.objects.filter(username='$DJANGO_SUPERUSER_USERNAME').update(rol='admin')
" || true
fi
