roomfinder
==========

Python scripts for finding free conference rooms from a Microsoft Exchange Server.

Requirements:
 
 - curl
 - Python 2.7
 - Access to Exchange Web Service (EWS) API of a Microsoft Exchange Server 2010 

Usage:

	$ python find_rooms.py -h
	usage: find_rooms.py [-h] -url URL -u USER [-d] prefix [prefix ...]

	positional arguments:
	  prefix                A list of prefixes to search for. E.g. 'conference
	                        confi'

	optional arguments:
	  -h, --help            show this help message and exit
	  -url URL, --url URL   url for exhange server, e.g.
	                        'https://mail.domain.com/ews/exchange.asmx'.
	  -u USER, --user USER  user name for exchange/outlook
	  -d, --deep            Attemp a deep search (takes longer).




Example:
	
	$ python find_rooms.py Konferenzr. Konfi -url https://mail.mycompany.com/ews/exchange.asmx -u maier --deep
	Password:
	After searching for prefix 'Konferenzr.' we found 100 rooms.
	After deep search for prefix 'Konferenzr.' we found 143 rooms.
	After searching for prefix 'Konfi' we found 151 rooms.
	After deep search for prefix 'Konfi' we found 151 rooms.  

This will create a CSV file `rooms.csv` holding a list of all rooms found with the prefix `Konfi` and `Konferenzr.` in their display names.

After doing so, this file need to be copied to roomfinder_update folder


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

