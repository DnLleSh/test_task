FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

COPY pyproject.toml ./
COPY uv.lock ./

RUN uv sync --frozen

COPY . .

RUN mkdir -p uploads/original uploads/thumbnails

RUN chmod -R 755 uploads/

EXPOSE 8000

CMD ["uv", "run", "python", "-m", "app.api.main"]
