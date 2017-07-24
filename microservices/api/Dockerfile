FROM python:alpine
EXPOSE 80

RUN mkdir /app
WORKDIR /app

COPY requirements.txt /app

# Install basic utilities
RUN apk add -U ca-certificates curl tzdata bash \
  && rm -rf /var/cache/apk/* \
  && pip install --no-cache-dir --requirement ./requirements.txt

COPY src/api.py /app

CMD [ "python","api.py" ]
