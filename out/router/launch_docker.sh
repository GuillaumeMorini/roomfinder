#!/bin/bash

docker build -t router .
docker stack rm router
docker stack deploy --compose-file docker-compose.yml router
