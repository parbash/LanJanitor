FROM python:3.9.5-alpine

ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1
ENV FLASK_APP /app/app.py

COPY requirements.txt /app/requirements.txt
COPY lanjanitor-cron /etc/cron.d/lanjanitor-cron

WORKDIR /app

RUN chmod 0644 /etc/cron.d/lanjanitor-cron

RUN apk add openssl                    # For Ansible
RUN apk add openssl-dev                # For Ansible
RUN apk add openssh-client             # For Ansible
RUN apk add linux-headers              # For Ansible
RUN apk add build-base                 # For Ansible
RUN apk add libffi-dev                 # For Ansible

RUN apk add openrc                     # For Cron
RUN apk add busybox-initscripts        # For Cron

RUN pip install -r requirements.txt

RUN crontab /etc/cron.d/lanjanitor-cron
RUN rc-update add crond

#ENTRYPOINT ["python"]
CMD ["/bin/sh","entrypoint.sh"]
