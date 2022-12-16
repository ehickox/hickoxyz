# pull official base image
FROM python:3.8.13-alpine

# install dependencies
RUN apk update && \
    apk add --virtual build-deps gcc musl-dev

# set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# set working directory
WORKDIR /usr/src/app

# add and install requirements
COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install -r requirements.txt

# add entrypoint.sh
COPY ./start.sh /usr/src/app/start.sh
RUN chmod +x /usr/src/app/start.sh

# add app
COPY . /usr/src/app