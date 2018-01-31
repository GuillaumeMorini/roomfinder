#!/usr/bin/env python2.7

import pika, os, sys, json, requests, datetime
import base64, urllib, unicodedata, re
import os, json, requests, sys, re, base64


try: 
    from BeautifulSoup import BeautifulSoup
    from HTMLParser import HTMLParser
except ImportError:
    from bs4 import BeautifulSoup
    from html.parser import HTMLParser

def guest(firstName,lastName,email):
    base_url="https://internet.cisco.com"
    uri1=":8443/sponsorportal/LoginCheck.action"
    uri2=":8443/sponsorportal/guest_accounts/AddGuestAccount.action"
    user=dir_user
    pwd=dir_pass

    s  = requests.Session()
    r=s.get(base_url)
    # print(r.text)

    parsed_html = BeautifulSoup(r.text)
    token=parsed_html.body.find('input', attrs={'id':'FORM_SECURITY_TOKEN'}).get("value")
    print "Token: "+str(token)
    # token="1b4be9f3-dd79-4232-b849-ac5b615b97df"

    try:
        response1 = s.post(
            url=base_url+uri1,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.1 Safari/603.1.30",
                "Referer": "https://internet.cisco.com:8443/sponsorportal/Logout.action",
                "Origin": "https://internet.cisco.com:8443",
                # "Cookie": "JSESSIONID=B640D7B33CCDFAE3E1FEF98048303FB9",
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
            data={
                "sponsorUser.loginUsername": user,
                "FORM_SECURITY_TOKEN": token,
                "L_T": "",
                "sponsorUser.password": pwd,
            },
        )

        date=datetime.datetime.now().strftime("%m/%d/%Y")
        startTime=datetime.datetime.now().strftime("T%I:%M:%S")

        try:
            response2 = s.post(
                url=base_url+uri2,
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.1 Safari/603.1.30",
                    "Referer": "https://internet.cisco.com:8443/sponsorportal/guest_accounts/GetAddAccountPage.action",
                    "Origin": "https://internet.cisco.com:8443",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                },
                data={
                    "guestUser.groupRole.id": "2f15d2c0-be86-11e1-ba69-0050568e002b",
                    "guestUser.endDate": date,
                    "guestUser.startTime": startTime,
                    "serverDate": date,
                    "serverTime": datetime.datetime.utcnow().strftime("%I:%M"),
                    "guestUser.endLimit": "7",
                    "guestUser.timezone": "GMT++02:00+Europe/Paris",
                    "FORM_SECURITY_TOKEN": token,
                    "guestUser.timeProfileDuration": "86400000",
                    "guestUser.notifyByEmail": "true",
                    "guestUser.endTime": startTime,
                    "guestUser.startLimit": "30",
                    "guestUser.timeProfile": "Valid_for_1_Day_after_initial_login",
                    "guestUser.languageNotification": "English",
                    "guestUser.firstName": firstName,
                    "guestUser.timeProfileType": "FromFirstLogin",
                    "guestUser.company": "Roomfinder",
                    "emailMandatory": "true",
                    "guestUser.startDate": date,
                    "guestUser.emailAddress": email,
                    "guestUser.lastName": lastName,
                    "nameToUse": "",
                },
            )
            return "Guest account created"

        except requests.exceptions.RequestException:
            print('HTTP Request failed')

    except requests.exceptions.RequestException:
        print('HTTP Request failed')

    return "Error during guest account creation"

