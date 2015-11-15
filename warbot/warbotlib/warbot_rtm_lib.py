import logging
import os
from slack import get_user_id_from_username

__author__ = 'shawkins'

warbot_responds_to = ["warbot", "computer in chief", "warby"]

logger = logging.getLogger("warbot_rtm")
fhandler1 = logging.FileHandler("warbot_app.out", mode='w')
logger.addHandler(fhandler1)
logger.setLevel(logging.DEBUG)

USERNAME = os.environ['PW_USER']
PASS = os.environ['PW_PASS']

def should_act_on_message(data):
    # Don't respond to himself
    warbot_userid = get_user_id_from_username("warbot")
    if str(data["user"]) == str(warbot_userid):
        return False
    # respond to all DM's
    if data["channel"].startswith("D"):
        return True
    text = str(data["text"]).lower().strip()
    any_term_found = False
    for term in warbot_responds_to:
        if text.startswith(term):
            any_term_found = True
            break
    return any_term_found

def error_message(additional_info=None):
    text = "I didn't understand that request, ask me for help if you need it!"
    if additional_info:
        text += "\n    More info: "+additional_info
    return text