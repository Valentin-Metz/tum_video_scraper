FROM python:3-bullseye

RUN apt-get update && apt-get install -y ffmpeg chromium chromium-driver
ARG TARGETARCH
RUN if [ $TARGETARCH = "arm64" ]; then \
        apt-get install -y libavformat-dev libavdevice-dev python3-av \
    ; fi

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir /app/output

ENV NO-SANDBOX 1

COPY ./src /app/src

ENTRYPOINT [ "python", "/app/src/main.py", "-c", "/app/config.yml", "-o", "/app/output" ]