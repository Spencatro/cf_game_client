import datetime

__author__ = 'shawkins'
import logging
import os
from pw_client import PWClient
import plotly.graph_objs as go
import plotly.plotly as py
import plotly.tools as tls

__author__ = 'shawkins'

money_string = '<b style="color: #28d020;">$</b>'
img_dict = {'steel': 'https://politicsandwar.com/img/resources/steel.png', 'oil': 'https://politicsandwar.com/img/resources/oil.png', 'aluminum': 'https://politicsandwar.com/img/resources/aluminum.png', 'lead': 'https://politicsandwar.com/img/resources/lead.png', 'bauxite': 'https://politicsandwar.com/img/resources/bauxite.png', 'food': 'https://politicsandwar.com/img/icons/16/steak_meat.png', 'money': 'https://politicsandwar.com/img/resources/money.png', 'munition': 'https://politicsandwar.com/img/resources/munitions.png', 'uranium': 'https://politicsandwar.com/img/resources/uranium.png', 'coal': 'https://politicsandwar.com/img/resources/coal.png', 'iron': 'https://politicsandwar.com/img/resources/iron.png', 'gasoline': 'https://politicsandwar.com/img/resources/gasoline.png'}
realstring_dict = {'steel': 'steel', 'oil': 'oil', 'lead': 'lead', 'aluminum': 'aluminum', 'munition': 'munitions', 'food': 'food', 'bauxite': 'bauxite', 'uranium': 'uranium', 'coal': 'coal', 'iron': 'iron', 'gasoline': 'gasoline'}

logger = logging.getLogger("pwc")
fhandler1 = logging.FileHandler("city_check.out", mode='w')
logger.addHandler(fhandler1)
logger.setLevel(logging.DEBUG)

USERNAME = os.environ['PW_USER']
PASS = os.environ['PW_PASS']
pwc = PWClient(USERNAME, PASS, logger=logger)

img_url = "https://politicsandwar.com/img/resources/"

five_days_ago = pwc.get_current_date_in_datetime() - datetime.timedelta(days=5)

records = pwc.get_alliance_bank_records_from_id(1356, records_since_datetime=five_days_ago)

nation_totals = {}
for nation in pwc.get_list_of_alliance_members_from_alliance_name("Charming Friends"):
    nation_totals[nation.nation_id] = 0

totals = {}
for record in records:

    for resource_key in record['resources'].keys():
        if resource_key not in totals.keys():
            totals[resource_key] = 0
        if record["reciever"] == "1356" and record["sender"] in nation_totals.keys():  # if it's an incoming transaction to the bank from an alliance nation
            totals[resource_key] -= record['resources'][resource_key]
        elif record["reciever"] not in nation_totals.keys() and record["sender"] not in nation_totals.keys():  # if it's an incoming transaction to the bank, or outgoing to non-alliance member
            continue
        else:
            totals[resource_key] += record['resources'][resource_key]

html_string = "<h1>Total amounts spent in last 5 days</h1>\n"
html_string += "<table>\n"

for key in totals.keys():
    if key == "money":
        html_string += "<tr>\n<td>\n"+money_string+"\n</td>\n<td>\n"+"{:,}".format(totals[key])+"\n</td>\n</tr>\n"
    else:
        html_string += "<tr>\n<td>\n<img src='"+img_dict[key]+"'>\n</td>\n<td>\n"+"{:,}".format(totals[key])+"\n</td>\n</tr>\n"

html_string += "</table>"

total_money_value = totals['money']

trade_values = {}
for item_type in realstring_dict.keys():
    item_value = realstring_dict[item_type]
    trade_url = "https://politicsandwar.com/index.php?id=90&display=world&resource1="+item_value+"&buysell=buy&ob=price&od=DESC&maximum=15&minimum=0&search=Go"
    nationtable = pwc._retrieve_nationtable(trade_url, 0)
    trade_tr = nationtable.findall(".//tr")[1]
    trade_td = trade_tr.findall(".//td")[5]
    trade_text = trade_td[0].text
    trade_num = int(trade_text.split("/")[0].replace(",",""))
    trade_values[item_type] = trade_num
    total_money_value += trade_num * totals[item_type]

trade_values["money"] = 1  # money value is 1:1 lol

html_string += "\n<h1>Estimated total value spent in last 5 days: "+money_string+"{:,}".format(total_money_value)+"</h1>\n"
html_string += "<h4>Note: this value is calculated by taking the current 'buy' trading prices and multiplying them by the amount of resources collected this turn.</h4>"

print html_string

for record in records:
    for resource_key in record["resources"].keys():
        if record["reciever"] == "1356" and record["sender"] in nation_totals.keys():
            nation_totals[record["sender"]] -= trade_values[resource_key] * record['resources'][resource_key]
        elif record["reciever"] not in nation_totals.keys() and record["sender"] not in nation_totals.keys():  # if it's an incoming transaction to the bank, or outgoing to non-alliance member
            continue
        else:
            nation_totals[record['reciever']] += trade_values[resource_key] * record['resources'][resource_key]

nation_keys = nation_totals.keys()

# get the start of the week
today = datetime.date.today()
last_monday = today + datetime.timedelta(days=-today.weekday())
month_day_year = last_monday.strftime("%m.%d.%Y")

x = []
y = []
titles = []

for nation in nation_keys:
    n_obj = pwc.get_nation_obj_from_ID(nation)
    score = n_obj.score
    value_taken = nation_totals[nation]
    label = n_obj.name
    if value_taken > 0:
        x.append(score)
        y.append(value_taken)
        titles.append(label)

trace = go.Scatter(x=x,
                   y=y,
                   text=titles,
                   mode='markers+text',
                   name="Score (x) vs. Total Value Taken (y)"
                   )
data = [trace]
layout = go.Layout(
    title=(r'Nation Bank Audits, last 5 days'),
    showlegend=True
)
fig = go.Figure(data=data, layout=layout)
plot_url = py.plot(fig, filename="PNW_Audits_weekof_"+month_day_year+"/audits_build_"+str(os.environ.get("BUILD_NUMBER")), auto_open=False)
print tls.get_embed(plot_url)