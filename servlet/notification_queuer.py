from datetime import datetime, timedelta
import pw_client

__author__ = 'sxh112430'

from threading import Thread
import time
import base64
import sys
import os
sys.path.append('mlibs') # for non-ide usage

from gmail.message import Message
from gmail.gmail import GMail
from pw_client import PWClient

import logging
logger = logging.getLogger("notification_queuer")
handler = logging.FileHandler('notification_queuer.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

USERNAME = os.environ['PWUSER']
PASS = os.environ['PWPASS']
pwc = PWClient(USERNAME, PASS)

class MinuteTicker:
    def __init__(self):
        self.abort = False
        self.beige_watches = {}
    def on_minute_do(self):
        while not self.abort:
            try:
                now = datetime.now()
                seconds_til_next_minute = 65 - now.second # go on :05 of each minute
                logger.debug("waiting "+str(seconds_til_next_minute)+" seconds")
                time.sleep(seconds_til_next_minute)

                # now do stuff
                pnw_time = pwc.get_current_date_in_datetime()

                removal_list = []
                try:
                    for key in self.beige_watches.keys():
                        nation = pwc.get_nation_obj_from_ID(key, skip_cache=True)
                        if nation.color != "Beige":
                            for recipient in self.beige_watches[key]:
                                try:
                                    send_email(recipient, "Nation "+str(key)+" has left beige!", "Warning! A nation on your watchlist has left beige! Link to nation: http://politicsandwar.com/nation/id="+str(key))
                                except Exception as e:
                                    logger.error(e)
                                    print e
                                finally:
                                    if key not in removal_list:
                                        removal_list.append(key)
                        else: # nation is still biege, run calc
                            pwc.calculate_beige_exit_time()
                            pass
                finally:
                    for to_remove in removal_list:
                        del self.beige_watches[to_remove]
            except Exception as e:
                logger.error(e)
                print e

minute_ticker = MinuteTicker()
t = Thread(target=minute_ticker.on_minute_do)
t.start()

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

@app.route('/add_beige_watch/<watcher_email>/<nation_id>/')
def add_beige_watch(watcher_email, nation_id):
    try:
        if nation_id in minute_ticker.beige_watches.keys():
            minute_ticker.beige_watches[nation_id].append(watcher_email)
        else:
            minute_ticker.beige_watches[nation_id] = [watcher_email]
    except Exception as e:
        print e
    return "ok"

def wait_to_mail(to, subject, body, time_to_wait):
    time_to_wait = int(time_to_wait)
    log("New in queue: message:",to,"/",subject,"/",body)
    while time_to_wait > 100:
        time.sleep(100)
        time_to_wait -= 100
        log("message:",to,"/",subject,"/",body,"/ still waiting:")
        log("\t",time_to_wait,"seconds")
    time.sleep(time_to_wait)
    now = datetime.now()
    body += "\n\nToday's date is: "+str(now.month)+"/"+str(now.day)+"/"+str(now.year)+" at "+str(now.hour)+":"+str(now.minute)
    log("Sending email NOW!",to,subject, body)
    send_email(to, subject, body)

def send_email(to, subject, html):
    b64_un = 'Y2hhcm1pbmcuZnJpZW5kcy5wbnc=\n'
    b64_pass = 'bWUydGhhbmtz\n'
    m = GMail(base64.decodestring(b64_un), base64.decodestring(b64_pass))
    m.connect()
    message = Message(subject, to=to, text=html)
    m.send(message)
    print "sending", to, subject, html
    m.close()

def log(*args):
    logstring = ""
    for arg in args:
        logstring += " " +str(arg)
    logger.debug(logstring)

if __name__ == '__main__':
    app.run(host='0.0.0.0')