#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding("utf-8")

import subprocess
import getpass
from string import Template
import xml.etree.ElementTree as ET
import csv, codecs
import argparse
import datetime
import json
import requests
from requests_ntlm import HttpNtlmAuth
from threading import Thread
from Queue import Queue

def doWork():
    # while True:
        data = q.get()
        response = send_request(data)
        doSomethingWithResult(response)
        q.task_done()

def send_request(data):
    headers = {}
    headers["Content-type"] = "text/xml; charset=utf-8"
    response=requests.post(url,headers = headers, data= data, auth= HttpNtlmAuth(user,password))
    sys.stderr.write("response: "+str(response)+"\n")
    if response.status_code == 200:
        return response
    else:
        return None

def doSomethingWithResult(response):
    global result
    if response is None:
        return "KO"
    else:
        tree = ET.fromstring(response.text)

        status = "Bidon"
        # arrgh, namespaces!!
        elems=tree.findall(".//{http://schemas.microsoft.com/exchange/services/2006/types}BusyType")
        for elem in elems:
            status=elem.text

        tree2=ET.fromstring(response.request.body)
        elems=tree2.findall(".//{http://schemas.microsoft.com/exchange/services/2006/types}Address")
        for e in elems:
            room=e.text

        print "Status for room: "+str(room)+" => "+status
        result.append((status, rooms[room], room))
        return "OK"

now = datetime.datetime.now().replace(microsecond=0)
starttime_default = now.isoformat()
end_time_default = None

parser = argparse.ArgumentParser()
parser.add_argument("-url","--url", help="url for exhange server, e.g. 'https://mail.domain.com/ews/exchange.asmx'.",required=True)
parser.add_argument("-u","--user", help="user name for exchange/outlook",required=True)
parser.add_argument("-p","--password", help="password for exchange/outlook", required=True)
parser.add_argument("-start","--starttime", help="Starttime e.g. 2014-07-02T11:00:00 (default = now)", default=starttime_default)
parser.add_argument("-end","--endtime", help="Endtime e.g. 2014-07-02T12:00:00 (default = now+2h)", default=end_time_default)
#parser.add_argument("-n","--now", help="Will set starttime to now and endtime to now+1h", action="store_true")
parser.add_argument("-f","--file", help="csv filename with rooms to check (default=rooms.csv). Format: Name,email",default="rooms.csv")

args=parser.parse_args()

url = args.url

rooms={}
reader = csv.reader(codecs.open(args.file, 'r', encoding='utf-8')) 
for row in reader: 
    rooms[unicode(row[1])]=unicode(row[0])

print "Rooms: "+str(rooms)

start_time = args.starttime
if not args.endtime:
    start = datetime.datetime.strptime( start_time, "%Y-%m-%dT%H:%M:%S" )
    end_time = (start + datetime.timedelta(hours=2)).isoformat()
else:
    end_time = args.endtime

user = args.user
password = args.password

xml_template = open("getavailibility_template.xml", "r").read()
xml = Template(xml_template)
for j in range(1,31):
    result=list()
    s=raw_input("avant")
    concurrent=len(rooms)+1
    threads=[]
    try:
        print "Init of Thread start"
        q = Queue(concurrent * 2)
        for room in rooms:
            t = Thread(target=doWork)
            threads.append(t)
            t.daemon = True
            t.start()
            print "End of init of Thread start"
            q.put(unicode(xml.substitute(email=room,starttime=start_time,endtime=end_time)).strip())
        print "End of send data to process to Thread"
        q.join()
        # for t in threads:
        #     t.join()
        print "End of join Thread"
    except KeyboardInterrupt:
        sys.exit(1)
    import json
    with open('available_rooms.json', 'w') as outfile:
        json.dump(("List of rooms status <br> for ILM building <br> from " + start_time + " <br> to " + end_time + ":",sorted(result, key=lambda tup: tup[1])), outfile)
    s=raw_input("apres")