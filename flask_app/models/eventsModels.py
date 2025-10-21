from flask_app.config.mysqlconnection import connectToMySQL
import re
from datetime import datetime
# Should dt_parse be imported from dateutil? or move the method created in controller here?


db = "mydb"

# columns in event table are: event_id, title, description, start_time, end_time,
#                             created_at, created_byFK, status

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
        UPDATE event
        SET title       = %(title)s,
            description = %(description)s,
            start_time  = %(start_time)s,
            end_time    = %(end_time)s
        WHERE event_id  = %(event_id)s;
        '''
        return connectToMySQL(db).query_db(query, data)

    @classmethod
    def deleteEvent(cls, data):
        query = '''
                DELETE FROM event
                WHERE event_id = %(event_id)s;
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
        SELECT * FROM event
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

    @classmethod
    def getOpenEvents(cls):
        query = """
        SELECT e.*
        FROM event e
        WHERE e.start_time <= NOW() AND e.end_time > NOW()
        ORDER BY e.start_time ASC;
        """
        return connectToMySQL(cls.db).query_db(query)
    
    @classmethod
    def getAllUpcoming(cls):
        query = """
        SELECT e.*
        FROM event e
        WHERE e.start_time > NOW()
        ORDER BY e.start_time ASC;
        """
        return connectToMySQL(cls.db).query_db(query)
    
    @classmethod
    def getAllClosed(cls):
        query = """
        SELECT e.*
        FROM event e
        WHERE e.end_time <= NOW()
        ORDER BY e.end_time DESC;
        """
        return connectToMySQL(cls.db).query_db(query)
    
    @classmethod
    def getAllWithStatus(cls):
        query = """
        SELECT
          e.*,
          CASE
            WHEN NOW() < e.start_time THEN 'upcoming'
            WHEN NOW() >= e.end_time THEN 'closed'
            ELSE 'open'
          END AS status
        FROM event e
        ORDER BY e.start_time ASC;
        """
        return connectToMySQL(cls.db).query_db(query)
    
    # was at top of eventsController.py, moved here for reuse
    @staticmethod
    def _compute_status(start_raw, end_raw):
        now = datetime.now()
        start = Events._parse_datetime(start_raw)
        end = Events._parse_datetime(end_raw)

        if not start and not end:
            return 'Unknown'
        if start and end:
            if now < start:
                return 'Waiting'
            if now > end:
                return 'Closed'
            return 'Open'
        if start and not end:
            return 'Waiting' if now < start else 'Open'
        if end and not start:
            return 'Closed' if now > end else 'Open'
        return 'Unknown'

    # was at top of eventsController.py, moved here for reuse
    @staticmethod
    def _parse_datetime(value):
        """Try to parse a DB value into a naive datetime. Return None if impossible."""
        if not value:
            return None
        # If it's already a datetime object
        if isinstance(value, datetime):
            return value
        # Try common string formats
        fmts = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]
        for f in fmts:
            try:
                return datetime.strptime(value, f)
            except Exception:
                continue
        # Fallback: try fromisoformat
        try:
            return datetime.fromisoformat(value)
        except Exception:
            return None
