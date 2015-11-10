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
    return jsonify({"text": "Sorry, my human teacher is still teaching me that one!"})


def watch_my_war(slack_uid, action):
    return jsonify({"text": "I'm afraid I haven't been taught how to do that yet :("})


def show_pipeline(action):
    return jsonify({"text": "Sorry, I'm still learning how to do that one!"})


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