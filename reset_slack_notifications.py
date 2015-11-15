import logging
import os
from pw_client import PWClient
from pw_client import MarketWatchDB

__author__ = 'shawkins'

logger = logging.getLogger("pwc")
USERNAME = os.environ['PW_USER']
PASS = os.environ['PW_PASS']
pwc = PWClient(USERNAME, PASS, logger=logger)

pwdb = MarketWatchDB()

realstring_dict = {'steel': 'steel', 'oil': 'oil', 'lead': 'lead', 'aluminum': 'aluminum', 'munition': 'munitions', 'food': 'food', 'bauxite': 'bauxite', 'uranium': 'uranium', 'coal': 'coal', 'iron': 'iron', 'gasoline': 'gasoline'}

pwdb.init_new_counter(realstring_dict)
