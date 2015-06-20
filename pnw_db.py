from datetime import datetime
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.mongo_client import MongoClient
import sys
sys.path.append("/var/www/falcon/pnw_stats_finder")
sys.path.append("/var/www/falcon/pnw_stats_finder/servlet/mlibs")
from servlet.settings import MAINTENANCE_MODE

__author__ = 'sxh112430'

from pw_client import PWClient
import os

rsc_key = 'resources'
collected_key = 'last_collected_date'
turns_since_collected_key = 'turns_since_collected'
owed_key = 'resources_owed'
total_paid_key = 'resources_paid'
can_collect_key = 'can_collect'
score_diff_key = 'score_diff'

class PWDB:
    def __init__(self, username=None, password=None, skip_pwclient=False):
        self.pwc = None
        self.__username = username
        self.__password = password

        if 'PWDBUSER' in os.environ:
            db_user = os.environ['PWDBUSER']
            db_pw = os.environ['PWDBPASS']
        else:
            with open("/var/www/falcon/dbauth") as uf:
                db_user = uf.readline().strip()
                db_pw = uf.readline().strip()
        if not skip_pwclient:
            self._init_pwc()

        self.mongo_client = MongoClient(host="falcon.spencer-hawkins.com")
        self.mongo_client.tax_db.authenticate(db_user, db_pw)
        self.tax_db = self.mongo_client.tax_db
        assert isinstance(self.tax_db, Database)

        self.nations = self.tax_db.nations
        assert isinstance(self.nations, Collection)

        self.tax_record_db = self.mongo_client.tax_record_db
        assert isinstance(self.tax_db, Database)

        self.falcon_records = self.tax_record_db.new_col
        assert isinstance(self.nations, Collection)

        self.falcon_withdraw_records = self.tax_record_db.falcon_withdraw_records
        assert isinstance(self.nations, Collection)

        self.graph_counter = self.tax_db.graph_counter
        assert isinstance(self.nations, Collection)

        self.falcon_counter = self.tax_record_db.falcon_counter
        assert isinstance(self.nations, Collection)

    def _init_pwc(self):
        if 'PWUSER' in os.environ:
            USERNAME = os.environ['PWUSER']
            PASS = os.environ['PWPASS']
        else:
            with open("/var/www/falcon/auth") as uf:
                USERNAME = uf.readline().strip()
                PASS = uf.readline().strip()
        if self.__username is None:
            self.__username = USERNAME
        if self.__password is None:
            self.__password = PASS

        self.pwc = PWClient(self.__username, self.__password)


    def nation_exists(self, nation_id):
        result = self.nations.find({'nation_id':nation_id})
        count = result.count()

        if count > 1:
            raise Exception("Malformed database!!! More than one nation exists at ID", nation_id)
        return count == 1

    def make_nation(self, nation_id):
        if self.nation_exists(nation_id):
            return False

        nation_obj = { 'nation_id': str(nation_id),
                       collected_key: self.pwc.get_current_date_in_datetime(),
                       owed_key: {},
                       turns_since_collected_key: 0,
                       total_paid_key: {}}

        if MAINTENANCE_MODE:
            nation_obj['maintenance'] = True

        return self.nations.insert_one(nation_obj).inserted_id

    def get_nation(self, nation_id, or_create=True):
        result = self.nations.find_one({'nation_id':str(nation_id)})
        if or_create:
            if result is None:
                self.make_nation(str(nation_id))  # Stick it in the DB
                result = self.get_nation(str(nation_id))  # lol, try again
        return result

    def list_members(self):
        # this function is mostly useless
        return [nation['nation_id'] for nation in self.nations.find()]

    def set_nation_attrib(self, nation_id, attrib, value):
        nation = self.get_nation(nation_id)
        nation[attrib] = value
        if not MAINTENANCE_MODE:
            self.nations.update({'nation_id':nation_id}, {"$set":nation}, upsert=True)


    def set_nation(self, nation_id, nation_dict):
        if not MAINTENANCE_MODE:
            self.nations.update({'nation_id':nation_id}, {"$set":nation_dict}, upsert=True)

    def increase_graph_counter(self):
        gcount = self.graph_counter.find_one()
        prev_num = gcount['graph_count']
        gcount['graph_count'] += 1
        self.graph_counter.update({'graph_count':prev_num}, {"$set":gcount})
        return prev_num + 1

    def increase_falcon_counter(self):
        fcount = self.falcon_counter.find_one()
        prev_num = fcount['falcon_record_count']
        fcount['falcon_record_count'] += 1
        self.falcon_counter.update({'falcon_record_count':prev_num}, {"$set":fcount})
        return prev_num + 1

    def increase_falcon_withdraw_counter(self):
        fcount = self.falcon_counter.find_one()
        prev_num = fcount['falcon_withdraw_count']
        fcount['falcon_withdraw_count'] += 1
        self.falcon_counter.update({'falcon_withdraw_count':prev_num}, {"$set":fcount})
        return prev_num + 1

    def create_record(self, time, gamedate, data):
        gametime_record = self.get_record_at_time(gamedate)
        record_obj = {
            'ticket':   self.increase_falcon_counter(),
            'realtime': time,
            'gametime': gamedate
        }
        record_obj.update(data)
        gametime_record['records'][record_obj['nation_id']] = record_obj
        self.falcon_records.update({'gametime': gamedate}, {"$set": gametime_record}, upsert=True)

    def create_withdraw_record(self, time, gamedate, data):
        ticket_no = self.increase_falcon_withdraw_counter()
        record_obj = {
            'ticket':   ticket_no,
            'realtime': time,
            'gametime': gamedate
        }
        record_obj.update(data)
        self.falcon_withdraw_records.insert_one(record_obj)
        return ticket_no

    def get_record_at_time(self, gametime, or_create=True):
        record = self.falcon_records.find_one({'gametime': gametime})
        if record is None and or_create:
            record = {'gametime':gametime, 'records': {}}
        return record

    def get_recent_withdraw_records(self, time_since):
        pass

    def get_recent_tax_records(self, time_since):
        time = datetime.now() - time_since
        return self.falcon_records.find({'gametime':{"$gt":time}})