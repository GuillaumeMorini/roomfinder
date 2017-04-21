#!/usr/bin/env python2.7

import pika, os, sys, json, requests
import base64, urllib, unicodedata, re

def on_request(ch, method, props, body):
    sys.stderr.write(" [x] Received %r\n" % body)
    #sys.stderr.write("Method: {}\n".format(method))     
    #sys.stderr.write("Properties: {}\n".format(properties))     
    data = json.loads(body)
    cmd=data['cmd']
    request_data=data["data"]
    sys.stderr.write("Command: {}\n".format(cmd))     
    sys.stderr.write("Data: {}\n".format(request_data))      

    if cmd == "test":
        txt="reply message for MQ"
    elif cmd == "dir":
        pass
    else:
        pass

    ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(correlation_id = \
                                                         props.correlation_id),
                     body=str(txt))
    ch.basic_ack(delivery_tag = method.delivery_tag)
    return txt

if __name__ == '__main__':
    rabbitmq = os.getenv("RABBITMQ_HOSTNAME")
    if (rabbitmq == None):
        rabbitmq = "localhost"

    rabbitmq_port = os.getenv("RABBITMQ_PORT")
    if (rabbitmq_port == None):
        rabbitmq_port = "5672"

    sys.stderr.write("Connecting to "+rabbitmq+" on port "+rabbitmq_port+"\n")
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host=rabbitmq, port=int(rabbitmq_port) ))
    channel = connection.channel()
    channel.queue_declare(queue='rpc_queue')
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(on_request, queue='rpc_queue')
    sys.stderr.write(' [*] Waiting for messages. To exit press CTRL+C\n')
    channel.start_consuming()
