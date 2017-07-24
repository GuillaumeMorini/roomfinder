#!/bin/bash

NAME=`basename $PWD`
docker build -t guismo/rf_$NAME:latest .
docker push guismo/rf_$NAME:latest
docker service update roomfinder_$NAME --image guismo/rf_$NAME --force