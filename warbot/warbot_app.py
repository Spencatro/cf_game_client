from flask import Flask, jsonify, request
import os
import re

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


def verify_token(token):
    if token != os.environ.get("incoming_slack_token"):
        pass


def remove_trigger(trigger, text):
    text = text.lower()
    trigger = trigger.lower()
    return text[text.index(trigger) + len(trigger) + 1:]


def notify_end_of_beige(slack_uid, action):
    pass


def watch_my_war(slack_uid, action):
    pass


def show_pipeline(action):
    pass


def get_help(action):

    helpstring = "Currently available commands:\n" \
                 "Help: shows this message! Examples:" \
                 "      'Warbot, help me!'" \
                 "      'Warbot, help'" \
                 "War notifier: notifies you when you will have enough points in a war for a ground battle. Examples:" \
                 "      'Warbot, notify me about war [war id number]'" \
                 "      'Warbot, war [war id number]'" \
                 "Beige watcher: notifies you when a certain nation is about to leave beige. Examples:" \
                 "      'Warbot, tell me when beige ends for [nation id number]'" \
                 "      'Warbot, tell me when I can fight [nation id number]'" \
                 "      'Warbot, beige [nation id number]'" \
                 "Show pipeline: shows nations in the current pipeline. Examples:" \
                 "      'Warbot, show me the pipeline'" \
                 "      'Warbot, pipeline'"

    return jsonify({"text": helpstring})


@app.route('/', methods=['POST'])
def hello_world():
    token = request.form.get("token")
    verify_token(token)
    originating_user_id = request.form.get("user_id")
    message_body = request.form.get("text")
    trigger = request.form.get("trigger_word")

    action = remove_trigger(trigger, message_body)
    if END_OF_BEIGE.match(action):
        return notify_end_of_beige(originating_user_id, action)
    elif WATCH_MY_WAR.match(action):
        return watch_my_war(originating_user_id, action)
    elif SHOW_ME_THE_PIPELINE.match(action):
        return show_pipeline(action)
    elif HELP.match(action):
        return get_help(action)

    return jsonify({"text": "I didn't understand that request, ask me for help if you need it!"})