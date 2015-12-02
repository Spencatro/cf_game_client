import logging
import os
from colour import Color
import datetime
import pygal
from pygal.style import CleanStyle, DarkStyle
from pw_client import PWClient, LeanPWDB
from bson.objectid import ObjectId
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

result = pwdb.add_market_watch_record(resource_dict)

# averages = {}
# for item_type in realstring_dict.keys():
#     res = pwdb.market_watch_collection.aggregate([{"$group": {"_id": None, "sell": {"$avg": "$values."+item_type+".sell"}, "buy": {"$avg": "$values."+item_type+".buy"}}}])
#     values = res.next()
#     averages[item_type] = {"sell": values["sell"], "buy": values["buy"]}

# get recent data
long_term_average_records = pwdb.get_recent_market_records(num_records=3000)
short_term_average_records = long_term_average_records[-1000:]
long_term_averages = []
for i in range(len(long_term_average_records)):
    current_record = long_term_average_records[i]
    average_dict = {}
    for item_type in realstring_dict.keys():
        average_dict[item_type] = {"buy": 0, "sell": 0}
        if len(long_term_averages) < 1:
            # calc for sells
            average_sell_at_index = current_record['values'][item_type]['sell']
            # calc for buys
            average_buy_at_index = current_record['values'][item_type]['buy']
        else:
            # fast rolling average without looping
            average_sell_at_index = long_term_averages[-1][item_type]['sell'] * len(long_term_averages) + current_record['values'][item_type]['sell']
            average_sell_at_index /= float(len(long_term_averages) + 1)
            average_buy_at_index = long_term_averages[-1][item_type]['buy'] * len(long_term_averages) + current_record['values'][item_type]['buy']
            average_buy_at_index /= float(len(long_term_averages) + 1)
        average_dict[item_type]["sell"] = average_sell_at_index
        average_dict[item_type]["buy"] = average_buy_at_index
    long_term_averages.append(average_dict)

short_term_averages = []
for i in range(len(short_term_average_records)):
    current_record = short_term_average_records[i]
    average_dict = {}
    for item_type in realstring_dict.keys():
        average_dict[item_type] = {"buy": 0, "sell": 0}
        if len(short_term_averages) < 1:
            # calc for sells
            average_sell_at_index = current_record['values'][item_type]['sell']
            # calc for buys
            average_buy_at_index = current_record['values'][item_type]['buy']
        else:
            # fast rolling average without looping
            average_sell_at_index = short_term_averages[-1][item_type]['sell'] * len(short_term_averages) + current_record['values'][item_type]['sell']
            average_sell_at_index /= float(len(short_term_averages) + 1)
            average_buy_at_index = short_term_averages[-1][item_type]['buy'] * len(short_term_averages) + current_record['values'][item_type]['buy']
            average_buy_at_index /= float(len(short_term_averages) + 1)
        average_dict[item_type]["sell"] = average_sell_at_index
        average_dict[item_type]["buy"] = average_buy_at_index
    short_term_averages.append(average_dict)
records = long_term_average_records[-600:]
long_term_averages = long_term_averages[-600:]
short_term_averages = short_term_averages[-600:]

# Generate charts
plot_embeds = {}
plot_urls = {}

for item_type in realstring_dict.keys():
    line_chart = pygal.Line(x_label_rotation=40, show_minor_x_labels=False, x_labels_major_every=96,
                            title=item_type+": price over time", style=DarkStyle)
    line_chart.x_labels = [r['time'].strftime("%b %e - %I:%M%p") for r in records]
    line_chart.add("Current Price", [r['values'][item_type]['sell'] for r in records])
    line_chart.add("10 Day Avg", [r[item_type]["sell"] for r in long_term_averages])
    line_chart.add("3  Day Avg", [r[item_type]["sell"] for r in short_term_averages])

    plot_embed = line_chart.render()

    # TODO: get url?
    plot_url = None

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

for item_type in realstring_dict.keys():
    # Make judgements on sells

    current_sell = resource_dict[item_type]["sell"]
    average_sell = long_term_averages[-1][item_type]["sell"]
    sell_diffp = (abs(long_term_averages[-1][item_type]["sell"] - resource_dict[item_type]["sell"]) / (.5 * (long_term_averages[-1][item_type]["sell"] + resource_dict[item_type]["sell"]))) * 100
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
            if pwdb.increment_buy_counter_for_type(item_type, sell_diffp):
                pass # TODO: this
                # post_good_buy(realstring_dict[item_type], make_trade_url(realstring_dict[item_type]), average_sell, current_sell, image_url=plot_urls[item_type]+".png")
        else:
            pwdb.reset_buy_counter(item_type)
        sell_diffp *= -1
    else:
        if sell_diffp >= 25.0:
            if pwdb.increment_sell_counter_for_type(item_type, sell_diffp):
                pass # TODO: this
                # post_good_sell(realstring_dict[item_type], make_trade_url(realstring_dict[item_type]), average_sell, current_sell, image_url=plot_urls[item_type]+".png")
        else:
            pwdb.reset_sell_counter(item_type)
        sell_color = str(orange_gradient[gradient_index])

    current_buy = resource_dict[item_type]["buy"]
    if current_buy > average_sell:
        buys_higher_than_avg_sells[item_type] = current_buy
    else:
        buys_higher_than_avg_sells[item_type] = -1

    buy_diffp = (abs(long_term_averages[-1][item_type]["buy"] - resource_dict[item_type]["buy"]) / (.5 * (long_term_averages[-1][item_type]["buy"] + resource_dict[item_type]["buy"]))) * 100
    html_string += "<tr>" \
                   "<td>"+realstring_dict[item_type].capitalize()+"</td>" \
                   "<td style='color:"+sell_color+";'>"+str(current_sell)+"</td>" \
                   "<td style='color:"+sell_color+";'>"+str(average_sell)+"</td>" \
                   "<td style='color:"+sell_color+";'>"+str(sell_diffp)+"</td>" \
                   "</tr>"
html_string += "</table>"
print html_string

# Print buy anomalies
for key in buys_higher_than_avg_sells.keys():
    if buys_higher_than_avg_sells[key] < 0:
        pwdb.reset_buy_offer_counter(key)
    else:
        html_string += "<h3>There is a buy offer for"+str(key)+ "("+str(buys_higher_than_avg_sells[key])+") that exceeds the average sell price! Take this trade!</h3>"
        good = realstring_dict[key]
        good_url = make_trade_url(good, ascending=False, sell=False)
        if pwdb.increment_buy_offer_counter_for_type(key):
            pass # TODO: this
            # post_good_buy_offer(good, good_url, averages[key]["sell"], buys_higher_than_avg_sells[key])

for key in plot_embeds:
    print plot_embeds[key]
