__author__ = 'sxh112430'
import os
from PWClient import PWClient
import time



USERNAME = os.environ['PWUSER']
PASS = os.environ['PWPASS']
pwc = PWClient(USERNAME, PASS)

n_5913 = pwc.get_nation_obj_from_ID(5913, skip_cache=True)

while n_5913.color == "Beige":
    pwc.__authenticate__()
    print "still beige", pwc.get_current_date_in_datetime(), n_5913.time_since_active, n_5913.color
    time.sleep(60 * 120)
    n_5913 = pwc.get_nation_obj_from_ID(5913, skip_cache=True)

print "NATION IS NOT BEIGE, current time:",pwc.get_current_date_in_datetime(), n_5913.time_since_active, n_5913.color