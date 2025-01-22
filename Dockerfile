FROM python:3.13-alpine AS base

LABEL name="LanJanitor"
LABEL version="2.0"
LABEL description="Dockerfile for LanJanitor application"

ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1
ENV FLASK_APP=/app/app.py

COPY requirements.txt /app/requirements.txt
#COPY lanjanitor-cron /etc/cron.d/lanjanitor-cron

WORKDIR /app

#RUN chmod 0644 /etc/cron.d/lanjanitor-cron

#For Ansible
RUN apk add --no-cache \
    openssl \
    openssl-dev \
    openssh-client \
    linux-headers \
    build-base \
    libffi-dev 
#For crontab
#RUN apk add --no-cache \
#    openrc \
#    busybox-initscripts

#For Python modules
RUN pip install -r requirements.txt

#RUN crontab /etc/cron.d/lanjanitor-cron
#RUN rc-update add crond

#ENTRYPOINT ["python"]
CMD ["/bin/sh","entrypoint.sh"]
