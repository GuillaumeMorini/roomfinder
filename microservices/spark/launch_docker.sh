#!/bin/bash

docker build -t roomfinder_spark .
docker stop roomfinder_spark
docker rm roomfinder_spark
docker run -d -p 5555:5000 \
	-e roomfinder_dispo_server="http://37.187.22.103:5002" \
	-e roomfinder_data_server=http://37.187.22.103:5001 \
    -e roomfinder_spark_bot_email=roomfinder@sparkbot.io \
    -e spark_token=OTI2NTcxY2MtODZhYy00N2IzLThlZDItY2Y2MmM5YmNkODA1Y2FhNmZlNTUtZDA5 \
    -e roomfinder_spark_bot_url=http://37.187.22.103:5555 \
    -e log_room_id=Y2lzY29zcGFyazovL3VzL1JPT00vODUzMmJhZjAtMmY2Yi0xMWU3LTlkZWItN2Q4Y2QxZWQ4YTdm \
    -v /root/roomfinder/roomfinder_spark/log:/log \
    --restart always \
	--name roomfinder_spark roomfinder_spark
