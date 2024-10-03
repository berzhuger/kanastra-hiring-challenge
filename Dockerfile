FROM python:3.12-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN pip install poetry

COPY pyproject.toml poetry.lock ./


RUN poetry install --no-root

COPY . .

EXPOSE 8000

CMD ["poetry", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]

FROM base AS test

RUN poetry add pytest pytest-cov

CMD ["poetry", "run", "pytest", "--cov=api", "--cov-report=term-missing"]
