from datetime import timedelta
from functools import update_wrapper
from flask import Flask, jsonify, request, make_response
from market import get_long_short_term_averages
from pw_client import LeanPWDB

__author__ = 'shawkins'

app = Flask(__name__)


def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator

@crossdomain('*')
@app.route('/')
def hw():
    return "welcome to the dashboard api. this doesn't do anything. what are you doing here? get out."

@crossdomain('*')
@app.route('/graph_data/market/days=<int:days>')
def market_data(days):
    pwdb = LeanPWDB()
    total_minutes = days * 24 * 60
    num_records = total_minutes / 5
    long_term_averages, short_term_averages = get_long_short_term_averages(pwdb, num_records)
    return jsonify({"long_term_averages": long_term_averages, "short_term_averages": short_term_averages})

if __name__=="__main__":
    app.run("0.0.0.0", 8090)