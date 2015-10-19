from datetime import datetime
import logging
import os
from tabulate import tabulate
from pw_client import PWClient

__author__ = 'shawkins'

logger = logging.getLogger("pwc")
fhandler1 = logging.FileHandler("city_check.out", mode='w')
logger.addHandler(fhandler1)
logger.setLevel(logging.DEBUG)

USERNAME = os.environ['PW_USER']
PASS = os.environ['PW_PASS']
pwc = PWClient(USERNAME, PASS, logger=logger)

infos = []
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

print tabulate(infos, headers=["Nation", "# cities", "Most recent city ..............", "Days since built"], tablefmt="grid")