import os
from pymongo import MongoClient

__author__ = 'shawkins'


class DBWrapper(object):

    def __init__(self):
        mongo_host = os.environ.get("mongodb_url")
        mongo_port = int(os.environ.get("mongodb_port"))
        mongo_dbname = os.environ.get("mongodb_dbname")
        mongo_user = os.environ.get("mongodb_user")
        mongo_password = os.environ.get("mongodb_password")
        mongo = MongoClient(host=mongo_host, port=mongo_port)
        self.pnw_db = mongo[mongo_dbname]
        self.pnw_db.authenticate(mongo_user, mongo_password)
