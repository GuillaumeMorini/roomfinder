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
     
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int("5001"))

