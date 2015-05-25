from datetime import datetime

__author__ = 'sxh112430'

from threading import Thread
import time
import base64
import sys
sys.path.append('mlibs') # for non-ide usage

from gmail.message import Message
from gmail.gmail import GMail

import logging
logger = logging.getLogger("notification_queuer")
handler = logging.FileHandler('notification_queuer.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/queue_n/<to>/<subject>/<body>/<time>/')
def queue_n(to, subject, body, time):
    t = Thread(target = lambda: wait_to_mail(to, subject, body, time))
    t.start()
    return "Notification queued to "+to+" in "+time

def wait_to_mail(to, subject, body, time_to_wait):
    time_to_wait = int(time_to_wait)
    while time_to_wait > 100:
        time_to_wait -= 100
        log("message:",to,"/",subject,"/",body,"/ still waiting:")
        log("\t",time_to_wait,"seconds")
        time.sleep(100)
    time.sleep(time_to_wait)
    now = datetime.now()
    body += "\n\nToday's date is: "+str(now.month)+"/"+str(now.day)+"/"+str(now.year)+" at "+str(now.hour)+":"+str(now.minute)
    log("Sending email NOW!",to,subject, body)
    send_email(to, subject, body)

def send_email(to, subject, body):
    b64_un = 'Y2hhcm1pbmcuZnJpZW5kcy5wbnc=\n'
    b64_pass = 'bWUydGhhbmtz\n'
    m = GMail(base64.decodestring(b64_un), base64.decodestring(b64_pass))
    m.connect()
    message = Message(subject, to=to, text=body)
    m.send(message)
    m.close()

def log(*args):
    logstring = ""
    for arg in args:
        logstring += " " +str(arg)
    logger.debug(logstring)

if __name__ == '__main__':
    app.run()