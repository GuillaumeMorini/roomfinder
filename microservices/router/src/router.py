#!/usr/bin/env python2.7

from flask import Flask, request, Response
import pika, os, json, uuid, requests, sys

app = Flask(__name__)

def on_response(ch, method, props, body):
    global corr_id
    global response
    if corr_id == props.correlation_id:
        response = body.replace("'",'"').replace('u"','"')
        sys.stderr.write('Response received: '+str(response)+'\n')
        return json.loads(response)
    else:
        return None

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
    corr_id = str(uuid.uuid4())
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

@app.route('/', methods=["POST"])
def index():    
    post_data = request.get_json()
    message = json.dumps(post_data)  
    reply=send_message_to_queue(message)
    return reply

if __name__ == '__main__':
    # Get MQ environment parameters to connect to RabbitMQ servers
    rabbitmq = os.getenv("RABBITMQ_HOSTNAME")
    if (rabbitmq == None):
        rabbitmq = "rabbitmq"

    rabbitmq_port = os.getenv("RABBITMQ_PORT")
    if (rabbitmq_port == None):
        rabbitmq_port = "5672"

    # Initialize MQ variables
    corr_id=None
    response=None
    connection=None
    channel=None
    callback_queue=None

    # Launch Flask web server
    app.run(debug=True, host='0.0.0.0', port=int("5000"))
