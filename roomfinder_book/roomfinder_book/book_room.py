#!/usr/bin/env python2.7

from flask import Flask, request
import json, datetime
import sys, os
from string import Template
import xml.etree.ElementTree as ET
import subprocess
import requests
from requests_ntlm import HttpNtlmAuth
from threading import Thread
from Queue import Queue
import argparse

def doWork():
    # while True:
        data = q.get()
        response = send_request(data)
        doSomethingWithResult(response)
        q.task_done()

def send_request(data):
    try:
        headers = {}
        headers["Content-type"] = "text/xml; charset=utf-8"
        sys.stderr.write('data='+str(data)+'\n')
        response=requests.post(url,headers = headers, data= data, auth= HttpNtlmAuth(user,password))
        return response
    except:
        return None

def doSomethingWithResult(response):
    if response is None:
        return "KO"
    else:
        tree = ET.fromstring(response.text.encode('utf-8'))

        status = "Free"
        # arrgh, namespaces!!
        elems=tree.findall(".//{http://schemas.microsoft.com/exchange/services/2006/types}BusyType")
        for elem in elems:
            status=elem.text

        tree2=ET.fromstring(response.request.body.encode('utf-8'))
        elems=tree2.findall(".//{http://schemas.microsoft.com/exchange/services/2006/types}Address")
        for e in elems:
            room=e.text

        sys.stderr.write(str(datetime.datetime.now().isoformat())+": Status for room: "+str(room)+" => "+status+"\n")
        result.append((status, rooms[room], room))
        return "OK"

FILE="available_rooms.json"

app = Flask(__name__)

def is_available(room_email,start_time,end_time):
    xml_template = open("getavailibility_template.xml", "r").read()
    xml = Template(xml_template)
    headers = {}
    headers["Content-type"] = "text/xml; charset=utf-8"
    data=unicode(xml.substitute(email=room_email,starttime=start_time,endtime=end_time)).strip()
    response=requests.post(url,headers = headers, data= data, auth= HttpNtlmAuth(user,password))
    tree = ET.fromstring(response.text.encode('utf-8'))
    status = "Free"
    # arrgh, namespaces!!
    elems=tree.findall(".//{http://schemas.microsoft.com/exchange/services/2006/types}BusyType")
    for elem in elems:
        status=elem.text
    return (status == "Free")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        room_name = request.form["room_name"]
        room_email = request.form["room_email"]
        user_email = request.form["user_email"]

        now = datetime.datetime.now().replace(microsecond=0)
        start_time = now.isoformat()
        end_time = (now + datetime.timedelta(hours=2)).isoformat()
        if is_available(room_email, start_time, end_time):
            book_room(room_name, room_email, user_email, user_email, start_time, end_time)
            return "Room "+str(room_name)+" booked for "+user_email+" from "+str(start_time)+" to "+str(end_time)
        else:
            return "Sorry, room "+str(room_name)+" not available !"
    else:
        return "Error should be a POST"

@app.route('/book', methods=['GET', 'POST'])
def book():
    if request.method == 'POST':
        j = request.get_json()
        sys.stderr.write("Type: "+str(type(j))+"\n")
        sys.stderr.write("j: "+str(j)+"\n")
        sys.stderr.write("user_name: "+str(j["user_name"])+"\n")
        sys.stderr.write("user_email: "+str(j["user_email"])+"\n")
        sys.stderr.write("start_time: "+str(j["starttime"])+"\n")
        sys.stderr.write("end_time: "+str(j["endtime"])+"\n")
        sys.stderr.write("room_name: "+str(j["room_name"])+"\n")

        xml_template = open("resolvenames_template.xml", "r").read()
        xml = Template(xml_template)
        data = unicode(xml.substitute(name=str(j["room_name"])))
        header = "\"content-type: text/xml;charset=utf-8\""
        command = "curl --silent --header " + header +" --data '" + data + "' --ntlm "+ "-u "+ user+":"+password+" "+ url
        #print "command: "+str(command)
        response = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True).communicate()[0]
        #print "response: "+str(response)
        tree = ET.fromstring(response.encode('utf-8'))

        room_name=""
        room_email=""
        elems=tree.findall(".//{http://schemas.microsoft.com/exchange/services/2006/types}Resolution")
        for elem in elems:
            tmp = elem.findall(".//{http://schemas.microsoft.com/exchange/services/2006/types}EmailAddress")[0].text
            if tmp.startswith("CONF_"):
                room_email = tmp
                room_name = elem.findall(".//{http://schemas.microsoft.com/exchange/services/2006/types}DisplayName")[0].text

        sys.stderr.write("room_email: "+str(room_email)+"\n")
        if room_email=="":
            return "Sorry, "+str(j["room_name"])+" does not exists !"
        else:
            if is_available(room_email,str(j["starttime"]), str(j["endtime"])):
                book_room(str(j["room_name"]), room_email, str(j["user_name"]), str(j["user_email"]), str(j["starttime"]), str(j["endtime"]))
                return "Room "+str(j["room_name"])+" booked for "+str(j["user_name"]+" from "+str(j["starttime"])+" to "+str(j["endtime"]))
            else:
                return "Sorry, room "+str(j["room_name"])+" is busy !"
    else:
        return "Error should be a POST"
   
@app.route('/dispo', methods=['POST'])
def dispo():
    j = request.get_json()
    if "key" not in j:
        return "Sorry, no building where specified !"
    sys.stderr.write("key: "+str(j["key"])+"\n")
    key=str(j["key"])
    if "start" not in j:
        return dispo_building(key)
    start=str(j["start"])
    end=None
    if "end" in j:
        end=str(j["end"])
    return dispo_building(key,start,end)

