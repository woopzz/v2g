FROM python:3.13

ARG USERNAME="peon"
ARG USER_UID=1000
ARG USER_GID=1000

ARG WORKDIR=/app

RUN \
    # Create user.
    groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    # Update the package base.
    && apt-get update \
    # Install ffmpeg.
    && apt-get install -y ffmpeg

WORKDIR $WORKDIR

COPY requirements.txt $WORKDIR
RUN pip install -r requirements.txt

ENV PYTHONPATH=/app

RUN chown -R $USERNAME:$USERNAME $WORKDIR

USER $USERNAME
