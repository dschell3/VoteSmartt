"""
Diagnostics: list recent events with option counts and computed status.

Usage:
  python scripts/diagnostics/list_event_option_counts.py
"""
# Maintenance note: Added to list events with candidate counts; useful for quick verification, could become an admin API, and can be removed if redundant.
from pprint import pprint
from flask_app.config.mysqlconnection import connectToMySQL
from flask_app.models.eventsModels import Events

DB = "mydb"


def main():
    try:
        events = connectToMySQL(DB).query_db(
            "SELECT event_id,title,start_time,end_time FROM event ORDER BY event_id DESC LIMIT 20;"
        ) or []
        out = []
        for e in events:
            cnt_res = connectToMySQL(DB).query_db(
                "SELECT COUNT(*) AS c FROM `option` WHERE option_event_id=%(eid)s;",
                {"eid": e["event_id"]},
            ) or []
            count = cnt_res[0]["c"] if cnt_res else 0
            status = Events.compute_status(e["start_time"], e["end_time"])
            out.append(
                {"event_id": e["event_id"], "title": e["title"], "status": status, "options": count}
            )
        pprint(out)
    except Exception as ex:
        print("ERROR:", ex)


if __name__ == "__main__":
    main()
