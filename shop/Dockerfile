FROM python:3.8.3

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /usr/src/app
#RUN apk update \
#    && apk add postgresql-dev gcc python3-dev musl-dev


RUN apt-get update
RUN apt-get upgrade -y && apt-get -y install postgresql gcc python3-dev musl-dev

RUN python -m pip install --upgrade pip
COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install -r /usr/src/app/requirements.txt
#RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r requirements.txt

EXPOSE 8000
RUN adduser --force-badname postgresUSER
USER postgresUSER
#   docker exec -it $1 bash -c

# COPY ./entrypoint.sh /usr/src/app/entrypoint.sh
COPY ./entrypoint.sh /usr/src/app/entrypoint.sh
#RUN sed -i 's/\r$//g' /usr/src/app/entrypoint.sh
#RUN chmod +x /usr/src/app/entrypoint.sh

# COPY . /usr/src/app/
COPY . .

#CMD ["/bin/ping", "localhost"]
#CMD ["python", "manage.py", "migrate"]
#CMD ["python", "manage.py", "runserver", "127.0.0.1:8000"]
#ENTRYPOINT ["sh", "entrypoint.sh"]

#ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]