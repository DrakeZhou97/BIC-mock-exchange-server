FROM python:3.12-alpine AS builder

WORKDIR /app

RUN apk add --no-cache gcc musl-dev

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
COPY src/ ./src/

RUN uv sync --no-dev --no-editable --frozen

# --- Production stage ---
FROM python:3.12-alpine

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

COPY src/ ./src/

ENV PATH="/app/.venv/bin:$PATH"

RUN adduser -D -u 1001 appuser
USER appuser

CMD ["python", "-m", "src"]
