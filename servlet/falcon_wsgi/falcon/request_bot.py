import threading
from income_tracker import owed_key, collected_key
from pnw_db import PWDB, turns_since_collected_key
import copy
import datetime

__author__ = 'sxh112430'
import os

class RequestBot:

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
        self.pwdb = PWDB(__username, __pass, skip_pwclient=True)

    def make_request(self, nation_id):
        nation_id = str(nation_id).strip()

        nation_tax_db = self.pwdb.get_nation(nation_id)

        money_owed =        nation_tax_db[owed_key]['money']
        food_owed =         nation_tax_db[owed_key]['food']
        coal_owed =         nation_tax_db[owed_key]['coal']
        uranium_owed =      nation_tax_db[owed_key]['uranium']
        oil_owed =          nation_tax_db[owed_key]['oil']
        lead_owed =         nation_tax_db[owed_key]['lead']
        iron_owed =         nation_tax_db[owed_key]['iron']
        bauxite_owed =      nation_tax_db[owed_key]['bauxite']
        gasoline_owed =     nation_tax_db[owed_key]['gasoline']
        munitions_owed =    nation_tax_db[owed_key]['munition']
        steel_owed =        nation_tax_db[owed_key]['steel']
        aluminum_owed =     nation_tax_db[owed_key]['aluminum']

        result = copy.deepcopy(nation_tax_db)

        nation_tax_db[owed_key]['money'] =    0
        nation_tax_db[owed_key]['food'] =     0
        nation_tax_db[owed_key]['coal'] =     0
        nation_tax_db[owed_key]['uranium'] =  0
        nation_tax_db[owed_key]['oil'] =      0
        nation_tax_db[owed_key]['lead'] =     0
        nation_tax_db[owed_key]['iron'] =     0
        nation_tax_db[owed_key]['bauxite'] =  0
        nation_tax_db[owed_key]['gasoline'] = 0
        nation_tax_db[owed_key]['munition'] = 0
        nation_tax_db[owed_key]['steel'] =    0
        nation_tax_db[owed_key]['aluminum'] = 0

        nation_tax_db[collected_key] = datetime.datetime.now() + datetime.timedelta(hours=2)
        nation_tax_db[turns_since_collected_key] = 0

        self.pwdb.set_nation(nation_id, nation_tax_db)

        thread = threading.Thread(target=lambda: self.critical(nation_id, money_owed, food_owed, coal_owed,
                                                               uranium_owed, oil_owed, lead_owed, iron_owed,
                                                               bauxite_owed, gasoline_owed, munitions_owed, steel_owed,
                                                               aluminum_owed))
        print "Starting thread, ", money_owed
        thread.start()

        return result

    def critical(self, nation_id, money_owed, food_owed, coal_owed, uranium_owed, oil_owed, lead_owed, iron_owed,
                 bauxite_owed, gasoline_owed, munitions_owed, steel_owed, aluminum_owed):

        self.pwdb._init_pwc()

        data = {}
        data['money_owed'] = money_owed
        data['food_owed'] = food_owed
        data['coal_owed'] = coal_owed
        data['uranium_owed'] = uranium_owed
        data['oil_owed'] = oil_owed
        data['lead_owed'] = lead_owed
        data['iron_owed'] = iron_owed
        data['bauxite_owed'] = bauxite_owed
        data['gasoline_owed'] = gasoline_owed
        data['munitions_owed'] = munitions_owed
        data['steel_owed'] = steel_owed
        data['aluminum_owed'] = aluminum_owed
        data['nation'] = nation_id

        gametime = self.pwdb.pwc.get_current_date_in_datetime()
        ticket_no = self.pwdb.create_withdraw_record(datetime.datetime.now(), gametime, data)

        self.pwdb.pwc.make_bank_withdrawal(nation_id, ticket_no, money=money_owed, food=food_owed, coal=coal_owed,
                                           uranium=uranium_owed, oil=oil_owed, lead=lead_owed, iron=iron_owed,
                                           bauxite=bauxite_owed, gasoline=gasoline_owed, munitions=munitions_owed,
                                           steel=steel_owed, aluminum=aluminum_owed)
        print "I'm finished! ", money_owed, ticket_no
