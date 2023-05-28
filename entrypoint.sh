#!/bin/bash

set -e
cd /usr/src/
echo "${0}: running migrations."
python manage.py makemigrations --merge
python manage.py migrate --noinput

echo "${0}: collecting statics."

python manage.py collectstatic --noinput
#cp -rv static/* static_shared/
python manage.py runserver 0.0.0.0:8000