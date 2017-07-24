FROM python:alpine
EXPOSE 80

# Add current folder as /app
RUN mkdir /app
WORKDIR /app

COPY requirements.txt /app

# Install basic utilities
RUN apk add -U ca-certificates curl tzdata bash \
  && rm -rf /var/cache/apk/* \
  && pip install --no-cache-dir --requirement ./requirements.txt

COPY src/dir.py /app

CMD [ "python","dir.py" ]
