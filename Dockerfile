FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:0.8.22 /uv /uvx /bin/
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src ./src
COPY .mosaic ./.mosaic
COPY evaluations ./evaluations
COPY evidence ./evidence
COPY fixtures ./fixtures
COPY examples ./examples
RUN uv sync --frozen --no-dev --no-extra datahub

ENV PATH="/app/.venv/bin:${PATH}"
ENV MOSAIC_PUBLIC_DEMO=true
EXPOSE 8123
CMD ["sh", "-c", "uvicorn mosaic.web.complete_app:create_app --factory --host 0.0.0.0 --port ${PORT:-8123}"]
