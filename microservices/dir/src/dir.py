#!/usr/bin/env python2.7

from flask import Flask, request, Response
import os, json, requests, sys

headers = {}
headers["Content-type"] = "application/json; charset=utf-8"

app = Flask(__name__)
URL="http://router.cisco.com/"

@app.route('/dir', methods=["POST"])
def dir():
    post_data = request.get_json()
    #sys.stderr.write('Message: '+str(post_data)+'\n')
    reply={}
    reply[u'cmd']=u"dir"
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
