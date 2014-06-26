#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding("utf-8")

from string import Template
from string import letters
from string import digits
import subprocess
import getpass
import xml.etree.ElementTree as ET
import argparse
import csv
import operator

def findRooms(prefix):
	rooms={}
	data = unicode(xml.substitute(name=prefix))

	header = "\"content-type: text/xml;charset=utf-8\""
	command = "curl --silent --header " + header +" --data '" + data + "' --ntlm "+"--negotiate "+ "-u "+ user+":"+password+" "+ url
	response = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True).communicate()[0]
	tree = ET.fromstring(response)

	elems=tree.findall(".//{http://schemas.microsoft.com/exchange/services/2006/types}Resolution")
	for elem in elems:
		email = elem.findall(".//{http://schemas.microsoft.com/exchange/services/2006/types}EmailAddress")
		name = elem.findall(".//{http://schemas.microsoft.com/exchange/services/2006/types}DisplayName")
		if len(email) > 0 and len(name) > 0:
			rooms[email[0].text] = name[0].text
	return rooms		

parser = argparse.ArgumentParser()
parser.add_argument("prefix", nargs='+',help="A list of prefixes to search for. E.g. 'conference confi'")
parser.add_argument("-url","--url", help="url for exhange server, e.g. 'https://mail.domain.com/ews/exchange.asmx'.",required=True)
parser.add_argument("-u","--user", help="user name for exchange/outlook", required=True)
parser.add_argument("-d","--deep", help="Attemp a deep search (takes longer).", action="store_true")
args=parser.parse_args()

url = args.url
user = args.user
password = getpass.getpass("Password:")

xml_template = open("resolvenames_template.xml", "r").read()
xml = Template(xml_template)

rooms={}

for prefix in args.prefix:
	rooms.update(findRooms(prefix))
	print "After searching for prefix '" + prefix + "' we found " + str(len(rooms)) + " rooms."

	deep = args.deep

	if deep: 
		symbols = letters + digits
		for symbol in symbols:
			prefix_deep = prefix + " " + symbol
			rooms.update(findRooms(prefix_deep))

		print "After deep search for prefix '" + prefix + "' we found " + str(len(rooms)) + " rooms."

writer = csv.writer(open("rooms.csv", "wb"))
for item in sorted(rooms.iteritems(), key=operator.itemgetter(1)):
	writer.writerow([item[1],item[0]])
