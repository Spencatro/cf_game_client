from datetime import datetime
import logging
import os
from pw_client import PWClient

__author__ = 'shawkins'


def list_to_tr(l):
    html_string = "<tr>\n"
    for i in l:
        html_string += "\t<td>"+str(i)+"</td>\n"
    html_string += "</tr>\n"
    return html_string


def matrix_to_table(matrix, headers):
    html_string = "<table>\n<tr>\n"
    for i in headers:
        html_string += "\t<th>"+i+"</th>\n"
    html_string += "</tr>\n"
    for l in matrix:
        html_string += list_to_tr(l)
    html_string += "</table>"
    return html_string


logger = logging.getLogger("pwc")
fhandler1 = logging.FileHandler("city_check.out", mode='w')
logger.addHandler(fhandler1)
logger.setLevel(logging.DEBUG)

USERNAME = os.environ['PW_USER']
PASS = os.environ['PW_PASS']
pwc = PWClient(USERNAME, PASS, logger=logger)

infos = []
goods = []
for nation in pwc.get_list_of_alliance_members_from_alliance_name("Charming Friends"):
    today = datetime.now()
    min_days = 9000
    most_recent_city = None
    for city in nation.cities:
        diff = today - city.founded
        if diff.days < min_days:
            min_days = diff.days
            most_recent_city = city.name
    info = [nation.name, len(nation.cities), ''.join(most_recent_city.splitlines()), min_days]
    if min_days > 10:
        infos.append(info)
    else:
        goods.append(info)

headers=["Nation", "# cities", "Most recent city ..............", "Days since built"]

if len(infos) > 0:
    print "<h1>Nations off cooldown (ready to build)</h1>"
    print matrix_to_table(infos, headers)
if len(goods) > 0:
    print "<h1>Nations on cooldown (good job!)</h1>"
    print matrix_to_table(goods, headers)
