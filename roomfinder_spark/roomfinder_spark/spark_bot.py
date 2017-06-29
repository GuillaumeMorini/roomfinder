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
import requests, json, re, urllib, random, socket
import xml.etree.ElementTree as ET
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
from subprocess import check_output

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
    post_data = request.get_json(force=True)
    sys.stderr.write("post_data="+str(post_data)+"\n")
    message_type="text"
    message_id = post_data["data"]["id"]
    message = get_message(message_id)
    print("message: "+str(message))
    reply=None

    # First make sure not processing a message from the bot
    if post_data['data']["personEmail"] == bot_email:
        return ""

    sys.stderr.write("text: "+str(message["text"].encode('utf-8'))+"\n")
    # if "markdown" in message:
    #     sys.stderr.write("markdown: "+str(message["markdown"].encode('utf-8'))+"\n")
    # if "html" in message:
    #     sys.stderr.write("html: "+str(message["html"].encode('utf-8'))+"\n")
    text=message["text"].lstrip().encode("utf-8")

    # If someone is mentioned, do not answer
    if 'mentionedPeople' in message:
        sys.stderr.write("mentionned: "+str(message["mentionedPeople"])+"\n")
        sys.stderr.write("Bot id    : "+str(bot_id)+"\n")
        if bot_id not in message["mentionedPeople"]:
            sys.stderr.write("Not the bot mentionned, do not answer !\n")
            return ""
        else:
            text=text.replace(bot_name,"").lstrip()

    if not (post_data['data']['personEmail'] in admin_list
        or post_data['data']['personEmail'].endswith('@cisco.com') 
        or post_data['data']['personEmail'].endswith('@ciscofrance.com') ) :
        reply="** This bot is reserved for Cisco Employees **"
        sys.stderr.write("reply: "+str(reply)+"\n")
        return send_message_to_room(post_data["data"]["roomId"], reply,message_type)

    sys.stderr.write("Incoming Room Message\tmessage: "+text+"\t")

    # Check if message contains word "dispo" and if so send results
    if text.lower().startswith("dispo") or text.lower().startswith("available"):
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
                reply += "* %s\n" % (result)
                #sys.stderr.write("Salle: "+result+"\n")
        else:
            reply = "Sorry, there is currently no available rooms"+reply+"\n"
    # Check if message contains word "options" and if so send options
    elif text.lower() in ["options","help","aide","?","/help","hello","hi"] :
        reply = "Here are the keywords you can use: \n"
        reply += "* **dispo** or **available** keyword will display the available rooms for the next 2 hours timeslot. For other buildings than ILM, you will have to add the prefix of your building, like **available SJC14-**\n"
        reply += "* **reserve** or **book** keyword will try to book, by default for the next 2 hours, the room mentionned after the keyword **book** or **reserve**. You can specify the duration of the meeting with the option 30m or 1h.\n"
        reply += "* **plan** or **map** keyword will display the map of the floor in **ILM building** mentionned after the keyword **plan** or **map**.\n"
        reply += "* **cherche** or **find** keyword will help you to find the floor of a room mentionned by its short name after the keyword.\n"
        reply += "* **in** or **inside** keyword will display a picture inside the room mentionned after the keyword in **ILM building**.\n"
        reply += "* **dir** keyword will display the directory entry for the CCO id mentionned after the keyword **dir**.\n"
        reply += "* **guest** keyword will create a guest wifi account for an attendee. You should specify after the keyword **guest** the attendee first name, last name and email, like **guest** john doe jdoe@email.com.\n"
        reply += "* **parking** keyword will display the available spots inside Cisco **ILM parking**.\n"
        reply += "* **add** keyword followed by an email will create a room between the bot and this email.\n"
        reply += "* **help** or **aide** will display a helping message to the Spark room.\n"
        if post_data['data']['personEmail'] in admin_list :
            reply += "* **/stats/** keyword will display the statistics of Roomfinder Cisco Spark Bot.\n"
            reply += "* **/advertise/** keyword, followed by a message, will display this message for all users of Roomfinder Cisco Spark Bot.\n"
        message_type="text"
    # Check if message contains phrase "add email" and if so add user to room
    elif text.lower().startswith("add "):
        # Get the email that comes
        emails = re.findall(r' [\w\.-]+@[\w\.-]+', text)
        pprint(emails)
        reply = "Adding users to demo room.\n"
        for email in emails:
            send_welcome_message(email)
            reply += "  - %s \n" % (email)
    elif text.lower().startswith("dir "):
        # Find the cco id
        cco=text.lower().replace('dir ','')
        reply = find_dir(cco)
        print "find_dir: "+str(reply)
        if type(reply) != str and type(reply) != unicode:
            message_type="localfine"
    elif text.lower().startswith("guest"):
        if post_data['data']['personEmail'] in admin_list :
            if text.lower() not in ["guest"]:
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
    elif text.lower().startswith("find ") or text.lower().startswith("cherche "):
        # Find the room
        room=text.lower().replace('find ','')
        room=room.lower().replace('cherche ','')
        reply = where_room(room.upper())
        print "where_room: "+str(reply)
        if not reply.startswith("Sorry"):
            rooms=reply.split(';')
            if len(rooms)==1:
                r=rooms[0].split('-')
                if (len(r)>=2):
                    reply="Here is the full name of the room: \n * "+rooms[0]
                    message_type="text"
                    # stats(post_data['data']['personEmail'],post_data['data']['roomId'])
                    # log(post_data['data']['personEmail']+" - " +post_data['data']['roomId'],str(text),reply)
                    # send_message_to_room(post_data["data"]["roomId"], reply,message_type)
                    floor=r[0]+'-'+r[1]
                    # #message_type="pdf"
                    reply += " \n <br> \n and the map of the floor: \n <br> \n * "+str(display_map(floor))
            else:
                reply="Do you mean:\n"
                for r in rooms:
                    reply+="* "+r+"\n"
                message_type="text"
        else:
            message_type="text"
    elif text.lower().startswith("image "):
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
    elif text.lower().startswith("plan") or text.lower().startswith("map"):
        # Find the floor
        if text.lower() in ["plan","map"]:
            reply = "Usage of map/plan command is:\n"
            reply += "\tmap/plan command followed by floor name like:\n"
            reply += "\t\tmap SJC05-3\n"        
            reply += "\t\t\tor\n"        
            reply += "\t\tplan ILM-7\n"        
        else:
            floor=text.lower().replace('map ','')
            floor=floor.lower().replace('plan ','')
            pattern = re.compile("^([0-7]+)$")
            m = pattern.match(floor)
            sys.stderr.write("display_map: "+floor+"\n")
            if m:
                # Map and number => ILM
                floor='ILM-'+m.group()
                reply = display_map(floor.upper())
                #message_type="pdf"
            else:
                pattern2 = re.compile("^([a-z0-9 ]+\-[0-9]+)$")
                m2 = pattern2.match(floor)
                if m2:
                    floor=m2.group()
                    reply = display_map(floor.upper())
                    #message_type="pdf"
                else:
                    reply = "No floor is corresponding. Try **map/plan floor_name** or **map/plan floor_name** \n<br>\n <blockquote> with floor_name like ILM-3 or SJC13-3 </blockquote>"
    elif text.lower().startswith("book") or text.lower().startswith("reserve"):
        if text.lower() in ["book","reserve"]:
            reply = "Usage of book/reserve command is:\n"
            reply += "\tbook/reserve command followed by room name like:\n"
            reply += "\t\t reserve ILM-7-HUGO\n"        
            reply += "\t\t\tor\n"        
            reply += "\t\t book SJC13-3-SMILE\n"  
        else:      
            # Find the room name
            end = len(text)
            if text.lower().startswith("book "):
                start = len('book ')
            elif text.lower().startswith("reserve "):
                start = len('reserve ')
            else:
                sys.stderr.write("I don't know how you arrive here ! This is a bug !\n")    
            room_name=text[start:end]
            sys.stderr.write("room_name= "+str(room_name)+"\n")
            reply = book_room(room_name.upper(),post_data['data']["personEmail"].lower(),getDisplayName(post_data['data']["personId"]))
            sys.stderr.write("book_room: "+reply+"\n")
    elif text.lower().startswith('in') or text.lower().startswith('inside') or text.lower().startswith('interieur'):
        if text.lower() in ["in","inside","interieur"]:
            reply = "Usage of in/inside/interieur command is:\n"
            reply += "\t in/inside/interieur command followed by room name like:\n"
            reply += "\t\t in ILM-7-HUGO\n"        
            reply += "\t\t\tor\n"        
            reply += "\t\t inside SJC13-3-SMILE\n"  
        else:      
            inside = text.split()[1].upper()
            if inside.lower().startswith('ilm') :
                reply=display_inside(inside)
                message_type="image"
            else :
                reply = "No Inside View. This feature is available only for ILM building."
    elif text.lower() in ["parking"] :
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
    elif text.lower().startswith('temp '):
        sonde = text.split()[1].upper()
        if (sonde == "ILM-1-GAUGUIN") :
            reply = netatmoOutdoor(sonde)
        else :
            reply = "No Temperature sensors available in this room"
    elif text.lower() == "/stats/":
        if post_data['data']['personEmail'] in admin_list :
            reply=readstats()
        else:
            reply = "##You have no admin rights to view stats##"
    elif text.lower().startswith("/advertise/"):
        if post_data['data']['personEmail'] in admin_list :
            if "html" in message:
                advertise(message["html"].replace("/advertise/","").lstrip().strip(),"html")
            else:
                advertise(text.replace("/advertise/","").lstrip().strip())
            reply=""
        else :
            reply = "##You have no admin rights to advertise##"
    # If nothing matches, send instructions
    else:
        # reply=natural_langage_bot(text.lower())
        # if reply == "":
        #     return reply
        reply="Command not found ! Type help to have the list of existing commands !"
    sys.stderr.write("reply: "+str(reply)+"\n")
    if reply != "":
        stats(post_data['data']['personEmail'],post_data['data']['roomId'])
        log(post_data['data']['personEmail']+" - " +post_data['data']['roomId'],str(text),reply)
        send_message_to_room(post_data["data"]["roomId"], reply,message_type)
        log_message_to_room(log_room_id, post_data['data']['personEmail'], text, reply,message_type)
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

    start, end, results = get_available()
    dispo_list=[r.split(' ')[0] for r in results]
    if room_name in dispo_list or not room_name.startswith('ILM-'):
        print "Room booked is available"

        now = datetime.datetime.now().replace(microsecond=0)
        starttime = (now - datetime.timedelta(minutes=5)).isoformat()
        endtime = (now - datetime.timedelta(minutes=5) + datetime.timedelta(hours=duration)).isoformat()

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
    return message


