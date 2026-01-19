ARG GO_VERSION=1.24.1
ARG UV_VERSION=0.9.25

FROM golang:${GO_VERSION} AS bridge-builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src/whatsapp-bridge
COPY whatsapp-bridge/go.mod whatsapp-bridge/go.sum ./
RUN go mod download

COPY whatsapp-bridge/ ./
RUN CGO_ENABLED=1 go build -o /out/whatsapp-bridge

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates libsqlite3-0 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=uv /uv /uvx /bin/

WORKDIR /app
COPY . /app

ENV UV_NO_DEV=1
WORKDIR /app/whatsapp-mcp-server
RUN uv sync --locked

WORKDIR /app
COPY --from=bridge-builder /out/whatsapp-bridge /app/whatsapp-bridge/whatsapp-bridge
COPY docker/entrypoint.sh /app/docker/entrypoint.sh
RUN chmod +x /app/docker/entrypoint.sh

VOLUME ["/app/whatsapp-bridge/store"]
EXPOSE 8000
ENTRYPOINT ["/app/docker/entrypoint.sh"]
