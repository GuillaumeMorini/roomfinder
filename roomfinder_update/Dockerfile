FROM python:2-alpine

# Proxy setting
ADD proxy.sh /tmp/proxy.sh
RUN /tmp/proxy.sh

# Add current folder as /app
ADD . /app
WORKDIR /app

# Install basic utilities
RUN apk add -U \
        ca-certificates curl tzdata \
  && rm -rf /var/cache/apk/* \
  && pip install --no-cache-dir --requirement ./requirements.txt

# This is failing for some odd pip upgrade error commenting out for now
#RUN pip install --upgrade pip

CMD [ "./roomfinder_update/update_server.sh" ]
