import os
from datetime import timedelta, datetime
from functools import update_wrapper
from flask import Flask, jsonify, request, make_response
from flask.templating import render_template
from market import get_long_short_term_averages, realstring_dict
from pw_client import LeanPWDB
from pw_client import PWClient

__author__ = 'shawkins'

app = Flask(__name__)


# needed since api.gitsubmit is a different domain than gitsubmit
def crossdomain(app=None, origin=None, methods=None, headers='Origin, X-Requested-With, Content-Type, Authorization, Accept',
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
            h['Access-Control-Expose-Headers'] = 'is_tree'
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator
@app.route('/')
@crossdomain(app=app, origin='*', methods=["GET"])
def hw():
    return "welcome to the dashboard api, nerd. this doesn't do anything. what are you doing here? get out."


@app.route('/graph_data/market/days=<int:days>/')
@crossdomain(app=app, origin='*', methods=["GET"])
def market_data(days):
    pwdb = LeanPWDB()
    total_minutes = days * 24 * 60
    num_records = total_minutes / 5
    long_term_averages, short_term_averages = get_long_short_term_averages(pwdb)
    long_term_averages = long_term_averages[-num_records:]
    short_term_averages = short_term_averages[-num_records:]
    last_record = long_term_averages[-1]
    types = realstring_dict.keys()
    return jsonify({"long_term_averages": long_term_averages, "short_term_averages": short_term_averages,
                    "last": last_record, "types": types})


@app.route('/defendability/')
@crossdomain(app=app, origin='*', methods=["GET"])
def defendability():
    pwdb = LeanPWDB()
    latest_list = pwdb.get_latest_nation_cache_list()
    nations_out = []
    avg_def_factor = 0
    avg_mil_percent = 0
    for nation in latest_list["nations"]:
        def_factor = nation["defendability_factor"]
        avg_def_factor += def_factor
        avg_mil_percent += nation["percent_score_military"]

        action_priority = nation["action_priority"]

        most_recent_city_founded_string = nation['cities'][-1]['founded']
        most_recet_datetime = datetime.strptime(most_recent_city_founded_string, "%Y-%m-%d")
        now = datetime.now()
        days_since_built = (now - most_recet_datetime).days
        obj_out = {'name': nation["name"],
                   'id': nation["nation_id"],
                   'score': nation["score"],
                   'num_cities': len(nation['cities']),
                   'days_since_last_built': days_since_built,
                   'percent_military_score': nation["percent_score_military"],
                   'def_factor': def_factor,
                   'action_priority': action_priority}

        nations_out.append(obj_out)
    avg_def_factor /= float(len(latest_list["nations"]))
    avg_mil_percent /= float(len(latest_list["nations"]))
    return jsonify({"list": nations_out, "avg_def_factor": avg_def_factor,
                    "avg_mil_percent": avg_mil_percent})


@app.route('/resource_pulse/')
@crossdomain(app=app, origin='*', methods=["GET"])
def rsc_pulse():
    USERNAME = os.environ['PW_USER']
    PASS = os.environ['PW_PASS']

    pwc = PWClient(USERNAME, PASS)
    trade_nums = {}
    for item_type in realstring_dict.keys():
        item_value = realstring_dict[item_type]
        trade_url = "https://politicsandwar.com/index.php?id=90&display=world&resource1="+item_value+"&buysell=buy&ob=price&od=DESC&maximum=15&minimum=0&search=Go"
        nationtable = pwc._retrieve_nationtable(trade_url, 0)
        trade_tr = nationtable.findall(".//tr")[1]
        trade_td = trade_tr.findall(".//td")[5]
        trade_text = trade_td[0].text
        trade_num = int(trade_text.split("/")[0].replace(",",""))
        trade_nums[item_type] = trade_num

    pwdb = LeanPWDB()
    latest_list = pwdb.get_latest_nation_cache_list()
    nations_out = []
    for nation in latest_list["nations"]:
        resource_only = 0
        for item_type in realstring_dict.keys():
            item_value = realstring_dict[item_type]
            trade_num = trade_nums[item_type]
            change = trade_num * nation["net_resource_production_ignore_power"][item_value]
            resource_only += change
        nation["resource_only_income"] = resource_only
        nation["resource_only_income"] -= nation["total_resource_spending"]
        obj_out = {'name': nation["name"],
                   'id': nation["nation_id"],
                   'score': nation["score"],
                   'num_resource_improvements': nation["num_resource_improvements"],
                   'resource_only_income': round(nation["resource_only_income"], 2),
                   'commerce_only_income': round(nation["commerce_only_income"], 2),
                   'all_income': round(nation["resource_only_income"] + nation["simple_net_income"] + nation["total_resource_spending"], 2),
                   'rev_factor': round(nation["resource_only_income"] / nation["num_resource_improvements"], 2)}
        nations_out.append(obj_out)
    return jsonify({"list": nations_out})


@app.route('/dashboard_beta/')
def dashboard_beta():
    return render_template('pages/index.html')

app.debug = True
if __name__ == "__main__":
    app.run("0.0.0.0", 8091)
