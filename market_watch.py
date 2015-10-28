import logging
import os
from colour import Color
import datetime
from pw_client import PWClient, LeanPWDB
import pymongo
from bson.objectid import ObjectId
import plotly.plotly as py
import plotly.graph_objs as go
import plotly.tools as tls
from slack import post_good_buy, post_good_buy_offer, post_good_sell

money_string = '<b style="color: #28d020;">$</b>'
img_dict = {'steel': 'https://politicsandwar.com/img/resources/steel.png', 'oil': 'https://politicsandwar.com/img/resources/oil.png', 'aluminum': 'https://politicsandwar.com/img/resources/aluminum.png', 'lead': 'https://politicsandwar.com/img/resources/lead.png', 'bauxite': 'https://politicsandwar.com/img/resources/bauxite.png', 'food': 'https://politicsandwar.com/img/icons/16/steak_meat.png', 'money': 'https://politicsandwar.com/img/resources/money.png', 'munition': 'https://politicsandwar.com/img/resources/munitions.png', 'uranium': 'https://politicsandwar.com/img/resources/uranium.png', 'coal': 'https://politicsandwar.com/img/resources/coal.png', 'iron': 'https://politicsandwar.com/img/resources/iron.png', 'gasoline': 'https://politicsandwar.com/img/resources/gasoline.png'}
realstring_dict = {'steel': 'steel', 'oil': 'oil', 'lead': 'lead', 'aluminum': 'aluminum', 'munition': 'munitions', 'food': 'food', 'bauxite': 'bauxite', 'uranium': 'uranium', 'coal': 'coal', 'iron': 'iron', 'gasoline': 'gasoline'}


def make_trade_url(good, ascending=True, sell=True):
    if sell:
        buysell = "sell"
    else:
        buysell = "buy"

    if ascending:
        asc_desc = "ASC"
    else:
        asc_desc = "DESC"
    return "https://politicsandwar.com/index.php?id=90&display=world&resource1=" + good + "&buysell=" + buysell +\
           "&ob=price&od=" + asc_desc + "&maximum=15&minimum=0&search=Go"


logger = logging.getLogger("pwc")
fhandler1 = logging.FileHandler("city_check.out", mode='w')
logger.addHandler(fhandler1)
logger.setLevel(logging.DEBUG)

USERNAME = os.environ['PW_USER']
PASS = os.environ['PW_PASS']
pwc = PWClient(USERNAME, PASS, logger=logger)
pwdb = LeanPWDB()

sky_blue = Color("#2b8dcc")
dark_blue = Color("#0d2b3e")

light_orange = Color("#FF7B0C")
dark_orange = Color("#7F4108")

orange_gradient = list(dark_orange.range_to(light_orange, 100))
blue_gradient = list(dark_blue.range_to(sky_blue, 100))

resource_dict = {}
for item_type in realstring_dict.keys():
    resource_dict[item_type] = {"buy": 0,
                                "sell": 0}

# get the buy high values
for item_type in realstring_dict.keys():
    item_value = realstring_dict[item_type]
    trade_url = "https://politicsandwar.com/index.php?id=90&display=world&resource1="+item_value+"&buysell=buy&ob=price&od=DESC&maximum=15&minimum=0&search=Go"
    nationtable = pwc._retrieve_nationtable(trade_url, 0)
    trade_tr = nationtable.findall(".//tr")[1]
    trade_td = trade_tr.findall(".//td")[5]
    trade_text = trade_td[0].text
    trade_num = int(trade_text.split("/")[0].replace(",",""))
    resource_dict[item_type]["buy"] = trade_num

# get the sell high values
for item_type in realstring_dict.keys():
    item_value = realstring_dict[item_type]
    trade_url = "https://politicsandwar.com/index.php?id=90&display=world&resource1="+item_value+"&buysell=sell&ob=price&od=ASC&maximum=15&minimum=0&search=Go"
    nationtable = pwc._retrieve_nationtable(trade_url, 0)
    trade_tr = nationtable.findall(".//tr")[1]
    trade_td = trade_tr.findall(".//td")[5]
    trade_text = trade_td[0].text
    trade_num = int(trade_text.split("/")[0].replace(",",""))
    resource_dict[item_type]["sell"] = trade_num

pwdb.add_market_watch_record(resource_dict)

# Generate charts
plot_embeds = {}
plot_urls = {}
previous_records = []
skipped_one = False
records = list(pwdb.market_watch_collection.find().sort('_id', pymongo.DESCENDING).limit(200))
records.reverse()
for rec in records:
    oid = ObjectId(rec["_id"])
    # yyyy-mm-dd HH
    oid_time = oid.generation_time.strftime("%Y-%m-%d %H:%M:%S")
    if not skipped_one:
        skipped_one = True
        continue
    turn_record = {"turn_date": oid_time}
    for item_type in realstring_dict.keys():
        average_upto_record = pwdb.market_watch_collection.aggregate([{"$match": {"_id": {"$lt": rec["_id"]}}}, {"$group": {"_id": None, "sell": {"$avg": "$values."+item_type+".sell"}, "buy": {"$avg": "$values."+item_type+".buy"}}}]).next()
        turn_record[item_type] = {"avg": average_upto_record, "turn": rec["values"][item_type]}
    previous_records.append(turn_record)

