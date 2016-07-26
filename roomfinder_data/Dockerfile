FROM python:2-alpine
EXPOSE 5001

# Install basic utilities
RUN export http_proxy=http://173.38.209.12:80 \
  && export https_proxy=http://173.38.209.12:80 \
  && apk add -U \
        ca-certificates \
  && rm -rf /var/cache/apk/* \
  && pip install --no-cache-dir \
          setuptools \
          wheel

# This is failing for some odd pip upgrade error commenting out for now
#RUN pip install --upgrade pip

ADD . /app
WORKDIR /app
RUN export http_proxy=http://173.38.209.12:80 \
  && export https_proxy=http://173.38.209.12:80 \
  && pip install --requirement ./requirements.txt

CMD [ "python", "./roomfinder_data/data_server.py" ]

