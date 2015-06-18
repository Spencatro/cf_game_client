from datetime import datetime, timedelta
from pnw_db import PWDB, turns_since_collected_key
from pw_client import PWClient, DEBUG_LEVEL_STFU
import os
from pnw_db import rsc_key, score_diff_key, collected_key, can_collect_key, total_paid_key, owed_key

__author__ = 'sxh112430'

MAX_COLLECTION_TIMEDELTA = timedelta(days=5)

class IncomeTracker:
    def __init__(self):
        if 'PWUSER' in os.environ:
            USERNAME = os.environ['PWUSER']
            PASS = os.environ['PWPASS']
        else:
            with open("/var/www/falcon/auth") as uf:
                USERNAME = uf.readline().strip()
                PASS = uf.readline().strip()
        __username = USERNAME
        __pass = PASS
        pwdb = PWDB(__username, __pass)
        pwc = pwdb.pwc
        assert isinstance(pwc, PWClient)

        now = datetime.now()

        pwc.debug = DEBUG_LEVEL_STFU
        records = pwc.get_alliance_tax_records_from_id(1356, only_last_turn=True)

        average_score = pwc.get_alliance_average_score_from_id(1356)
        total_score = pwc.get_alliance_score_from_id(1356)

        ACTUAL_TOTAL = {}
        # For testing
        for record in records:
            for resource_type in record[rsc_key].keys():
                if resource_type not in ACTUAL_TOTAL.keys():
                    ACTUAL_TOTAL[resource_type] = 0
                ACTUAL_TOTAL[resource_type] += record[rsc_key][resource_type]

        # Get the lowest difference (negative) so we can keep everything else positive
        min_difference = 0
        for record in records:
            nation_obj = pwc.get_nation_obj_from_ID(record['sender'])
            record['nation_obj'] = nation_obj
            record[score_diff_key] = nation_obj.score - average_score
            if record[score_diff_key] < min_difference:
                min_difference = record[score_diff_key]

        # move everything to positive
        for record in records:
            record[score_diff_key] += min_difference * 3  # Move everything up to positive
            record[score_diff_key] *= record[score_diff_key]  # square it

        # Places where we will keep track of stuff
        # This is the total amount of stuff collected
        total_collected_this_turn = {}
        # This is how much was returned to little nations
        total_returned_from_collected = {}

        turn_data = {}
        # Apply baserate
        for record in records:
            nation_id = record['sender']
            turn_data[nation_id] = {}
            turn_data[nation_id]['paid'] = {}
            turn_data[nation_id]['owed'] = {}

            turn_data[nation_id]['score'] = record['nation_obj'].score
            turn_data[nation_id]['avg_alliance_score'] = average_score
            turn_data[nation_id]['total_alliance_score'] = total_score

            nation_tax_db = pwdb.get_nation(nation_id)
            last_collected_date = nation_tax_db[collected_key]

            record[can_collect_key] = True
            if pwc.get_current_date_in_datetime() - last_collected_date > MAX_COLLECTION_TIMEDELTA:
                record[can_collect_key] = False

            resources = record[rsc_key]

            # Auto-take baserate
            for resource_type in resources.keys():
                if resource_type not in total_collected_this_turn.keys():
                    total_collected_this_turn[resource_type] = 0

                if resource_type not in turn_data[nation_id]['owed'].keys():
                    turn_data[nation_id]['owed'][resource_type] = 0

                if resource_type not in turn_data[nation_id]['paid'].keys():
                    turn_data[nation_id]['paid'][resource_type] = 0

                if resource_type not in total_returned_from_collected.keys():
                    total_returned_from_collected[resource_type] = 0

                if resource_type not in nation_tax_db[owed_key].keys():
                    nation_tax_db[owed_key][resource_type] = 0

                if resource_type not in nation_tax_db[total_paid_key].keys():
                    nation_tax_db[total_paid_key][resource_type] = 0

                amount_sent = resources[resource_type]  # Total sent in
                nation_tax_db[total_paid_key][resource_type] = amount_sent
                turn_data[nation_id]['paid'][resource_type] = amount_sent

                # Register how much was collected
                total_collected_this_turn[resource_type] += amount_sent
            
            nation_name = pwdb.pwc.get_nation_name_from_id(nation_id)
            turn_data[nation_id]['name'] = nation_name
            turn_data[nation_id]['nation_id'] = nation_id
            nation_tax_db['name'] = nation_name

            if not turns_since_collected_key in nation_tax_db.keys():
                nation_tax_db[turns_since_collected_key] = 0

            nation_tax_db[turns_since_collected_key] += 1

            if not record[can_collect_key]:
                nation_tax_db[turns_since_collected_key] = -1
            if record['nation_obj'].color.strip() == "Gray":
                nation_tax_db[turns_since_collected_key] = -2

            pwdb.set_nation(nation_id, nation_tax_db)
            turn_data[nation_id]['date'] = record['date']

        # Determine who is still owed from reserves
        collectors = [record for record in records if record[can_collect_key]
                      and not record['nation_obj'].color.strip() == "Gray"]

        """
        Differential percentage is a metric that calculates the "percent difference" you are away from the alliance score
        average. Everything is moved such that all differences are considered "positive," which sets the highest player at
        "zero." This way, everyone collects, but those who are on the lower end collect much more than those on the higher end.
        """

        # Only include collectors in diff sum
        differential_sum = 0
        for record in collectors:
            differential_sum += record[score_diff_key]


        sum_diff_percentage = 0

        for record in collectors:

            nation_id = record['sender']
            nation_tax_db = pwdb.get_nation(nation_id)

            diff_percentage = record[score_diff_key] / differential_sum
            print nation_id, "gets", diff_percentage, "%"
            sum_diff_percentage += diff_percentage
            owed_percentage = 0.9 * diff_percentage

            for resource_type in total_collected_this_turn.keys():
                amount = total_collected_this_turn[resource_type]
                amount_owed = amount * owed_percentage
                nation_tax_db[owed_key][resource_type] += amount_owed
                total_returned_from_collected[resource_type] += amount_owed
                turn_data[nation_id]['owed'][resource_type] += amount_owed

            pwdb.set_nation(nation_id, nation_tax_db)

        for nation_key in turn_data.keys():
            nation_data = turn_data[nation_key]
            pwdb.create_record(now, nation_data['date'], nation_data)

        # print "Diff percent total: ",sum_diff_percentage

        for key in ACTUAL_TOTAL.keys():
            print "         ", key
            print "actual   ", ACTUAL_TOTAL[key]
            print "collected", total_collected_this_turn[key]
            print "returned ", total_returned_from_collected[key]
            #
            # # Inputs equaled output
            print "==?"
            print total_collected_this_turn[key]
            print ACTUAL_TOTAL[key]
