#!/usr/bin/env python2.7

from flask import Flask, request, Response
import os, json, requests, sys

commands=[
  "advertise",
  "stats",
  "help",
  "add",
  "available",
  "book",
  "plan",
  "inside",
  "find",
  "dir",
  "parking"
]
# Overwrite commands to only handle available as function name of Flask route should be unique
# Need to find a way to parameter it linked to variable name
commands=["available"]

headers = {}
headers["Content-type"] = "application/json; charset=utf-8"

app = Flask(__name__)

for cmd in commands:
    @app.route('/'+cmd, methods=["GET","POST"])
# Need to replace toto by cmd variable value
    def toto():
        URL=cmd+".cisco.com"
        post_data = request.get_json()
        sys.stderr.write('Message: '+str(post_data)+'\n')
        reply={}
        reply[u'cmd']=cmd
        reply[u'data']=post_data
        page = requests.post(URL, headers = headers, json=reply)
        txt=page.text.replace("'",'"').replace('u"','"')
        sys.stderr.write('Reply: '+str(txt)+'\n')
        reply=json.loads(txt)
        sys.stderr.write('Reply JSON: '+str(reply)+'\n')
        return str(reply)

if __name__ == '__main__':
    # Launch Flask web server
    app.run(debug=True, host='0.0.0.0', port=int("5000"))
