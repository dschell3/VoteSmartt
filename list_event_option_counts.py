from flask_app.config.mysqlconnection import connectToMySQL  # Maintenance note: Legacy diagnostic script; superseded by scripts/diagnostics version; safe to delete when organized.
from flask_app.models.eventsModels import Events

try:
    events = connectToMySQL().query_db("SELECT event_id,title,start_time,end_time FROM event ORDER BY event_id DESC LIMIT 20;") or []
    out = []
    for e in events:
        cnt_res = connectToMySQL().query_db("SELECT COUNT(*) AS c FROM `option` WHERE option_event_id=%(eid)s;", {'eid': e['event_id']}) or []
        count = cnt_res[0]['c'] if cnt_res else 0
        status = Events.compute_status(e['start_time'], e['end_time'])
        out.append({ 'event_id': e['event_id'], 'title': e['title'], 'status': status, 'options': count })
    print(out)
except Exception as ex:
    print('ERROR listing events/options:', ex)
