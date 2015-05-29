__author__ = 'sxh112430'
import os
from PWClient import PWClient
import time
import logging
logger = logging.getLogger("pwc")
fhandler1 = logging.FileHandler("watch.out", mode='w')
logger.addHandler(fhandler1)
logger.setLevel(logging.INFO)

USERNAME = os.environ['PWUSER']
PASS = os.environ['PWPASS']
pwc = PWClient(USERNAME, PASS, logger=logger)

n_5913 = pwc.get_nation_obj_from_ID(5913, skip_cache=True)
logger.info("test from watch")

while n_5913.color == "Beige":
    pwc.__authenticate__()
    logger.info("still beige "+str( pwc.get_current_date_in_datetime())+" "+str( n_5913.time_since_active)+" "+str( n_5913.color))
    time.sleep(60 * 120)
    n_5913 = pwc.get_nation_obj_from_ID(5913, skip_cache=True)

logger.info("NATION IS NOT BEIGE, current time:"+str(pwc.get_current_date_in_datetime())+" "+str( n_5913.time_since_active) + " "+str( n_5913.color))