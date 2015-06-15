from servlet.wsgi.falcon.income_tracker import owed_key, collected_key
from pnw_db import PWDB

__author__ = 'sxh112430'
import os

class RequestBot:
    def __init__(self):
        __username = os.environ['PWUSER']
        __pass = os.environ['PWPASS']
        self.pwdb = PWDB(__username, __pass)
        self.pwc = self.pwdb.pwc

    def make_request(self, nation_id):
        nation_tax_db = self.pwdb.get_nation(nation_id)
        nation_tax_db[collected_key] = self.pwc.get_current_date_in_datetime()

        money_owed = nation_tax_db[owed_key]['money']
        food_owed = nation_tax_db[owed_key]['food']
        coal_owed = nation_tax_db[owed_key]['coal']
        uranium_owed = nation_tax_db[owed_key]['uranium']
        oil_owed = nation_tax_db[owed_key]['oil']
        lead_owed = nation_tax_db[owed_key]['lead']
        iron_owed = nation_tax_db[owed_key]['iron']
        bauxite_owed = nation_tax_db[owed_key]['bauxite']
        gasoline_owed = nation_tax_db[owed_key]['gasoline']
        munitions_owed = nation_tax_db[owed_key]['munitions']
        steel_owed = nation_tax_db[owed_key]['steel']
        aluminum_owed = nation_tax_db[owed_key]['aluminum']

        self.pwc.make_bank_withdrawal(17270, money=money_owed, food=food_owed, coal=coal_owed, uranium=uranium_owed,
                                      oil=oil_owed, lead=lead_owed, iron=iron_owed, bauxite=bauxite_owed,
                                      gasoline=gasoline_owed, munitions=munitions_owed, steel=steel_owed,
                                      aluminum=aluminum_owed)

        return nation_tax_db[owed_key]

