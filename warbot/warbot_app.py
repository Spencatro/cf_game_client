from flask import Flask, jsonify

__author__ = 'shawkins'

app = Flask(__name__)
app.debug = True  # TODO: unset this after release!


@app.route('/', methods=['POST'])
def hello_world():
    return jsonify({"text": "hello, human"})