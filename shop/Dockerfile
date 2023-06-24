FROM python:3.8.3

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /usr/src/app
# RUN apk update  && apk add postgresql-dev gcc python3-dev musl-dev
# postgresql-dev gcc python3-dev musl-dev
# postgresql postgresql-contrib

RUN apt-get update
RUN apt-get upgrade -y && apt-get -y install postgresql gcc python3-dev musl-dev

RUN python -m pip install --upgrade pip
COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install -r /usr/src/app/requirements.txt

#RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r requirements.txt

EXPOSE 8000
RUN adduser --force-badname postgresUSER
USER postgresUSER


#   docker exec -it container_name bash -c /bin/bash
#   docker exec -it container_name bash -c "python manage.ru runserver"

COPY --chown=postgresUSER ./entrypoint.sh /usr/src/app/entrypoint.sh
COPY --chown=postgresUSER ./celery_entrypoint.sh /usr/src/app/celery_entrypoint.sh

#RUN sed -i 's/\r$//g' /usr/src/app/entrypoint.sh

RUN chmod +x /usr/src/app/entrypoint.sh
RUN chmod +x /usr/src/app/celery_entrypoint.sh

USER root

COPY . /usr/src/app/
COPY --chown=root ../assets /usr/src/app/assets
COPY --chown=root ../media /usr/src/app/media
#
RUN chown root:root /usr/src/app/media
RUN chown root:root /usr/src/app/assets

RUN chmod 777 /usr/src/app/media
RUN chmod +x /usr/src/app/assets
#CMD ["/bin/ping", "localhost"]
#CMD ["python", "manage.py", "runserver", "127.0.0.1:8000"]
#ENTRYPOINT ["sh", "entrypoint.sh"]

ENTRYPOINT ["/usr/src/app/entrypoint.sh"]