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

# Я в душе не чаю, зачем нужна следующая команда, но без неё вызов pip install на архитектуре linux/arm64 падает.
# Связаные ссылки:
# https://webcache.googleusercontent.com/search?q=cache:R6EG8IVigbMJ:https://pythontechworld.com/issue/pypa/pip/11435&cd=1&hl=ru&ct=clnk&gl=ru
# О да! Решение, найденное в удалённой ветке какого-то форума!
# https://github.com/hofstadter-io/hof/commit/838e8bbe2171ba8b9929b0ffa812c0f1ed61e975#diff-185fff912be701240e6e971b5548217a2027904efe9e365728169da65eb4983b
RUN ln -s /bin/uname /usr/local/bin/uname
# https://github.com/docker/buildx/issues/495#issuecomment-995503425
RUN ln -s /usr/bin/dpkg-split /usr/sbin/dpkg-split
RUN ln -s /usr/bin/dpkg-deb /usr/sbin/dpkg-deb
RUN ln -s /bin/rm /usr/sbin/rm
RUN ln -s /bin/tar /usr/sbin/tar

RUN --mount=type=cache,target=/var/cache,sharing=locked apt update && apt install -y libportaudio2

RUN groupadd --gid 1001 python && useradd --create-home python --uid 1001 --gid python
USER python:python
WORKDIR /home/python

COPY ./requirements-docker.txt ./requirements.txt
RUN --mount=type=cache,target=/home/python/.cache,uid=1001,gid=1001 pip install -r ./requirements.txt
RUN --mount=type=cache,target=/home/python/.cache,uid=1001,gid=1001 pip install thefuzz

#COPY * .
COPY --chown=python:python empty_folder ./irene
COPY lingua_franca ./irene/lingua_franca
COPY media ./irene/media
COPY mic_client ./irene/mic_client
COPY model ./irene/model
COPY mpcapi ./irene/mpcapi
COPY plugins ./irene/plugins
COPY utils ./irene/utils
COPY webapi_client ./irene/webapi_client

COPY localhost.crt ./irene/localhost.crt
COPY localhost.key ./irene/localhost.key
COPY jaa.py ./irene/jaa.py
COPY vacore.py ./irene/vacore.py
COPY runva_webapi.py ./irene/runva_webapi.py
#COPY --chown=python:python options_docker ./irene/options
COPY --chown=python:python runva_webapi_docker.json ./irene/runva_webapi.json
COPY docker_plugins ./irene/plugins

#COPY --link --from=frontend-builder /home/frontend/dist/ ./irene_plugin_web_face_frontend/frontend-dist/
COPY --link --from=silero-downloader /home/downloader/models/silero_model.pt ./irene/silero_model.pt
# COPY --link --chown=1001:1001 --from=vosk-downloader /home/downloader/models/ ./vosk-models/
# COPY --link --chown=1001:1001 --from=ssl-generator /home/generator/ssl/ ./ssl/

EXPOSE 5003

#VOLUME /home/python/irene
# ENV IRENE_HOME=/irene
WORKDIR /home/python/irene
#ENTRYPOINT ["python", "-m", "irene", "--default-config", "/home/python/config"]
ENTRYPOINT ["python", "runva_webapi.py"]
#ENTRYPOINT uvicorn runva_webapi:app --proxy-headers --host 0.0.0.0 --port 8089