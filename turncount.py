import math
from pnw_db import PWDB, collected_key, turns_since_collected_key
from pw_client import PWClient

__author__ = 'sxh112430'

pwdb = PWDB('hawkins.spencer@gmail.com', 'plaintext1')
pwc = pwdb.pwc

for nid in pwdb.list_members():
    ndb = pwdb.get_nation(nid)
    print nid, type(nid), pwc.count_turns_since(ndb[collected_key])
    if type(nid) == int:
        pwdb.nations.remove(ndb)
    else:
        ndb[turns_since_collected_key] = math.ceil(pwc.count_turns_since(ndb[collected_key]))
        pwdb.set_nation(nid, ndb)

