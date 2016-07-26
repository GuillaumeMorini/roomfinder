FROM python:2-alpine

# Install basic utilities
RUN export http_proxy=http://173.38.209.12:80 \
  && export https_proxy=http://173.38.209.12:80 \
  && apk add -U \
        ca-certificates curl tzdata \
  && rm -rf /var/cache/apk/* \
  && pip install --no-cache-dir \
          setuptools \
          wheel \
  && cp /usr/share/zoneinfo/Europe/Paris /etc/localtime

# This is failing for some odd pip upgrade error commenting out for now
#RUN pip install --upgrade pip

ADD . /app
WORKDIR /app
RUN export http_proxy=http://173.38.209.12:80 \
  && export https_proxy=http://173.38.209.12:80 \
  && pip install --requirement ./requirements.txt

ENV http_proxy=http://173.38.209.12:80
ENV https_proxy=http://173.38.209.12:80
ENV no_proxy=10*,*.cisco.com,192.168.*,172.*

CMD [ "./roomfinder_update/update_server.sh" ]
