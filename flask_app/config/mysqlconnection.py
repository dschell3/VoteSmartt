import pymysql.cursors
import os
from urllib.parse import urlparse

def get_db_config():
    """Parse database configuration from environment variable or use defaults."""
    database_url = os.environ.get('CLEARDB_DATABASE_URL')
    
    if database_url:
        # Parse the URL: mysql://user:password@host:port/database
        parsed = urlparse(database_url)
        
        return {
            'host': parsed.hostname,
            'port': parsed.port or 3306,
            'user': parsed.username,
            'password': parsed.password,
            'db': parsed.path.lstrip('/'),  # Remove leading slash
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor,
            'autocommit': True,
            'ssl': {'ssl': True}  # Aiven requires SSL
        }
    else:
        # Fallback for local development
        return {
            'host': 'localhost',
            'port': 3306,
            'user': 'root',
            'password': 'rootroot',
            'db': 'votesmartt',
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor,
            'autocommit': True,
        }

DB_CONFIG = get_db_config()

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


# import pymysql.cursors
# class MySQLConnection:
#     def __init__(self, db):
#         connection = pymysql.connect(host = 'localhost',
#                                     user = 'root', # change the user and password as needed
#                                     password = 'rootroot', 
#                                     db = db,
#                                     charset = 'utf8mb4',
#                                     cursorclass = pymysql.cursors.DictCursor,
#                                     autocommit = True)
#         self.connection = connection
#     def query_db(self, query, data=None):
#         with self.connection.cursor() as cursor:
#             try:
#                 query = cursor.mogrify(query, data)
#                 print("Running Query:", query)

#                 executable = cursor.execute(query, data)
#                 if query.lower().find("insert") >= 0:
#                     # if the query is an insert, return the id of the last row, since that is the row we just added
#                     self.connection.commit()
#                     return cursor.lastrowid
#                 elif query.lower().find("select") >= 0:
#                     # if the query is a select, return everything that is fetched from the database
#                     # the result will be a list of dictionaries
#                     result = cursor.fetchall()
#                     return result
#                 else:
#                     # if the query is not an insert or a select, such as an update or delete, commit the changes
#                     # return nothing
#                     self.connection.commit()
#             except Exception as e:
#                 # in case the query fails
#                 print("Something went wrong", e)
#                 return False
#             finally:
#                 # close the connection
#                 self.connection.close() 
# # this connectToMySQL function creates an instance of MySQLConnection, which will be used by server.py
# # connectToMySQL receives the database we're using and uses it to create an instance of MySQLConnection
# def connectToMySQL(db):
#     return MySQLConnection(db)