@app.route('/where', methods=['POST'])
def where():
    j = request.get_json()
    if "room" not in j:
        return "Sorry, no room where specified !"
    room=str(j["room"])
    sys.stderr.write("room: "+room+"\n")
    rooms=findRooms(prefix=room,anywhere=True)
    sys.stderr.write("rooms: "+str(rooms)+"\n")
    # if len(rooms)==1:
    #     reply="Here is the full name of the room: \n * "+str(rooms.items()[0][1])
    # else:
    #     reply="Do you mean:\n"
    #     for r in rooms:
    #         reply+="* "+str(rooms[r])+"\n"
    reply=""
    if len(rooms)==0:
        return "Sorry, no room with this name found !"
    for r in rooms:
        reply+=str(rooms[r])+";"
    return reply[0:len(reply)-1]

def findRooms(prefix=None,anywhere=False):
    global rooms

    rooms={}
    xml_template = open("resolvenames_template.xml", "r").read()
    xml = Template(xml_template)

    data = unicode(xml.substitute(name=prefix))

    header = "\"content-type: text/xml;charset=utf-8\""
    #command = "curl --silent --header " + header +" --data '" + data + "' --ntlm "+"--negotiate "+ "-u "+ user+":"+password+" "+ url
    command = "curl --silent --header " + header +" --data '" + data + "' --ntlm "+ "-u "+ user+":"+password+" "+ url
    #print "command: "+str(command)
    response = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True).communicate()[0]
    #print "response: "+str(response)
    tree = ET.fromstring(response.encode('utf-8'))

    elems=tree.findall(".//{http://schemas.microsoft.com/exchange/services/2006/types}Resolution")
    for elem in elems:
        email = elem.findall(".//{http://schemas.microsoft.com/exchange/services/2006/types}EmailAddress")
        name = elem.findall(".//{http://schemas.microsoft.com/exchange/services/2006/types}DisplayName")
        if prefix is not None:
            if len(email) > 0 and len(name) > 0 :
                if email[0].text.startswith("conf_") or email[0].text.startswith("CONF_"):
                    if name[0].text.startswith(prefix) or anywhere:
                        rooms[email[0].text] = name[0].text
    return rooms        


def dispo_building(b,start=None, end=None):
    global result
    global q
    result=list()
    now = datetime.datetime.now().replace(microsecond=0)
    if start is None:
        start = now
    if end is None:
        end = (start + datetime.timedelta(hours=2))

    findRooms(b)
    sys.stderr.write("List of rooms: "+str(rooms)+"\n")

    xml_template = open("getavailibility_template.xml", "r").read()
    xml = Template(xml_template)

    q = Queue(len(rooms) * 2 + 2)
    try:
        for room in rooms:
            t = Thread(target=doWork)
            t.daemon = True
            t.start()
            sys.stderr.write(str(datetime.datetime.now().isoformat())+": End of init of Thread start\n")
            data=unicode(xml.substitute(email=room,starttime=start.isoformat(),endtime=end.isoformat())).strip()
            q.put(data)
        sys.stderr.write(str(datetime.datetime.now().isoformat())+": End of send data to process to Thread\n")
        q.join()
        sys.stderr.write(str(datetime.datetime.now().isoformat())+": End of join Thread\n")
    except KeyboardInterrupt:
        sys.exit(1)

    sys.stderr.write(str(datetime.datetime.now().isoformat())+": Response of Post to data server: "+str(result)+"\n")
    toto=(("List of rooms status","for "+str(b)+" building","from " + str(start),"to " + str(end)),sorted(result, key=lambda tup: tup[1]))
    return json.dumps(toto)
   
def book_room(room_name, room_email, user_name, user_email, start_time, end_time):
    xml_template = open("book_room.xml", "r").read()
    xml = Template(xml_template)
    data = unicode(xml.substitute(starttime=start_time,endtime=end_time,user=user_name,user_email=user_email,room=room_name,room_email=room_email))
    header = "\"content-type: text/xml;charset=utf-8\""
    command = "curl --silent --header " + header +" --data '" + data + "' --ntlm "+ "-u "+ user+":"+password+" "+ url
    response = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True).communicate()[0]
    return str(response)   

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser("Room Finder Book Room Service")
    parser.add_argument("-url","--url", help="url for exchange server, e.g. 'https://mail.domain.com/ews/exchange.asmx'.")
    parser.add_argument("-d","--data", help="url for data server, e.g. 'http://data.domain.com:5000'.")
    parser.add_argument("-u","--user", help="user for exchange server, e.g. 'toto@toto.com'.")
    parser.add_argument("-p","--password", help="password for exchange server.")
    args = parser.parse_args()

    url = args.url

    if (url == None):
        url = os.getenv("roomfinder_exchange_server")
        # print "Exchange URL: " + str(url)
        if (url == None):
            get_exchange_server = raw_input("What is the Exchange server URL? ")
            # print "Input URL: " + str(get_exchange_server)
            url = get_exchange_server

    # sys.stderr.write("Exchange URL: " + url + "\n")

    data = args.data

    if (data == None):
        data = os.getenv("roomfinder_data_server")
        # print "Exchange URL: " + str(url)
        if (data == None):
            get_data_server = raw_input("What is the Data server URL? ")
            # print "Input URL: " + str(get_exchange_server)
            data = get_data_server

    # sys.stderr.write("Data server URL: " + data + "\n")

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

    q = None
    result=list()
    rooms={}
    try:
    	app.run(debug=True, host='0.0.0.0', port=int("5000"))
    except:
    	try:
    		app.run(debug=True, host='0.0.0.0', port=int("5000"))
    	except:
    		print "Web server error"
