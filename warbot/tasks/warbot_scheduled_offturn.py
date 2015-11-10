"""
This task should run very far off-turn (probably not long after the turn has flipped), so that
it has no chance of being caught in the middle of a turn
"""
import json

import logging
import os
from pw_client import PWClient
from slack import pm_user_from_warbot
from warbot.warbotlib.warbot_db import WarbotDB


wardb = WarbotDB()
logger = logging.getLogger("pwc")
fhandler1 = logging.FileHandler("preturn.out", mode='w')
logger.addHandler(fhandler1)
logger.setLevel(logging.DEBUG)

USERNAME = os.environ['PW_USER']
PASS = os.environ['PW_PASS']
pwc = PWClient(USERNAME, PASS, logger=logger)

for record in wardb.beige_checks.find({"state": {"$ne": "error"}}):
    r_id = record["_id"]
    nation_id_to_check = record["nation_id"]
    nation = pwc.get_nation_obj_from_ID(nation_id_to_check)
    if nation.beige_turns_left == 1:
        print "setting target to watch: ", record
        record["state"] = "notify"
        wardb.beige_checks.update({"_id": r_id}, record)
    elif nation.beige_turns_left is None:
        test_attachment = {
            "color": "#A80000",
            "text": "Error occured watching nation "+str(record["nation_id"]) + " (" + record["nation_name"] + ") ..."
                    "\nIt appears they are not in beige. Please notify @spencer about error with record `"+str(record["_id"])+"`\n",
            "title": "PNW: "+record["nation_name"],
            "title_link": "https://politicsandwar.com/nation/id="+str(record["nation_id"])
        }
        pm_user_from_warbot(record["requesting_user_slack_id"], "Beige watch notification", attachments=json.dumps([test_attachment]))
        record["state"] = "error"
        wardb.beige_checks.update({"_id": record["_id"]}, record)