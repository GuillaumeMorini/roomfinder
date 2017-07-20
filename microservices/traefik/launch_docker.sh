#!/bin/bash

source ../.env
docker-compose down
docker-compose up -d
