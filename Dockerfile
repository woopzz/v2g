FROM python:3.13-slim-bookworm AS base

COPY --from=ghcr.io/astral-sh/uv:0.4.9 /uv /usr/local/bin/uv

ARG USERNAME="peon"
ARG USER_UID=1000
ARG USER_GID=1000

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg=7:5.1.6-0+deb12u1

ARG WORKDIR=/app

WORKDIR $WORKDIR

COPY . $WORKDIR

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

COPY . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

ENV WORKDIR=$WORKDIR \
    PYTHONPATH=$WORKDIR

RUN chown -R $USERNAME:$USERNAME $WORKDIR
USER $USERNAME

CMD ["uv", "run", "./v2g/main.py"]

FROM base as dev

USER root

RUN apt-get install -y --no-install-recommends \
    sudo \
    git
RUN echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

USER $USERNAME
