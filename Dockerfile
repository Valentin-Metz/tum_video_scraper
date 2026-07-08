FROM python:3-bullseye

RUN apt-get update && apt-get install -y ffmpeg firefox-esr wget
ARG TARGETARCH
RUN if [ $TARGETARCH = "arm64" ]; then \
        apt-get install -y libavformat-dev libavdevice-dev python3-av \
    ; fi

# webdriver-manager is unmaintained and pulls adm-zip 0.5.18, whose optional
# chaining breaks under the Node 12 that python:3-bullseye ships. Fetch
# geckodriver straight from Mozilla instead.
ARG GECKODRIVER_VERSION=0.37.0
RUN case "$TARGETARCH" in \
        amd64) GECKO_TAR=geckodriver-v${GECKODRIVER_VERSION}-linux64.tar.gz ;; \
        arm64) GECKO_TAR=geckodriver-v${GECKODRIVER_VERSION}-linux-aarch64.tar.gz ;; \
        *) echo "unsupported arch: $TARGETARCH" >&2; exit 1 ;; \
    esac && \
    wget -q -O /tmp/${GECKO_TAR} \
        https://github.com/mozilla/geckodriver/releases/download/v${GECKODRIVER_VERSION}/${GECKO_TAR} && \
    tar -xzf /tmp/${GECKO_TAR} -C /usr/local/bin && \
    rm -f /tmp/${GECKO_TAR} && \
    geckodriver --version

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir /app/output

ENV NO-SANDBOX=1

COPY ./src /app/src

ENTRYPOINT [ "python", "/app/src/main.py", "-c", "/app/config.yml", "-o", "/app/output" ]
