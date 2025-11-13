"""Utility script to create the password_reset_token table using existing DB config.
Safe to run multiple times; uses IF NOT EXISTS.
"""
from flask_app.config.mysqlconnection import connectToMySQL
import os

SQL_PATH = os.path.join('docs', 'sql', 'password_reset_token.sql')

def main():
    # Read SQL file
    if not os.path.exists(SQL_PATH):
        print(f"SQL file not found: {SQL_PATH}")
        return
    with open(SQL_PATH, 'r', encoding='utf-8') as f:
        sql_text = f.read()

    # Split into statements (rudimentary) and execute
    conn = connectToMySQL('mydb')
    statements = [s.strip() for s in sql_text.split(';') if s.strip()]
    for stmt in statements:
        # Ensure each ends with semicolon for our wrapper (optional)
        if not stmt.endswith(';'):
            stmt_exec = stmt + ';'
        else:
            stmt_exec = stmt
        res = conn.query_db(stmt_exec)
        print(f"Executed: {stmt[:50]}... -> {res}")

    # Verify creation
    verify = conn.query_db("SHOW TABLES LIKE 'password_reset_token';")
    if verify:
        print("SUCCESS: password_reset_token table exists.")
    else:
        print("FAIL: password_reset_token table not found after execution.")

if __name__ == '__main__':
    main()
