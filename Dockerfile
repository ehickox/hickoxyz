# pull official base image
FROM python:3.11.1-alpine

# install dependencies
RUN apk update && \
    apk add --virtual build-deps gcc musl-dev

# set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PROJECT_DIR=/usr/src/app

# upgrade pip
RUN pip install --upgrade pip
RUN pip install pipenv

# set working directory
WORKDIR ${PROJECT_DIR}

# add app
COPY . ${PROJECT_DIR}

# add and install requirements
RUN pipenv install --system --deploy

# make start.sh executable
RUN chmod +x start.sh

CMD ./start.sh
