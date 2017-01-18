#! /usr/bin/python
'''
    Spark Bot for Room Finder Application

    This Bot will use a provided Spark Account (identified by the Developer Token)
    and create a new room to use for interacting with the Roomfinder application.  Users can
    check current available rooms. 

    This is the an example Service for a basic microservice demo application.
    The application was designed to provide a simple demo for Cisco Mantl

    There are several pieces of information needed to run this application.  It is
    suggested to set them as OS Environment Variables.  Here is an example on how to
    set them:

    # Address and key for app server
    export roomfinder_data_server=http://ip_or_name:5001
    # Details on the Cisco Spark Account to Use
    export roomfinder_spark_bot_email=toto@domain.com

    Find Cisco Spark developer token on http://developer.ciscospark.com
    export spark_token=...

    # Address and key for the Spark Bot itself
    export roomfinder_spark_bot_url=http://public_ip_or_name:5000
'''

__author__ = 'gmorini'


# ToDo - Method to monitor incoming 1 on 1 messages

from flask import Flask, request, Response
import requests, json, re, urllib, random
import xml.etree.ElementTree as ET
import ntpath
import datetime
from requests_toolbelt.multipart.encoder import MultipartEncoder
import pika  
import uuid

app = Flask(__name__)

ROOM_TITLE="Roomfinder"
spark_host = "https://api.ciscospark.com/"
spark_headers = {}
spark_headers["Content-type"] = "application/json"
app_headers = {}
app_headers["Content-type"] = "application/json"
google_headers = {}
google_headers["User-Agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.112 Safari/534.30"

@app.route('/', methods=["POST"])
def process_webhook():
    # Verify that the request is propery authorized
    # authz = valid_request_check(request)
    # if not authz[0]:
    #     return authz[1]

    post_data = request.get_json(force=True)
    # pprint(post_data)

    # Check what room this came from
    # If Demo Room process for open room
    if post_data["data"]["roomId"] == demo_room_id:
        # print("Incoming Demo Room Message.")
        process_demoroom_message(post_data)
    # If not the demo room, assume its a user individual message
    else:
        # print("Incoming Individual Message.")
        sys.stderr.write("Incoming Individual Message\n")

    return ""

@app.route("/demoroom/members", methods=["POST", "GET"])
def process_demoroom_members():
    # Verify that the request is propery authorized
    #authz = valid_request_check(request)
    #if not authz[0]:
    #    return authz[1]

    status = 200
    if request.method == "POST":
        data = request.form
        try:
            sys.stderr.write("Adding %s to demo room.\n" % (data["email"]))
            add_email_demo_room(data["email"], demo_room_id)
            status = 201
        except KeyError:
            error = {"Error":"API Expects dictionary object with single element and key of 'email'"}
            status = 400
            resp = Response(json.dumps(error), content_type='application/json', status=status)
            return resp

    demo_room_members = get_membership_for_room(demo_room_id)
    resp = Response(
        json.dumps(demo_room_members, sort_keys=True, indent = 4, separators = (',', ': ')),
        content_type='application/json',
        status=status)

    return resp


# Bot functions to process the incoming messages posted by Cisco Spark
def process_demoroom_message(post_data):
    sys.stderr.write("Beginning of process_demoroom_message\n")
    sys.stderr.write("post_data="+str(post_data)+"\n")
    message_type="text"
    message_id = post_data["data"]["id"]
    message = get_message(message_id)
    #print(message)

    # First make sure not processing a message from the bot
    if message["personEmail"] == bot_email:
        return ""

    # If someone is mentioned, do not answer
    if 'mentionedPeople' in message:
        return ""

    sys.stderr.write("message="+str(message)+"\n")

    text=message["text"].encode("utf-8")
    sys.stderr.write("Incoming Room Message\tmessage: "+text+"\t")

    # Check if message contains word "dispo" and if so send results
    if text.lower().find("dispo") > -1 or text.lower().find("available") > -1:
        buildings = re.findall(r' [a-zA-Z][a-zA-Z0-9\-]+', text)
        sys.stderr.write('Building founds: '+str(len(buildings))+"\n")
        for b in buildings:
            sys.stderr.write(' - '+str(b)+"\n")
        if len(buildings) > 0 :
            building=buildings[0][1:]
            u = dispo_server + "/dispo?key="+str(building)
            page = requests.get(u, headers = app_headers)
            tally = page.json()
            sys.stderr.write("Tally: "+str(tally)+"\n")
            #tally = sorted(tally.items(), key = lambda (k,v): v, reverse=True)
            results=(i[1] for i in tally[1] if i[0]=="Free")
            start = " in building "+str(building)+" "+tally[0][2]
            end = tally[0][3]

        else:
            start, end, results = get_available()
        number = re.findall(r' [0-9]+', text)
        print "number: "+str(number)
        toto=list(results)
        sys.stderr.write("result: "+str(toto)+"\n")

        # Test if there is a criteria on the number of seats
        if number:
            if len(number) == 1:
                inf = int(number[0])
                filtered_results=[result for result in toto if int(result.split('(')[1].split(')')[0])>=inf]
                sys.stderr.write("filtered_results: "+str(filtered_results)+"\n")
                reply = ", with more than "+str(inf)+" seats, "+start+" "+end
            else:
                inf = int(number[0])
                sup = int(number[1])
                filtered_results=[result for result in toto if int(result.split('(')[1].split(')')[0])>=inf and int(result.split('(')[1].split(')')[0])<=sup]
                sys.stderr.write("filtered_results: "+str(filtered_results)+"\n")
                reply = ", with more than "+str(inf)+" and less than "+str(sup)+" seats, "+start+" "+end
        else:
            reply = " "+start+" "+end
            filtered_results=toto


        titi=list(filtered_results)
        # Test if filtered result list is empty or not
        if titi:
            reply = "The current available rooms"+reply+" are:\n"
            for result in titi:
                reply += "  - %s\n" % (result)
                #sys.stderr.write("Salle: "+result+"\n")
        else:
            reply = "Sorry, there is currently no available rooms"+reply+"\n"
    # Check if message contains word "options" and if so send options
    elif text.lower().find("options") > -1 or text.lower().find("help") > -1 or text.lower().find("aide") > -1:
        #options = get_options()
        reply = "The options are limited right now ! This is a beta release ! \n"
        reply += "  - any sentence with \"dispo\" or \"available\" keyword will display the current available rooms for the next 2 hours timeslot.\n"
        reply += "  - any sentence with \"reserve\" or \"book\" keyword will try to book the room mentionned after the keyword \"book\" or \"reserve\".\n"
        reply += "  - any sentence with \"plan\" or \"map\" keyword will display the map of the floor mentionned after the keyword \"plan\" or \"map\".\n"
        reply += "  - any sentence with \"dir\" keyword will display the directory entry for the CCO id mentionned after the keyword \"dir\".\n"
        reply += "  - any sentence with \"options\" keyword will display this.\n"
        reply += "  - any sentence with \"add email\" followed by an email will add this email to the Spark room.\n"
        reply += "  - any sentence with \"help\" or \"aide\" will display a helping message to the Spark room.\n"
        reply += "  - any other sentences will display some fun messages to the Spark room.\n"
        #for option in options:
            #reply += "  - %s \n" % (option)
    # Check if message contains phrase "add email" and if so add user to room
    elif text.lower().find("add email") > -1:
        # Get the email that comes
        emails = re.findall(r'[\w\.-]+@[\w\.-]+', text)
        # pprint(emails)
        reply = "Adding users to demo room.\n"
        for email in emails:
            add_email_demo_room(email, demo_room_id)
            reply += "  - %s \n" % (email)
    # Check if message contains phrase "help" and display generic help message
    elif text.lower().find("dir") > -1:
        # Find the cco id
        cco_list = re.findall(r'[\w ]+', text)
        print "cco_list= "+str(cco_list)
        cco_list.reverse()
        cco=cco_list.pop()
        while cco.find("dir") > -1:
            cco=cco_list.pop()
        reply = find_dir(cco)
        print "find_dir: "+str(reply)
        if type(reply) != str and type(reply) != unicode:
            message_type="localfine"
    elif text.lower().find("image") > -1:
        # Find the cco id
        keyword_list = re.findall(r'[\w-]+', text)
        print "keyword_list= "+str(keyword_list)
        keyword_list.reverse()
        keyword=keyword_list.pop()
        while keyword.find("image") > -1:
            keyword=keyword_list.pop()
        reply = find_image(keyword)
        print "find_image: "+reply
        if reply.startswith('http'):
            message_type="image"
    elif text.lower().find("plan") > -1 or text.lower().find("map") > -1 :
        # Find the floor
        keyword_list = re.findall(r'ILM-[1-7]', text) + re.findall(r'[1-7]', text)
        print "keyword_list= "+str(keyword_list)
        keyword_list.reverse()
        floor=keyword_list.pop()
        reply = display_map(floor)
        print "display_map: "+floor
        message_type="image"
    elif text.lower().find("book") > -1 or text.lower().find("reserve") > -1 :
        # Find the room name
        keyword_list = re.findall(r'[\w-]+', text)
        sys.stderr.write("keyword_list= "+str(keyword_list)+"\n")
        keyword_list.reverse()
        keyword=keyword_list.pop()
        while keyword.lower().find("book") > -1 or keyword.lower().find("reserve") > -1:
            keyword=keyword_list.pop()
        reply = book_room(keyword.upper(),message["personEmail"].lower(),getDisplayName(message["personId"]))
        sys.stderr.write("book_room: "+reply+"\n")
    # If nothing matches, send instructions
    else:
        reply=natural_langage_bot(text.lower())
        if reply == "":
            return reply
    sys.stderr.write("reply: "+str(reply)+"\n")
    send_message_to_room(demo_room_id, reply,message_type)

def getDisplayName(id):
    spark_u = spark_host + "v1/people/"+id
    page = requests.get(spark_u, headers = spark_headers)
    displayName = page.json()["displayName"]
    return displayName

def on_response(ch, method, props, body):
    global corr_id
    global response
    if corr_id == props.correlation_id:
        response = body

def send_message_to_queue(message):
    global corr_id
    global response
    global connection
    global channel
    global callback_queue

    response=None
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="37.187.22.103",port=2765,heartbeat_interval=30))  
    channel = connection.channel()
    result=channel.queue_declare(exclusive=True)
    callback_queue = result.method.queue
    channel.basic_consume(on_response, no_ack=True,
                                   queue=callback_queue)
    corr_id=str(uuid.uuid4())

    response = None
    corr_id =  str(uuid.uuid4())
    channel.basic_publish(  exchange='',
                            routing_key="rpc_queue",
                            properties=pika.BasicProperties(
                                         reply_to = callback_queue,
                                         correlation_id = corr_id),
                            body=message)

    print(" [x] Sent data to RabbitMQ")   

    while response is None:
        connection.process_data_events()
    print(" [x] Get response from RabbitMQ")   
    return str(response)    

