#!/usr/bin/env python2.7

import pika, os, sys, json, requests

def on_request(ch, method, properties, body):
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
        pass
    elif cmd == "sr":
        pass
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

    sys.stderr.write("Connecting to "+rabbitmq+" on port "+rabbitmq_port+"\n")
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host="localhost" ))
    channel = connection.channel()
    channel.queue_declare(queue='rpc_queue')
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(on_request, queue='rpc_queue')
    sys.stderr.write(' [*] Waiting for messages. To exit press CTRL+C\n')
    channel.start_consuming()

