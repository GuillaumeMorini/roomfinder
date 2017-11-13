#!/usr/bin/env python2.7

import sys

reload(sys)
sys.setdefaultencoding("utf-8")
from flask import Flask, render_template, request
import datetime
import os, sys
import requests

app = Flask(__name__, static_folder='static')


@app.route('/')
def index():
    u = data_server + "/"
    try:
        page = requests.get(u)
        options = page.json()
        room_list = options
    except:
        try:
            page = requests.get(u)
            options = page.json()
            room_list = options
        except:
            room_list = (("Temporary unavailable !"), ())
    return render_template('home.html', room_list=room_list,
                           title="Room Finder Web Application",
                           current_time=datetime.datetime.now(),
                           book_url=book_url)


@app.route("/about")
def about():
    return render_template('about.html', title="About", current_time=datetime.datetime.now())


@app.route("/form")
def form():
    return render_template('form.html',
                           title="Add yourself to the Cisco Spark room",
                           current_time=datetime.datetime.now())


@app.route("/add", methods=["POST"])
def add():
    status = 200
    if request.method == "POST":
        email = request.form['email']
        try:
            page = requests.post(spark_server + '/demoroom/members', data={'email': email})
            options = page.json()
            sys.stderr.write("reply: " + str(options) + "\n")
            return render_template('added.html', email=email)
        except KeyError:
            return render_template('error.html', email=email)


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser("Room Finder Web Service")
    parser.add_argument(
        "-d", "--data", help="Address of data server", required=False
    )
    parser.add_argument(
        "-s", "--spark", help="Address of Spark bot server", required=False
    )
    parser.add_argument(
        "-b", "--book", help="Address of book room server", required=False
    )
    args = parser.parse_args()

    data_server = args.data
    # print "Arg Data: " + str(data_server)
    if (data_server == None):
        data_server = os.getenv("roomfinder_data_server")
        # print "Env Data: " + str(data_server)
        if (data_server == None):
            get_data_server = raw_input("What is the data server address? ")
            # print "Input Data: " + str(get_data_server)
            data_server = get_data_server

    # print "Data Server: " + data_server
    sys.stderr.write("Data Server: " + data_server + "\n")

    book_url = args.book
    if (book_url == None):
        book_url = os.getenv("roomfinder_book_server")
        if (book_url == None):
            get_book_url = raw_input("What is the book server address? ")
            # print "Input Data: " + str(get_data_server)
            book_url = get_book_url

    sys.stderr.write("Book Server: " + book_url + "\n")

    spark_server = args.spark
    # print "Arg Data: " + str(data_server)
    if (spark_server == None):
        spark_server = os.getenv("roomfinder_spark_server")
        # print "Env Data: " + str(data_server)
        if (spark_server == None):
            get_spark_server = raw_input("What is the Cisco Spark bot server address? ")
            # print "Input Data: " + str(get_data_server)
            spark_server = get_spark_server

    # print "Data Server: " + data_server
    sys.stderr.write("Spark bot Server: " + spark_server + "\n")

    try:
        app.run(host='0.0.0.0', port=int("5000"))
    except:
        try:
            app.run(host='0.0.0.0', port=int("5000"))
        except:
            print "Web server error"
