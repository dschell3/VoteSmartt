from flask_app.config.mysqlconnection import connectToMySQL  # Maintenance note: Minimal existence probe; superseded by diagnostics/inspect_schema; safe to delete.

try:
    res = connectToMySQL().query_db("SHOW TABLES LIKE 'option';")
    print(res)
except Exception as e:
    print('ERROR:', e)
