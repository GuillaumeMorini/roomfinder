#!/bin/bash

docker build -t available .
docker stack rm available
docker stack deploy --compose-file docker-compose.yml available
