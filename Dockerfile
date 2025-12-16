FROM python:3.13-slim-bookworm AS builder


COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /uvx /bin
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-editable --no-dev

COPY . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable --no-dev

FROM python:3.13-slim-bookworm

# It's imporatant because we collect logs from stdout and stderr.
ENV PYTHONUNBUFFERED=1

ARG USERNAME="peon"
ARG USER_UID=1000
ARG USER_GID=1000

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg

COPY --from=builder --chown=$USER_UID:$USER_GID /app/.venv /app/.venv
COPY ./scripts/run_workers.sh /app/run_workers.sh

USER $USERNAME

CMD ["/app/.venv/bin/python", "-m", "v2g.server"]
