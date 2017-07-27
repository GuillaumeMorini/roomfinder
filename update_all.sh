#!/bin/bash

for NAME in `ls microservices`
do 
	cd microservices/$NAME
	docker build -t guismo/rf_$NAME:latest .
	docker push guismo/rf_$NAME:latest
	docker service update roomfinder_$NAME --image guismo/rf_$NAME --force
	cd ../..
done
