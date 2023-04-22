FROM python:3.8.3

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /usr/src/app
#RUN apk update \
#    && apk add postgresql-dev gcc python3-dev musl-dev
RUN apt-get update
RUN apt-get upgrade -y && apt-get -y install postgresql gcc python3-dev musl-dev

RUN python -m pip install --upgrade pip
COPY shop/requirements.txt /usr/src/requirements.txt
RUN pip install -r /usr/src/requirements.txt
#RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r requirements.txt

COPY ./shop /usr/src/app

EXPOSE 8000
RUN adduser --force-badname postgresUSER
USER postgresUSER

COPY shop/entrypoint.sh /usr/src/app/entrypoint.sh
#COPY shop/entrypoint.sh /usr/src/app/entrypoint.sh

#CMD ["/bin/ping", "localhost"]
CMD ["python", "manage.py", "migrate"]
CMD ["python", "manage.py", "runserver", "127.0.0.1:8000"]
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
