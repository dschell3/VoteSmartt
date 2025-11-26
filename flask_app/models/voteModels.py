from datetime import datetime
from flask_app.models.eventsModels import Events, compute_status
from flask_app.config.mysqlconnection import connectToMySQL

db = "mydb"

class Vote:
    
    # columns in vote table are: vote_id, voted_at, vote_user_id, vote_option_id
    db = db

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
        SELECT 
            v.vote_id,
            v.voted_at,
            e.event_id,
            e.title as event_name,
            e.start_time,
            e.end_time,
            o.option_text
        FROM vote v
        JOIN `option` o ON o.option_id = v.vote_option_id
        JOIN event e ON e.event_id = o.option_event_id
        WHERE v.vote_user_id = %(user_id)s
        ORDER BY v.voted_at DESC
        LIMIT %(limit)s;
        """
        result = connectToMySQL(db).query_db(query, data)
        
        if not result:
            return []
        
        votes = []
        for row in result:
            status = compute_status(row['start_time'], row['end_time'])
            votes.append({
                'vote_id': row['vote_id'],
                'event_name': row['event_name'],
                'date': row['voted_at'],
                'status': status.lower(),
                'vote_type': row['option_text'],
                'event_id': row['event_id']
            })
        
        return votes
        
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
    
    # Gets comprehensive voting statistics for user dashboard
    @classmethod
    def getStatsForUser(cls, data):
        """Get comprehensive voting statistics for a user."""
        user_id = data['user_id']
        
        # Query 1: Get total votes and last vote date in one query
        query_votes = """
        SELECT 
            COUNT(*) as total_votes,
            MAX(voted_at) as last_vote_date
        FROM vote
        WHERE vote_user_id = %(user_id)s;
        """
        result_votes = connectToMySQL(db).query_db(query_votes, {'user_id': user_id})
        
        # Handle empty results safely
        if not result_votes or result_votes is False:
            return {
                'total_votes': 0,
                'participation_rate': 0.0,
                'events_participated': 0,
                'last_vote_date': 'Never'
            }
        
        total_votes = result_votes[0]['total_votes'] or 0
        last_vote_date = result_votes[0]['last_vote_date']
        
        # Query 2: Count unique events user has participated in
        query_events = """
        SELECT COUNT(DISTINCT o.option_event_id) as events_participated
        FROM vote v
        JOIN `option` o ON o.option_id = v.vote_option_id
        WHERE v.vote_user_id = %(user_id)s;
        """
        result_events = connectToMySQL(db).query_db(query_events, {'user_id': user_id})
        
        # Safe access with default
        events_participated = 0
        if result_events and len(result_events) > 0:
            events_participated = result_events[0].get('events_participated', 0) or 0
        
        # Query 3: Calculate participation rate
        query_available = """
        SELECT COUNT(*) as total_available
        FROM event
        WHERE end_time < NOW() 
        AND created_byFK != %(user_id)s;
        """
        result_available = connectToMySQL(db).query_db(query_available, {'user_id': user_id})
        
        # Safe access with default
        total_available = 0
        if result_available and len(result_available) > 0:
            total_available = result_available[0].get('total_available', 0) or 0
        
        # Calculate participation rate
        if total_available > 0:
            participation_rate = round((events_participated / total_available) * 100, 1)
        else:
            participation_rate = 0.0
        
        # Format last vote date
        if last_vote_date:
            if isinstance(last_vote_date, str):
                try:
                    from datetime import datetime
                    last_vote_date = datetime.strptime(last_vote_date, '%Y-%m-%d %H:%M:%S')
                except:
                    pass
            last_vote_display = last_vote_date.strftime('%b %d, %Y') if hasattr(last_vote_date, 'strftime') else str(last_vote_date)
        else:
            last_vote_display = 'Never'
        
        return {
            'total_votes': total_votes,
            'participation_rate': participation_rate,
            'events_participated': events_participated,
            'last_vote_date': last_vote_display
        }
    
    @staticmethod
    def isEditable(event: 'Events') -> bool:
        # Determine if the vote can be edited based on the event's status.
        return compute_status(event.start_time, event.end_time) == "Open"

    