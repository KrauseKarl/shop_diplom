#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "________________________  PostgreSQL started"
fi

#while ! python manage.py flush --no-input   2>&1; do
#   echo "flush is in progress status"
#   sleep 0.1
#done
#
#echo "________________________  flush DONE"
#
#while ! python manage.py migrate  --noinput  2>&1; do
#   echo "migration is in progress status"
#   sleep 0.1
#done
#
#echo "________________________  migration DONE"
#
#
#while ! python manage.py shell  < fixtures/contenttype.py  2>&1; do
#   echo "shell is in progress status"
#   sleep 0.1
#done
#
#echo "________________________  shell DONE"
#
#while ! python manage.py loaddata  fixtures/data.json 2>&1; do
#   echo "load data is in progress status"
#   sleep 0.1
#done
#
#echo "________________________  load data DONE"

#while ! python manage.py collectstatic  --noinput  2>&1; do
#   echo "collectstatic is in progress status"
#   sleep 0.1
#done

#echo "*** collectstatic DONE"

echo "________________________  FULL Django docker is fully configured successfully "

# gunicorn shop.wsgi:application --bind 0.0.0.0:8000
python manage.py runserver 0.0.0.0:8000

exec "$@"