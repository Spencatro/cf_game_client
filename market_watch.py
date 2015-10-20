import os
import pymongo

__author__ = 'shawkins'
mongo_host = os.environ.get("mongodb_url")
mongo_port = int(os.environ.get("mongodb_port"))
mongo_dbname = os.environ.get("mongodb_dbname")
mongo_user = os.environ.get("mongodb_user")
mongo_password = os.environ.get("mongodb_password")

mongo = pymongo.MongoClient(host=mongo_host, port=mongo_port)
pnw_db = mongo[mongo_dbname]
pnw_db.authenticate(mongo_user, mongo_password)
test_collection = pnw_db["test_collection"]
test_collection.insert_one({"this is a test!": "cool"})