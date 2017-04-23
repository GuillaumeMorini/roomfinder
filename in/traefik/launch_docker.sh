#!/bin/bash

docker stack rm traefik
docker stack deploy --compose-file docker-compose.yml traefik

