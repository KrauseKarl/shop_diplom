#!/bin/sh

until cd /usr/src/app/
do
    echo "Waiting for server volume..."
done


celery  -A shop.celery:app worker --concurrency 1 -E  --loglevel=INFO

echo "*** celery DONE "