#!/usr/bin/env python2.7

from flask import Flask, request, Response
import os, json, requests, sys

headers = {}
headers["Content-type"] = "application/json; charset=utf-8"

app = Flask(__name__)

@app.route('/parking', methods=["GET"])
def parking():
    page = requests.get(PARKING_URL)
    result = page.json()
    return result
    
if __name__ == '__main__':
    # Get Parking URL from environment
    PARKING_URL = os.getenv("PARKING_URL")
    if (PARKING_URL == None):
        PARKING_URL = "http://173.38.154.145/parking/getcounter.py"
    # Launch Flask web server
    app.run(debug=True, host='0.0.0.0', port=int("5000"))
