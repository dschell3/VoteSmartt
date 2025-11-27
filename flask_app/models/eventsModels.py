"""
==============================================================================
Events Model - represents operations for voting events
==============================================================================

This module handles all database operations related to voting events including
creation, retrieval, modification, and deletion. It also provides timezone-aware
status computation to determine if events are Waiting, Open, or Closed.

Timezone Strategy (KISS Principle):
    - Database stores naive datetimes in Pacific time
    - PACIFIC_OFFSET defined once, used everywhere
    - compute_status() is the single source of truth for status calculation

Database Table: event
    - event_id (INT, PK, AUTO_INCREMENT)
    - title (VARCHAR(45))
    - description (VARCHAR(255))
    - start_time (DATETIME)
    - end_time (DATETIME)
    - created_at (DATETIME)
    - created_byFK (INT, FK -> user.user_id)
    - status (VARCHAR(45))

Related Tables:
    - user (via created_byFK foreign key)
    - option (options/candidates belong to events)
"""

from flask_app.config.mysqlconnection import connectToMySQL
from datetime import datetime, timezone, timedelta

# =============================================================================
# MODULE CONSTANTS
# =============================================================================

db = "mydb"

# Pacific Standard Time offset from UTC (UTC-8)
# This doesn't handle DST, but keeps things simple. 
# For production, consider using pytz or zoneinfo for proper DST handling.
PACIFIC_OFFSET = timedelta(hours=-8)


# =============================================================================
# TIMEZONE HELPER FUNCTIONS - Used by model and can be imported by controllers
# =============================================================================

def get_now_pacific():
    """
    This function converts the current UTC time to Pacific time and strips
    the timezone info, making it suitable for comparison with database values
    which are stored as naive Pacific datetimes.
    
    Args:
        None
    
    Returns:
        datetime: Current time in Pacific timezone as naive datetime object.
                  Timezone info is stripped for database compatibility.
    """
    now_utc = datetime.now(timezone.utc)        # Current time in UTC
    now_pacific = now_utc + PACIFIC_OFFSET      # Convert to Pacific time
    return now_pacific.replace(tzinfo=None)     # Strip timezone info


def parse_datetime(value):
    """
    Handles multiple input formats including datetime objects, strings in
    various formats, and None values.

    Args:
        value: String, datetime, or None
        
    Returns:
        Naive datetime or None
    """
    if not value:                               # Handles None or empty
        return None
    if isinstance(value, datetime):             # Handle datetime objects
        # Strip timezone if present, return as-is
        return value.replace(tzinfo=None) if value.tzinfo else value
    
    # Handle common string formats
    value = str(value).strip()
    for fmt in ['%Y-%m-%d %H:%M:%S', 
                '%Y-%m-%dT%H:%M:%S', 
                '%Y-%m-%dT%H:%M', 
                '%Y-%m-%d %H:%M', 
                '%Y-%m-%d']:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue                            # return None if all formats fail
    return None                                 # No format matched, Unable to parse


def compute_status(start_raw, end_raw):
    """
    Compute event status: Waiting, Open, Closed, or Unknown.
        - 'Waiting': Current time is before start_time (event hasn't started)
        - 'Open': Current time is between start_time and end_time (voting active)
        - 'Closed': Current time is at or after end_time (voting ended)
        - 'Unknown': Both start and end times are missing
    
    Args:
        start_raw: Event start time (string or datetime, in Pacific)
        end_raw: Event end time (string or datetime, in Pacific)
        
    Returns:
        str: 'Waiting', 'Open', 'Closed', or 'Unknown'
    """
    start_dt = parse_datetime(start_raw)
    end_dt = parse_datetime(end_raw)
    
    if not start_dt and not end_dt:             # Both times missing
        return 'Unknown'
    
    # Get current time in Pacific (naive) for comparison with DB values
    now = get_now_pacific()
    
    # Simple comparisons - all times are naive Pacific
    if start_dt and end_dt:                     # Both times present
        if now < start_dt:
            return 'Waiting'
        elif now >= end_dt:
            return 'Closed'
        else:
            return 'Open'
    # Only start time present, waiting if before start, otherwise open indefinitely
    elif start_dt and not end_dt:                 
        return 'Waiting' if now < start_dt else 'Open'
    # Only end time present, closed if past end, otherwise open
    elif end_dt and not start_dt:               
        return 'Closed' if now >= end_dt else 'Open'
    
    return 'Unknown'                            # Fallback, should not reach here  


