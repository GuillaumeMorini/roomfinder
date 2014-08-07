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

After doing so, you can get the status for each of the rooms by calling

	$ python find_available_room.py -h
    usage: find_available_room.py [-h] -url URL -u USER [-start STARTTIME]
                                  [-end ENDTIME] [-f FILE]
    
    optional arguments:
      -h, --help            show this help message and exit
      -url URL, --url URL   url for exhange server, e.g.
                            'https://mail.domain.com/ews/exchange.asmx'.
      -u USER, --user USER  user name for exchange/outlook
      -start STARTTIME, --starttime STARTTIME
                            Starttime e.g. 2014-07-02T11:00:00 (default = now)
      -end ENDTIME, --endtime ENDTIME
                            Endtime e.g. 2014-07-02T12:00:00 (default = now+1h)
      -f FILE, --file FILE  csv filename with rooms to check (default=rooms.csv).
                            Format: Name,email


Example:
	
	$ python find_available_room.py -url https://mail.mycompany.com/ews/exchange.asmx -u maier -start 2014-07-03T13:00:00 -end 2014-07-03T17:00:00
	Password:
	Busy       Konferenzr. Asterix                                              konf.asterix@mycompany.com                                  
	Tentative  Konferenzr. Personal                                             Konferenzr.Personal@mycompany.com             
	Busy       Konferenzr. Obelix                                               konferenzr.obelix@mycompany.com              
	Busy       Konfi  Idefix                                                    konfi_idefix@mycompany.com                                   
	Free       Konferenzr. Miraculix                                            miraculix@mycompany.com       
	...

Since the auto-generated list `rooms.csv` can be very huge it is recommended to copy that list to another file, e.g. `favorite_rooms.csv` and edit that file so that it only holds the meetings rooms you are interested in. After doing so, you can get the status for you favorite rooms very quickly using:

	$ python find_available_room.py -url https://mail.mycompany.com/ews/exchange.asmx -u maier -start 2014-07-03T13:00:00 -end 2014-07-03T17:00:00 -f favorite_rooms.csv
	Password:
	Free       Konferenzr. 007                                                  007@mycompany.com                                         
	Busy       Konferenzr. Asterix                                              konf.asterix@mycompany.com                                         
	Busy       Konferenzr. Obelix                                               konferenzr.obelix@mycompany.com   

                                      



