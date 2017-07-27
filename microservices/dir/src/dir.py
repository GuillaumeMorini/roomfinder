#!/usr/bin/env python3

from flask import Flask, request, Response, jsonify
import os, json, requests, sys, re, base64
import urllib.parse

# Timeout for requests get and post
TIMEOUT=1

headers = {}
headers["Content-type"] = "application/json; charset=utf-8"

dir_server="https://collab-tme.cisco.com/ldap/?have=cn&want=cn,description,manager,telephonenumber,mobile,title,co,ciscoitbuilding,postofficebox&values="
dir_server_2="https://collab-tme.cisco.com/ldap/?have=description&want=cn,description,telephonenumber,mobile,title,co,ciscoitbuilding,postofficebox&values="
dir_detail_server="http://wwwin-tools.cisco.com/dir/reports/"
pic_server="http://wwwin.cisco.com/dir/photo/zoom/"


app = Flask(__name__)

def find_dir(cco):
    sys.stderr.write('cco: '+str(cco)+'\n')
    u = dir_server + urllib.parse.quote('*'+cco+'*')
    try:
        r=requests.get(u, timeout=TIMEOUT)
    except requests.exceptions.RequestException:
        sys.stderr.write('Timeout looking for exact CCO\n')
        return '{}'
    reply=r.json()
    if 'responseCode' not in reply :
        sys.stderr.write('no responseCode looking for exact CCO\n')
        return "{}"
    if  reply["responseCode"] != 0:
        sys.stderr.write("Exact CCO not found !\n")
        u = dir_server_2 + urllib.parse.quote('*'+cco+'*')
        try:
            r=requests.get(u, timeout=TIMEOUT)
        except requests.exceptions.RequestException:
            sys.stderr.write('Timeout looking for name\n')
            return "{}"
        reply=r.json()
        if 'responseCode' not in reply or reply["responseCode"] != 0:
            sys.stderr.write('no responseCode looking for name\n')
            return "{}"
    if "results" not in reply :
        sys.stderr.write('no results\n')
        return "{}"
    l=reply["results"]
    sys.stderr.write(str(l)+"\n")
    if cco not in l:
        if len(l) > 1:
            sys.stderr.write("List of CCO found !\n")
            sys.stderr.write("reply: "+str(l)+"\n")
            return json.dumps(l).replace("\'","\"")
        else:
            sys.stderr.write("One person found !\n")
            cco=list(l.keys())[0]
    sys.stderr.write("cco2: "+str(cco)+"\n")
    # Add picture URL from picture server
    reply["results"][cco]["pic"]=pic_server+cco+".jpg"
    # Add Link to directory
    reply["results"][cco]["link"]=dir_detail_server+cco
    # Add manager name
    manager_cco=reply["results"][cco]["manager"].split(',')[0].split('=')[1]
    u = dir_server + manager_cco
    try:
        r=requests.get(u, timeout=TIMEOUT)
    except requests.exceptions.RequestException:
        sys.stderr.write('Timeout looking for manager name\n')
        return "{}"
    reply2=r.json()
    if 'responseCode' not in reply2 or reply2["responseCode"] != 0 or "results" not in reply2 :
        sys.stderr.write('no responseCode or results looking for manager name\n')
        return "{}"
    sys.stderr.write(str(reply2["results"])+"\n")
    reply["results"][cco]["manager_name"]=reply2["results"][manager_cco]["description"]+" ("+manager_cco+")"
    # Add building
    location=reply["results"][cco]["postofficebox"]
    if location is None:
            reply["results"][cco]["building"]="None"
    else:    
        end = location.find('/')
        if end > 0 :
            reply["results"][cco]["building"]=location[0:end]
        else:
            reply["results"][cco]["building"]="None"
    sys.stderr.write("reply: "+str(reply["results"])+"\n")
    return json.dumps(reply["results"]).replace("\'","\"")

@app.route('/dir', methods=["POST"])
def dir():
    post_data = request.get_json()
    reply=find_dir(post_data["cco"])
    return reply

if __name__ == '__main__':
    # Launch Flask web server
    app.run(debug=True, host='0.0.0.0', port=int("80"))
