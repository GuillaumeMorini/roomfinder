#!/usr/bin/env python2.7

import sys
reload(sys)
sys.setdefaultencoding("utf-8")

from string import Template
import xml.etree.ElementTree as ET
import csv, codecs, os
import argparse
import datetime
import json
import requests
from requests_ntlm import HttpNtlmAuth
from threading import Thread
from Queue import Queue

def doWork():
    while True:
        data = q.get()
        response = send_request(data)
        doSomethingWithResult(response)
        q.task_done()

def send_request(data):
    try:
        headers = {}
        headers["Content-type"] = "text/xml; charset=utf-8"
        #sys.stderr.write('data='+str(data))
        response=requests.post(url,headers = headers, data= data, auth= HttpNtlmAuth(user,password))
        return response
    except:
        return None

def doSomethingWithResult(response):
    if response is None:
        return "KO"
    else:
        tree = ET.fromstring(response.text)

        status = "Free"
        # arrgh, namespaces!!
        elems=tree.findall(".//{http://schemas.microsoft.com/exchange/services/2006/types}BusyType")
        for elem in elems:
            status=elem.text

        tree2=ET.fromstring(response.request.body)
        elems2=tree2.findall(".//{http://schemas.microsoft.com/exchange/services/2006/types}Address")
        for e in elems2:
            room=e.text

        #sys.stderr.write(str(now.isoformat())+": Get BusyType for room "+str(rooms[room])+": len: "+str(len(elems))+" => "+str(elems[0])+"\n")
        sys.stderr.write(str(now.isoformat())+": Status for room "+str(rooms[room])+": "+str(room)+" => "+status+"\n")
        result.append((status, rooms[room], room))

if __name__ == '__main__':
    now = datetime.datetime.now().replace(microsecond=0)
    starttime_default = now.isoformat()
    end_time_default = None

    from argparse import ArgumentParser
    parser = ArgumentParser("Room Finder Update Service")
    parser.add_argument(
        "-d", "--data", help="Address of data server", required=False
    )
    parser.add_argument("-url","--url", help="url for exchange server, e.g. 'https://mail.domain.com/ews/exchange.asmx'.")
    parser.add_argument("-u","--user", help="user for exchange server, e.g. 'toto@toto.com'.")
    parser.add_argument("-p","--password", help="password for exchange server.")
    parser.add_argument("-start","--starttime", help="Starttime e.g. 2014-07-02T11:00:00 (default = now)", default=starttime_default)
    parser.add_argument("-end","--endtime", help="Endtime e.g. 2014-07-02T12:00:00 (default = now+1h)", default=end_time_default)
    #parser.add_argument("-n","--now", help="Will set starttime to now and endtime to now+1h", action="store_true")
    parser.add_argument("-f","--file", help="csv filename with rooms to check (default=rooms.csv). Format: Name,email",default="rooms.csv")

    args = parser.parse_args()

    data_server = args.data
    # print "Arg Data: " + str(data_server)
    if (data_server == None):
        data_server = os.getenv("roomfinder_data_server")
        # print "Env Data: " + str(data_server)
        if (data_server == None):
            get_data_server = raw_input("What is the data server address? ")
            # print "Input Data: " + str(get_data_server)
            data_server = get_data_server

    # print "Data Server: " + data_server
    # sys.stderr.write("Data Server: " + data_server + "\n")

    # book_server = args.book
    # # print "Arg Book: " + str(book_server)
    # if (book_server == None):
    #     book_server = os.getenv("roomfinder_book_server")
    #     # print "Env Book: " + str(book_server)
    #     if (book_server == None):
    #         get_book_server = raw_input("What is the book server address? ")
    #         # print "Input Book: " + str(get_book_server)
    #         book_server = get_book_server

    # # print "Book Server: " + book_server
    # # sys.stderr.write("Book Server: " + book_server + "\n")

    url = args.url

    if (url == None):
        url = os.getenv("roomfinder_exchange_server")
        # print "Exchange URL: " + str(url)
        if (url == None):
            get_exchange_server = raw_input("What is the Exchange server URL? ")
            # print "Input URL: " + str(get_exchange_server)
            url = get_exchange_server

    # sys.stderr.write("Exchange URL: " + url + "\n")

    user = args.user

    if (user == None):
        user = os.getenv("roomfinder_exchange_user")
        # print "Exchange user: " + str(user)
        if (user == None):
            get_exchange_user = raw_input("What is the Exchange user? ")
            # print "Input Exchange user: " + str(get_exchange_user)
            user = get_exchange_user

    # sys.stderr.write("Exchange user: " + user + "\n")

    password = args.password

    if (password == None):
        password = os.getenv("roomfinder_exchange_password")
        # print "Exchange password: " + str(password)
        if (password == None):
            get_exchange_password = raw_input("What is the Exchange server password? ")
            # print "Input Exchange password: " + str(get_exchange_password)
            password = get_exchange_password

    # sys.stderr.write("Exchange password: " + password + "\n")

    file = args.file

    if (file == None):
        file = os.getenv("roomfinder_rooms_file")
        # print "Rooms file: " + file
        if (file == None):
            get_rooms_file = raw_input("What is the rooms filename? ")
            # print "Rooms file: " + get_rooms_file
            file = get_rooms_file

    # sys.stderr.write("Rooms filename: " + file + "\n")

    rooms={}
    reader = csv.reader(codecs.open(file, 'r', encoding='utf-8')) 
    for row in reader: 
        rooms[unicode(row[1])]=unicode(row[0])

    start_time = args.starttime
    if not args.endtime:
        start = datetime.datetime.strptime( start_time, "%Y-%m-%dT%H:%M:%S" )
        end_time = (start + datetime.timedelta(hours=2)).isoformat()
    else:
        end_time = args.endtime

    sys.stderr.write(str(now.isoformat())+": Lookup for availability from "+str(start_time)+" to "+str(end_time)+"\n")

    # page = requests.get(book_server+'/dispo') # find how to send the list of rooms read from previous file
    # result = page.text() # format result

    xml_template = open("getavailibility_template.xml", "r").read()
    xml = Template(xml_template)
    result=list()

    concurrent=31
    q = Queue(concurrent * 2)
    for i in range(concurrent):
        t = Thread(target=doWork)
        t.daemon = True
        t.start()
    sys.stderr.write(str(now.isoformat())+": End of init of Thread start\n")
    try:
        for room in rooms:
            q.put(unicode(xml.substitute(email=room,starttime=start_time,endtime=end_time)).strip())
        sys.stderr.write(str(now.isoformat())+": End of send data to process to Thread\n")
        q.join()
        sys.stderr.write(str(now.isoformat())+": End of join Thread\n")
    except KeyboardInterrupt:
        sys.exit(1)

    # Post json object out to data_server URL
    u = data_server + "/post"
    r = requests.post(u,json=json.dumps(((("List of rooms status","for ILM building","from " + start_time,"to " + end_time),sorted(result, key=lambda tup: tup[1])))))
    sys.stderr.write(str(now.isoformat())+": Response of Post to data server: "+r.text+"\n")