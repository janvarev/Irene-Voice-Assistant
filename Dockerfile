# Stage 1: Download Vosk model
FROM --platform=$BUILDPLATFORM curlimages/curl:7.85.0 as vosk-downloader
WORKDIR /home/downloader/models
RUN curl https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip -o ./c611af587fcbdacc16bc7a1c6148916c-vosk-model-small-ru-0.22.zip

# Stage 2: Build final image
FROM python:3.10-slim

WORKDIR /home/python

# Install system dependencies
RUN --mount=type=cache,target=/var/cache,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    libportaudio2 \
    libsndfile1-dev \
    libatomic1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies


# Copy application files
COPY requirements-docker.txt irene/requirements.txt
COPY lingua_franca irene/lingua_franca
COPY media irene/media
COPY mic_client irene/mic_client
COPY model irene/model
COPY mpcapi irene/mpcapi
COPY plugins irene/plugins
COPY utils irene/utils
COPY webapi_client irene/webapi_client
COPY temp irene/temp

COPY localhost.crt irene/localhost.crt
COPY localhost.key irene/localhost.key
COPY jaa.py irene/jaa.py
COPY vacore.py irene/vacore.py
COPY runva_webapi.py irene/runva_webapi.py
COPY options_docker irene/options
COPY runva_webapi_docker.json irene/runva_webapi.json
COPY docker_plugins irene/plugins

# Copy downloaded Vosk model
COPY --link --chown=1000:1000 --from=vosk-downloader /home/downloader/models/ ./vosk-models/

EXPOSE 5003

WORKDIR /home/python/irene
ENTRYPOINT ["/bin/sh", "-c", "pip install -r requirements.txt && python runva_webapi.py"]