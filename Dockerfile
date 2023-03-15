# syntax=docker/dockerfile:1

FROM python:3.9-slim-buster

WORKDIR /evabot

COPY requirements.txt .

RUN apt-get update && \
    apt-get install -y locales git libjpeg-dev zlib1g-dev gcc && \
    rm -rf /var/lib/apt/lists/* && \
    sed -i -e 's/# fr_FR.UTF-8 UTF-8/fr_FR.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales && \
    pip install --upgrade pip && \
    pip install -r requirements.txt && \
    locale-gen fr_FR.UTF-8

ENV LANG fr_FR.UTF-8
ENV LANGUAGE fr_FR:fr
ENV LC_ALL fr_FR.UTF-8
ENV TOKEN=
ENV HOST_DB=
ENV USER_DB=
ENV PASSWD_DB=
ENV DB=

COPY . .

CMD [ "python", "main.py"]
