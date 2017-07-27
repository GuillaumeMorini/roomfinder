FROM python:alpine
RUN apk add -U ca-certificates curl tzdata bash curl \
  && rm -rf /var/cache/apk/*
RUN curl https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-amd64.zip >/tmp/ngrok.zip && \
    unzip -d /usr/local/bin /tmp/ngrok.zip && \
    rm -f /tmp/ngrok.zip
RUN curl -L https://github.com/stedolan/jq/releases/download/jq-1.5/jq-linux64 >/usr/local/bin/jq && \
    chmod +x /usr/local/bin/jq

RUN mkdir /app
WORKDIR /app

COPY requirements.txt /app
RUN pip install --no-cache-dir --requirement ./requirements.txt

COPY src/spark_bot.py /app
COPY start.sh /

CMD ["/start.sh"]