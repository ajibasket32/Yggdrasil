ARG PYTHON_IMAGE=python:3.12.10-slim
FROM ${PYTHON_IMAGE}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip==26.1.2 \
    && pip install --no-cache-dir poetry==2.3.4

COPY backend/pyproject.toml backend/poetry.lock ./
ARG POETRY_INSTALL_ARGS="--only main --no-root"
RUN poetry install ${POETRY_INSTALL_ARGS}

COPY backend/app ./app
COPY backend/alembic.ini ./
COPY backend/uvicorn_logging.json ./
COPY database/migrations /database/migrations
COPY docker/backend/entrypoint.sh ./entrypoint.sh

RUN sed -i 's/\r$//' /app/entrypoint.sh \
    && useradd --create-home --uid 10001 yggdrasil \
    && chmod +x /app/entrypoint.sh \
    && chown -R yggdrasil:yggdrasil /app

USER yggdrasil

EXPOSE 8000

CMD ["/app/entrypoint.sh"]