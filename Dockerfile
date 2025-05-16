FROM python:3.13.3-alpine AS builder
LABEL authors="ig-rudenko"

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apk add --update --no-cache mariadb-connector-c-dev net-snmp-tools busybox-extras openssh-client \
	&& apk add --no-cache --virtual .build-deps \
		mariadb-dev python3-dev \
		gcc \
		musl-dev \
        curl ca-certificates \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
	&& pip install mysqlclient ruamel.yaml.clib \
	&& apk del .build-deps

COPY pyproject.toml uv.lock /app/

RUN /root/.local/bin/uv export --format requirements-txt > /app/requirements.txt

RUN pip install --upgrade pip --no-cache-dir && pip install -r requirements.txt --no-cache-dir;

RUN addgroup -g 10001 appgroup \
    && adduser -D -h /app -u 10002 app appgroup \
    && chown -R app:app /app;

COPY --chown=app:appgroup . /app

RUN chmod +x run.sh

USER app

EXPOSE 8000