# =============================================================================
# EVENTS MODEL CLASS
# =============================================================================

class Events:
    """
    Represents a voting event (poll, survey, election, competition) in the
    system. Provides CRUD operations and utility methods for event management.
    Attributes correspond to the 'event' database table.
    """
    
    # DB identifier for mySQL connection
    db = db

    
    def __init__(self, data):
        """
        Creates an Events object by mapping database column values to
        instance attributes. 
        """
        self.event_id = data['event_id']
        self.title = data['title']
        self.description = data['description']
        self.start_time = data['start_time']
        self.end_time = data['end_time']
        self.created_byFK = data['created_byFK']
        self.created_at = data['created_at']
        self.status = data['status']

    # =========================================================================
    # CRUD OPERATIONS
    # =========================================================================

    @classmethod
    def createEvent(cls, data):
        """
        Inserts a new event record with the provided data. The created_at
        timestamp is automatically set to the current time using MySQL's NOW().
        
        Args:
            data (dict): Dictionary containing event data:
                         
        Returns:
            int: event_id of the newly created event, or False if the insert failed.
        """
        query = '''
        INSERT INTO event (title, description, start_time, end_time, created_byFK, created_at, status)
        VALUES (%(title)s, %(description)s, %(start_time)s, %(end_time)s, %(created_byFK)s, NOW(), %(status)s);
        '''
        return connectToMySQL(db).query_db(query, data)

    @classmethod
    def editEvent(cls, data):
        """
        Updates the title, description, start_time, and end_time of an event.
        Note: created_byFK and created_at are intentionally NOT updated to
        preserve the original creation metadata.
        
        Args:
            data (dict): Dictionary containing update data:
        
        Returns:
            bool: True if update was successful, False otherwise.
        
        Note:
            The status field is not updated here because it should be
            computed dynamically based on current time vs start/end times.
        """
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
        """
        Delete an event from the database.
        
        Permanently removes an event record. Associated options (candidates)
        should be deleted via cascade or explicitly before calling this.
        
        Args:
            data (dict): Dictionary containing:
                         - 'event_id' (int): ID of event to delete (required)
        
        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        query = '''
        DELETE FROM event
        WHERE event_id = %(event_id)s;
        '''
        return connectToMySQL(db).query_db(query, data)

    # =========================================================================
    # READ OPERATIONS - QUERY METHODS
    # =========================================================================

    @classmethod
    def getAllWithCreators(cls):
        """
        Performs a LEFT JOIN with the user table to include creator's name.
        Results are sorted by computed status (Open first, then Waiting, then
        Closed) and then by start_time ascending within each status group.
        
        The status is computed in SQL using CASE expressions to ensure
        consistency with the Python compute_status() function.
        
        Args:
            None
        
        Returns:
            list[Events]: List of Events objects with additional attributes:
                          Returns empty list if no events exist.
        """
        now = get_now_pacific()             # Current time in Pacific (naive)
        
        query = """
        SELECT
            e.*,
            u.first_name AS creator_first_name,
            u.last_name AS creator_last_name,
            CASE
                WHEN %(now)s < e.start_time THEN 'Waiting'
                WHEN %(now)s >= e.end_time THEN 'Closed'
                ELSE 'Open'
            END AS computed_status
        FROM event e
        LEFT JOIN user u ON e.created_byFK = u.user_id
        ORDER BY
            FIELD(
                CASE
                    WHEN %(now)s < e.start_time THEN 'Waiting'
                    WHEN %(now)s >= e.end_time THEN 'Closed'
                    ELSE 'Open'
                END,
                'Open', 'Waiting', 'Closed'
            ),
            e.start_time ASC;
        """
        result = connectToMySQL(db).query_db(query, {'now': now})
        
        # Transform DB rows into Events objects with extra attributes
        events = []
        if result:
            for row in result:
                event = cls(row)
                event.creator_first_name = row.get('creator_first_name', '')
                event.creator_last_name = row.get('creator_last_name', '')
                event.creator_full_name = f"{row.get('creator_first_name', '')} {row.get('creator_last_name', '')}".strip()
                event.computed_status = row.get('computed_status', 'Unknown')
                events.append(event)
        
        return events

    @classmethod
    def getOne(cls, data):
        """
        Performs a LEFT JOIN with user table to include creator's name.
        This is the primary method for fetching event details for display.
        
        Args:
            data (dict): Dictionary containing:
                         - 'event_id' (int): ID of event to retrieve (required)
        
        Returns:
            Events: Events object with additional creator attributes if found:
                    Returns None if event not found.
        """
        
        # Join event with user to get creator info
        query = """
        SELECT e.*, u.first_name, u.last_name
        FROM event e
        LEFT JOIN user u ON e.created_byFK = u.user_id
        WHERE e.event_id = %(event_id)s;
        """
        result = connectToMySQL(db).query_db(query, data)
        if not result:
            return None
        
        # Create Events object with creator info
        event = cls(result[0])
        event.creator_first_name = result[0].get('first_name', '')
        event.creator_last_name = result[0].get('last_name', '')
        event.creator_full_name = f"{result[0].get('first_name', '')} {result[0].get('last_name', '')}".strip()
        return event

    @classmethod
    def getRecommendations(cls, data):
        """
        Used to suggest other events to users after they view or vote on an
        event. Excludes the currently viewed event and orders by start_time.
        
        Args:
            data (dict): Dictionary containing:
                         - 'event_id' (int): Current event ID to exclude
        
        Returns:
            list[Events]: List of up to 3 Events objects, sorted by start_time.
                          Returns empty list if no other events exist.
        """
        query = """
        SELECT * FROM event
        WHERE event_id != %(event_id)s
          AND start_time IS NOT NULL
        ORDER BY start_time ASC
        LIMIT 3;
        """
        result = connectToMySQL(db).query_db(query, {'event_id': data.get('event_id')})
        return [cls(row) for row in result] if result else []

    @classmethod
    def getUpcoming(cls, limit=None):
        """
        Retrieves events whose start_time is after the current Pacific time.
        Useful for displaying "upcoming events" sections on dashboards.
        
        Args:
            limit (int, optional): Maximum number of events to return.
                                   If None, returns all upcoming events.
        
        Returns:
            list[Events]: List of Events objects with future start times,
                          sorted by start_time ascending (soonest first).
                          Returns empty list if no upcoming events.
        """
        now = get_now_pacific()
        
        query = "SELECT * FROM event WHERE start_time > %(now)s ORDER BY start_time ASC"
        if limit:
            query += f" LIMIT {limit}"
        query += ";"
        result = connectToMySQL(db).query_db(query, {'now': now})
        # return list of Events objects or empty list
        return [cls(row) for row in result] if result else []       


    # =========================================================================
    # INSTANCE METHODS - Operations on individual event objects
    # =========================================================================

    def get_editable_fields(self) -> dict:
        """
        Implements business rules for field editability:
            - Waiting (not started): All fields editable
            - Open (voting in progress): Can edit title, description, end_time
                                         Cannot edit start_time (already passed)
            - Closed (voting ended): Only description editable
        
        Args:
            None 
        
        Returns:
            dict: Dictionary with field editability flags:
                  - 'title' (bool): True if title can be edited
                  - 'description' (bool): True if description can be edited
                  - 'start_time' (bool): True if start_time can be edited
                  - 'end_time' (bool): True if end_time can be edited
                  - 'status' (str): Current computed status of the event
        """
        # Initialize with default values
        editable = {
            'title': True,
            'description': True,
            'start_time': False,
            'end_time': False,
            'status': 'Unknown'
        }
        
        try:
            # Use compute_status - pass raw values, let it handle parsing
            status = compute_status(self.start_time, self.end_time)
            editable['status'] = status
            
            # Apply business rules based on status
            if status == 'Waiting':             
                editable['start_time'] = True
                editable['end_time'] = True
            elif status == 'Open':              
                editable['end_time'] = True
            elif status == 'Closed':            
                editable['title'] = False
                
        except Exception as e:
            # Log error but return defaults
            print(f"[ERROR] get_editable_fields failed: {e}")
        
        return editable

    def isCreatedBy(self, user) -> bool:
        """
        Compares the event's creator ID with the provided user's ID.
        Used for permission checks (e.g., can user edit this event?).
        
        Args:
            user: User object with a user_id attribute, or None.
        
        Returns:
            bool: True if the user created this event, False otherwise.
                  Returns False if user is None or comparison fails.
        """
        if not user:
            return False
        try:
            # Convert both IDs to int for safe comparison
            self_id = int(self.created_byFK)
            user_id = int(user.user_id)
            # Compare IDs
            result = self_id == user_id
            return result
        except (ValueError, TypeError) as e:
            return False    # On error, treat as not created by user


