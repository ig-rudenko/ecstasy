FROM python:3.13.0a4-alpine

ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN apk add --update --no-cache mariadb-connector-c-dev net-snmp-tools busybox-extras \
	&& apk add --no-cache --virtual .build-deps \
		mariadb-dev python3-dev \
		gcc \
		musl-dev \
	&& pip install mysqlclient ruamel.yaml.clib \
	&& apk del .build-deps

COPY requirements.txt .

RUN pip install --upgrade pip --no-cache-dir && pip install -r requirements.txt --no-cache-dir;

COPY . .
