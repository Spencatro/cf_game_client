from db_wrapper import DBWrapper


class WarbotDB(DBWrapper):
    def __init__(self):
        super(WarbotDB, self).__init__()
        self.beige_checks = self.pnw_db["beige_checks"]
        self.war_watches = self.pnw_db["war_watches"]
        self.global_beige_watches = self.pnw_db["global_beige_watches"]

    def create_personal_beige_watch_record(self, slack_uid, nation_id, nation_name, beige_turns):
        record = {"requesting_user_slack_id": slack_uid,
                  "nation_name": nation_name,
                  "nation_id": nation_id,
                  "state": "watch"}
        if beige_turns == 1:
            record["state"] = "notify"
        self.beige_checks.insert_one(record)