def find_dir(cco):
    # Timeout for requests get and post
    TIMEOUT=1

    headers = {}
    headers["Content-type"] = "application/json; charset=utf-8"

    dir_server="https://collab-tme.cisco.com/ldap/?have=cn&want=cn,description,manager,telephonenumber,mobile,title,co,ciscoitbuilding,postofficebox&values="
    dir_server_2="https://collab-tme.cisco.com/ldap/?have=description&want=cn,description,manager,telephonenumber,mobile,title,co,ciscoitbuilding,postofficebox&values="
    dir_detail_server="http://wwwin-tools.cisco.com/dir/reports/"
    pic_server="http://wwwin.cisco.com/dir/photo/zoom/"

    index=cco
    cco=cco.encode('utf-8')
    sys.stderr.write('cco: '+str(cco)+'\n')
    u = dir_server + urllib.pathname2url('*'+cco+'*')
    try:
        r=requests.get(u, timeout=TIMEOUT)
    except requests.exceptions.RequestException as e:
        sys.stderr.write('Timeout looking for exact CCO. Exception: '+str(e)+'\n')
        return 'Timeout looking for exact CCO\n'
    reply=r.json()
    if 'responseCode' not in reply :
        sys.stderr.write('no responseCode looking for exact CCO\n')
        return 'no responseCode looking for exact CCO\n'
    if  reply["responseCode"] != 0:
        sys.stderr.write("Exact CCO not found !\n")
        u = dir_server_2 + urllib.pathname2url('*'+cco+'*')
        try:
            r=requests.get(u, timeout=TIMEOUT)
        except requests.exceptions.RequestException as e:
            sys.stderr.write('Timeout looking for name. Exception: '+str(e)+'\n')
            return 'Timeout looking for name\n'
        reply=r.json()
        if 'responseCode' not in reply or reply["responseCode"] != 0:
            if reply["responseCode"] == 2:
                sys.stderr.write('Nobody found with this name or CCO in the directory\n')
                return 'Nobody found with this name or CCO in the directory\n'
            else:
                sys.stderr.write('Connection error to the directory\n')
                return 'Connection error to the directory\n'                
        else:
            for r in reply["results"]:
                index=r
                reply["results"][r]["description"]=index
    else:
        sys.stderr.write("Exact CCO found !\n")
        for r in reply["results"]:
            reply["results"][r]["cn"]=r

    if "results" not in reply :
        sys.stderr.write('no results\n')
        return 'no results\n'
    l=reply["results"]
    sys.stderr.write(str(l)+"\n")
    if cco not in l:
        if len(l) > 1:
            sys.stderr.write("List of CCO found !\n")
            sys.stderr.write("reply: "+str(l)+"\n")
            txt="Are you looking for one of these people:"
            for e in l:
                cco=l[e]["cn"]
                name=l[e]["description"]
                txt+="\n * "+str(name.encode('utf-8'))+" ("+str(cco)+")"
            return txt
        else:
            sys.stderr.write("One person found !\n")
            index=list(l.keys())[0]
            cco=l[index]["cn"]
            #reply["results"][index]["description"]=index
    else:
        index=cco
    sys.stderr.write("cco2: "+str(cco)+"\n")
    sys.stderr.write("index: "+str(index.encode('utf-8'))+"\n")
    # Add picture URL from picture server
    reply["results"][index]["pic"]=pic_server+cco+".jpg"
    response = requests.get(reply["results"][index]["pic"], stream=True)
    encoded_string = base64.b64encode(response.raw.read())
    # Add Link to directory
    reply["results"][index]["link"]=dir_detail_server+cco
    # Add manager name
    if "manager" in reply["results"][index] and reply["results"][index]["manager"] is not None:
        sys.stderr.write("Manager found\n")
        manager_cco=reply["results"][index]["manager"].split(',')[0].split('=')[1]
        u = dir_server + manager_cco
        try:
            r=requests.get(u, timeout=TIMEOUT)
        except requests.exceptions.RequestException:
            sys.stderr.write('Timeout looking for manager name\n')
            return 'Timeout looking for manager name\n'
        reply2=r.json()
        if 'responseCode' not in reply2 or reply2["responseCode"] != 0 or "results" not in reply2 :
            sys.stderr.write('no responseCode or results looking for manager name\n')
            return 'no responseCode or results looking for manager name\n'
        sys.stderr.write("Manager: "+str(reply2["results"])+"\n")
        reply["results"][index]["manager_name"]=reply2["results"][manager_cco]["description"]+" ("+manager_cco+")"
    else:
        sys.stderr.write("Manager not found\n")
        # No manager
        pass
    # Add building
    location=reply["results"][index]["postofficebox"]
    if location is None:
        sys.stderr.write("Location not found\n")
        reply["results"][index]["building"]="None"
    else:    
        sys.stderr.write("Location found\n")
        end = location.find('/')
        if end > 0 :
            reply["results"][index]["building"]=location[0:end]
        else:
            reply["results"][index]["building"]="None"
    sys.stderr.write("reply: "+str(reply["results"])+"\n")

    text = ""
    if reply["results"][index]["description"] != None:
        text+=reply["results"][index]["description"]+"<br>;"
    else:
        text+=";"
    if reply["results"][index]["title"] != None:
        text+=reply["results"][index]["title"]+"<br>;"
    else:
        text+=";"
    if reply["results"][index]["manager"] != None and "manager_name" in reply["results"][index]:
        text+=reply["results"][index]["manager_name"]+"<br>;"
    else:
        text+=";"
    phone_text=""
    if reply["results"][index]["telephonenumber"] != None:
        phone_text+="<b>Work</b>: "+reply["results"][index]["telephonenumber"]+"<br>"
    if reply["results"][index]["mobile"] != None:
        phone_text+="<b>Mobile</b>: "+reply["results"][index]["mobile"]+"<br>"
    text+=phone_text+";"+encoded_string+";"+"<b>Internal directory</b>: <a href=\"http://wwwin-tools.cisco.com/dir/details/"+reply["results"][index]["cn"]+"\">link</a>"
    return text.encode('utf-8')

