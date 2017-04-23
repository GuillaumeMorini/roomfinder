#!/bin/bash

docker build -t router_in .
docker stack rm router_in
docker stack deploy --compose-file docker-compose.yml router_in
