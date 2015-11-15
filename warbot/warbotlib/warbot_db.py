from db_wrapper import DBWrapper


class WarbotDB(DBWrapper):
    def __init__(self):
        super(WarbotDB, self).__init__()
        self.beige_checks = self.pnw_db["beige_checks"]
        self.war_watches = self.pnw_db["war_watches"]
        self.global_beige_watches = self.pnw_db["global_beige_watches"]
        self.registered_users = self.pnw_db["registered_users"]

    def set_war_to_watch(self, slack_uid, slack_username, nation_id, war_id):
        record = {
            "requesting_user_slack_id": slack_uid,
            "requesting_user_slack_username": slack_username
        }

    def create_personal_beige_watch_record(self, slack_uid, nation_id, nation_name, beige_turns):
        record = {
            "requesting_user_slack_id": slack_uid,
            "nation_name": nation_name,
            "nation_id": nation_id,
            "state": "watch"
        }
        if beige_turns == 1:
            record["state"] = "notify"
        if self.beige_checks.find({"requesting_user_slack_id": slack_uid, "nation_id": nation_id}).count() < 1:
            self.beige_checks.insert_one(record)
            return True
        return False

    def update_user_map(self, slack_uid, slack_username, pnw_nation_id, pnw_nation_name):
        obj = {
            "slack_uid": slack_uid,
            "slack_username": slack_username,
            "nation_id": str(pnw_nation_id),
            "nation_name": pnw_nation_name
        }
        self.registered_users.update({"slack_uid": slack_uid}, obj, upsert=True)
