import pymysql.cursors

DB_CONFIG = {
    'host': 'mysql-34862870-votesystemdb.d.aivencloud.com',
    'port': 18174,
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
        config = DB_CONFIG.copy()
        if db:
            config['db'] = db
        self.connection = pymysql.connect(**config)

    def query_db(self, query, data=None):
        with self.connection.cursor() as cursor:
            try:
                executable = cursor.execute(query, data)
                if query.lower().startswith("select"):
                    return cursor.fetchall()
                elif query.lower().startswith("insert"):
                    self.connection.commit()
                    return cursor.lastrowid
                else:
                    self.connection.commit()
            except Exception as e:
                print("Database error:", e)
                return False
            finally:
                # Do NOT close the connection here if you plan to reuse it
                pass

# This helper function is used in models
def connectToMySQL(db=None):
    return MySQLConnection(db)