def building(name):
    name=name.upper()
    sys.stderr.write("Looking for building with name: "+name+"\n")
    url="http://wwwin.cisco.com/c/dam/cec/organizations/gbs/wpr/serverBuildingOnlineDetail.txt"
    try:
        s = requests.Session()
        r=s.get(url)
        #sys.stderr.write(str(r.text.encode('utf-8'))+"\n")
        headers={'Content-type': 'application/x-www-form-urlencoded'}
        data="userid="+dir_user+"&password="+dir_pass+"&target=&login-button=Log+In&login-button-login=Next&login-button-login=Log+in"
        response=s.post(sso_url,data,headers)
        if response.status_code==200:
            if response.text:
                buildings=json.loads(response.text)
                found=[]
                for theater,t in buildings.iteritems():
                    #print theater, ":", t["theaterName"]
                    for region in t["regions"]:
                        #print "\t",region["regionCode"], ":", region["regionName"]
                        for country in region["countries"]:
                            #print "\t\t",country["countryName"]
                            for state in country["states"]:
                                #print "\t\t\t",state["stateName"]
                                for city in state["cities"]:
                                    #print "\t\t\t\t",city["cityName"]
                                    for campus in city["campuses"]:
                                        #print "\t\t\t\t\t",campus["campusName"]
                                        for building in campus["buildings"]:
                                            import re
                                            if re.match('[a-zA-Z][a-zA-Z0-9]', building["buildingId"]):
                                                #print "\t\t\t\t\t\t",building["buildingId"],building["buildingName"]
                                                if (
                                                     country["countryName"].find(name) >= 0 or
                                                     state["stateName"].find(name) >= 0 or
                                                     city["cityName"].find(name) >= 0 or
                                                     campus["campusName"].find(name) >= 0 or
                                                     building["buildingId"].find(name) >= 0 or
                                                     building["buildingName"].find(name) >= 0
                                                   ) :
                                                        sys.stderr.write("Found "+name+" in one of "+country["countryName"]+" "+state["stateName"]+" "+city["cityName"]+" "+campus["campusName"]+" "+building["buildingName"]+"\n")
                                                        found.append({"id": building["buildingId"],"name": building["buildingName"]})
                if len(found)>15:
                    return "Sorry too much building ! Please refine your request !"
                elif len(found)==0:
                    return "Sorry not found !"
                else:
                    txt="Are you looking for one of these buildings:"
                    for e in found:
                        id=e["id"]
                        name=e["name"]
                        txt+="\n * "+str(id.encode('utf-8'))+" ("+str(name.encode('utf-8'))+")"
                return txt
        return "Connection error to building server"
    except Exception as e:
        return "Connection error to building server"


