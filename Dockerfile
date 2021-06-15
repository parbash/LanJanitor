FROM python:3.9.5-alpine
ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN apk add openssl
RUN apk add openssl-dev
RUN apk add openssh-client
RUN apk add linux-headers
RUN apk add build-base
RUN apk add libffi-dev
RUN pip install -r requirements.txt
ENTRYPOINT ["python"]
CMD ["app.py"]