#!/bin/bash

#source .env
#docker login
#for NAME in `ls microservices`
#do 
#	cd microservices/$NAME
#	docker build -t guismo/rf_$NAME:latest .
#	docker push guismo/rf_$NAME:latest
#	cd ../..
#done

docker stack rm roomfinder
sleep 1
docker stack deploy --compose-file docker-compose.yml roomfinder

