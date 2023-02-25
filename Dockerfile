# pull official base image
FROM python:3.11.2-alpine

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

# add and install requirements
# doing this separately allows docker to cache
# dependencies when code changes
COPY ./Pipfile ${PROJECT_DIR}/Pipfile
COPY ./Pipfile.lock ${PROJECT_DIR}/Pipfile.lock
RUN pipenv install --system --deploy

# add entrypoint.sh
COPY ./start.sh ${PROJECT_DIR}/start.sh
RUN chmod +x ${PROJECT_DIR}/start.sh

# add app
COPY . ${PROJECT_DIR}

CMD ./start.sh
