import pygal
from income_tracker import IncomeTracker
from pnw_db import owed_key, total_paid_key
from pnw_db import PWDB
import os
from pw_client import Nation

__author__ = 'sxh112430'

class Grapher:
    def __init__(self):
        __username = os.environ['PWUSER']
        __pass = os.environ['PWPASS']
        self.pwdb = PWDB(__username, __pass)
        self.pwc = self.pwdb.pwc

    def score_vs_resources(self, alliance_id):
        nations = self.pwc.get_list_of_alliance_members_from_ID(alliance_id)
        owed_list = {}
        paid_list = {}
        tax_list = {}
        for ally in nations:
            assert isinstance(ally, Nation)
            nation_id = ally.nation_id
            nation_score = ally.score
            nation_db = self.pwdb.get_nation(nation_id)
            for key in nation_db[owed_key].keys():
                owed = nation_db[owed_key][key]
                paid = nation_db[total_paid_key][key]
                if paid <= 0:
                    tax_rate = 0
                else:
                    tax_rate = owed / float(paid)
                if not key in tax_list.keys():
                    tax_list[key] = []
                    owed_list[key] = []
                    paid_list[key] = []
                owed_list[key].append((nation_score, owed))
                paid_list[key].append((nation_score, paid))
        xy_plot = pygal.XY()
        # xy_plot.add("Amount owed vs Score", owed_list)
        # xy_plot.add("Amount paid vs Score", paid_list)
        for key in tax_list:
            if key == "money":
                xy_plot.add(key+" paid", paid_list[key], secondary=True)
                xy_plot.add(key+" returned", owed_list[key], secondary=True)
            else:
                xy_plot.add(key+" paid", paid_list[key])
                xy_plot.add(key+" return", owed_list[key])
        xy_plot.render_to_file('score_v_rsc.svg')


ic = IncomeTracker()
g = Grapher()
g.score_vs_resources(1356)