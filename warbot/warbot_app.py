from flask import Flask, jsonify, request
import os

__author__ = 'shawkins'

app = Flask(__name__)
app.debug = True  # TODO: unset this after release!

def verify_token(token):
    if token != os.environ.get("incoming_slack_token"):
        #do something
        pass


def remove_trigger(trigger, text):
    text = text.lower()
    trigger = trigger.lower()
    return text[text.index(trigger) + len(trigger) + 1:]


@app.route('/', methods=['POST'])
def hello_world():
    token = request.form.get("token")
    verify_token(token)
    originating_user_id = request.form.get("user_id")
    message_body = request.form.get("text")
    trigger = request.form.get("trigger_word")

    print remove_trigger(trigger, message_body)

    return jsonify({"text": "hello, human"})