def map(floor):
    #http://wwwin.cisco.com/c/dam/cec/organizations/gbs/wpr/FloorPlans/ILM-AFP-5.pdf
    s=floor.split('-')
    if len(s)!=2:
        return "Not Found"
    else:
        #return "http://wwwin.cisco.com/c/dam/cec/organizations/gbs/wpr/FloorPlans/"+s[0].replace(' ','')+"-AFP-"+s[1]+".pdf"
        url="http://wwwin.cisco.com/c/dam/cec/organizations/gbs/wpr/FloorPlans/"+s[0].replace(' ','')+"-AFP-"+s[1]+".pdf"
        sys.stderr.write("Getting map on url: "+url+"\n")
        try:
            s = requests.Session()
            r=s.get(url)
            #sys.stderr.write(str(r.text.encode('utf-8'))+"\n")
            headers={'Content-type': 'application/x-www-form-urlencoded'}
            data="userid="+dir_user+"&password="+dir_pass+"&target=&login-button=Log+In&login-button-login=Next&login-button-login=Log+in"
            response=s.post(sso_url,data,headers, stream=True)
            if response.headers["Content-Type"] == "application/pdf":
                sys.stderr.write("Content is a pdf file\n")
                encoded_string = base64.b64encode(response.raw.read())
                sys.stderr.write("Encoded string:\n"+str(encoded_string)+"\n")

                return json.dumps({"text": "Here is the map !\n", "pdf":  encoded_string })
            else:
                return "Connection error to map server"
        except requests.exceptions.ConnectionError:
            return "Connection error to map server"

def on_request(ch, method, props, body):
    sys.stderr.write(" [x] Received %r\n" % body)
    #sys.stderr.write("Method: {}\n".format(method))     
    #sys.stderr.write("Properties: {}\n".format(properties))     
    data = json.loads(body)
    cmd=data['cmd']
    request_data=data["data"]
    sys.stderr.write("Command: {}\n".format(cmd))     
    sys.stderr.write("Data: {}\n".format(request_data))      

    if cmd == "book":
        sys.stderr.write("Request booking of a room to %s\n" % book_server)  
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    	page = requests.post(book_server+'/book',data = json.dumps(request_data),headers=headers)
        txt=page.text
        sys.stderr.write("txt: {}\n".format(txt.encode('utf-8')))
    elif cmd == "dir":
        cco= request_data["cco"]
        sys.stderr.write("Request directory entry in %s for %s\n" % (str(dir_server.encode('utf-8')), str(cco.encode('utf-8'))))  
        print "dir_server: "+dir_server
        txt=find_dir(cco).decode('utf-8')
        sys.stderr.write("txt: {}\n".format(txt.encode('utf-8')))
    elif cmd == "map":
        floor = request_data["floor"]
        sys.stderr.write("Request map for %s\n" % str(floor.encode('utf-8')) )  
        txt=map(floor).encode('utf-8')
        #sys.stderr.write("txt: {}\n".format(txt))
    elif cmd == "building":
        b = request_data["building"]
        sys.stderr.write("Request building lookup for %s\n" % str(b.encode('utf-8')) )  
        txt=building(b) #.encode('utf-8')
        sys.stderr.write("txt: {}\n".format(txt))
    elif cmd == "sr":
        pass
    elif cmd == "dispo":
        sys.stderr.write("Request dispo of a room to %s\n" % book_server)  
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        page = requests.post(book_server+'/dispo',data = json.dumps(request_data),headers=headers)
        txt=page.text.encode('utf-8')
        sys.stderr.write("txt: {}\n".format(txt))
    elif cmd == "where":
        sys.stderr.write("Request where is a room to %s\n" % book_server)  
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        page = requests.post(book_server+'/where',data = json.dumps(request_data),headers=headers)
        txt=page.text.encode('utf-8')
        sys.stderr.write("txt: {}\n".format(txt))
    elif cmd == "guest":
        sys.stderr.write("Request for a guest account creation\n")  
        firstName= request_data["firstName"]
        lastName= request_data["lastName"]
        email= request_data["email"]
        sys.stderr.write("Request guest account for %s %s <%s>\n" % (firstName.encode('utf-8'), lastName.encode('utf-8'), email.encode('utf-8')) )  
        txt=guest(firstName,lastName,email).encode('utf-8')
        sys.stderr.write("txt: {}\n".format(txt))

    ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(correlation_id = \
                                                         props.correlation_id),
                     body=txt)
    ch.basic_ack(delivery_tag = method.delivery_tag)
    return txt

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser("Room Finder Router Service")
    parser.add_argument("-r","--rabbitmq", help="IP or hostname for rabbitmq server, e.g. 'rabbit.domain.com'.")
    parser.add_argument("-p","--port", help="tcp port for rabitmq server, e.g. '2765'.")
    parser.add_argument("-b","--book", help="URL for roomfinder book server, e.g. 'http://book.domain.com:1234'.")
    parser.add_argument("-d", "--dir", help="Address of directory server", required=False)
    parser.add_argument("-e", "--dir-detail", help="Address of detailed directory server", required=False)
    parser.add_argument(
        "-i", "--photo", help="Address of photo directory server", required=False
    )
    parser.add_argument("-u","--user", help="URL for user of directory server.")
    parser.add_argument("-k","--password", help="URL for password of directory server.")
    parser.add_argument("-s","--sso", help="URL for SSO.")