for item_type in realstring_dict.keys():

    t1x = [previous_records[-1]["turn_date"]]
    t1y = [previous_records[-1][item_type]["avg"]["sell"]]
    trace1 = go.Scatter(x=t1x,
                        y=t1y,
                        mode='lines+markers',
                        name="Average price at turn",
                        line=dict(
                            shape='spline'
                        ))
    trace2 = go.Scatter(x=t1x,
                        y=[record[item_type]["turn"]["sell"] for record in previous_records],
                        mode='lines+markers',
                        name="Current price at turn",
                        line=dict(
                            shape='spline'
                        ))
    data = [trace1, trace2]
    layout = go.Layout(
        title=(realstring_dict[item_type] + ': price and average over time').capitalize(),
        showlegend=True
    )
    # get the start of the week
    today = datetime.date.today()
    last_monday = today + datetime.timedelta(days=-today.weekday())
    month_day_year = last_monday.strftime("%m.%d.%Y")

    fig = go.Figure(data=data, layout=layout)
    plot_url = py.plot(fig, filename="PNWMarketWatch_weekof_"+month_day_year+"/"+item_type, auto_open=False, fileopt='extend')
    plot_embed = tls.get_embed(plot_url)
    plot_embeds[item_type] = plot_embed
    plot_urls[item_type] = plot_url

html_string = "<table border='1' rules='all'>\n"
html_string += \
    "<tr>" \
    "<th>Resource</th>" \
    "<th>Current (low) sell price</th>" \
    "<th>Average (low) sell price</th>" \
    "<th>Percent difference</th>" \
    "</tr>\n"

buys_higher_than_avg_sells = {}

averages = {}
for item_type in realstring_dict.keys():
    res = pwdb.market_watch_collection.aggregate([{"$group": {"_id": None, "sell": {"$avg": "$values."+item_type+".sell"}, "buy": {"$avg": "$values."+item_type+".buy"}}}])
    values = res.next()
    averages[item_type] = {"sell": values["sell"], "buy": values["buy"]}
    # Make judgements on sells

    current_sell = resource_dict[item_type]["sell"]
    average_sell = averages[item_type]["sell"]
    sell_diffp = (abs(averages[item_type]["sell"] - resource_dict[item_type]["sell"]) / (.5 * (averages[item_type]["sell"] + resource_dict[item_type]["sell"]))) * 100
    gradient_index = 0
    if sell_diffp > 25:
        gradient_index = 99
    else:
        gradient_index = int(100 * float(sell_diffp) / 25.0)
        if gradient_index >= 100:
            gradient_index = 99

    if average_sell > current_sell:
        sell_color = str(blue_gradient[gradient_index])
        if sell_diffp >= 25.0:
            post_good_buy(realstring_dict[item_type], make_trade_url(realstring_dict[item_type]), average_sell, current_sell, image_url=plot_urls[item_type]+".png")
        sell_diffp *= -1
    else:
        if sell_diffp >= 25.0:
            post_good_sell(realstring_dict[item_type], make_trade_url(realstring_dict[item_type]), average_sell, current_sell, image_url=plot_urls[item_type]+".png")
        sell_color = str(orange_gradient[gradient_index])

    current_buy = resource_dict[item_type]["buy"]
    if current_buy > average_sell:
        buys_higher_than_avg_sells[item_type] = current_buy

    buy_diffp = (abs(averages[item_type]["buy"] - resource_dict[item_type]["buy"]) / (.5 * (averages[item_type]["buy"] + resource_dict[item_type]["buy"]))) * 100
    html_string += "<tr>" \
                   "<td>"+realstring_dict[item_type].capitalize()+"</td>" \
                   "<td style='color:"+sell_color+";'>"+str(current_sell)+"</td>" \
                   "<td style='color:"+sell_color+";'>"+str(average_sell)+"</td>" \
                   "<td style='color:"+sell_color+";'>"+str(sell_diffp)+"</td>" \
                   "</tr>"
html_string += "</table>"
print html_string

# Print buy anomalies
if len(buys_higher_than_avg_sells.keys()) > 0:
    for key in buys_higher_than_avg_sells.keys():
        html_string += "<h3>There is a buy offer for"+str(key)+ "("+str(buys_higher_than_avg_sells[key])+") that exceeds the average sell price! Take this trade!</h3>"
        good = realstring_dict[key]
        good_url = make_trade_url(good, ascending=False, sell=False)
        post_good_buy_offer(good, good_url, averages[key]["sell"], buys_higher_than_avg_sells[key])

for key in plot_embeds:
    print plot_embeds[key]


