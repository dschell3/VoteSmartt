from datetime import datetime
from flask_app.models.eventsModels import Events
from flask_app.config.mysqlconnection import connectToMySQL

db = "mydb"

class Vote:
    
    # columns in vote table are: vote_id, voted_at, vote_user_id, vote_option_id
    
    def __init__(self, data):
        self.vote_id = data['vote_id']
        self.voted_at = data['voted_at']
        self.vote_user_id = data['vote_user_id']
        self.vote_option_id = data['vote_option_id']

    @classmethod
    def getByID(cls, data):
        query = "SELECT * FROM vote WHERE vote_id = %(vote_id)s;"
        result = connectToMySQL(db).query_db(query, data)
        return cls(result[0]) if result else None
    
    @classmethod
    def getByUserAndEvent(cls, data):
        # gets the ballot (vote) for a specific user in a specific event
        # enforces one vote per user per event
        query = """
        SELECT v.* FROM vote v
        JOIN `option` o ON o.option_id = v.vote_option_id
        WHERE v.vote_user_id = %(user_id)s
        AND o.option_event_id = %(event_id)s
        LIMIT 1;
        """
        result = connectToMySQL(db).query_db(query, data)
        return cls(result[0]) if result else None
    
    @classmethod  
    def getRecentForUser(cls, data):
        query = """
        SELECT * FROM vote
        WHERE vote_user_id = %(user_id)s
        ORDER BY voted_at DESC
        LIMIT %(limit)s;
        """
        result = connectToMySQL(db).query_db(query, data)
        return [cls(r) for r in (result or [])]
    
    @classmethod
    def castVote(cls, data):
        query = '''
        INSERT INTO vote (voted_at, vote_user_id, vote_option_id)
        VALUES (NOW(), %(vote_user_id)s, %(vote_option_id)s);
        '''
        return connectToMySQL(db).query_db(query, data)
    
    @classmethod
    def changeVote(cls, data):
        query = """
        UPDATE vote v
        JOIN `option` o ON o.option_id = v.vote_option_id
        SET v.vote_option_id = %(new_option_id)s, v.voted_at = NOW()
        WHERE v.vote_user_id = %(user_id)s
        AND o.option_event_id = %(event_id)s;
        """
        return connectToMySQL(db).query_db(query, data)
    
    @classmethod
    def deleteVote(cls, data):
        query = """
        DELETE v FROM vote v
        JOIN `option` o ON o.option_id = v.vote_option_id
        WHERE v.vote_user_id = %(user_id)s
          AND o.option_event_id = %(event_id)s;
        """
        return connectToMySQL(db).query_db(query, data)
    
    @classmethod
    def tallyVotesForEvent(cls, data):
        # returns list of options with their vote counts for a given event
        query = """
        SELECT o.option_id, o.option_text, COUNT(v.vote_id) AS votes
        FROM `option` o
        LEFT JOIN vote v
        ON v.vote_option_id = o.option_id
        WHERE o.option_event_id = %(event_id)s
        GROUP BY o.option_id, o.option_text
        ORDER BY votes DESC, o.option_text ASC;
        """
        return connectToMySQL(db).query_db(query, data)
    
    @classmethod
    def isEditable(self, event: 'Events', now: datetime) -> bool:
        # Determine if the vote can be edited based on the event's status.
        return event.isOpen(event.start_time, event.end_time, now)

    