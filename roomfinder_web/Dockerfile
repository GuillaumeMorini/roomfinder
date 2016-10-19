FROM python:2-alpine
EXPOSE 5000

# Add current folder as /app
ADD . /app
WORKDIR /app

# Install basic utilities
RUN export http_proxy=http://proxy-wsa.esl.cisco.com:80/ \
  && export https_proxy=http://proxy-wsa.esl.cisco.com:80/ \ 
  && apk add -U \
        ca-certificates \
  && rm -rf /var/cache/apk/* \
  && pip install --no-cache-dir --requirement ./requirements.txt

# This is failing for some odd pip upgrade error commenting out for now
#RUN pip install --upgrade pip

CMD [ "python", "./roomfinder_web/web_server.py" ]

