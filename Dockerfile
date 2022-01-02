FROM python:3-bullseye

RUN apt-get update && apt-get install -y ffmpeg chromium chromium-driver
ARG TARGETARCH
RUN if [ $TARGETARCH = "arm64" ]; then \
        apt-get install -y libavformat-dev libavdevice-dev python3-av \
    ; fi

WORKDIR /app/src

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir /app/output

COPY main.py tum_live.py panopto.py downloader.py ./

ENTRYPOINT [ "python", "./main.py", "-c", "/app/config.yml", "-o", "/app/output" ]