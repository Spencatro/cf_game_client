import logging
import os
from pw_client import PWClient

__author__ = 'shawkins'

money_string = '<b style="color: #28d020;">$</b>'
img_dict = {'steel': 'https://politicsandwar.com/img/resources/steel.png', 'oil': 'https://politicsandwar.com/img/resources/oil.png', 'aluminum': 'https://politicsandwar.com/img/resources/aluminum.png', 'lead': 'https://politicsandwar.com/img/resources/lead.png', 'bauxite': 'https://politicsandwar.com/img/resources/bauxite.png', 'food': 'https://politicsandwar.com/img/icons/16/steak_meat.png', 'money': 'https://politicsandwar.com/img/resources/money.png', 'munition': 'https://politicsandwar.com/img/resources/munitions.png', 'uranium': 'https://politicsandwar.com/img/resources/uranium.png', 'coal': 'https://politicsandwar.com/img/resources/coal.png', 'iron': 'https://politicsandwar.com/img/resources/iron.png', 'gasoline': 'https://politicsandwar.com/img/resources/gasoline.png'}

logger = logging.getLogger("pwc")
fhandler1 = logging.FileHandler("city_check.out", mode='w')
logger.addHandler(fhandler1)
logger.setLevel(logging.DEBUG)

USERNAME = os.environ['PW_USER']
PASS = os.environ['PW_PASS']
pwc = PWClient(USERNAME, PASS, logger=logger)

img_url = "https://politicsandwar.com/img/resources/"

records = pwc.get_alliance_tax_records_from_id(1356, only_last_turn=True)

totals = {}
for record in records:
    for resource_key in record['resources'].keys():
        if resource_key not in totals.keys():
            totals[resource_key] = 0
        totals[resource_key] += record['resources'][resource_key]

html_string = "<h1>Total amounts collected last turn</h1>\n"
html_string += "<table>\n"

for key in totals.keys():
    if key == "money":
        html_string += "<tr>\n<td>\n"+money_string+"\n</td>\n<td>\n"+str(totals[key])+"\n</td>\n</tr>\n"
    else:
        html_string += "<tr>\n<td>\n<img src='"+img_dict[key]+"'>\n</td>\n<td>\n"+str(totals[key])+"\n</td>\n</tr>\n"

html_string += "</table>"

html_string += "<h1>Estimated total amounts collected next day</h1>\n"
html_string += "<table>\n"

for key in totals.keys():
    if key == "money":
        html_string += "<tr>\n<td>\n"+money_string+"\n</td>\n<td>\n"+str(totals[key]*12)+"\n</td>\n</tr>\n"
    else:
        html_string += "<tr>\n<td>\n<img src='"+img_dict[key]+"'>\n</td>\n<td>\n"+str(totals[key]*12)+"\n</td>\n</tr>\n"

html_string += "</table>"
print html_string