def book_room(room_name,user_email,user_name):
    sys.stderr.write("Beginning process to book a room and especially this room: "+room_name+"\n")

    start, end, results = get_available()
    dispo_list=[r.split(' ')[0] for r in results]
    if room_name in dispo_list:
        print "Room booked is available"

        now = datetime.datetime.now().replace(microsecond=0)
        starttime = now.isoformat()
        endtime = (now + datetime.timedelta(hours=2)).isoformat()

        # page = requests.get(book_server+'/book?starttime='+starttime+'&endtime='+endtime+'&user_name='+user_name+'&user_email'+user_email+'&room_name='+room_name) # find how to send the list of rooms read from previous file
        # return page.text() # format result
        # Previous 2 lines should replace next 6 lines
        data = {  
            "cmd": "book",         
            "data": {"starttime": starttime, "endtime": endtime, "user_name": user_name, "user_email": user_email, "room_name": room_name}
        }    
        message = json.dumps(data)  
        return send_message_to_queue(message)
    else:
        print "Room booked is not available"
        return "Room "+str(room_name)+", you are trying to book, is not available !"

# Use Program-o API to reply in natural langage
def natural_langage_bot(message):
    data={}
    # 6 is Program O - The original chatbot
    data['bot_id']=2
    data['say']=message
    #data['convo_id']="exampleusage_1231232"
    data['format']="xml"
    u = "http://www.guismo.fr.eu.org/Program-O/chatbot/conversation_start.php?"+urllib.urlencode(data)
    try:
        page = requests.get(u)
        tree = ET.fromstring(page.content)
        answer=tree.find('chat').find('line').find('response').text
        return answer
    except:
        return ""

