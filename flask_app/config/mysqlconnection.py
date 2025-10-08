import pymysql.cursors

DB_CONFIG = {
    'host': 'avinadmin-projectgolf.l.aivencloud.com',
    'port': 19352,
    'user': 'avnadmin',
    'password': '***REMOVED***',
    'db': 'defaultdb',  # default database
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
    'autocommit': True,
    'ssl': {'ca': 'flask_app/config/ca.pem'}  # Path to CA certificate
}

class MySQLConnection:
    def __init__(self, db=None):
        print("DEBUG: Connecting to DB ->", db)
        config = DB_CONFIG.copy()
        if db:
            config['db'] = db
        self.connection = pymysql.connect(**config)

    def query_db(self, query, data=None):
        with self.connection.cursor() as cursor:
            try:
                query_type = query.strip().lower()  # ✅ remove leading/trailing spaces/newlines
                executable = cursor.execute(query, data)

                if query_type.startswith("select"):
                    result = cursor.fetchall()
                    # print(f"DEBUG: SELECT returned {len(result)} rows")
                    return result

                elif query_type.startswith("insert"):
                    self.connection.commit()
                    new_id = cursor.lastrowid
                    print(f"DEBUG: INSERT successful, new ID = {new_id}")
                    return new_id

                else:
                    self.connection.commit()
                    print("DEBUG: Non-SELECT/INSERT query executed successfully.")
                    return True

            except Exception as e:
                print("Database error:", e)
                return False
            finally:
                pass  # Connection stays open for reuse

# This helper function is used in models
def connectToMySQL(db=None):
    return MySQLConnection(db)
