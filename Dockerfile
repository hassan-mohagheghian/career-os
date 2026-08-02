FROM python:3.14-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY apps/ ./apps/

RUN pip install uv && uv sync --frozen --no-dev

EXPOSE 5000

CMD ["uv", "run", "uvicorn", "apps.backend.entrypoints.api:app", "--host", "0.0.0.0", "--port", "5000"]
