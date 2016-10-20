#!/bin/sh

#curl -sLO "http://downloads.sourceforge.net/project/proxytunnel/proxytunnel%20source%20tarballs/proxytunnel%201.9.0/proxytunnel-1.9.0.tgz"
#tar xzvf proxytunnel-1.9.0.tgz
#cd proxytunnel-1.9.0
#make
#cd ..
echo "Running ./proxytunnel -a 5672 -p proxy-wsa.esl.cisco.com:80 -d $roomfinder_rabbitmq_server:$roomfinder_rabbitmq_port &"
./proxytunnel -a 5672 -p proxy-wsa.esl.cisco.com:80 -d $roomfinder_rabbitmq_server:$roomfinder_rabbitmq_port &
exec python ./roomfinder_router/router.py