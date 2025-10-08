import pymysql.cursors

DB_CONFIG = {
    'host': 'avinadmin-projectgolf.l.aivencloud.com',
    'port': 19352,
    'user': 'avnadmin',
    'password': '***REMOVED***',
    'db': 'defaultdb', 
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
    'autocommit': True,
    'ssl': {'ca': 'flask_app/config/ca.pem'}  
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
                query_type = query.strip().lower() 
                executable = cursor.execute(query, data)

                if query_type.startswith("select"):
                    result = cursor.fetchall()
                    return result

                elif query_type.startswith("insert"):
                    self.connection.commit()
                    new_id = cursor.lastrowid
                    return new_id

                else:
                    self.connection.commit()
                    return True

            except Exception as e:
                print("Database error:", e)
                return False
            finally:
                pass 

def connectToMySQL(db=None):
    return MySQLConnection(db)
