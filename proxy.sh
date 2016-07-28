#!/bin/sh

if ping -c 1 www.ovh.fr ; then
    echo "direct internet doing nothing"
else
    echo "proxy environment detected setting proxy"
    export http_proxy=http://173.38.209.12:80 \
  && export https_proxy=http://173.38.209.12:80 \
  && export no_proxy=10*,*.cisco.com,192.168.*,172.*
fi

