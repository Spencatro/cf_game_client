from flask import Flask, jsonify
from market_watch import get_long_short_term_averages

__author__ = 'shawkins'

app = Flask(__name__)

@app.route('/')
def hw():
    return "welcome to the dashboard api. this doesn't do anything. what are you doing here? get out."

@app.route('/graph_data/market/days=<days>')
def market_data(days):
    long_term_averages, short_term_averages = get_long_short_term_averages()
    return jsonify({"long_term_averages": long_term_averages, "short_term_averages": short_term_averages})