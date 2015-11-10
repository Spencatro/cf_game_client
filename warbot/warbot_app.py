import logging
from flask import Flask, jsonify, request
import os
import re
from pw_client import PWClient
from warbot.warbotlib.warbot_db import WarbotDB

__author__ = 'shawkins'

app = Flask(__name__)
app.debug = True  # TODO: unset this after release!


class Matcher(object):

    def __init__(self, patterns, description, arguments_string, text_prefix):
        pattern_string = "".join([".*" + term + ".*|" for term in patterns])[:-1]
        self.regex = re.compile(pattern_string)
        self.helpstring = description + "\nMatching terms: "+text_prefix+"\n"
        for term in patterns:
            self.helpstring += "    - "+term+" "+arguments_string+"\n"

END_OF_BEIGE = re.compile(".*beige.*|.*i can fight.*")
SHOW_ME_THE_PIPELINE = re.compile(".*pipeline.*")
WATCH_MY_WAR = re.compile(".*war.*|.*points.*")
HELP = re.compile(".*help.*")
REGISTER = re.compile(".*register.*")
WHO_IS_NATION = re.compile(".*who is nation.*")
WHO_IS_USER = re.compile(".*who is user.*")

wardb = WarbotDB()
logger = logging.getLogger("pwc")
fhandler1 = logging.FileHandler("warbot_app.out", mode='w')
logger.addHandler(fhandler1)
logger.setLevel(logging.DEBUG)

USERNAME = os.environ['PW_USER']
PASS = os.environ['PW_PASS']
pwc = PWClient(USERNAME, PASS, logger=logger)


def verify_token(token):
    if token != os.environ.get("incoming_slack_token"):
        pass


def remove_trigger(trigger, text):
    text = text.lower()
    trigger = trigger.lower()
    return text[text.index(trigger) + len(trigger) + 1:]


def notify_end_of_beige(slack_uid, slack_username, action):
    nation_ids = [int(s) for s in action.split() if s.isdigit()]
    nations_added = []
    not_in_beige = []
    for nation_id in nation_ids:
        try:
            nation = pwc.get_nation_obj_from_ID(nation_id)
        except:
            continue
        if nation.beige_turns_left is not None:
            wardb.create_personal_beige_watch_record(slack_uid, nation_id, nation.name, nation.beige_turns_left)
            nations_added.append(nation.name)
        else:
            not_in_beige.append(nation.name)
    if len(nations_added) > 0:
        text = "OK, " + str(slack_username) + ", I'll notify you when " + ", ".join(nations_added) + " leaves beige"
    else:
        text = "I didn't find any nations to add in your query! Try `warbot help` if you need!"
    if len(not_in_beige) > 0:
        text += "\nbtw, it looks like " + ", ".join(not_in_beige) + " aren't in beige ya dingus"

    return jsonify({"text": text})


def watch_my_war(slack_uid, slack_username, action):
    return jsonify({"text": "I'm afraid I haven't been taught how to do that yet :("})


def show_pipeline(action):
    return jsonify({"text": "Sorry, I'm still learning how to do that one!"})


def register_user(slack_uid, slack_username, action):

    nation_ids = [int(s) for s in action.split() if s.isdigit()]
    if len(nation_ids) != 1:
        return error_message()
    nation_id = nation_ids[0]

    nation_obj = pwc.get_nation_obj_from_ID(nation_id)
    name = nation_obj.name

    wardb.update_user_map(slack_uid, slack_username, nation_id, name)


def get_help(action):
    helpstring = "Currently available commands:\n" \
                 "Help: shows this message! Examples:\n" \
                 "      `Warbot, help me!`\n" \
                 "      `Warbot, help`\n" \
                 "War notifier: notifies you when you will have enough points in a war for a ground battle. Examples:\n" \
                 "      `Warbot, notify me about war [war id number]`\n" \
                 "      `Warbot, war [war id number]`\n" \
                 "Beige watcher: notifies you when a certain nation is about to leave beige. Examples:\n" \
                 "      `Warbot, tell me when beige ends for [nation id number]`\n" \
                 "      `Warbot, tell me when I can fight [nation id number]`\n" \
                 "      `Warbot, beige [nation id number]`\n" \
                 "Show pipeline: shows nations in the current pipeline. Examples:\n" \
                 "      `Warbot, show me the pipeline`\n" \
                 "      `Warbot, pipeline`\n"

    return jsonify({"text": helpstring})


def who_is_nation(action):
    nation_ids = [int(s.replace("?", "")) for s in action.split() if s.replace("?", "").isdigit()]
    if len(nation_ids) != 1:
        return error_message()
    nation_id = nation_ids[0]
    cursor = wardb.registered_users.find({"nation_id": str(nation_id)})
    if cursor.count() != 1:
        return jsonify({"text": "Sorry, I don't know who "+str(nation_id)+"is"})
    record = cursor.next()
    return jsonify({"text": "Nation "+str(nation_id)+" ("+record["nation_name"]+") is "+record["slack_username"]})


def who_is_user(action):
    last_term = action.split(" ")[-1].replace("?", "")

    cursor = wardb.registered_users.find({"slack_username": str(last_term)})
    if cursor.count() != 1:
        return jsonify({"text": "Sorry, I don't know who "+str(last_term)+"is"})
    record = cursor.next()
    return jsonify({"text": "User "+str(last_term)+" is nation "+record["nation_id"]+" ("+record["nation_name"]+")"})


def error_message():
    return jsonify({"text": "I didn't understand that request, ask me for help if you need it!"})


@app.route('/', methods=['POST'])
def hello_world():
    token = request.form.get("token")
    verify_token(token)
    originating_user_id = request.form.get("user_id")
    originating_user_name = request.form.get("user_name")
    message_body = request.form.get("text").lower()
    trigger = request.form.get("trigger_word").lower()

    action = remove_trigger(trigger, message_body)
    if END_OF_BEIGE.match(action):
        return notify_end_of_beige(originating_user_id, originating_user_name, action)
    elif WATCH_MY_WAR.match(action):
        return watch_my_war(originating_user_id, originating_user_name, action)
    elif SHOW_ME_THE_PIPELINE.match(action):
        return show_pipeline(action)
    elif HELP.match(action):
        return get_help(action)
    elif REGISTER.match(action):
        return register_user(originating_user_id, originating_user_name, action)
    elif WHO_IS_NATION.match(action):
        return who_is_nation(action)
    elif WHO_IS_USER.match(action):
        return who_is_user(action)

    return error_message()


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=8818)