ARG PYTHON_VERSION=3.10
ARG UV_VERSION=latest

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv_installer

FROM python:${PYTHON_VERSION}-slim AS builder
COPY --from=uv_installer /uv /uvx /bin/
WORKDIR /app
ADD . /app

RUN apt-get update && apt-get install -y git openssh-client

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync

FROM python:${PYTHON_VERSION}-slim AS runtime
ENV IS_CONTAINER=true
COPY --from=uv_installer /uv /uvx /bin/
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/assistant_engine /app/assistant_engine
COPY --from=builder /app/botbrew_commons /app/botbrew_commons
COPY --from=builder /app/nowisthetime_legacy /app/nowisthetime_legacy
COPY --from=builder /app/.env /app/.env
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "nowisthetime_legacy.main:app", "--host", "0.0.0.0", "--port", "8000"]