#    parser.add_argument("-p","--password", help="password for exchange server.")
    args = parser.parse_args()

    rabbitmq = args.rabbitmq
    if (rabbitmq == None):
        rabbitmq = os.getenv("roomfinder_rabbitmq_server")
        if (rabbitmq == None):
            get_rabbitmq_server = raw_input("What is the rabbitmq server IP or hostname? ")
            rabbitmq = get_rabbitmq_server

    rabbitmq_port = args.port
    if (rabbitmq_port == None):
        rabbitmq_port = os.getenv("roomfinder_rabbitmq_port")
        if (rabbitmq_port == None):
            get_rabbitmq_port = raw_input("What is the rabbitmq TCP port? ")
            rabbitmq_port = get_rabbitmq_port

    book_server = args.book
    if (book_server == None):
        book_server = os.getenv("roomfinder_book_server")
        if (book_server == None):
            get_book_server = raw_input("What is the book server URL? ")
            book_server = get_book_server

    dir_server = args.dir
    # print "Arg Dir: " + str(dir_server)
    if (dir_server == None):
        dir_server = os.getenv("roomfinder_dir_server")
        # print "Env Dir: " + str(dir_server)
    # print "Dir Server: " + dir_server
    sys.stderr.write("Directory Server: " + str(dir_server) + "\n")


    dir_detail_server = args.dir_detail
    if (dir_detail_server == None):
        dir_detail_server = os.getenv("roomfinder_dir_detail_server")

    dir_user = args.user
    if (dir_user == None):
        dir_user = os.getenv("roomfinder_dir_user")
    sys.stderr.write("Directory User: " + str(dir_user) + "\n")

    dir_pass = args.password
    if (dir_pass == None):
        dir_pass = os.getenv("roomfinder_dir_pass")
    sys.stderr.write("Directory Password " + str(dir_pass) + "\n")

    sso_url = args.sso
    if (sso_url == None):
        sso_url = os.getenv("roomfinder_sso_url")
    sys.stderr.write("SSO URL: " + str(sso_url) + "\n")

    sys.stderr.write("Connecting to "+rabbitmq+" on port "+rabbitmq_port+"\n")
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host="localhost", port=5672 ))
    channel = connection.channel()
    channel.queue_declare(queue='rpc_queue')
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(on_request, queue='rpc_queue')
    sys.stderr.write(' [*] Waiting for messages. To exit press CTRL+C\n')
    channel.start_consuming()

