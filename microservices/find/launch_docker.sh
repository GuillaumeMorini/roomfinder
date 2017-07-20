#!/bin/bash

source ../.env
NAME=`basename $PWD`
docker build -t $NAME .
docker stack rm $NAME
docker stack deploy --compose-file docker-compose.yml $NAME
