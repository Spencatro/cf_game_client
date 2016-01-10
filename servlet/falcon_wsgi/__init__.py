from datetime import datetime, timedelta
import pprint
import plotly
from plotly.graph_objs import *
import plotly.plotly as py

with open("/var/www/falcon/plotlyauth") as pfile:
    user = pfile.readline().strip()
    pw = pfile.readline().strip()
    plotly.plotly.sign_in(username=user, api_key=pw)

__author__ = 'sxh112430'

import sys
sys.path.append("/var/www/falcon/pnw_stats_finder")
sys.path.append("/var/www/falcon/pnw_stats_finder/servlet/mlibs")
from servlet.falcon_wsgi.falcon.income_tracker import MAX_COLLECTION_TIMEDELTA
from servlet.settings import MAINTENANCE_MODE
from threading import Thread
import time
import base64
import os
from pnw_db import PWDB, owed_key, turns_since_collected_key
from gmail.message import Message
from gmail.gmail import GMail
from pw_client import PWClient, NationDoesNotExistError
from falcon.request_bot import RequestBot

import logging
logger = logging.getLogger("notification_queuer")
handler = logging.FileHandler('/var/www/falcon/pnw_stats_finder/notification_queuer.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


if 'PWUSER' in os.environ:
    USERNAME = os.environ['PWUSER']
    PASS = os.environ['PWPASS']
else:
    with open("/var/www/falcon/auth") as uf:   
        USERNAME = uf.readline().strip()
        PASS = uf.readline().strip()
pwc = PWClient(USERNAME, PASS)

from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route('/')
def hello_world():
    if MAINTENANCE_MODE:
        return render_template('maintenance.html')
    return render_template('homeform.html')


@app.route('/datadump/')
def datadump():
    pwdb = PWDB()
    ret_list = {}
    for document in pwdb.falcon_records.find():
        ret_list[str(document["_id"])] = {}
        for key in document:
            if type(document[key]) is dict:
                ret_list[str(document["_id"])][key] = document[key]
            else:
                ret_list[str(document["_id"])][key] = str(document[key])
    return jsonify(ret_list)

@app.route('/payout_history/nation_id=<nation_id>/turns=<turns>/resource=<resource_type>/')
def individual_history(nation_id, turns, resource_type):

    num_days = float(turns) / 12.0
    time_difference = timedelta(days=num_days)

    pwdb = PWDB()

    records = []

    turn_numbers = []
    nation_payouts = []
    nation_scores = []
    average_nation_scores = []

    for record in pwdb.get_recent_tax_records(time_since=time_difference):
        records.append(record)

    records.sort(key=lambda x: x['gametime'])

    texts = []

    for idx in range(len(records)):
        time_record = records[idx]
        turn_number = idx
        record = time_record['records'][nation_id]
        turn_total = 0
        for nation_key in time_record['records'].keys():
            nation_record = time_record['records'][nation_key]
            turn_total += nation_record['owed'][resource_type]
        nation_score = record['score']
        nation_payout = record['owed'][resource_type]
        average_nation_score = record['avg_alliance_score']
        payout_as_percent = nation_payout / float(turn_total)

        if not 'hidden' in record.keys():
            turn_numbers.append(turn_number)
            nation_payouts.append(nation_payout)
            nation_scores.append(nation_score)
            average_nation_scores.append(average_nation_score)
            annotation = record['name']

            texts.append(annotation)

    trace1 = Scatter(
        x=turn_numbers,
        y=nation_payouts,
        mode="lines+markers",
        text=texts,
        name="Payout ("+str(resource_type)+")",

        marker=Marker(
            color='rgb(0, 127, 0)',
            size=12,
            symbol='circle',
            line=Line(
                color='rgb(204, 204, 204)',
                width=1
            ),
            opacity=0.9
        ),
        line=Line(
            shape='spline'
        )
    )

    trace2 = Scatter(
        x=turn_numbers,
        y=nation_scores,
        mode="lines+markers",
        name="Score",
        text=texts,

        marker=Marker(
            color='rgb(127, 0, 0)',
            size=12,
            symbol='circle',
            line=Line(
                color='rgb(204, 204, 204)',
                width=1
            ),
            opacity=0.9
        ),
        line=Line(
            shape='spline'
        ),
        yaxis='y2'
    )


    trace3 = Scatter(
        x=turn_numbers,
        y=average_nation_scores,
        mode="lines+markers",
        name="Average Alliance Score",

        marker=Marker(
            color='rgb(0, 0, 127)',
            size=12,
            symbol='circle',
            line=Line(
                color='rgb(204, 204, 204)',
                width=1
            ),
            opacity=0.9
        ),
        line=Line(
            shape='spline'
        ),
        yaxis='y2'
    )


    data = Data([trace1, trace2, trace3])

    layout = Layout(
        margin=Margin(
            l=0,
            r=0,
            b=0,
            t=0
        ),
        xaxis=XAxis(title='Turn'),
        yaxis=YAxis(title='Payout ('+str(resource_type)+')'),
        yaxis2=YAxis(
            title='Score',
            overlaying='y',
            side='right'
        )

    )


    fig = Figure(data=data, layout=layout)
    plot_url = py.plot(fig, filename='individual_payout_history-'+str(nation_id)+"-"+str(turns)+'-'+str(resource_type), auto_open=False)

    html = plotly.tools.get_embed(plot_url)

    return render_template("graph.html", title="FALCON Payouts: "+str(nation_id)+": "+str(resource_type)+
                                               " over the last "+str(turns)+" turns", graph=html)



@app.route('/payout_history/turns=<turns>/resource=<resource_type>/')
def falcon_history(turns, resource_type):

    num_days = float(turns) / 12.0
    time_difference = timedelta(days=num_days)

    pwdb = PWDB()

    records = []

    xes = []
    yes = []
    zes = []

    colors = {
        "17274": {
            "color": "rgb(102, 0, 204)",
            "x": [],
            "y": [],
            "z": [],
            "texts": [],
            "name":"Butterkupistan"
        },
        "17269": {
            "color": "rgb(255, 204, 0)",
            "x": [],
            "y": [],
            "z": [],
            "texts": [],
            "name":"Parents just don't understand"
        },
        "17270": {
            "color": "rgb(178, 0, 0)",
            "x": [],
            "y": [],
            "z": [],
            "texts": [],
            "name": "New URAB"
        }
    }

    for record in pwdb.get_recent_tax_records(time_since=time_difference):
        records.append(record)

    first_timerecord = records[len(records) - 1]

    color_switch_counter = 0

    max_nation_score = 0
    for nkey in first_timerecord['records']:
        score = first_timerecord['records'][nkey]['score']
        max_nation_score = max(max_nation_score, score)

    keys = first_timerecord['records'].keys()
    keys.sort(key=lambda x: first_timerecord['records'][x]['score'])

    for nation_key in keys:
        if nation_key not in colors.keys():

            score = first_timerecord['records'][nation_key]['score']
            as_percent = score / float(max_nation_score)

            str_p = str(int(as_percent * 60) + 180)

            if color_switch_counter % 4 == 0:
                my_color = "rgb("+str_p+", 180, 180)"

            if color_switch_counter % 4 == 1:
                my_color = "rgb(180, 180, "+str_p+")"

            if color_switch_counter % 4 == 2:
                my_color = "rgb("+str_p+", "+str_p+", "+str_p+")"

            if color_switch_counter % 4 == 3:
                my_color = "rgb(180, "+str_p+", 180)"

            color_switch_counter += 1

            colors[nation_key] = {
                "color": my_color,
                "x": [],
                "y": [],
                "z": [],
                "texts": [],
                "name": first_timerecord['records'][nation_key]['name']
            }

    records.sort(key=lambda x: x['gametime'])

    texts = []

    for idx in range(len(records)):
        time_record = records[idx]
        x = idx
        for record_key in time_record['records'].keys():
            record = time_record['records'][record_key]
            y = record['score']
            z = record['owed'][resource_type]

            if not 'hidden' in record.keys():
                if record['nation_id'] in colors.keys():
                    colors[record['nation_id']]['x'].append(x)
                    colors[record['nation_id']]['y'].append(y)
                    colors[record['nation_id']]['z'].append(z)

                    annotation = record['name']

                    colors[record['nation_id']]['texts'].append(annotation)
                else:
                    xes.append(x)
                    yes.append(y)
                    zes.append(z)

                    annotation = record['name']

                    texts.append(annotation)

    traces = []

    for nation_key in colors.keys():
        color_trace = Scatter3d(
            x=colors[nation_key]["x"],
            y=colors[nation_key]["y"],
            z=colors[nation_key]["z"],
            mode="markers",
            text=colors[nation_key]['texts'],
            name=colors[nation_key]['name'],

            marker=Marker(
                color=colors[nation_key]["color"],
                size=8,
                symbol='circle',
                # line=Line(
                #     color=colors[nation_key]["color"],
                #     width=1
                # ),
                opacity=0.9
            )
        )
        traces.append(color_trace)

    data = Data(traces)
    layout = Layout(
        margin=Margin(
            l=0,
            r=0,
            b=0,
            t=0
        ),
        title="Score vs. Payout ($) over time",
        scene=Scene(
            xaxis=XAxis(title='Turn'),
            yaxis=YAxis(title='Score'),
            zaxis=ZAxis(title='Payout ('+str(resource_type)+')')
        )
    )


    fig = Figure(data=data, layout=layout)
    plot_url = py.plot(fig, filename='payout_history-'+str(turns)+'-'+str(resource_type), auto_open=False)

    html = plotly.tools.get_embed(plot_url)

    return render_template("graph.html", title="FALCON Payouts: "+str(resource_type)+" over the last "+str(turns)+ " turns", graph=html)

@app.route('/available/')
def available():
    if MAINTENANCE_MODE:
        return render_template('maintenance.html')
    pwdb = PWDB()
    collections = pwdb.tax_db.nations

    all_owed = {}
    for n in collections.find():
        for key in n[owed_key]:
            if key not in all_owed:
                all_owed[key] = 0
            all_owed[key] += n[owed_key][key]
    renderstring = "<h1>Minimum reserves required</h1><br />Do not leave " \
                   "the bank with less than the following amounts at <b>any time</b><br >"

    renderstring += "Minimum money: {:+.4f} <br />".format(all_owed["money"])
    for key in all_owed:
        if key != "money":
            renderstring += "Minimum "+key+": {:+.4f} <br />".format(all_owed[key])

    return renderstring

@app.route('/list_taxed_members/')
def list_taxed_members():
    if MAINTENANCE_MODE:
        return render_template('maintenance.html')
    pwdb = PWDB()
    tlist = pwdb.list_members()
    return jsonify(tlist=tlist)

@app.route('/slackers/')
def find_slackers():

    if MAINTENANCE_MODE:
        return render_template('maintenance.html')

    pwdb = PWDB()
    nations = pwdb.tax_db.nations

    all_nations = []
    for nation in nations.find():
        all_nations.append(nation)

    all_nations.sort(key=lambda x: x[turns_since_collected_key], reverse=True)

    renderstring = "<h1>Slackers!</h1>"
    for nation in all_nations:
        color = "#999"
        if nation[turns_since_collected_key] < 2:
            color = "#DDD"
        if nation[turns_since_collected_key] > 5:
            color = "#000"
        if nation[turns_since_collected_key] > 10:
            color = "#F99"
        if nation[turns_since_collected_key] > 20:
            color = "#F00"
        renderstring += "<p style='color:"+color+";'>Nation "+nation['name']+" has not collected in " + \
                        str(nation[turns_since_collected_key])+" turns!"
        if nation[turns_since_collected_key] >= MAX_COLLECTION_TIMEDELTA.total_seconds() / 60 / 60 / 2:
            renderstring += " This nation is no longer accruing revenue from FALCON, due to inactivity!"
        renderstring += "</p>"

    return renderstring


def do_request(nation_id):
    if MAINTENANCE_MODE:
        return render_template('maintenance.html')
    reqbot = RequestBot()
    results = reqbot.make_request(str(nation_id))
    renderstring = ""
    num_turns = results[turns_since_collected_key]
    if num_turns < 1:
        renderstring += "<h1>Request rejected</h1> <h2>It has not been a turn since your last request!</h2><br />"
    else:
        renderstring += "<h1>Request accepted!</h1><h2>It has been "+str(num_turns) +\
                        " turns since your last collection.</h2><br />"

    avg_money_per_turn = 0
    if num_turns >= 1:
        avg_money_per_turn = results[owed_key]["money"] / float(num_turns)

    # renderstring += "money returned: "+str(results[owed_key]["money"])+" (average of " +\
    #                 str(avg_money_per_turn)+" per turn and "+str(avg_money_per_turn * 12)+" per day)<br /><br />"
    #
    renderstring += "money returned: <b>{:+.2f}</b> (average of {:+.2f} per turn and <b>{:+.2f}</b> per day)<br /><br />".format(
            results[owed_key]["money"], avg_money_per_turn, avg_money_per_turn * 12)

    for key in results[owed_key].keys():
        if key != "money":
            avg = 0
            if num_turns >= 1:
                avg = results[owed_key][key] / float(num_turns)
            renderstring += key+" returned: <b>{:+.2f}</b> (average of {:+.2f} per turn and <b>{:+.2f}</b> per day)<br /><br />".format(
            results[owed_key][key], avg, avg * 12)

    return renderstring

@app.route('/request/<nation_id>/')
def request_with_id(nation_id):
    if MAINTENANCE_MODE:
        return render_template('maintenance.html')
    return do_request(nation_id)


@app.route('/request/', methods=['POST'])
def make_request():
    if MAINTENANCE_MODE:
        return render_template('maintenance.html')

    if request.method == 'POST':
        nation_id = request.form['nid']
        return do_request(nation_id)

@app.route('/queue_n/<to>/<subject>/<body>/<time>/')
def queue_n(to, subject, body, time):
    if MAINTENANCE_MODE:
        return render_template('maintenance.html')
    t = Thread(target = lambda: wait_to_mail(to, subject, body, time))
    t.start()
    return "Notification queued to "+to+" in "+time

def wait_to_mail(to, subject, body, time_to_wait):
    time_to_wait = int(time_to_wait)
    log("New in queue: message:",to,"/",subject,"/",body)
    while time_to_wait > 100:
        time.sleep(100)
        time_to_wait -= 100
        log("message:",to,"/",subject,"/",body,"/ still waiting:")
        log("\t",time_to_wait,"seconds")
    time.sleep(time_to_wait)
    now = datetime.now()
    body += "\n\nToday's date is: "+str(now.month)+"/"+str(now.day)+"/"+str(now.year)+" at "+str(now.hour)+":"+str(now.minute)
    log("Sending email NOW!",to,subject, body)
    send_email(to, subject, body)

def send_email(to, subject, html):
    b64_un = 'Y2hhcm1pbmcuZnJpZW5kcy5wbnc=\n'
    b64_pass = 'bWUydGhhbmtz\n'
    m = GMail(base64.decodestring(b64_un), base64.decodestring(b64_pass))
    m.connect()
    message = Message(subject, to=to, text=html)
    m.send(message)
    print "sending", to, subject, html
    m.close()

def log(*args):
    logstring = ""
    for arg in args:
        logstring += " " +str(arg)
    logger.debug(logstring)

if __name__ == '__main__':
    app.run(debug=True)
