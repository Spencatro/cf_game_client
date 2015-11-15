import datetime
from db_wrapper import DBWrapper

class MarketWatchDB(DBWrapper):
    """ this will replace pnw_db.py eventually """

    def __init__(self):
        super(MarketWatchDB, self).__init__()
        self.market_watch_collection = self.pnw_db["market_watch"]
        self.market_watch_notification_collection = self.pnw_db["market_watch_notifications"]

    def add_market_watch_record(self, resource_dict):
        today = datetime.datetime.now()
        record = {"values": resource_dict,
                  "time": today}
        return self.market_watch_collection.insert_one(record)

    def get_notification_counts(self):
        return self.market_watch_notification_collection.find().sort("_id", pymongo.DESCENDING)[0]

    def _increment_notification_for_type(self, item_type, record_type, percentage):
        percentage_key = "last_"+record_type+"_percentage"
        n_record = self.get_notification_counts()
        n_id = n_record["_id"]
        n_record[item_type][record_type] += 1
        last_percentage = n_record[item_type][percentage_key]
        if abs(abs(last_percentage) - abs(percentage)) > 10:
            n_record[item_type][record_type] = 1
            n_record[item_type][percentage_key] = percentage
        count = n_record[item_type][record_type]
        okay_to_notify = count <= 1
        self.market_watch_notification_collection.update({"_id": n_id}, n_record)
        return okay_to_notify

    def increment_buy_counter_for_type(self, item_type, percentage):
        return self._increment_notification_for_type(item_type, "buy", percentage)

    def increment_sell_counter_for_type(self, item_type, percentage):
        return self._increment_notification_for_type(item_type, "sell", percentage)

    def increment_buy_offer_counter_for_type(self, item_type):
        return self._increment_notification_for_type(item_type, "buy_offer", 0)

    def init_new_counter(self, realstring_dict):
        new_record = {}
        for key in realstring_dict.keys():
            new_record[key] = {"buy": 0, "last_buy_percentage": 0, "sell": 0, "last_sell_percentage": 0, "buy_offer": 0, "last_buy_offer_percentage": 0}
        self.market_watch_notification_collection.insert_one(new_record)

    def _reset_counter(self, item_type, record_type):
        percentage_key = "last_"+record_type+"_percentage"
        n_record = self.get_notification_counts()
        n_id = n_record["_id"]
        n_record[item_type][record_type] = 0
        n_record[item_type][percentage_key] = 0
        self.market_watch_notification_collection.update({"_id": n_id}, n_record)

    def reset_buy_counter(self, item_type):
        self._reset_counter(item_type, "buy")

    def reset_sell_counter(self, item_type):
        self._reset_counter(item_type, "buy")

    def reset_buy_offer_counter(self, item_type):
        self._reset_counter(item_type, "buy_offer")