FROM python:3.9-alpine

ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN apk add --update --no-cache mariadb-connector-c-dev \
	&& apk add --no-cache --virtual .build-deps \
		mariadb-dev python3-dev \
		gcc \
		musl-dev \
	    net-snmp-tools busybox-extras \
	&& pip install mysqlclient ruamel.yaml.clib \
	&& apk del .build-deps

COPY requirements.txt .

RUN pip install --upgrade pip --no-cache-dir && pip install -r requirements.txt --no-cache-dir;

COPY . .
