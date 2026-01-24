FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.9.24 /uv /uvx /bin/

# Optimizations
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /package

# So we won't have to use "uv run" every time.
ENV PATH="/package/.venv/bin:$PATH"

COPY pyproject.toml uv.lock ./

RUN uv sync --locked

# For development docker-compose will overwrite folder
COPY src /package/src
COPY alembic.ini ./
COPY alembic /package/alembic

# Since I cant execute it on Windows
COPY start.sh .
RUN chmod +x start.sh

EXPOSE 8000

ENTRYPOINT ["/package/start.sh"]