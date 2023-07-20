#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "***** PostgreSQL started *****"
fi

#while ! python manage.py flush --no-input   2>&1; do
#   echo "flush is in progress status"
#   sleep 0.1
#done
#
#echo "***** flush DONE *****"
#
while ! python manage.py migrate  --noinput  2>&1; do
   echo "migration is in progress status"
   sleep 0.1
done

echo "***** migration DONE *****"


while ! python manage.py shell  < installations/contenttype.py  2>&1; do
   echo "shell is in progress status"
   sleep 0.1
done

echo "***** shell (contenttype cache delete) DONE *****"

while ! python manage.py shell  < installations/superusercreator.py  2>&1; do
   echo "shell is in progress status"
   sleep 0.1
done

echo "***** shell (super user created) DONE *****"

while ! python manage.py loaddata  fixtures/db.json 2>&1; do
   echo "load data is in progress status"
   sleep 0.1
done

echo "***** load fixtures (DATA) DONE *****"



while ! python manage.py collectstatic  --noinput  2>&1; do
   echo "collectstatic is in progress status"
   sleep 0.1
done

echo "*** collectstatic DONE *****"


echo "***** FULL Django docker is fully configured  *****"
echo "***** successfully  *****"

gunicorn shop.wsgi:application --bind 0.0.0.0:8000

exec "$@"