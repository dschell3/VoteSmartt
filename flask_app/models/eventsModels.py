from flask_app.config.mysqlconnection import connectToMySQL
import re

db = "mydb"

class Events:
    def __init__(self, data):
        self.event_id = data['event_id']
        self.title = data['title']
        self.description = data['description']
        self.start_time = data ['start_time']
        self.end_time = data ['end_time']
        self.created_byFK = data['created_byFK']
        self.created_at = data ['created_at']
        self.status = data ['status']
        

    @classmethod
    def createEvent(cls, data):
        query = '''
        INSERT INTO event (title, description, start_time, end_time, created_byFK, created_at, status)
        VALUES (%(title)s, %(description)s, %(start_time)s, %(end_time)s, %(created_byFK)s, NOW(), %(status)s);
        '''
        return connectToMySQL(db).query_db(query, data)

    @classmethod
    def editEvent(cls, data):
        query = '''
                UPDATE event \
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
                FROM event
                WHERE id = %(id)s \
                '''
        return connectToMySQL(db).query_db(query, data)

    @classmethod
    def getAll(cls):
        query = "SELECT * FROM event;"
        result = connectToMySQL(db).query_db(query)
        events = []
        for i in result:
            events.append(cls(i))
        return events

    @classmethod
    def getOne(cls, data):
        query = "SELECT * FROM event WHERE event_id = %(event_id)s;"
        result = connectToMySQL(db).query_db(query, data)
        if not result:
            return None
        return cls(result[0])

    @classmethod
    def getRecommendations(cls, data):
        """Return up to 3 upcoming event (by start_time) excluding the provided event_id."""
        query = """
        SELECT * FROM events
        WHERE event_id != %(event_id)s
          AND (start_time IS NOT NULL)
        ORDER BY start_time ASC
        LIMIT 3;
        """
        params = { 'event_id': data.get('event_id') }
        result = connectToMySQL(db).query_db(query, params)
        events = []
        if not result:
            return events
        for row in result:
            events.append(cls(row))
        return events




