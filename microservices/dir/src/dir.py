#!/usr/bin/env python3

from flask import Flask, request, Response
import os, json, requests, sys, re, base64
import urllib.parse


headers = {}
headers["Content-type"] = "application/json; charset=utf-8"

dir_server="https://collab-tme.cisco.com/ldap/?have=cn&want=cn,description,manager,telephonenumber,mobile,title,co,ciscoitbuilding&values="
dir_server_2="https://collab-tme.cisco.com/ldap/?have=description&want=cn,description,telephonenumber,mobile,title,co,ciscoitbuilding&values="
dir_detail_server="http://wwwin-tools.cisco.com/dir/reports/"
pic_server="http://wwwin.cisco.com/dir/photo/zoom/"


app = Flask(__name__)

def find_dir(cco):
    sys.stderr.write('cco: '+str(cco)+'\n')
    u = dir_server + urllib.parse.quote('*'+cco+'*')
    r=None
    try:
        r=requests.get(u)
        reply=r.json()
        if 'responseCode' in reply:
            if reply["responseCode"] != 0:
                u = dir_server_2 + urllib.parse.quote('*'+cco+'*')
                r=None
                try:
                    r=requests.get(u)
                except requests.exceptions.ConnectionError:
                    return "{}"
                reply=r.json()
                if 'responseCode' in reply:
                    if reply["responseCode"] != 0:
                        return "{}"
            l=reply["results"]
            print(l)
            if cco not in l:
                if len(l) > 1:
                    return str(l)
                else:
                    cco=list(l.keys())[0]
            print("cco: "+cco)
            reply["results"][cco]["pic"]=pic_server+cco+".jpg"
            reply["results"][cco]["link"]=dir_detail_server+cco
            manager_cco=reply["results"][cco]["manager"].split(',')[0].split('=')[1]
            u = dir_server + manager_cco
            r=requests.get(u)
            reply2=r.json()
            print(reply2["results"])
            reply["results"][cco]["manager_name"]=reply2["results"][manager_cco]["description"]
            return str(reply["results"][cco])
        else:
            return "{}"
    except requests.exceptions.ConnectionError:
        return "{}"

@app.route('/dir', methods=["POST"])
def dir():
    post_data = request.get_json()
    reply=find_dir(post_data["cco"])
    return reply

if __name__ == '__main__':
    # Launch Flask web server
    app.run(debug=True, host='0.0.0.0', port=int("80"))
