FROM python:2-alpine
EXPOSE 5000

# Add current folder as /app
ADD . /app
WORKDIR /app

# Install basic utilities
RUN export http_proxy=http://173.38.209.12:80 \
  && export https_proxy=http://173.38.209.12:80 \
  && apk add -U \
        ca-certificates curl tzdata \
  && rm -rf /var/cache/apk/* \
  && pip install --no-cache-dir --requirement ./requirements.txt

CMD [ "python", "./roomfinder_spark/spark_bot.py" ]

