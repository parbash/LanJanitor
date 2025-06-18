FROM python:3.11-alpine

ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1
ENV FLASK_APP /app/app.py

COPY requirements.txt /app/requirements.txt
COPY lanjanitor-cron /etc/cron.d/lanjanitor-cron

WORKDIR /app

RUN chmod 0644 /etc/cron.d/lanjanitor-cron

# Install runtime and build dependencies, then remove build deps after pip install
RUN apk update && \
    apk add --no-cache \
        openssl \
        openssh-client \
        openrc \
        cronie && \
    apk add --no-cache --virtual .build-deps \
        build-base \
        linux-headers \
        libffi-dev \
        openssl-dev && \
    pip install --upgrade pip && \
    pip install -r requirements.txt && \
    apk del .build-deps

COPY ./app /app

RUN crontab /etc/cron.d/lanjanitor-cron
#RUN rc-update add crond

#ENTRYPOINT ["python"]
CMD ["/bin/sh","entrypoint.sh"]
