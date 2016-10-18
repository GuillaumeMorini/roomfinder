#!/usr/bin/env python2.7

from flask import Flask, request
import json
import sys

FILE="available_rooms.json"

app = Flask(__name__,static_folder='static')

@app.route('/')
def index():
    file = open(FILE, 'r')
    return file.read()

@app.route('/post', methods=['GET', 'POST'])
def post():
    if request.method == 'POST':
        j = request.get_json()
        print "Type: "+str(type(j))
        print "j: "+str(j)
        with open(FILE, 'w') as outfile:
            outfile.write(str(j))
        return "OK updated"
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

        file = open(FILE, 'r')
        room_email=""
        x = json.load(file)
        for i in x[1]:
            if i[1].find("ILM-7-HUGO")>-1:
                room_email=i[2]
        sys.stderr.write("room_email: "+str(room_email)+"\n")
        if room_email=="":
            return "Sorry "+str(j["room_name"])+" is not available"
        else
            return "Room "+str(j["room_name"])+" booked for "+str(j["user_name"])
    else:
        return "Error should be a POST"
        
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int("5001"))

