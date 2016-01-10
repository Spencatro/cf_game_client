from flask import Flask, jsonify
from market import get_long_short_term_averages
from pw_client import LeanPWDB

__author__ = 'shawkins'

app = Flask(__name__)

@app.route('/')
def hw():
    return "welcome to the dashboard api. this doesn't do anything. what are you doing here? get out."

@app.route('/graph_data/market/days=<days>')
def market_data(days):
    pwdb = LeanPWDB()
    long_term_averages, short_term_averages = get_long_short_term_averages(pwdb)
    return jsonify({"long_term_averages": long_term_averages, "short_term_averages": short_term_averages})

app.run("0.0.0.0", 8090)