def find_dir(cco):
    sys.stderr.write("Beginning process to find someone in the directory and especially this person: "+cco+"\n")

    data = {  
        "cmd": "dir",         
        "data": {"cco": cco}
    }    
    message = json.dumps(data)  
    reply=send_message_to_queue(message)
    if reply.find(";") == -1 :
        return reply
    else:
        tab = reply.split(';')
        return tab[0],tab[1],tab[2],tab[3],tab[4],tab[5]


def display_map(floor):
    sys.stderr.write("Display map of floor: "+floor+"\n")

    t=re.search(r'ILM-[1-7]',floor)
    if t is not None:
        return "http://www.guismo.fr.eu.org/plan/"+t.group(0)+".PNG"
    else:
        t=re.search(r'[1-7]',floor)
        if t is not None:
            return "http://www.guismo.fr.eu.org/plan/ILM-"+t.group(0)+".PNG"
        else:
            return "Floor "+ floor + " not known"

def find_image(keyword):
    u = "http://api.flickr.com/services/feeds/photos_public.gne?tags="+keyword+"&lang=en-us&format=json"
    page = requests.get(u)
    test=page.text.encode('utf-8').replace('jsonFlickrFeed(','').replace(')','').replace('\\\'','\\\\\'')
    j=json.loads(test)
    if len(j["items"]) > 0 :
        i=random.randrange(0, len(j["items"]))
        link=j["items"][i]["media"]["m"]
        return link
    else:
        return "Sorry no image found !"

