# pull official base image
FROM python:3.13.9-alpine

# install dependencies
RUN apk update && \
    apk add --no-cache gcc musl-dev curl

# set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PROJECT_DIR=/usr/src/app

# install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && ln -sf /root/.local/bin/uv /usr/local/bin/uv

# set working directory
WORKDIR ${PROJECT_DIR}

# add and install requirements
# doing this separately allows docker to cache
# dependencies when code changes
COPY ./pyproject.toml ${PROJECT_DIR}/pyproject.toml
COPY ./uv.lock ${PROJECT_DIR}/uv.lock
RUN uv sync --frozen --no-dev

# ensure venv on PATH
ENV PATH=${PROJECT_DIR}/.venv/bin:$PATH

# add entrypoint.sh
COPY ./start.sh ${PROJECT_DIR}/start.sh
RUN chmod +x ${PROJECT_DIR}/start.sh

# add app
COPY . ${PROJECT_DIR}

CMD ./start.sh
