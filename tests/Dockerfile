FROM python:3.13-bookworm

ARG USERNAME="peon"
ARG USER_UID=1000
ARG USER_GID=1000

ARG TERRAFORM_VERSION=1.14.7

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME

COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /uvx /bin
ENV UV_LINK_MODE=copy

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg

RUN curl -fsSL https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip -o /tmp/terraform.zip \
  && unzip /tmp/terraform.zip -d /tmp \
  && mv /tmp/terraform /usr/local/bin/ \
  && rm -rf /tmp/* \
  && terraform version

ARG WORKDIR="/app"
WORKDIR $WORKDIR

COPY . $WORKDIR
RUN chown -R $USER_UID:$USER_GID /app

USER $USERNAME
RUN --mount=type=cache,target=/home/$USERNAME/.cache/uv,uid=$USER_UID,gid=$USER_GID \
    uv sync --locked
