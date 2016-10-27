#!/usr/bin/env python2.7

import pika, os, sys, json, requests

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
        sys.stderr.write("Request directory entry in %s\n" % dir_server)  
        print "dir_server: "+dir_server
        print "photo_server: "+photo_server

        u = dir_server + cco
        try:
            page = requests.get(u)
        except requests.exceptions.ConnectionError:
            return "Connection error to directory server"
        try: 
            from BeautifulSoup import BeautifulSoup
        except ImportError:
            from bs4 import BeautifulSoup
        html = page.text
        parsed_html = BeautifulSoup(html)
        name=parsed_html.body.find('span', attrs={'class':'name'})
        sys.stderr.write("name: "+str(name)+"\n")
        if not hasattr(name, 'text'):
            return "CCO id not found !"
        else:
            title=parsed_html.body.find('span', attrs={'class':'title'})
            sys.stderr.write("title: "+str(title)+"\n")
            manager=parsed_html.body.find('a', attrs={'class':'hover-link'})
            sys.stderr.write("manager: "+str(manager)+"\n")
            
            u = photo_server + cco + ".jpg"
            txt=""
            with open('/app/output.jpg', 'wb') as handle:
                response = requests.get(u, stream=True)
                if response.ok:
                    for block in response.iter_content(1024):
                        handle.write(block)    
                txt=name.text+";"+title.text+";"+manager.text+";"+"/app/output.jpg"+";"+"<a href=\"http://wwwin-tools.cisco.com/dir/details/"+cco+"\">directory link</a>"
        sys.stderr.write("txt: {}\n".format(txt))    
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
    parser.add_argument(
        "-d", "--dir", help="Address of directory server", required=False
    )
    parser.add_argument(
        "-i", "--photo", help="Address of photo directory server", required=False
    )
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

    photo_server = args.photo
    # print "Arg Photo: " + str(photo_server)
    if (photo_server == None):
        photo_server = os.getenv("roomfinder_photo_server")
        # print "Env Photo: " + str(photo_server)
    # print "Photo Server: " + photo_server
    sys.stderr.write("Directory Photo Server: " + str(photo_server) + "\n")

    sys.stderr.write("Connecting to "+rabbitmq+" on port "+rabbitmq_port+"\n")
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host="localhost" ))
    channel = connection.channel()
    channel.queue_declare(queue='rpc_queue')
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(on_request, queue='rpc_queue')
    sys.stderr.write(' [*] Waiting for messages. To exit press CTRL+C\n')
    channel.start_consuming()

