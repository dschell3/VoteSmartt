'''
==============================================================================
Vote Model - Manages ballot/vote records for voting events
==============================================================================

This module provides the Vote class for managing user votes (ballots) within
the VoteSmartt system. Each vote links a user to their selected option within
an event, enforcing the one-vote-per-user-per-event business rule.

Database Table: vote
Columns:
    - vote_id (int): Primary key, auto-increment
    - voted_at (datetime): Timestamp when vote was cast/updated
    - vote_user_id (int): Foreign key to user.user_id
    - vote_option_id (int): Foreign key to option.option_id

Class Relationships:
    - Vote *--1 User: Many votes can be cast by one user (across events)
    - Vote *--1 Option: Many votes can select one option
    - Vote *--1 Event: Indirectly through Option (option_event_id)

VoteSmartt Rules:
    - Each user can cast only ONE vote per event (enforced via getByUserAndEvent)
    - Votes can only be cast/changed/deleted when event status is 'Open'
    - Admins (isAdmin=1) cannot cast votes (if super admin implemented in future)
    - Event creators cannot vote on their own events
    - Votes are timestamped with voted_at updated on each change
'''

from flask_app.models.eventsModels import Events, compute_status
from flask_app.config.mysqlconnection import connectToMySQL

db = "mydb"

