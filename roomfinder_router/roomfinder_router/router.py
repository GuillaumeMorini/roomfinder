#!/usr/bin/env python2.7

import pika, os, sys, json, requests, datetime
import base64, urllib, unicodedata, re

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

def map(floor):
    #http://wwwin.cisco.com/c/dam/cec/organizations/gbs/wpr/FloorPlans/ILM-AFP-5.pdf
    s=floor.split('-')
    if len(s)!=2:
        return "Not Found"
    else:
        return "http://wwwin.cisco.com/c/dam/cec/organizations/gbs/wpr/FloorPlans/"+s[0].replace(' ','')+"-AFP-"+s[1]+".pdf"

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
        sys.stderr.write("txt: {}\n".format(txt))    
    elif cmd == "dir":
        cco= request_data["cco"]
        sys.stderr.write("Request directory entry in %s for %s\n" % (str(dir_server.encode('utf-8')), str(cco.encode('utf-8'))))  
        print "dir_server: "+dir_server
        txt=find_dir(cco)
        sys.stderr.write("txt: {}\n".format(txt))
    elif cmd == "map":
        floor = request_data["floor"]
        sys.stderr.write("Request map for %s\n" % str(floor.encode('utf-8')) )  
        txt=map(floor)
        sys.stderr.write("txt: {}\n".format(txt))
    elif cmd == "sr":
        pass
    elif cmd == "dispo":
        sys.stderr.write("Request dispo of a room to %s\n" % book_server)  
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        page = requests.post(book_server+'/dispo',data = json.dumps(request_data),headers=headers)
        txt=page.text
        sys.stderr.write("txt: {}\n".format(txt))
    elif cmd == "where":
        sys.stderr.write("Request where is a room to %s\n" % book_server)  
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        page = requests.post(book_server+'/where',data = json.dumps(request_data),headers=headers)
        txt=page.text
        sys.stderr.write("txt: {}\n".format(txt))
    elif cmd == "guest":
        sys.stderr.write("Request for a guest account creation\n")  
        firstName= request_data["firstName"]
        lastName= request_data["lastName"]
        email= request_data["email"]
        sys.stderr.write("Request guest account for %s %s <%s>\n" % (firstName.encode('utf-8'), lastName.encode('utf-8'), email.encode('utf-8')) )  
        txt=guest(firstName,lastName,email)
        sys.stderr.write("txt: {}\n".format(txt))

    ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(correlation_id = \
                                                         props.correlation_id),
                     body=str(txt))
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
        host="localhost" ))
    channel = connection.channel()
    channel.queue_declare(queue='rpc_queue')
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(on_request, queue='rpc_queue')
    sys.stderr.write(' [*] Waiting for messages. To exit press CTRL+C\n')
    channel.start_consuming()

