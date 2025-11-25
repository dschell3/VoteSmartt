# Maintenance note: Added to quickly inspect tables/foreign-keys; helpful for debugging, could be improved with CLI args, and safe to delete if you prefer DB tools.
"""
Diagnostics: inspect existence of core tables and vote foreign keys.

Usage:
  python scripts/diagnostics/inspect_schema.py
"""
from pprint import pprint
from flask_app.config.mysqlconnection import connectToMySQL

DB = "mydb"


def list_tables():
    return connectToMySQL(DB).query_db(
        """
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = %(schema)s AND table_name IN ('option','choices','vote','event','user');
        """,
        {"schema": DB}
    ) or []


def list_vote_fks():
    return connectToMySQL(DB).query_db(
        """
        SELECT kcu.constraint_name, kcu.column_name, kcu.referenced_table_name, kcu.referenced_column_name
        FROM information_schema.key_column_usage kcu
        WHERE kcu.table_schema=%(schema)s AND kcu.table_name='vote' AND kcu.referenced_table_name IS NOT NULL;
        """,
        {"schema": DB}
    ) or []


def sample_rows():
    opt = connectToMySQL(DB).query_db(
        "SELECT option_id, option_event_id, option_text FROM `option` ORDER BY option_id DESC LIMIT 5;"
    ) or []
    chs = connectToMySQL(DB).query_db(
        "SELECT * FROM choices ORDER BY 1 DESC LIMIT 5;"
    ) or []
    return {"option": opt, "choices": chs}


def main():
    print("== Tables ==")
    pprint(list_tables())

    print("\n== vote foreign keys ==")
    pprint(list_vote_fks())

    print("\n== samples ==")
    pprint(sample_rows())


if __name__ == "__main__":
    main()
