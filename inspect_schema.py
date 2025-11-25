from flask_app.config.mysqlconnection import connectToMySQL

print("== Tables like option/choices via information_schema ==")
tables = connectToMySQL("mydb").query_db(
    """
    SELECT table_name FROM information_schema.tables
    WHERE table_schema = %(schema)s AND table_name IN ('option','choices','vote');
    """,
    {"schema": "mydb"}
)
print(tables)

print("\n== vote foreign keys ==")
fk_rows = connectToMySQL("mydb").query_db(
    """
    SELECT kcu.constraint_name, kcu.column_name, kcu.referenced_table_name, kcu.referenced_column_name
    FROM information_schema.key_column_usage kcu
    WHERE kcu.table_schema=%(schema)s AND kcu.table_name='vote' AND kcu.referenced_table_name IS NOT NULL;
    """,
    {"schema": "mydb"}
)
print(fk_rows)

print("\n== option sample rows ==")
opt = connectToMySQL("mydb").query_db("SELECT option_id, option_event_id, option_text FROM `option` ORDER BY option_id DESC LIMIT 5;")
print(opt)

print("\n== choices sample rows ==")
chs = connectToMySQL("mydb").query_db("SELECT * FROM choices ORDER BY 1 DESC LIMIT 5;")
print(chs)