# Utilities to interact with the Roomfinder-App Server
def get_available():
    u = app_server + "/"
    page = requests.get(u, headers = app_headers)
    tally = page.json()
    #print "Tally: "+str(tally)
    #tally = sorted(tally.items(), key = lambda (k,v): v, reverse=True)
    room_list=(i[1].split()[0]+" "+i[1].split()[1] for i in tally[1] if i[0]=="Free")
    start = tally[0][2]
    end = tally[0][3]
    return start, end, room_list

def get_options():
    u = app_server + "/options"
    page = requests.get(u, headers=app_headers)
    options = page.json()["options"]
    return options

# Roomfinder Demo Room Setup
def setup_demo_room():
    rooms = current_rooms()
    # pprint(rooms)

    # Look for a room called "Roomfinder Demo"
    demo_room_id = ""
    for room in rooms:
        if room["title"] == ROOM_TITLE:
            # print("Found Room")
            demo_room_id = room["id"]
            break

    # If demo room not found, create it
    if demo_room_id == "":
        demo_room = create_demo_room()
        demo_room_id = demo_room["id"]
        # pprint(demo_room)

    return demo_room_id

def create_demo_room():
    spark_u = spark_host + "v1/rooms"
    spark_body = {"title":ROOM_TITLE}
    page = requests.post(spark_u, headers = spark_headers, json=spark_body)
    room = page.json()
    return room

# Utility Add a user to the Roomfinder Demo Room
def add_email_demo_room(email, room_id):
    spark_u = spark_host + "v1/memberships"
    spark_body = {"personEmail": email, "roomId" : room_id}
    page = requests.post(spark_u, headers = spark_headers, json=spark_body)
    membership = page.json()
    sys.stderr.write("reply: "+str(membership)+"\n")
    return membership


# Spark Utility Functions
#### Message Utilities
def send_message_to_email(email, message):
    spark_u = spark_host + "v1/messages"
    message_body = {
        "toPersonEmail" : email,
        "text" : message
    }
    page = requests.post(spark_u, headers = spark_headers, json=message_body)
    message = page.json()
    return message

def post_localfile(roomId, encoded_photo, text='', html='', toPersonId='', toPersonEmail=''):
    filename='/app/output.jpg'
    with open(filename, 'wb') as handle:
        handle.write(encoded_photo.decode('base64'))    
    openfile = open(filename, 'rb')
    filename = ntpath.basename(filename)
    payload = {'roomId': roomId, 'files': (filename, openfile, 'image/jpg')}
    #payload = {'roomId': roomId}
    if text:
        payload['text'] = text
    if html:
        payload['html'] = html
    if toPersonId:
        payload['toPersonId'] = toPersonId
    if toPersonEmail:
        payload['toPersonEmail'] = toPersonEmail
    m = MultipartEncoder(fields=payload)
    headers = {'Authorization': "Bearer " + spark_token, 'Content-Type': m.content_type}
    page = requests.request("POST",url=spark_host + "v1/messages", data=m, headers = headers )
    sys.stderr.write( "page: "+str(page)+"\n" )
    message=page.json()
    file_dict = json.loads(page.text)
    file_dict['statuscode'] = str(page.status_code)
    sys.stderr.write( "statuscode: "+str(file_dict['statuscode'])+"\n" )
    sys.stderr.write( "file_dict: "+str(file_dict)+"\n" )
    return message

