import random,string,os,datetime,base64
import jinja2 
def id_generator(size=114, chars='ABCDEF' + string.digits):
	return ''.join(random.choice(chars) for _ in range(size))

def render(tpl_path, context):
    path, filename = os.path.split(tpl_path)
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(path or './')
    ).get_template(filename).render(context)

uid=id_generator()
time=datetime.datetime.now().replace(microsecond=0).isoformat().replace('-','').replace(':','')+'Z'
name='Franck Bonneau'
cco='fbonneau'
email='fbonneau@cisco.com'
# room_name='ILM-5-BEAUBOURG (16) Video (2-Screen)(Public)'
# room_email='CONF_7992@cisco.com'
room_name='Remy Cronier (rcronier)'
room_email='rcronier@cisco.com'
tz_name='Central European Standard Time'
start_time=datetime.datetime.now().replace(microsecond=0).isoformat().replace('-','').replace(':','')
end_time=(datetime.datetime.now()+ datetime.timedelta(hours=2)).replace(microsecond=0).isoformat().replace('-','').replace(':','')

context = {
    'uid': uid,
    'time': time,
    'name': name,
    'cco': cco,
    'email': email,
    'room_name': room_name,
    'room_email': room_email,
    'tz_name': tz_name,
    'start_time': start_time,
    'end_time': end_time
}

result = render('./invite.j2', context)
#print (result)

import smtplib

def prompt(prompt):
    return input(prompt).strip()

fromaddr = email
fromlong = "\""+name+" ("+cco+")\" <"+email+">"
toaddrs  = room_email
tolong   = "\""+room_name+"\" <"+room_email+">"
ccaddrs  = 'gmorini@cisco.com'
cclong  = '\"Guillaume Morini (gmorini)\" <gmorini@cisco.com>'
subject  = name + "'s Meeting"
# Add the From: and To: headers at the start!

marker = "AUNIQUEMARKER"
body = """
Reserved by Roomfinder
"""
encodedcontent = base64.b64encode(str.encode(result))

part0 = """From: %s
To: %s
CC: %s
Subject: %s
Date: %s
""" % (fromlong,tolong,cclong,subject,datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000"))



part1 = """Content-Language: en-US
Content-Type: multipart/mixed; boundary=%s
MIME-Version: 1.0

--%s
""" % (marker, marker)

# Define the message action
part2 = """Content-Type: text/plain

%s

--%s
""" % (body,marker)

# Define the attachment section
part3 = """Content-Type: text/calendar; charset="utf-8"; method=REQUEST
Content-Transfer-Encoding: base64

%s

--%s--
""" %(encodedcontent.decode(), marker)
msg = part0 + part1 + part2 + part3

print("Message length is", len(msg))
print("Mesage is\n\n"+msg)




server = smtplib.SMTP('mail.cisco.com')
server.set_debuglevel(1)
server.sendmail(fromaddr, [toaddrs,ccaddrs], msg)
server.quit()