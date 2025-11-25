"""Run DB migration 0001_add_reset_columns.sql using the project's DB config.

This script will:
 - create a quick snapshot table `user_backup` if it doesn't exist
 - apply the SQL file `migrations/0001_add_reset_columns.sql`

Run this from the project root inside your venv:
  source venv/bin/activate
  python3 scripts/run_migration.py

The script uses the DB config in `flask_app/config/mysqlconnection.py` so no
credentials need to be passed on the command line.
"""
from flask_app.config.mysqlconnection import connectToMySQL
import pathlib
import sys

SQL_PATH = pathlib.Path('migrations/0001_add_reset_columns.sql')

if not SQL_PATH.exists():
    print(f"Migration file not found: {SQL_PATH}")
    sys.exit(1)

sql = SQL_PATH.read_text()

def run_query(query):
    db = connectToMySQL('mydb')
    return db.query_db(query)

def backup_user_table():
    print('Creating user_backup snapshot (if not exists)...')
    # Create a snapshot copy of the current user table. Use LIKE + INSERT so
    # we preserve schema (including primary key) which some servers require.
    q1 = "CREATE TABLE IF NOT EXISTS user_backup LIKE user;"
    res1 = run_query(q1)
    if res1 is False:
        print('Failed to create user_backup table structure.')
        return False

    # Truncate existing snapshot and repopulate
    q2 = "TRUNCATE TABLE user_backup;"
    res2 = run_query(q2)
    if res2 is False:
        print('Failed to truncate user_backup table.')
        return False

    q3 = "INSERT INTO user_backup SELECT * FROM user;"
    res3 = run_query(q3)
    if res3 is False:
        print('Failed to copy data into user_backup.')
        return False

    print('Backup created (or updated) in user_backup.')
    return True

def apply_migration():
    print('Applying migration SQL...')
    res = run_query(sql)
    if res is False:
        print('Migration failed. See DB output above.')
        return False
    print('Migration applied successfully.')
    return True

if __name__ == '__main__':
    ok = backup_user_table()
    if not ok:
        print('Aborting migration due to backup failure.')
        sys.exit(1)

    ok = apply_migration()
    if not ok:
        sys.exit(2)

    print('Done.')
