# syntax=docker/dockerfile:1
FROM --platform=$BUILDPLATFORM curlimages/curl:7.85.0 as silero-downloader

WORKDIR /home/downloader/models

RUN curl https://models.silero.ai/models/tts/ru/v3_1_ru.pt -o ./silero_model.pt

#
# FROM --platform=$BUILDPLATFORM curlimages/curl:7.85.0 as vosk-downloader
#
# WORKDIR /home/downloader/models
#
# RUN curl https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip -o ./c611af587fcbdacc16bc7a1c6148916c-vosk-model-small-ru-0.22.zip
#
# FROM --platform=$BUILDPLATFORM python:3.9-slim-bullseye as ssl-generator
#
# WORKDIR /home/generator/ssl
#
# RUN openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -sha256 -nodes -days 365 -subj "/C=RU/CN=*"

FROM python:3.9-slim-bullseye

ARG BUILD_USER=python
ARG BUILD_HOME=/home/${BUILD_USER}
ARG BUILD_DIR=irene
ARG FULL_PATH=${BUILD_HOME}/${BUILD_DIR}

RUN groupadd --gid 1001 ${BUILD_USER} && useradd --create-home ${BUILD_USER} --uid 1001 --gid ${BUILD_USER} \
&& mkdir ${FULL_PATH}

COPY --chown=${BUILD_USER}:${BUILD_USER} . ${FULL_PATH}

RUN cp ${FULL_PATH}/runva_webapi_docker.json ${FULL_PATH}/runva_webapi.json \
&& cp ${FULL_PATH}/docker_plugins/* ${FULL_PATH}/plugins \
&& cp ${FULL_PATH}/plugins_inactive/plugin_tts_silero_v3.py ${FULL_PATH}/plugins

RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
    --mount=target=/var/cache/apt,type=cache,sharing=locked \
    --mount=type=cache,target=/root/.cache \
    rm -f /etc/apt/apt.conf.d/docker-clean \
&& apt update \
&& apt -y  -o 'Acquire::Retries=3' upgrade \
&& apt-get install -y -o 'Acquire::Retries=3' \
    libportaudio2 \
&& pip install -r ./${FULL_PATH}/requirements-docker.txt \
&& pip install thefuzz

WORKDIR ${BUILD_HOME}
USER ${BUILD_USER}:${BUILD_USER}

#COPY --link --from=frontend-builder /home/frontend/dist/ ./irene_plugin_web_face_frontend/frontend-dist/
COPY --link --from=silero-downloader /home/downloader/models/silero_model.pt ${FULL_PATH}/silero_model.pt
# COPY --link --chown=1001:1001 --from=vosk-downloader /home/downloader/models/ ./vosk-models/
# COPY --link --chown=1001:1001 --from=ssl-generator /home/generator/ssl/ ./ssl/

USER root:root
RUN chown -R ${BUILD_USER}:${BUILD_USER} ${BUILD_HOME}
USER ${BUILD_USER}:${BUILD_USER}

EXPOSE 5003

WORKDIR ${FULL_PATH}
ENTRYPOINT ["python3", "./runva_webapi.py"]
