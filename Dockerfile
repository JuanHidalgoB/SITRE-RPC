#SITRE-RPC — Dockerfile (imagen base compartida para server y client)

FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Instalar uv 
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY proto/   proto/
COPY server/  server/
COPY src/     src/
COPY client/  client/

RUN mkdir -p generated && \
    .venv/bin/python -m grpc_tools.protoc \
        -I proto \
        --python_out=generated \
        --grpc_python_out=generated \
        proto/sitre.proto && \
    touch generated/__init__.py

RUN mkdir -p resultados mlruns

ENV PATH="/app/.venv/bin:$PATH"
