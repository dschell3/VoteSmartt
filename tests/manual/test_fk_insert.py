"""
Manual check: verify vote FK to `option` allows insert and cleanup.
Run only against a development database.
"""
"""# Maintenance note: Quick smoke test for FK health; could be replaced with pytest; delete if automated tests cover this."""
from flask_app.config.mysqlconnection import connectToMySQL

DB = 'mydb'

db = connectToMySQL(DB)

user = db.query_db("SELECT user_id FROM user ORDER BY user_id DESC LIMIT 1;")
opt = db.query_db("SELECT option_id FROM `option` ORDER BY option_id DESC LIMIT 1;")
print('user:', user)
print('option:', opt)

if user and opt:
    uid = user[0]['user_id']
    oid = opt[0]['option_id']
    ins = db.query_db("INSERT INTO vote (voted_at, vote_user_id, vote_option_id) VALUES (NOW(), %s, %s);", (uid, oid))
    print('insert result:', ins)
    # cleanup
    if ins:
        db.query_db("DELETE FROM vote WHERE vote_id=%s;", (ins,))
        print('cleanup ok')
else:
    print('missing user or option; nothing to insert')