def send_message_to_room(room_id, message,message_type):
    spark_u = spark_host + "v1/messages"
    if message_type == "text":
        message_body = {
            "roomId" : room_id,
            "text" : message
        }
    elif message_type == "image":
        message_body = {
            "roomId" : room_id,
            "text" : "",
            "files" : [message]
        }        
    elif message_type == "html":
        message_body = {
            "roomId" : room_id,
            "html" : message
        }        
    else:
        name=message[0]
        title=message[1]
        manager=message[2]
        phone=message[3]
        photo=message[4]
        dir_url=message[5]
        return post_localfile(room_id,photo,html='Name: '+str(name)+' \nTitle: '+str(title)+' \nManager: '+str(manager)+'\n'+str(phone)+dir_url)
    sys.stderr.write( "message_body: "+str(message_body)+"\n" )
    page = requests.post(spark_u, headers = spark_headers, json=message_body)
    message = page.json()
    return message

def get_message(message_id):
    spark_u = spark_host + "v1/messages/" + message_id
    page = requests.get(spark_u, headers = spark_headers)
    message = page.json()
    return message

#### Webhook Utilities
def current_webhooks():
    spark_u = spark_host + "v1/webhooks"
    page = requests.get(spark_u, headers = spark_headers)
    webhooks = page.json()
    return webhooks["items"]

def create_webhook(roomId, target, webhook_name = "New Webhook"):
    spark_u = spark_host + "v1/webhooks"
    spark_body = {
        "name" : webhook_name,
        "targetUrl" : target,
        "resource" : "messages",
        "event" : "created",
        "filter" : "roomId=" + roomId
    }
    page = requests.post(spark_u, headers = spark_headers, json=spark_body)
    webhook = page.json()
    return webhook

def update_webhook(webhook_id, target, name):
    spark_u = spark_host + "v1/webhooks/" + webhook_id
    spark_body = {
        "name" : name,
        "targetUrl" : target
    }
    page = requests.put(spark_u, headers = spark_headers, json=spark_body)
    webhook = page.json()
    return webhook

def delete_webhook(webhook_id):
    spark_u = spark_host + "v1/webhooks/" + webhook_id
    page = requests.delete(spark_u, headers = spark_headers)

def setup_webhook(room_id, target, name):
    webhooks = current_webhooks()
    pprint(webhooks)

    # Look for a Web Hook for the Room
    webhook_id = ""
    for webhook in webhooks:
        if webhook["filter"] == "roomId=" + room_id:
            print("Found Webhook")
            webhook_id = webhook["id"]
            break

    # If Web Hook not found, create it
    if webhook_id == "":
        webhook = create_webhook(room_id, target, name)
        webhook_id = webhook["id"]
    # If found, update url
    else:
        webhook = update_webhook(webhook_id, target, name)

    pprint(webhook)
    #sys.stderr.write("New WebHook Target URL: " + webhook["targetUrl"] + "\n")

    return webhook_id

#### Room Utilities
def current_rooms():
    spark_u = spark_host + "v1/rooms"
    page = requests.get(spark_u, headers = spark_headers)
    rooms = page.json()
    return rooms["items"]

def leave_room(room_id):
    # Get Membership ID for Room
    membership_id = get_membership_for_room(room_id)
    spark_u = spark_host + "v1/memberships/" + membership_id
    page = requests.delete(spark_u, headers = spark_headers)

def get_membership_for_room(room_id):
    spark_u = spark_host + "v1/memberships?roomId=%s" % (room_id)
    page = requests.get(spark_u, headers = spark_headers)
    memberships = page.json()["items"]

    return memberships

# Standard Utility
# def valid_request_check(request):
#     try:
#         if request.headers["key"] == secret_key:
#             return (True, "")
#         else:
#             error = {"Error": "Invalid Key Provided."}
#             sys.stderr.write(str(error) + "\n")
#             status = 401
#             resp = Response(json.dumps(error), content_type='application/json', status=status)
#             return (False, resp)
#     except KeyError:
#         error = {"Error": "Method requires authorization key."}
#         sys.stderr.write(str(error) + "\n")
#         status = 400
#         resp = Response(json.dumps(error), content_type='application/json', status=status)
#         return (False, resp)