class Vote:
    """
    Represents a user's vote/ballot for a specific option within an event.
    Attributes correspond to the 'vote' database table.
    """
    db = db         # DB identifier for mySQL connection

    def __init__(self, data):
        """
        Initialize a Vote instance from database row data.
        """
        self.vote_id = data['vote_id']
        self.voted_at = data['voted_at']
        self.vote_user_id = data['vote_user_id']
        self.vote_option_id = data['vote_option_id']

    # =========================================================================
    # CREATE OPERATIONS - Cast new votes
    # =========================================================================

    @classmethod
    def castVote(cls, data):
        """
        Inserts a new vote record for a user selecting an option.
        
        Args:
            data (dict): Dictionary containing:
                         - 'vote_user_id' (int): ID of user casting vote
                         - 'vote_option_id' (int): ID of selected option
        
        Returns:
            int: The vote_id of the newly created vote, or False on failure.
        """
        query = '''
        INSERT INTO vote (voted_at, vote_user_id, vote_option_id)
        VALUES (NOW(), %(vote_user_id)s, %(vote_option_id)s);
        '''
        return connectToMySQL(db).query_db(query, data)

    # =========================================================================
    # READ OPERATIONS - Retrieve vote records
    # =========================================================================

    @classmethod
    def getByID(cls, data):
        """
        Retrieve a single vote by its primary key.
        
        Args:
            data (dict): Dictionary containing:
                         - 'vote_id' (int): ID of vote to retrieve
        
        Returns:
            Vote: Vote object if found, None otherwise.
        """
        query = "SELECT * FROM vote WHERE vote_id = %(vote_id)s;"
        result = connectToMySQL(db).query_db(query, data)
        return cls(result[0]) if result else None
    
    @classmethod
    def getByUserAndEvent(cls, data):
        """
        Retrieve a user's vote for a specific event.
        
        This is the primary method for enforcing the one-vote-per-user-per-event
        rule. Since votes link to options (not directly to events), this method
        joins through the option table to find votes by event.
        
        Args:
            data (dict): Dictionary containing:
                         - 'user_id' (int): ID of the user
                         - 'event_id' (int): ID of the event
        
        Returns:
            Vote: Vote object if user has voted in event, None otherwise.
        """
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
        """
        Retrieve a user's recent voting history for dashboard display.
        Used on the user dashboard to show recent activity.
        
        Args:
            data (dict): Dictionary containing:
                         - 'user_id' (int): ID of the user
                         - 'limit' (int): Maximum number of votes to return
        
        Returns:
            list[dict]: List of vote records, each containing:
                        - 'vote_id' (int): Vote's ID
                        - 'event_name' (str): Title of the event
                        - 'date' (datetime): When vote was cast
                        - 'status' (str): Event status (lowercase)
                        - 'vote_type' (str): Selected option text
                        - 'event_id' (int): Event's ID for linking
                        Returns empty list if user has no votes.
        """
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
        
        # Transform results into desired format
        votes = []
        for row in result:
            # Determine event status
            status = compute_status(row['start_time'], row['end_time'])
            # Build vote record formatted for dashboard
            votes.append({
                'vote_id': row['vote_id'],
                'event_name': row['event_name'],
                'date': row['voted_at'],
                'status': status.lower(),
                'vote_type': row['option_text'],
                'event_id': row['event_id']
            })
        
        return votes

    # =========================================================================
    # UPDATE OPERATIONS - Modify existing votes
    # =========================================================================

    @classmethod
    def changeVote(cls, data):
        """
        Update a user's existing vote to a different option.
        
        Finds the user's vote within the specified event and updates the
        selected option. Also updates voted_at to the current timestamp.
        
        Args:
            data (dict): Dictionary containing:
                         - 'user_id' (int): ID of user changing vote
                         - 'event_id' (int): ID of event containing vote
                         - 'new_option_id' (int): ID of new option selection
        
        Returns:
            bool: True if update successful, False otherwise.
        """
        query = """
        UPDATE vote v
        JOIN `option` o ON o.option_id = v.vote_option_id
        SET v.vote_option_id = %(new_option_id)s, v.voted_at = NOW()
        WHERE v.vote_user_id = %(user_id)s
        AND o.option_event_id = %(event_id)s;
        """
        return connectToMySQL(db).query_db(query, data)
    
    # =========================================================================
    # DELETE OPERATIONS - Remove/retract votes
    # =========================================================================

    @classmethod
    def deleteVote(cls, data):
        """
        Delete (retract) a user's vote from an event.
        
        Allows users to completely remove their vote while an event is
        still open. Uses JOIN to ensure only the vote for the specified
        event is deleted.
        
        Args:
            data (dict): Dictionary containing:
                         - 'user_id' (int): ID of user retracting vote
                         - 'event_id' (int): ID of event to retract from
        
        Returns:
            bool: True if deletion successful, False otherwise.
        """
        query = """
        DELETE v FROM vote v
        JOIN `option` o ON o.option_id = v.vote_option_id
        WHERE v.vote_user_id = %(user_id)s
          AND o.option_event_id = %(event_id)s;
        """
        return connectToMySQL(db).query_db(query, data)
    
    # =========================================================================
    # AGGREGATION OPERATIONS - Vote counting and statistics
    # =========================================================================

    @classmethod
    def tallyVotesForEvent(cls, data):
        """
        Counts votes for each option in an event.
        Returns all options for the event with their vote counts, sorted
        by votes descending. Used by the Result model to calculate
        percentages and determine winners.
        
        Args:
            data (dict): Dictionary containing:
                         - 'event_id' (int): ID of event to tally
        
        Returns:
            list[dict]: List of option tallies, each containing:
                        - 'option_id' (int): Option's ID
                        - 'option_text' (str): Option's display text
                        - 'votes' (int): Number of votes received
                        Results sorted by votes DESC, then option_text ASC.
        """
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
    def getStatsForUser(cls, data):
        """
        Get comprehensive voting statistics for a user's dashboard.
        Calculates total votes cast, participation rate, events participated,
        and last vote date. Used to display user engagement metrics.
        
        Args:
            data (dict): Dictionary containing:
                         - 'user_id' (int): ID of user to get stats for
        
        Returns:
            dict: Statistics dictionary containing:
                  - 'total_votes' (int): Total votes cast by user
                  - 'participation_rate' (float): Percentage of available
                    events user has participated in (0.0-100.0)
                  - 'events_participated' (int): Count of unique events
                  - 'last_vote_date' (str): Formatted date or 'Never'
        """
        user_id = data['user_id']
        
        # Query 1: Get total votes and last vote date in one query
        # COUNT(*) returns 0 (not NULL) if no votes, MAX returns NULL if no votes
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
        
        # Extract values with fallback to 0/None if NULL returned
        total_votes = result_votes[0]['total_votes'] or 0
        last_vote_date = result_votes[0]['last_vote_date'] # will be None if no votes
        
        # Query 2: Count unique events user has participated in
        # Must JOIN through option table b/c votes link to options, not events directly
        # DISTINCT ensures we count events, not individual votes (user votes once per event)
        query_events = """
        SELECT COUNT(DISTINCT o.option_event_id) as events_participated
        FROM vote v
        JOIN `option` o ON o.option_id = v.vote_option_id
        WHERE v.vote_user_id = %(user_id)s;
        """
        result_events = connectToMySQL(db).query_db(query_events, {'user_id': user_id})
        
        # Safely extract count with default to 0 if query fails or returns NULL
        events_participated = 0
        if result_events and len(result_events) > 0:
            events_participated = result_events[0].get('events_participated', 0) or 0
        
        # Query 3: Calculate participation rate
        # Only count CLOSED events (end_time < NOW) since open events are still in progress
        # Exclude events created by this user (creators cannot vote on own events)
        query_available = """
        SELECT COUNT(*) as total_available
        FROM event
        WHERE end_time < NOW() 
        AND created_byFK != %(user_id)s;
        """
        result_available = connectToMySQL(db).query_db(query_available, {'user_id': user_id})
        
        # Safely extract count, defaulting to 0 if query fails or returns NULL
        total_available = 0
        if result_available and len(result_available) > 0:
            total_available = result_available[0].get('total_available', 0) or 0
        
        # Calculate participation rate, avoiding division by zero
        if total_available > 0:
            participation_rate = round((events_participated / total_available) * 100, 1)
        else:
            participation_rate = 0.0
        
        # Format last vote date
        if last_vote_date:
            # Handle string vs datetime object
            if isinstance(last_vote_date, str):
                try:
                    from datetime import datetime
                    last_vote_date = datetime.strptime(last_vote_date, '%Y-%m-%d %H:%M:%S')
                except:
                    pass    # retain as string if parsing fails
            # Format as 'MMM DD, YYYY' if datetime object, otherwise use string directly
            last_vote_display = last_vote_date.strftime('%b %d, %Y') if hasattr(last_vote_date, 'strftime') else str(last_vote_date)
        else:
            last_vote_display = 'Never' # User has never voted
        
        return {
            'total_votes': total_votes,
            'participation_rate': participation_rate,
            'events_participated': events_participated,
            'last_vote_date': last_vote_display
        }
    
    # =========================================================================
    # UTILITY METHODS - Helper functions for vote operations
    # =========================================================================

    @staticmethod
    def isEditable(event: 'Events') -> bool:
        """
        Determine if votes for the given event can be modified.
        Votes are only editable when the event status is 'Open'. This is
        a convenience method that wraps compute_status for vote-specific
        logic.
        
        Args:
            event (Events): Event object with start_time and end_time
        
        Returns:
            bool: True if event is Open (votes can be modified),
                  False if Waiting or Closed.
        """
        return compute_status(event.start_time, event.end_time) == "Open"

    