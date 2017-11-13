#! /usr/bin/python
'''
    Cisco Spark Bot for Room Finder Application

    This Bot will use a provided bot Cisco Spark Account (identified by the Developer Token)
    to interact with the Roomfinder application.  Users can
    check current available rooms, book them and found them on a map. 

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

__author__ = 'gmorini@cisco.com'

from flask import Flask, request, Response
import os, requests, json, re, urllib, socket
import ntpath
import datetime
from requests_toolbelt.multipart.encoder import MultipartEncoder
import pika  
import uuid

import urllib2
import lnetatmo
import time
import unicodedata
import feedparser

admin_list=["rcronier@cisco.com","gmorini@cisco.com","johnroomfinder@gmail.com"]
log_dir="/log/"

app = Flask(__name__)

spark_host = "https://api.ciscospark.com/"
spark_headers = {}
spark_headers["Content-type"] = "application/json; charset=utf-8"
app_headers = {}
app_headers["Content-type"] = "application/json"
google_headers = {}
google_headers["User-Agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.112 Safari/534.30"

def return_utf(s):
    if isinstance(s, unicode): 
        return s.encode('utf-8')
    if isinstance(s, int): 
        return str(s).encode('utf-8')
    if isinstance(s, float): 
        return str(s).encode('utf-8')
    if isinstance(s, complex): 
        return str(s).encode('utf-8')
    if isinstance(s, str): 
        return s

def netatmoOutdoor(sonde):
    authorization = lnetatmo.ClientAuth()
    devList = lnetatmo.WeatherStationData(authorization)
    msg= (sonde +" current temperature : %s C" % ( devList.lastData()[sonde]['Temperature']))
    return msg
    
def netatmoIndoor(sonde):
    authorization = lnetatmo.ClientAuth()
    devList = lnetatmo.WeatherStationData(authorization)
    msg= (sonde + " current temperature : %s C" % ( devList.lastData()[sonde]['Temperature']))
    return msg
   
def stats(user,roomid):
    logfile = open(log_dir+"ILM-RoomFinder-Bot.log", 'r+')
    line = logfile.readlines()
    #sys.stderr.write('line='+str(line)+'\n')
    j = 1
    logfile.seek(0)
    for i in line:
        if i != '' and i!= "\r\n" and i!= "\n" and i.split()[0].lower().startswith(user) :
            j = int(i.split()[1])+1
        else : 
            logfile.write(i)
    logfile.write(user +" "+ str(j) + " " + roomid + "\r\n")
    logfile.truncate()
    logfile.close()
    return False

#REMOVE USER FROM THE ADVERTISING
def optout(user):
    f = open(log_dir+"ILM-RoomFinder-Bot.log","r+")
    d = f.readlines()
    f.seek(0)
    for i in d:
        if (i.startswith(user) == 0) :
            f.write(i)
    f.truncate()
    f.close()
    return False

def log(user, request, response):
    f = open(log_dir+user +'.log', 'a+')
    f.write("\r\n" + datetime.datetime.now().replace(microsecond=0).isoformat() + " - " + str(request) + " - " + str(response) + "\r\n")
    f.close()
    return True

def readstats():
    logs=""
    nbUsers = 0
    nbMsg = 0
    logfile = open(log_dir+'ILM-RoomFinder-Bot.log', 'r+')
    for line in logfile:
        
        if line != '' and line!= "\r\n" and line!= "\n" :
            nbMsg = nbMsg + int(line.split()[1])
            nbUsers = nbUsers + 1
    logfile.close()
    logs = "* nb Users : " + str(nbUsers) + "\r\n" + "* nb Requests : " + str(nbMsg)
    return logs
    
def advertise(msg,message_type="text"):
    logfile = open(log_dir+'ILM-RoomFinder-Bot.log', 'r+')
    for line in logfile:
        
        if line != '' and line!= "\r\n" and line!= "\n" :
            roomid = line.split()[2]
            send_message_to_room(roomid, msg, message_type)
    logfile.close()
    return True

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
            reply=send_welcome_message(data["email"])
            status = 201
            resp = Response(reply, content_type='application/json', status=status)
        except KeyError:
            error = {"Error":"API Expects dictionary object with single element and key of 'email'"}
            status = 400
            resp = Response(json.dumps(error), content_type='application/json', status=status)
    # demo_room_members = get_membership()
    # resp = Response(
    #     json.dumps(demo_room_members, sort_keys=True, indent = 4, separators = (',', ': ')),
    #     content_type='application/json',
    #     status=status)
    else:
        resp = Response("OK", status=status)
    return resp

@app.route('/', methods=["POST"])
# Bot functions to process the incoming messages posted by Cisco Spark
def process_webhook():
    text=""
    post_data = request.get_json(force=True)
    sys.stderr.write("post_data="+str(post_data)+"\n")
    message_type="text"
    message_id = post_data["data"]["id"]
    message = get_message(message_id)
    sys.stderr.write("message: "+str(message)+"\n")
    reply=None
    removed = False

    # First make sure not processing a message from the bot
    if post_data['data']["personEmail"] == bot_email:
        return ""

    # if "markdown" in message:
    #     sys.stderr.write("markdown: "+str(message["markdown"].encode('utf-8'))+"\n")
    # if "html" in message:
    #     sys.stderr.write("html: "+str(message["html"].encode('utf-8'))+"\n")
    if "errors" in message or "text" not in message:
        message["text"]=""
        text=""
    else:
        text=message["text"].replace('@Roomfinder','').lstrip().rstrip().lower().encode("utf-8")
        text=message["text"].replace('Roomfinder','').lstrip().rstrip().lower().encode("utf-8")
    sys.stderr.write("text: "+str(message["text"].encode('utf-8'))+"\n")

    if "event" in message and message["event"] == 'deleted' :
        sys.stderr.write('Message deleted\n')
        return ""

    # If someone is mentioned, do not answer
    if 'mentionedPeople' in message:
        sys.stderr.write("mentionned: "+str(message["mentionedPeople"])+"\n")
        sys.stderr.write("Bot id    : "+str(bot_id)+"\n")
        if bot_id not in message["mentionedPeople"]:
            sys.stderr.write("Not the bot mentionned, do not answer !\n")
            return ""
        else:
            sys.stderr.write("Bot mentionned, removing the bot name !\n")
            text=text.replace(bot_name,"").lstrip()

    if not (post_data['data']['personEmail'] in admin_list
        or post_data['data']['personEmail'].endswith('@cisco.com') 
        or post_data['data']['personEmail'].endswith('@ciscofrance.com') ) :
        reply="** This bot is reserved for Cisco Employees **"
        sys.stderr.write("reply: "+str(reply)+"\n")
        return send_message_to_room(post_data["data"]["roomId"], reply,message_type)

    sys.stderr.write("Incoming Room Message\tmessage: "+text+"\t")

    # Check if message contains word "dispo" and if so send results
    if text.startswith("dispo") or text.startswith("available"):
        buildings = re.findall(r' [a-zA-Z][a-zA-Z0-9\-]+', text)
        sys.stderr.write('Building founds: '+str(len(buildings))+"\n")
        for b in buildings:
            sys.stderr.write(' - '+str(b)+"\n")
        if len(buildings) == 0 :
            buildings=[" ILM-"]

        building=buildings[0][1:]
        try:
            u = dispo_server + "/dispo?key="+str(building)
            page = requests.get(u, headers = app_headers)
            tally = page.json()
            sys.stderr.write("Tally: "+str(tally)+"\n")
            #tally = sorted(tally.items(), key = lambda (k,v): v, reverse=True)
            results=(i[1] for i in tally[1] if i[0]=="Free")
            start = " in building "+str(building)+" "+tally[0][2]
            end = tally[0][3]

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
    #                reply = ", with more than "+str(inf)+" seats, "+start+" "+end
                    reply = ", with more than "+str(inf)+" seats, int the next 2 hours"
                else:
                    inf = int(number[0])
                    sup = int(number[1])
                    filtered_results=[result for result in toto if inf <= int(result.split('(')[1].split(')')[0]) <= sup]
                    sys.stderr.write("filtered_results: "+str(filtered_results)+"\n")
    #                reply = ", with more than "+str(inf)+" and less than "+str(sup)+" seats, "+start+" "+end
                    reply = ", with more than "+str(inf)+" and less than "+str(sup)+" seats in the next 2 hours"               
            else:
    #            reply = " "+start+" "+end
                reply = " in the next 2 hours"
                filtered_results=toto

            titi=list(filtered_results)
            # Test if filtered result list is empty or not
            if titi:
                reply = "The current available rooms"+reply+" are:\n"

                for result in titi:
                    reply += "* %s\n" % (result)
                    #sys.stderr.write("Salle: "+result+"\n")
                reply += "\nYou can book one of the rooms with the keyword : **book ROOM-NAME [option: 30m or 1h]**"
            else:
                reply = "Sorry, there are currently no available rooms"+reply+"\n"
        except Exception as e:
            reply="Dispo server is not available !"
    # Check if message contains word "options" and if so send options
    elif text in ["options","help","aide","?","/help","hello","hi"] :
        reply = "Here are the keywords you can use: \n"
        reply += "* **dispo** or **available** keyword will display the available rooms for the next 2 hours timeslot. For other buildings than ILM, you will have to add the prefix of your building, like **available SJC14-**\n"
        reply += "* **reserve** or **book** keyword will try to book, by default for the next 2 hours, the room mentionned after the keyword **book** or **reserve**. You can specify the duration of the meeting with the option 30m or 1h.\n"
        reply += "* **plan** or **map** keyword will display the map of the floor in **ILM building** mentionned after the keyword **plan** or **map**.\n"
        reply += "* **cherche** or **find** keyword will help you to find the floor of a room mentionned by its short name after the keyword.\n"
        reply += "* **batiment** or **building** keyword will help you to find a building id based on name of the building/town/country mentionned after the keyword, like **building Toronto** or **batiment ILM**.\n"
        reply += "* **in** or **inside** keyword will display a picture inside the room mentionned after the keyword in **ILM building**.\n"
        reply += "* **dir** keyword will display the directory entry for the CCO id mentionned after the keyword **dir**.\n"
        reply += "* [disabled] **guest** keyword will create a guest wifi account for an attendee. You should specify after the keyword **guest** the attendee first name, last name and email, like **guest** john doe jdoe@email.com.\n"
        reply += "* **parking** keyword will display the available spots inside Cisco **ILM parking**.\n"
        reply += "* **add** keyword followed by an email will create a room between the bot and this email.\n"
        reply += "* [new] **optout** or **bye** keyword will remove you from the list of users. You will no longer receive ads until you send me a new request.\n"        
        reply += "* **help** or **aide** will display a helping message to the Spark room.\n"
        reply += "\nAll the the bot request are documented in [EN](https://cisco.jiveon.com/docs/DOC-1766766) and [FR](https://cisco.jiveon.com/docs/DOC-1765746). \r\n"
        reply += "\nDo not hesitate to help us improve RoomFinder by joining the [RoomFinder Support Space](http://incis.co/VNDI)\n"
        if post_data['data']['personEmail'] in admin_list :
            reply += "* **/stats/** keyword will display the statistics of Roomfinder Cisco Spark Bot.\n"
            reply += "* **/advertise/** keyword, followed by a message, will display this message for all users of Roomfinder Cisco Spark Bot.\n"
        message_type="text"
    # Check if message contains phrase "add email" and if so add user to room
    elif text.startswith("add "):
        # Get the email that comes
        emails = re.findall(r' [\w\.-]+@[\w\.-]+', text)
        pprint(emails)
        reply = "Adding users to demo room.\n"
        for email in emails:
            send_welcome_message(email)
            reply += "  - %s \n" % (email)
    elif text.startswith("dir"):
        if text.rstrip() == "dir" :
            reply  = "Usage of dir command is: \n"
            reply += "\t\tdir cco_id \n"
            reply += "\tor \n"
            reply += "\t\tdir firstname lastname \n"
        else:
            # Find the cco id
            cco=text.replace('dir ','')
            reply = find_dir(cco)
            print "find_dir: "+str(reply)
            if type(reply) != str and type(reply) != unicode:
                message_type="localfine"
    elif text.startswith("guest"):
        if post_data['data']['personEmail'] in admin_list :
            if text not in ["guest"]:
                # Find the 
                args=text.split()
                if len(args) == 4:
                    reply = guest(args[1],args[2],args[3])
                    sys.stderr.write( "guest: "+str(reply)+"\n" )
                else:
                    reply = "Usage of guest command is:\n"
                    reply += "\tguest firstName lastName email\n"
            else:
                reply = "Usage of guest command is:\n"
                reply += "\tguest firstName lastName email\n"
        else:
            reply = "## We have been asked by Infosec to shutdown the Guest feature. We are working with them to find a way to restore this succesfull service. ##"
    elif text.startswith("find ") or text.startswith("cherche "):
        # Find the room
        room=text.replace('find ','')
        room=room.replace('cherche ','')
        reply = where_room(room.upper())
        print "where_room: "+str(reply)
        if not reply.startswith("Sorry"):
            rooms=reply.split(';')
            if len(rooms)==1:
                r=rooms[0].split('-')
                if (len(r)>=2):
                    floor=r[0]+'-'+r[1]
                    floor_map_raw=display_map(floor)
                    floor_map=json.loads(floor_map_raw)
                    floor_map["text"]="Here is the full name of the room, and the map of the floor: \n * "+rooms[0]
                    # stats(post_data['data']['personEmail'],post_data['data']['roomId'])
                    # log(post_data['data']['personEmail']+" - " +post_data['data']['roomId'],str(text),reply)
                    # send_message_to_room(post_data["data"]["roomId"], reply,message_type)
                    # #message_type="pdf"
                    reply=json.dumps(floor_map)
                    message_type="pdf"
            else:
                reply="Do you mean:\n"
                for r in rooms:
                    reply+="* "+r+"\n"
                message_type="text"
        else:
            message_type="text"
    elif text.startswith("image "):
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
    elif text.startswith("plan") or text.startswith("map"):
        # Find the floor
        if text in ["plan","map"]:
            reply = "Usage of map/plan command is:\n"
            reply += "\tmap/plan command followed by floor name like:\n"
            reply += "\t\tmap SJC05-3\n"        
            reply += "\t\t\tor\n"        
            reply += "\t\tplan ILM-7\n"        
        else:
            floor=text.replace('map ','')
            floor=floor.replace('plan ','')
            pattern = re.compile("^([0-7]+)$")
            m = pattern.match(floor)
            if m:
                # Map and number => ILM
                floor='ILM-'+m.group()
                sys.stderr.write("display_map: "+floor+"\n")
                reply = display_map(floor.upper())
                message_type="pdf"
            else:
                pattern2 = re.compile("^([a-z0-9 ]+\-[0-9]+)$")
                m2 = pattern2.match(floor)
                if m2:
                    floor=m2.group()
                    sys.stderr.write("display_map: "+floor+"\n")
                    reply = display_map(floor.upper())
                    if reply != "Connection error to map server":
                        message_type="pdf"
                else:
                    t=floor.split("-")
                    if len(t) == 3 :
                        floor=t[0]+"-"+t[1]
                        sys.stderr.write("display_map: "+floor+"\n")
                        reply = display_map(floor.upper())
                        if reply != "Connection error to map server":
                            message_type="pdf"
                    else:
                        reply = "No floor is corresponding. Try **map/plan floor_name** or **map/plan floor_name** \n<br>\n <blockquote> with floor_name like ILM-3 or SJC13-3 </blockquote>"
    elif text.lower().startswith("building") or text.lower().startswith("batiment"):
        # Find the floor
        if text.lower() in ["building","batiment"]:
            reply = "Usage of building/batiment command is:\n"
            reply += "\tbuilding/batiment command followed by building/town/country name like:\n"
            reply += "\t\tbuiding Toronto\n"        
            reply += "\t\t\tor\n"        
            reply += "\t\tbatiment ILM\n"        
        else:
            building=text.lower().replace('building ','')
            building=building.lower().replace('batiment ','')
            reply = display_building(building.upper())
    elif text.startswith("book") or text.startswith("reserve"):
        if text in ["book","reserve"]:
            reply = "Usage of book/reserve command is:\n"
            reply += "\tbook/reserve command followed by room name like:\n"
            reply += "\t\t reserve ILM-7-HUGO\n"        
            reply += "\t\t\tor\n"        
            reply += "\t\t book SJC13-3-SMILE\n"  
        else:      
            # Find the room name
            end = len(text)
            if text.startswith("book "):
                start = len('book ')
            elif text.startswith("reserve "):
                start = len('reserve ')
            else:
                sys.stderr.write("I don't know how you arrive here ! This is a bug !\n")    
            room_name=text[start:end]
            sys.stderr.write("room_name= "+str(room_name)+"\n")
            reply = book_room(room_name.upper(),post_data['data']["personEmail"],getDisplayName(post_data['data']["personId"]))
            sys.stderr.write("book_room: "+reply+"\n")
    elif text.startswith('in') or text.startswith('inside') or text.startswith('interieur'):
        if text in ["in","inside","interieur"]:
            reply = "Usage of in/inside/interieur command is:\n"
            reply += "\t in/inside/interieur command followed by room name like:\n"
            reply += "\t\t in ILM-7-HUGO\n"        
            reply += "\t\t\tor\n"        
            reply += "\t\t inside SJC13-3-SMILE\n"  
        else:      
            inside = text.split()[1].upper()
            if inside.startswith('ILM') :
                reply=display_inside(inside)
                message_type="image"
            else :
                reply = "No Inside View. This feature is available only for ILM building."
    elif text in ["parking"] :
        try:
            page = requests.get("http://173.38.154.145/parking/getcounter.py", timeout=0.5)
            result = page.json()
            reply = "Free cars parking: "+str(result["car"]["count"])+" over "+str(result["car"]["total"])+"<br>"
            reply += "Free motorbikes parking: "+str(result["motorbike"]["count"])+" over "+str(result["motorbike"]["total"])+"<br>"
            reply += "Free bikecycles parking: "+str(result["bicycle"]["count"])+" over "+str(result["bicycle"]["total"])
        except requests.exceptions.RequestException as e:  # This is the correct syntax
            sys.stderr.write("Timeout or HTTP error code on parking API")
            reply = "Sorry parking information is not available !"
        except socket.timeout as e:
            sys.stderr.write("Timeout or HTTP error code on parking API")
            reply = "Sorry parking information is not available !"
    elif text.startswith('temp '):
        sonde = text.split()[1].upper()
        if (sonde == "ILM-1-GAUGUIN") :
            reply = netatmoOutdoor(sonde)
        else :
            reply = "No Temperature sensors available in this room"
    elif text == "/stats/":
        if post_data['data']['personEmail'] in admin_list :
            reply=readstats()
        else:
            reply = "##You have no admin rights to view stats##"
    elif text == "optout" or text.startswith('bye') or text.startswith('quit'):
            reply = "##Bye bye " + post_data['data']['personEmail'] + ", I am removing you from the list of users. ##"
            optout(post_data['data']['personEmail'])
            removed = True
    elif text.startswith("/advertise/"):
        if post_data['data']['personEmail'] in admin_list :
            if "html" in message:
                advertise(message["html"].replace("/advertise/","").lstrip().strip(),"html")
            else:
                advertise(message["text"].replace("/advertise/","").lstrip().strip())
            reply=""
        else :
            reply = "##You have no admin rights to advertise##"
    # If nothing matches, send instructions
    else:
        # reply=natural_langage_bot(text)
        # if reply == "":
        #     return reply
        if text=="":
            reply="There seem to be an error with Cisco Spark ! Sorry about that, try again later !"
        else:
            reply="Command not found ! Type help to have the list of existing commands !"
    sys.stderr.write("reply: "+"{0:.3000}".format(reply)+"\n")
    if reply != "":
        if not removed :
            stats(post_data['data']['personEmail'],post_data['data']['roomId'])
        log(post_data['data']['personEmail']+" - " +post_data['data']['roomId'],str(text),reply)
        send_message_to_room(post_data["data"]["roomId"], reply,message_type)
        log_message_to_room(log_room_id, post_data['data']['personEmail'], str(text.encode('utf-8')), reply,message_type)
    return ""

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
    duration=2

    if room_name.endswith(' 1H') or room_name.endswith(' 1 H') or room_name.endswith(' 1 HOUR') or room_name.endswith(' 1HOUR')  or room_name.endswith(' 1 HOURS') or room_name.endswith(' 1HOURS') :
        duration=1
        room_name=room_name.replace(' 1HOURS','').replace(' 1 HOURS','').replace(' 1 HOUR','').replace(' 1HOUR','').replace(' 1 H','').replace(' 1H','')
    elif room_name.endswith(' 30M') or room_name.endswith(' 30 M') or room_name.endswith(' 30MIN') or room_name.endswith(' 30 MIN') or room_name.endswith(' 30MINS') or room_name.endswith(' 30 MINS') or room_name.endswith(' 30MINUTES') or room_name.endswith(' 30 MINUTES') or room_name.endswith(' 30MINUTE') or room_name.endswith(' 30 MINUTE') :
        duration=0.5
        room_name=room_name.replace(' 30MINS','').replace(' 30 MINS','').replace(' 30MINUTES','').replace(' 30 MINUTES','').replace(' 30MINUTE','').replace(' 30 MINUTE','')
        room_name=room_name.replace(' 30MIN','').replace(' 30 MIN','').replace(' 30M','').replace(' 30 M','')
    elif room_name.endswith(' 2H') or room_name.endswith(' 2 H') or room_name.endswith(' 2HOUR') or room_name.endswith(' 2 HOUR') or room_name.endswith(' 2HOURS') or room_name.endswith(' 2 HOURS') :
        duration=2
        room_name=room_name.replace(' 2HOURS','').replace(' 2 HOURS','').replace(' 2HOUR','').replace(' 2 HOUR','').replace(' 2H','').replace(' 2 H','')

    sys.stderr.write("After removing duration, room:_name is "+room_name+"\n")

    now = datetime.datetime.now().replace(microsecond=0)
    starttime = (now - datetime.timedelta(minutes=5)).isoformat()
    endtime = (now - datetime.timedelta(minutes=5) + datetime.timedelta(hours=duration)).isoformat()

    data = {  
        "cmd": "book",         
        "data": {"starttime": starttime, "endtime": endtime, "user_name": user_name, "user_email": user_email, "room_name": room_name}
    }    
    message = json.dumps(data)  
    return send_message_to_queue(message)

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

def guest(firstName, lastName, email):
    sys.stderr.write("Beginning process to request a guest account for "+firstName+" "+lastName+" <"+email+">\n")
    data = {  
        "cmd": "guest",         
        "data": {
            "firstName" : firstName,
            "lastName"  : lastName,
            "email"     : email
        }
    }    
    message = json.dumps(data)  
    reply=send_message_to_queue(message)
    return reply

def where_room(room):
    sys.stderr.write("Beginning process to find this room: "+room+"\n")
    data = {  
        "cmd": "where",         
        "data": {"room": room}
    }    
    message = json.dumps(data)  
    reply=send_message_to_queue(message)
    return reply

def display_map(floor):
    sys.stderr.write("Display map of floor: "+floor+"\n")
    data = {  
        "cmd": "map",         
        "data": {"floor": floor}
    }    
    message = json.dumps(data)  
    reply=send_message_to_queue(message)
    return reply

def display_building(building):
    sys.stderr.write("Display building for: "+building+"\n")
    data = {  
        "cmd": "building",         
        "data": {"building": building}
    }    
    message = json.dumps(data)  
    reply=send_message_to_queue(message)
    return reply

def display_inside(room):
    sys.stderr.write("Display inside of room: "+room+"\n")
    t=re.search(r'ILM-[1-7]',room)
    if t is not None:
        return "http://www.guismo.fr.eu.org/in/"+room+".jpg"
    else:
        return "Room "+ room + " not known"

def find_image(keyword):
    u = "http://api.flickr.com/services/feeds/photos_public.gne?tags="+keyword+"&lang=en-us&format=json"
    page = requests.get(u)
    test=page.text.encode('utf-8').replace('jsonFlickrFeed(','').replace(')','').replace('\\\'','\\\\\'')
    j=json.loads(test)
    if len(j["items"]) > 0 :
        i= ord(os.urandom(1))%len(j["items"])
        link=j["items"][i]["media"]["m"]
        return link
    else:
        return "Sorry no image found !"


# Spark Utility Functions
#### Message Utilities
def send_welcome_message(email):
    spark_u = spark_host + "v1/messages"
    message_body = {
        "toPersonEmail" : email,
        "markdown" : "Welcome in a chat room with **RoomFinder**, the 1:1 Bot to help you interact with Cisco Buildings\nType **help** to list the existing commands.\n"
    }
    page = requests.post(spark_u, headers = spark_headers, json=message_body)
    message = page.json()
    return message

def post_localfile(roomId, encoded_photo, text='', html='', markdown='', toPersonId='', toPersonEmail=''):
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
    if markdown:
        payload['markdown'] = markdown
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
    handle.close()
    openfile.close()
    return message

def post_pdffile(roomId, encoded_file, text='', html='', markdown='', toPersonId='', toPersonEmail=''):
    filename='/app/output.pdf'
    with open(filename, 'wb') as handle:
        handle.write(encoded_file.decode('base64'))    
    openfile = open(filename, 'rb')
    filename = ntpath.basename(filename)
    payload = {'roomId': roomId, 'files': (filename, openfile, 'application/pdf')}
    #payload = {'roomId': roomId}
    if text:
        payload['text'] = text
    if html:
        payload['html'] = html
    if markdown:
        payload['markdown'] = markdown
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
    handle.close()
    openfile.close()
    return message


def log_message_to_room(room_id, author, message, message_reply,message_type="text"):
    spark_u = spark_host + "v1/messages"
    if message_type == "text":
        message_body = {
            "roomId" : room_id,
            "markdown" : "Author: "+author+" <br> Request: "+message+" <br> Reply: "+message_reply.decode('utf-8')
        }
    elif message_type == "image":
        message_body = {
            "roomId" : room_id,
            "text" : "Author: "+author+" <br> Request: "+message+" <br> Reply: ",
            "files" : [message_reply]
        }        
    elif message_type == "html":
        message_body = {
            "roomId" : room_id,
            "html" : "Author: "+author+" \n Request: "+message+" \n Reply: "+message_reply
        }        
    elif message_type == "pdf":
        s = json.loads(message_reply)
        if "text" in s and "pdf" in s:
            return post_pdffile(room_id,s["pdf"],markdown="Author: "+author+" <br /> Request: "+message+" <br /> Reply: "+s["text"])
        else:
            message_body = {
                "roomId" : room_id,
                "html" : "Author: "+author+" \n Request: "+message+" \n Reply: Unreadadble reply !\n"
            }        
    else:
        try:
            sys.stderr.write("message_reply: "+str(message_reply)+"\n")
            name=message_reply[0]
            sys.stderr.write("After get name from message_reply\n")
            title=message_reply[1]
            manager=message_reply[2]
            phone=message_reply[3]
            photo=message_reply[4]
            dir_url=message_reply[5]
            author
            tmp=""
            tmp+="Author: "+return_utf(author)+" <br>\n Request: "+return_utf(message)+" <br>\n Reply: <br>\n "

            sys.stderr.write("Before name\n")
            sys.stderr.write("Type: "+str(type(name))+"\n")

            if name!= "":
                sys.stderr.write("After test on name\n")
                tmp+="<b>Name</b>: "+return_utf(name)+'\n'

            sys.stderr.write("After name\n")

            if title != "":
                tmp+='<b>Title</b>: '+return_utf(title)+'\n'
            if manager != "":
                tmp+='<b>Manager</b>: '+return_utf(manager)+'\n'
            if phone != "":
                tmp+=return_utf(phone)
            if dir_url != "":
                tmp+=return_utf(dir_url)
            #sys.stderr.write("tmp: "+str(tmp.encode('utf-8'))+"\n")
            sys.stderr.write("Before post_localfile\n")

        except Exception as ex:
            sys.stderr.write("Exception: "+str(ex))

        return post_localfile(room_id,photo,html=tmp)

    sys.stderr.write( "message_body: "+str(message_body)+"\n" )
    page = requests.post(spark_u, headers = spark_headers, json=message_body)
    message = page.json()
    #return message
    return ""


def send_message_to_room(room_id, message,message_type="text"):
    spark_u = spark_host + "v1/messages"
    if message_type == "text":
        message_body = {
            "roomId" : room_id,
            "markdown" : message
        }
    elif message_type == "image":
        message_body = {
            "roomId" : room_id,
            "text" : "",
            "files" : [message]
        }        
    elif message_type == "html":
        sys.stderr.write("Post HTML message\n")
        message_body = {
            "roomId" : room_id,
            "html" : message
        }
    elif message_type == "pdf":
        s = json.loads(message)
        if "text" in s and "pdf" in s:
            return post_pdffile(room_id,s["pdf"],markdown=s["text"])
        else:
            message_body = {
                "roomId" : room_id,
                "html" : "Unreadadble reply !\n"
            }        
    else:
        name=message[0]
        title=message[1]
        manager=message[2]
        phone=message[3]
        photo=message[4]
        dir_url=message[5]
        tmp=""
        if name!= "":
            tmp+="<b>Name</b>: "+str(name)+'\n'
        if title != "":
            tmp+='<b>Title</b>: '+str(title)+'\n'
        if manager != "":
            tmp+='<b>Manager</b>: '+str(manager)+'\n'
        if phone != "":
            tmp+=str(phone)
        if dir_url != "":
            tmp+=dir_url
        return post_localfile(room_id,photo,html=tmp)
    sys.stderr.write( "message_body: "+str(message_body)+"\n" )
    page = requests.post(spark_u, headers = spark_headers, json=message_body)
    message = page.json()
    #return message
    return ""

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

def create_webhook(target, webhook_name = "New Webhook"):
    spark_u = spark_host + "v1/webhooks"
    spark_body = {
        "name" : webhook_name,
        "targetUrl" : target,
        "resource" : "messages",
        "event" : "created"
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

def setup_webhook(target, name):
    webhooks = current_webhooks()
    pprint(webhooks)

    # Look for a Web Hook for the Room
    webhook_id = ""
    for webhook in webhooks:
        print("Found Webhook")
        webhook_id = webhook["id"]
        break

    # If Web Hook not found, create it
    if webhook_id == "":
        webhook = create_webhook(target, name)
        webhook_id = webhook["id"]
    # If found, update url
    else:
        webhook = update_webhook(webhook_id, target, name)

    pprint(webhook)
    #sys.stderr.write("New WebHook Target URL: " + webhook["targetUrl"] + "\n")

    return webhook_id

#### Room Utilities
def get_membership(room_id):
    spark_u = spark_host + "v1/memberships?roomId=%s" % (room_id)
    page = requests.get(spark_u, headers = spark_headers)
    memberships = page.json()["items"]

    return memberships

def get_bot_id():
    spark_u = spark_host + "v1/people/me"
    page = requests.get(spark_u, headers = spark_headers)
    reply = page.json()
    return reply["id"]

def get_bot_name():
    spark_u = spark_host + "v1/people/me"
    page = requests.get(spark_u, headers = spark_headers)
    reply = page.json()
    return reply["displayName"]

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
    parser.add_argument(
        "--logroomid", help="Cisco Spark Room ID to log messages", required=False
    )
    # parser.add_argument(
    #     "-s", "--secret", help="Key Expected in API Calls", required=False
    # )
    args = parser.parse_args()

    # Set application run-time variables
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

    log_room_id = args.logroomid
    # print "Log room id: " + str(log_room_id)
    if (log_room_id == None):
        log_room_id = os.getenv("log_room_id")
        # print "Env log_room_id: " + str(log_room_id)
        if (log_room_id == None):
            get_log_room_id = raw_input("What is the Cisco Spark Log Room ID? ")
            # print "Input log_room_id: " + str(get_log_room_id)
            log_room_id = get_log_room_id
    # print "log_room_id: " + log_room_id
    # sys.stderr.write("log_room_id: " + log_room_id + "\n")
    sys.stderr.write("log_room_id: "+str(log_room_id)+"\n")

    # Set Authorization Details for external requests
    spark_headers["Authorization"] = "Bearer " + spark_token
    #app_headers["key"] = app_key

    # Setup Web Hook to process demo room messages
    webhook_id = setup_webhook(bot_url, "Roomfinder Bot Webhook")
    sys.stderr.write("Roomfinder Demo Web Hook ID: " + webhook_id + "\n")

    bot_id=get_bot_id()
    bot_name=get_bot_name()
    sys.stderr.write("Bot ID: "+bot_id+"\n")
    sys.stderr.write("Bot Name: "+bot_name+"\n")

    corr_id=None
    response=None
    connection=None
    channel=None
    callback_queue=None

    app.run(debug=False, host='0.0.0.0', port=int("5000"), threaded=True)
