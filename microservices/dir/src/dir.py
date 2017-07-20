#!/usr/bin/env python3

from flask import Flask, request, Response
import os, json, requests, sys

headers = {}
headers["Content-type"] = "application/json; charset=utf-8"

app = Flask(__name__)

def find_dir(cco):
    f = { 'q' : cco.encode('utf-8') }
    u = dir_server + urllib.urlencode(f)
    r = None
    try:
        s = requests.Session()
        r=s.get(u)
        print(str(r.text.encode('utf-8')))
        headers={'Content-type': 'application/x-www-form-urlencoded'}
        data="userid="+dir_user+"&password="+dir_pass+"&target=&smauthreason=&smquerydata=&smagentname=&postpreservationdata=&SMENC=&SMLOCALE="
        r=s.post(sso_url,data,headers)
    except requests.exceptions.ConnectionError:
        return "Connection error to directory server"
    html = HTMLParser().unescape(r.text)
    #sys.stderr.write("html: "+str(html.encode('utf-8'))+"\n")
    parsed_html = BeautifulSoup(html)
    table=parsed_html.body.find('table', attrs={'id':'resultsTable'})
    if table is not None:
        result_list=[unicodedata.normalize('NFKD',i.text) for i in table.findAll('a',attrs={'class':'hover-link'})]
        found=False
        for n in result_list:
            m = re.search(r"\(([A-Za-z0-9]+)\)", n)
            if m.group(1) == cco:
                u=dir_detail_server+cco
                r=s.get(u)
                print(r.text)
                html = HTMLParser().unescape(r.text)
                sys.stderr.write("html: "+str(html.encode('utf-8'))+"\n")
                parsed_html = BeautifulSoup(html)
                found=True
                print("Found!")
        if not found:
            txt="Are you looking for one of these people:"
            for i in result_list:
                txt+="\n * "+str(i.encode("utf-8"))
            return txt
    name=parsed_html.body.find('h2', attrs={'class':'userName'})
    sys.stderr.write("name: "+str(name)+"\n")
    if not hasattr(name, 'text'):
        return "CCO id not found !"
    else:
        tmp=parsed_html.body.find('p', attrs={'class':'userId'})
        print("tmp: "+str(tmp))
        m=re.search(r"\(([A-Za-z0-9]+)\)", str(tmp))
        print("m: "+str(m))
        real_cco=str(m.group(1))
        sys.stderr.write("real_cco: "+str(real_cco)+"\n")
        title=parsed_html.body.find('p', attrs={'class':'des'})
        sys.stderr.write("title: "+str(title)+"\n")
        manager=parsed_html.body.find('a', attrs={'class':'hover-link'})
        sys.stderr.write("manager: "+str(manager)+"\n")
        phone_text=""
        phone=parsed_html.body.find('div', attrs={'id':'dir_phone_links'})
        if phone is not None:
            for p in phone.findAll('p'):
                if p.text.find("Work") > -1 or p.text.find("Mobile") > -1 :
                    phone_text+=str(p.text)+"<br>"
        u = str(parsed_html.body.find('div',attrs={'class':'profImg'}).find('img')['src'])
        response = requests.get(u, stream=True)
        encoded_string = base64.b64encode(response.raw.read())

        reply = ""
        if name != None:
            reply+=name.text+"<br>;"
        else:
            reply+=";"
        if title != None:
            reply+=title.text.replace('.',' ')+"<br>;"
        else:
            reply+=";"
        if manager != None:
            reply+=manager.text+"<br>;"
        else:
            reply+=";"
        reply+=phone_text+";"+encoded_string+";"+"<a href=\"http://wwwin-tools.cisco.com/dir/details/"+real_cco+"\">directory link</a>"
        return reply


@app.route('/dir', methods=["POST"])
def dir():
    post_data = request.get_json()
    #sys.stderr.write('Message: '+str(post_data)+'\n')
    reply=find_dir(post_data)
    return reply

if __name__ == '__main__':
    # Launch Flask web server
    app.run(debug=True, host='0.0.0.0', port=int("5000"))
