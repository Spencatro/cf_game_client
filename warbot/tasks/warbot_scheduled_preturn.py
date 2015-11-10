"""
This task should run about 5 minutes before the turn changes. It should occur extremely quickly, so there's no
chance of it getting interrupted by a turn (and doesn't care anyways)
"""

import json
import logging
import os
from pw_client import PWClient
from slack import pm_user_from_warbot
from warbot.warbotlib.warbot_db import WarbotDB

__author__ = 'shawkins'

wardb = WarbotDB()
logger = logging.getLogger("pwc")
fhandler1 = logging.FileHandler("preturn.out", mode='w')
logger.addHandler(fhandler1)
logger.setLevel(logging.DEBUG)

USERNAME = os.environ['PW_USER']
PASS = os.environ['PW_PASS']
pwc = PWClient(USERNAME, PASS, logger=logger)

for record in wardb.beige_checks.find({"state": "notify"}):
    test_attachment = {
        "color": "#2883BD",
        "text": "Nation "+str(record["nation_id"]) + " (" + record["nation_name"]+") is about to leave beige!\n",
        "title": "PNW: "+record["nation_name"],
        "title_link": "https://politicsandwar.com/nation/id="+str(record["nation_id"])
    }
    pm_user_from_warbot(record["requesting_user_slack_id"], "Beige watch notification", attachments=json.dumps([test_attachment]))
