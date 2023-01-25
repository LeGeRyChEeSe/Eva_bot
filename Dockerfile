# syntax=docker/dockerfile:1

FROM python:3.9.4

WORKDIR /evabot

COPY requirements.txt requirements.txt

RUN apt-get update && \
    apt-get install -y locales && \
    sed -i -e 's/# fr_FR.UTF-8 UTF-8/fr_FR.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales

RUN pip3 install -r requirements.txt
RUN locale-gen fr_FR.UTF-8

ENV LANG fr_FR.UTF-8
ENV LANGUAGE fr_FR:fr
ENV LC_ALL fr_FR.UTF-8
ENV TOKEN TOKEN
ENV HOST_DB HOST_DB
ENV USER_DB USER_DB
ENV PASSWD_DB PASSWD_DB
ENV DB DB

COPY . .

CMD [ "python", "main.py"]