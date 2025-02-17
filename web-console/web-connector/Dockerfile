FROM python:3.13.2-alpine
LABEL authors="irudenko"

RUN apk add --no-cache openssh-client && \
    pip install --upgrade --no-cache-dir pip && \
    pip install --no-cache-dir webssh;

EXPOSE 8080

ENTRYPOINT ["wssh"]
