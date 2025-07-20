FROM python:3.12-alpine

ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1
ENV FLASK_APP=/lanjanitor/lanjanitor.py

COPY requirements.txt /lanjanitor/requirements.txt
COPY lanjanitor-cron /etc/cron.d/lanjanitor-cron

WORKDIR /lanjanitor

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

COPY ./lanjanitor /lanjanitor

RUN crontab /etc/cron.d/lanjanitor-cron
#RUN rc-update add crond

#ENTRYPOINT ["python"]
CMD ["/bin/sh","entrypoint.sh"]
