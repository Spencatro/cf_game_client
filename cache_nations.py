import json
import os
import pprint

import jsonpickle

from pw_client import PWClient, LeanPWDB

USERNAME = os.environ['PW_USER']
PASS = os.environ['PW_PASS']
pwc = PWClient(USERNAME, PASS)
pwdb = LeanPWDB()
nations = list(pwc.get_list_of_alliance_members_from_alliance_name("Charming Friends"))
nations_sorted = sorted(nations, key=lambda nid: nid.military.get_score() / nid.score)

db_object = {'nations': []}

for nation in nations_sorted:

    nation.military.score = nation.military.get_score()

    max_score_can_be_declared_by = nation.score / 0.75
    min_score_can_be_declared_by = nation.score / 1.75

    holes_above = 0
    holes_below = 0

    spread = max_score_can_be_declared_by - min_score_can_be_declared_by

    total_defendability = 0
    total_checked = 0
    # print "checking", nation.name, nation.score
    print min_score_can_be_declared_by, max_score_can_be_declared_by
    for other in nations_sorted:
        if nation == other:
            continue

        # print "\t", other.name, other.score

        max_score_can_declare_on = other.score * 1.75
        min_score_can_declare_on = other.score * 0.75

        # print "\t", min_score_can_declare_on, max_score_can_declare_on

        covered_min = max(min_score_can_be_declared_by, min_score_can_declare_on)
        covered_max = min(max_score_can_be_declared_by, max_score_can_declare_on)

        covered = covered_max - covered_min

        covered_percentage = float(covered) / float(spread)
        covered_percentage = max(covered_percentage, 0)
        total_defendability += covered_percentage
        total_checked += 1

        count = 0

        if covered_min > min_score_can_be_declared_by:
            # print "\thole below +1"
            count += 1
            holes_below += (1 - covered_percentage)
        if covered_max < max_score_can_be_declared_by:
            # print "\thole above +1"
            count += 1
            holes_above += (1 - covered_percentage)

    def_factor = total_defendability / float(total_checked)

    vuln_factor = holes_below - holes_above
    nation.military.score = nation.military.get_score()
    nation.percent_score_military = 100.0 * nation.military.score / float(nation.score)
    nation.defendability_factor = 100.0 * def_factor
    nation.action_priority = 100.0 * vuln_factor / float(len(nations))

    db_object['nations'].append(json.loads(jsonpickle.encode(nation, unpicklable=False)))

pwdb.cache_nation_list(db_object)