Roomfinder
==========

![logo](./logo_128.png?raw=true "Roomfinder")

[![Build Status](http://drone.guismo.fr.eu.org:8000/api/badges/GuillaumeMorini/roomfinder/status.svg?branch=dev)](http://drone.guismo.fr.eu.org:8000/GuillaumeMorini/roomfinder)

ChatBot written in Python for finding free conference rooms from a Microsoft Exchange Server.

You need to launch :
 - roomfinder_data to store the database
 - roomfinder_update to update the database regularly based on the exchange server
 - roomfinder_web to be able to present it in a web (html) format
 - roomfinder_spark to have a Cisco Spark bot


roomfinder_data
=================
Need to be accessible to every other containers

roomfinder_update
=================
Need to be run with IP access to Exchange server

roomfinder_web
=================
Need to be accessible from end users

roomfinder_spark
=================
Need to have a Public IP to be accessible from Cisco Spark backend

