#FROM alpine:edge
#FROM python:3-alpine
FROM python:3-bullseye

#RUN echo "https://dl-cdn.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories
#RUN echo "@edge_testing https://dl-cdn.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories
#RUN apk add --no-cache python3 py3-numpy py3-pip ffmpeg firefox geckodriver
#RUN apk add --no-cache python3 py3-numpy py3-pip ffmpeg firefox geckodriver gcc g++ make python3-dev
#RUN apk add --no-cache python3 py3-numpy py3-pip ffmpeg firefox geckodriver@edge_testing gcc g++ make python3-dev
#RUN apk add --no-cache py3-numpy ffmpeg firefox geckodriver@edge_testing
RUN apt-get update -y && apt-get install ffmpeg firefox-esr wget -y

WORKDIR /app/src

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.30.0/geckodriver-v0.30.0-linux64.tar.gz \
    && tar -xf geckodriver-v0.30.0-linux64.tar.gz \
    && mv geckodriver /usr/local/bin/ \
    && rm geckodriver-v0.30.0-linux64.tar.gz

RUN mkdir /app/config && mkdir /app/output


COPY main.py tum_live.py panopto.py downloader.py ./

CMD [ "python", "./main.py", "-c", "/app/config/config.yml", "-o", "/app/output" ]