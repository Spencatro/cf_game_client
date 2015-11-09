from flask import Flask, jsonify, request
import sys

__author__ = 'shawkins'

app = Flask(__name__)
app.debug = True  # TODO: unset this after release!


@app.route('/', methods=['POST'])
def hello_world():
    print request.form
    sys.stderr.write(request.form)
    return jsonify({"text": "hello, human"})