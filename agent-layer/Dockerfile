FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install the package (source must be present for a src-less flat layout).
COPY pyproject.toml ./
COPY forge ./forge
RUN pip install --no-cache-dir .

# Migrations run on container start, before the API comes up.
COPY alembic.ini ./
COPY alembic ./alembic

RUN useradd --create-home --uid 1000 forge && chown -R forge:forge /app
USER forge

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn forge.main:app --host 0.0.0.0 --port 8000"]
