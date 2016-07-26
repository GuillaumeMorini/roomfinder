#!/bin/sh

echo "nameserver 144.254.71.184" > /etc/resolv.conf
echo "nameserver 173.38.200.100" >> /etc/resolv.conf
cd /app
while true
do
	python roomfinder_update/update_server.py
	sleep 300
done
