#!/usr/bin/env python2.7

from flask import Flask, request
import json
import sys, os

app = Flask(__name__)

def book_room(room_name, room_email, user_name, user_email, start_time, end_time):
    xml_template = open("book_room.xml", "r").read()
    xml = Template(xml_template)
    data = unicode(xml.substitute(starttime=start_time,endtime=end_time,user=user_name,user_email=user_email,room=room_name,room_email=room_email))
    header = "\"content-type: text/xml;charset=utf-8\""
    command = "curl --silent --header " + header +" --data '" + data + "' --ntlm "+ "-u "+ user+":"+password+" "+ url
    response = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True).communicate()[0]
    return str(response)

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

        file = open(FILE, 'r')
        room_email=""
        x = json.load(file)
        for i in x[1]:
            if i[1].find(str(j["room_name"]))>-1:
                room_email=i[2]
        sys.stderr.write("room_email: "+str(room_email)+"\n")
        if room_email=="":
            return "Sorry "+str(j["room_name"])+" is not available"
        else:
            book_room(str(j["room_name"]), room_email, str(j["user_name"]), str(j["user_email"]), str(j["starttime"]), str(j["endtime"]))
            return "Room "+str(j["room_name"])+" booked for "+str(j["user_name"]+" from "+str(j["starttime"])+" to "+str(j["endtime"]))
    else:
        return "Error should be a POST"
   
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        room_name = request.form["room_name"]
        room_email = request.form["room_email"]

        now = datetime.datetime.now().replace(microsecond=0)
        start_time = now.isoformat()
        end_time = (now + datetime.timedelta(hours=2)).isoformat()
        book_room(room_name, room_email, "Roomfinder", "gmorini@cisco.com", start_time, end_time)
        return "Room "+str(room_name)+" booked from "+str(start_time)+" to "+str(end_time)
    else:
        return "Error should be a POST"
   

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser("Room Finder Book Room Service")
    parser.add_argument("-url","--url", help="url for exchange server, e.g. 'https://mail.domain.com/ews/exchange.asmx'.")
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

    try:
    	app.run(debug=True, host='0.0.0.0', port=int("5000"))
    except:
    	try:
    		app.run(debug=True, host='0.0.0.0', port=int("5000"))
    	except:
    		print "Web server error"
