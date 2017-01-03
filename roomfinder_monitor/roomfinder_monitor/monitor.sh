#!/bin/bash

TMP=/tmp/docker_list

echo "$IPADDR     $WEB_URL" >> /etc/hosts

while true
do
	curl -s $DATA_URL > /dev/null 2>&1
	if [ $? -ne 0 ]
	then
	  echo "data is not working" 
	  echo "data is not working" | mail -s "$EMAIL_SUBJECT" $TO_EMAIL_ADDRESS
	else
		curl -s $WEB_URL > /dev/null 2>&1
		if [ $? -ne 0 ]
		then
		  echo "web is not working" 
		  echo "web is not working" | mail -s "$EMAIL_SUBJECT" $TO_EMAIL_ADDRESS
		fi
		curl -s $BOOK_URL > /dev/null 2>&1
		if [ $? -ne 0 ]
		then
		  echo "book is not working" 
		  echo "book is not working" | mail -s "$EMAIL_SUBJECT" $TO_EMAIL_ADDRESS
		fi
		curl -s $SPARK_URL > /dev/null 2>&1
		if [ $? -ne 0 ]
		then
		  echo "spark is not working" 
		  echo "spark is not working" | mail -s "$EMAIL_SUBJECT" $TO_EMAIL_ADDRESS
		fi
		docker ps | grep roomfinder > $TMP
		for c in $CONTAINER_LIST
		do
			grep $c $TMP
			if [ $? -ne 0 ]
			then
		  		echo "$c is not working" 
		  		echo "$c is not working" | mail -s "$EMAIL_SUBJECT" $TO_EMAIL_ADDRESS
			fi
		done
	fi
	sleep 30
done
