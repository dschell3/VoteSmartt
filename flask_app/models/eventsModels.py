from flask_app.config.mysqlconnection import connectToMySQL
import re

db = "votingSystem"

class Events:
    def __init__(self, data):
        self.event_id = data['event_id']
        self.title = data['title']
        self.description = data['description']
        self.start_time = data ['start_time']
        self.end_time = data ['end_time']
        self.created_by = data['created_by']
        self.created_at = data ['created_at']
        self.event_user_fk = data ['event_user_fk']

    @classmethod
    def createEvent(cls, data):
        query = '''
        INSERT INTO events (title, description, start_time, end_time, created_by, created_at, event_user_fk)
        VALUES (%(title)s, %(description)s, %(start_time)s, %(end_time)s, %(created_by)s, NOW(), %(event_user_fk)s);
        '''
        return connectToMySQL(db).query_db(query, data)

    @classmethod
    def editEvent(cls, data):
        query = '''
                UPDATE events \
                SET title       = %(title)s, \
                    description = %(description)s, \
                    start_time  = %(start_time)s, \
                    end_time    = %(end_time)s, \
                    modified_at = %(modified_at)s
                WHERE id = %(id)s \
                '''
        return connectToMySQL(db).query_db(query, data)

    @classmethod
    def deleteEvent(cls, data):
        query = '''
                DELETE
                FROM events
                WHERE id = %(id)s \
                '''
        return connectToMySQL(db).query_db(query, data)

    @classmethod
    def getAll(cls):
        query = "SELECT * FROM events;"
        result = connectToMySQL(db).query_db(query)
        events = []
        for i in result:
            events.append(cls(i))
        return events

    @classmethod
    def getSpecific(cls, data):
        query = "SELECT * FROM events WHERE title = %(title)s;"
        result = connectToMySQL(db).query_db(query, data)
        if not result:
            return None
        return cls(result[0])




