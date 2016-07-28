FROM python:2-alpine
EXPOSE 5000

# Proxy setting
ADD proxy.sh /tmp/proxy.sh
RUN /tmp/proxy.sh

# Install basic utilities
RUN apk add -U \
        ca-certificates \
  && rm -rf /var/cache/apk/* \
  && pip install --no-cache-dir --requirement ./requirements.txt

# This is failing for some odd pip upgrade error commenting out for now
#RUN pip install --upgrade pip

ADD . /app
WORKDIR /app

CMD [ "python", "./roomfinder_web/web_server.py" ]

