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

now = datetime.datetime.now().replace(microsecond=0)
starttime_default = now.isoformat()
end_time_default = None

parser = argparse.ArgumentParser()
parser.add_argument("-url","--url", help="url for exhange server, e.g. 'https://mail.domain.com/ews/exchange.asmx'.",required=True)
parser.add_argument("-u","--user", help="user name for exchange/outlook",required=True)
parser.add_argument("-start","--starttime", help="Starttime e.g. 2014-07-02T11:00:00 (default = now)", default=starttime_default)
parser.add_argument("-end","--endtime", help="Endtime e.g. 2014-07-02T12:00:00 (default = now+1h)", default=end_time_default)
#parser.add_argument("-n","--now", help="Will set starttime to now and endtime to now+1h", action="store_true")
parser.add_argument("-f","--file", help="csv filename with rooms to check (default=rooms.csv). Format: Name,email",default="rooms.csv")

args=parser.parse_args()

url = args.url

start_time = args.starttime
if not args.endtime:
	start = datetime.datetime.strptime( start_time, "%Y-%m-%dT%H:%M:%S" )
	end_time = (start + datetime.timedelta(hours=2)).isoformat()
else:
	end_time = args.endtime
user = "gmorini@cisco.com"
password = "Put12vol"

xml_template = open("book_room.xml", "r").read()
xml = Template(xml_template)
data = unicode(xml.substitute(starttime=start_time,endtime=end_time,user="gmorini",user_email=user,room="ILM-7-HUGO",room_email="CONF_5515@cisco.com"))

header = "\"content-type: text/xml;charset=utf-8\""
command = "curl --silent --header " + header +" --data '" + data + "' --ntlm "+ "-u "+ user+":"+password+" "+ url
response = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True).communicate()[0]

print str(response)

tree = ET.fromstring(response)

