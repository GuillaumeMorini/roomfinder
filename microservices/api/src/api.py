#!/usr/bin/env python2.7

from flask import Flask, request, Response, abort
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

headers = {}
headers["Content-type"] = "application/json; charset=utf-8"

app = Flask(__name__)

@app.route('/<cmd>', methods=["GET","POST"])
def api(cmd):
  sys.stderr.write('In api microservices !\n')
  if cmd in commands:
    URL='http://'+cmd+'/'+cmd
    post_data = request.get_json()
    sys.stderr.write('Message: '+str(post_data)+'\n')
    page = requests.post(URL, headers = headers, json=post_data)
    txt=page.text.replace("'",'"').replace('u"','"')
    sys.stderr.write('Reply: '+str(txt)+'\n')
    reply=json.loads(txt)
    sys.stderr.write('Reply JSON: '+str(reply)+'\n')
    return str(reply)
  else:
    abort(404)

if __name__ == '__main__':
    # Launch Flask web server
    app.run(debug=True, host='0.0.0.0', port=int("80"))
