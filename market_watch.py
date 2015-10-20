import logging
import os
import pprint
from pw_client import PWClient, LeanPWDB

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
pwdb = LeanPWDB()

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