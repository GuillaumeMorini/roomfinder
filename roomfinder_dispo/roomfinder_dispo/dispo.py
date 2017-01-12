#!/usr/bin/env python2.7

import sys
reload(sys)
sys.setdefaultencoding("utf-8")
from flask import Flask, render_template, request, jsonify
import argparse
import datetime
import os, sys
import requests
from socket import error as SocketError
import errno
import json
import pika  
import uuid

app = Flask(__name__)

@app.route("/book", methods=["GET"])
def book():
    starttime=request.args.get('starttime', '')
    endtime=request.args.get('endtime', '')
    user_name=request.args.get('user_name', '')
    user_email=request.args.get('user_email', '')
    room_name=request.args.get('room_name', '')

    if starttime is None or endtime is None or user_name is None or user_email is None or room_name is None:
        return "no parameter provided to book request\n"
    data = {  
            "cmd": "book",         
            "data": {"starttime": starttime, "endtime": endtime, "user_name": user_name, "user_email": user_email, "room_name": room_name}
    }    
    message = json.dumps(data)  
    return send_message_to_queue(message)



@app.route("/dispo", methods=["GET"])
def dispo():
    key=request.args.get('key', '')
    sys.stderr.write( "key: "+str(key)+'\r\n')
    if key is not None and str(key) is not "":
        data = {  
            "cmd": "dispo",         
            "data": {"key": key}
        }    
        message = json.dumps(data)  
        return send_message_to_queue(message)
    return "no parameter provided to dispo request\n"

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
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq,port=int(rabbitmq_port),heartbeat_interval=30))  
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
    return response    



if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser("Room Finder Dispo Service")
    parser.add_argument("-r","--rabbitmq", help="IP or hostname for rabbitmq server, e.g. 'rabbit.domain.com'.")
    parser.add_argument("-p","--port", help="tcp port for rabitmq server, e.g. '2765'.")
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


    try:
    	app.run(debug=True, host='0.0.0.0', port=int("5000"))
    except:
    	try:
    		app.run(debug=True, host='0.0.0.0', port=int("5000"))
    	except:
    		print "Dispo web services error"