if __name__ == '__main__':
    from argparse import ArgumentParser
    import os, sys
    from pprint import pprint

    # Setup and parse command line arguments
    parser = ArgumentParser("Roomfinder Spark Interaction Bot")
    parser.add_argument(
        "-t", "--token", help="Spark User Bearer Token", required=False
    )
    parser.add_argument(
        "-a", "--app", help="Address of app server", required=False
    )
    parser.add_argument(
        "-d", "--dir", help="Address of directory server", required=False
    )
    parser.add_argument(
        "-p", "--photo", help="Address of photo directory server", required=False
    )
    parser.add_argument(
        "-u", "--boturl", help="Local Host Address for this Bot", required=False
    )
    parser.add_argument(
        "-b", "--botemail", help="Email address of the Bot", required=False
    )
    parser.add_argument(
        "-f", "--dispo", help="Address of dispo server", required=False
    )
    parser.add_argument(
        "--demoemail", help="Email Address to Add to Demo Room", required=False
    )
    # parser.add_argument(
    #     "-s", "--secret", help="Key Expected in API Calls", required=False
    # )
    parser.add_argument(
        "-r", "--room", help="Spark Room Name", required=False
    )

    args = parser.parse_args()

    # Set application run-time variables
    # Values can come from
    #  1. Command Line
    #  2. OS Environment Variables
    #  3. Raw User Input
    bot_url = args.boturl
    if (bot_url == None):
        bot_url = os.getenv("roomfinder_spark_bot_url")
        if (bot_url == None):
            bot_url = raw_input("What is the URL for this Spark Bot? ")
    # print "Bot URL: " + bot_url
    sys.stderr.write("Bot URL: " + bot_url + "\n")

    bot_email = args.botemail
    if (bot_email == None):
        bot_email = os.getenv("roomfinder_spark_bot_email")
        if (bot_email == None):
            bot_email = raw_input("What is the Email Address for this Bot? ")
    # print "Bot Email: " + bot_email
    sys.stderr.write("Bot Email: " + bot_email + "\n")

    app_server = args.app
    # print "Arg App: " + str(app_server)
    if (app_server == None):
        app_server = os.getenv("roomfinder_data_server")
        # print "Env App: " + str(app_server)
        if (app_server == None):
            get_app_server = raw_input("What is the data server address? ")
            # print "Input App: " + str(get_app_server)
            app_server = get_app_server
    # print "App Server: " + app_server
    sys.stderr.write("Data Server: " + str(app_server) + "\n")

    dispo_server = args.dispo
    if (dispo_server == None):
        dispo_server = os.getenv("roomfinder_dispo_server")
        if (dispo_server == None):
            get_dispo_server = raw_input("What is the dispo server address? ")
            # print "Input App: " + str(get_app_server)
            dispo_server = get_dispo_server
    # print "App Server: " + app_server
    sys.stderr.write("Dispo Server: " + str(dispo_server) + "\n")

    spark_token = args.token
    # print "Spark Token: " + str(spark_token)
    if (spark_token == None):
        spark_token = os.getenv("spark_token")
        # print "Env Spark Token: " + str(spark_token)
        if (spark_token == None):
            get_spark_token = raw_input("What is the Cisco Spark Token? ")
            # print "Input Spark Token: " + str(get_spark_token)
            spark_token = get_spark_token
    # print "Spark Token: " + spark_token
    # sys.stderr.write("Spark Token: " + spark_token + "\n")
    sys.stderr.write("Spark Token: REDACTED\n")

    # secret_key = args.secret
    # if (secret_key == None):
    #     secret_key = os.getenv("roomfinder_spark_bot_secret")
    #     if (secret_key == None):
    #         get_secret_key = raw_input("What is the Authorization Key to Require? ")
    #         secret_key = get_secret_key
    # sys.stderr.write("Secret Key: " + secret_key + "\n")

    ROOM_TITLE = args.room
    if (ROOM_TITLE == None):
        ROOM_TITLE = os.getenv("roomfinder_room_name")
        if (ROOM_TITLE == None):
            get_room_name = raw_input("What is the name of the Room?")
            ROOM_TITLE = get_room_name
    sys.stderr.write("Room Name: " + ROOM_TITLE + "\n" )

    # Set Authorization Details for external requests
    spark_headers["Authorization"] = "Bearer " + spark_token
    #app_headers["key"] = app_key


    # Setup The MyHereo Spark Demo Room
    demo_room_id = setup_demo_room()
    sys.stderr.write("Roomfinder Demo Room ID: " + demo_room_id + "\n")

    # Setup Web Hook to process demo room messages
    webhook_id = setup_webhook(demo_room_id, bot_url, "Roomfinder Demo Room Webhook")
    sys.stderr.write("Roomfinder Demo Web Hook ID: " + webhook_id + "\n")


    # If Demo Email was provided, add to room
    demo_email = args.demoemail
    if demo_email:
        sys.stderr.write("Adding " + demo_email + " to the demo room.\n")
        add_email_demo_room(demo_email, demo_room_id)

    corr_id=None
    response=None
    connection=None
    channel=None
    callback_queue=None

    app.run(debug=True, host='0.0.0.0', port=int("5000"))
