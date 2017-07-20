#!/bin/bash

source ../.env
NAME=`basename $PWD`
docker stop $NAME
docker rm $NAME
docker run -d  \
    --net=roomfinder-network \
    -p $RABBITMQ_PORT:5672 \
	--name $NAME $NAME
