from datetime import datetime
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.mongo_client import MongoClient

__author__ = 'sxh112430'

from pw_client import PWClient
import os

rsc_key = 'resources'
collected_key = 'last_collected_date'
owed_key = 'resources_owed'
total_paid_key = 'resources_paid'
can_collect_key = 'can_collect'
score_diff_key = 'score_diff'

class PWDB:
    def __init__(self, username=None, password=None):

        if 'PWUSER' in os.environ:
            USERNAME = os.environ['PWUSER']
            PASS = os.environ['PWPASS']
        else:
            with open("/var/www/falcon/auth") as uf:
                USERNAME = uf.readline().strip()
                PASS = uf.readline().strip()
        if username is None:
            username = USERNAME
        if password is None:
            password = PASS

        self.pwc = PWClient(username, password)

        self.mongo_client = MongoClient()

        self.tax_db = self.mongo_client.tax_db
        assert isinstance(self.tax_db, Database)

        self.nations = self.tax_db.nations
        assert isinstance(self.nations, Collection)

        self.graph_counter = self.tax_db.graph_counter
        assert isinstance(self.nations, Collection)

    def nation_exists(self, nation_id):
        result = self.nations.find({'nation_id':nation_id})
        count = result.count()

        if count > 1:
            raise Exception("Malformed database!!! More than one nation exists at ID", nation_id)
        return count == 1

    def make_nation(self, nation_id):
        if self.nation_exists(nation_id):
            return False
        return self.nations.insert_one({'nation_id': nation_id,
                                        collected_key: self.pwc.get_current_date_in_datetime(),
                                        owed_key: {},
                                        total_paid_key: {}}).inserted_id

    def get_nation(self, nation_id, or_create = True):
        result = self.nations.find_one({'nation_id':nation_id})
        if or_create:
            if result is None:
                self.make_nation(nation_id)  # Stick it in the DB
                result = self.get_nation(nation_id)  # lol, try again
        return result

    def list_members(self):
        # this function is mostly useless
        return [nation['nation_id'] for nation in self.nations.find()]

    def set_nation_attrib(self, nation_id, attrib, value):
        nation = self.get_nation(nation_id)
        nation[attrib] = value
        self.nations.update({'nation_id':nation_id}, {"$set":nation}, upsert=True)


    def set_nation(self, nation_id, nation_dict):
        self.nations.update({'nation_id':nation_id}, {"$set":nation_dict}, upsert=True)

    def increase_graph_counter(self):
        gcount = self.graph_counter.find_one()
        prev_num = gcount['graph_counter']
        gcount['graph_counter'] += 1
        self.graph_counter.update({'graph_counter':prev_num}, {"$set":gcount})
        return prev_num + 1