def log_message_to_room(room_id, author, message, message_reply,message_type="text"):
    spark_u = spark_host + "v1/messages"
    if message_type == "text":
        message_body = {
            "roomId" : room_id,
            "markdown" : "Author: "+author+" <br> Request: "+message+" <br> Reply: "+message_reply
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
    else:
        name=message_reply[0]
        title=message_reply[1]
        manager=message_reply[2]
        phone=message_reply[3]
        photo=message_reply[4]
        dir_url=message_reply[5]
        tmp="Author: "+author+" <br>\n Request: "+message+" <br>\n Reply: <br>\n "

        if name!= "":
            tmp+="Name: "+str(name)+'\n'
        if title != "":
            tmp+='Title: '+str(title)+'\n'
        if manager != "":
            tmp+='Manager: '+str(manager)+'\n'
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
    else:
        name=message[0]
        title=message[1]
        manager=message[2]
        phone=message[3]
        photo=message[4]
        dir_url=message[5]
        tmp=""
        if name!= "":
            tmp+="Name: "+str(name)+'\n'
        if title != "":
            tmp+='Title: '+str(title)+'\n'
        if manager != "":
            tmp+='Manager: '+str(manager)+'\n'
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

    corr_id=None
    response=None
    connection=None
    channel=None
    callback_queue=None

    app.run(debug=True, host='0.0.0.0', port=int("5000"))
