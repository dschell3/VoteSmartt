from flask_app.config.mysqlconnection import connectToMySQL
from datetime import datetime, timezone, timedelta

db = "mydb"

# columns in event table are: event_id, title, description, start_time, end_time,
#                             created_at, created_byFK, status

# Timezone configuration - can be changed later without modifying queries
# For now, Pacific timezone (UTC-8). Later this could come from:
# - Flask app config
# - Environment variable
# - User preferences
# - Event-specific settings
STORAGE_TIMEZONE_OFFSET = timedelta(hours=-8)  # Pacific Standard Time


class Events:
    db = db

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
    def getAllWithCreators(cls):
        """
        Get all events with creator information.
        
        Returns:
            List[Event]: Events sorted by status (Open, Waiting, Closed)
                        then by start_time within each status group.
                        Each event includes computed status and creator info.
        """
        # Get events with creator info
        query = """
        SELECT e.*, u.first_name, u.last_name
        FROM event e
        LEFT JOIN user u ON e.created_byFK = u.user_id
        ORDER BY e.start_time ASC;
        """
        result = connectToMySQL(db).query_db(query)
        events = []
        for row in result:
            # Create event object with additional creator info
            event = cls(row)
            event.creator_first_name = row.get('first_name', '')
            event.creator_last_name = row.get('last_name', '')
            event.creator_full_name = f"{row.get('first_name', '')} {row.get('last_name', '')}".strip()
            events.append(event)
        
        # Compute status for each event
        for event in events:
            try:
                event.status = cls.compute_status(event.start_time, event.end_time)
            except Exception:
                event.status = 'Unknown'
        
        # Sort by status priority, then by start time
        status_priority = {
            'Open': 0,
            'Waiting': 1,
            'Closed': 2,
            'Unknown': 3
        }
        
        def get_sort_key(event):
            """Generate sort key: (status_priority, start_datetime)"""
            priority = status_priority.get(event.status, 3)
            
            # Parse start time for sorting
            start_dt = cls.parse_datetime(event.start_time)
            if start_dt is None:
                start_dt = datetime.max  # Push invalid dates to end
            
            return (priority, start_dt)
        
        # Sort events
        try:
            events.sort(key=get_sort_key)
        except Exception:
            pass  # If sorting fails, return in database order
        
        return events

    @classmethod
    def getOne(cls, data):
        """
        Get a single event by ID with creator information.
        
        Args:
            data: Dictionary with 'event_id' key
            
        Returns:
            Events object with additional creator attributes:
            - creator_first_name
            - creator_last_name  
            - creator_full_name
        """
        query = """
        SELECT e.*, u.first_name, u.last_name
        FROM event e
        LEFT JOIN user u ON e.created_byFK = u.user_id
        WHERE e.event_id = %(event_id)s;
        """
        result = connectToMySQL(db).query_db(query, data)
        if not result:
            return None
        
        # Create event object with additional creator info
        event = cls(result[0])
        event.creator_first_name = result[0].get('first_name', '')
        event.creator_last_name = result[0].get('last_name', '')
        event.creator_full_name = f"{result[0].get('first_name', '')} {result[0].get('last_name', '')}".strip()
        
        return event

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

    '''
    @classmethod
    def getOpenEvents(cls):
        """Get currently open events using timezone-adjusted comparison."""
        now_in_storage_tz = cls._get_utc_now_as_storage_timezone()
        
        query = """
        SELECT e.*
        FROM event e
        WHERE e.start_time <= %(now)s AND e.end_time > %(now)s
        ORDER BY e.start_time ASC;
        """
        data = {'now': now_in_storage_tz}
        result = connectToMySQL(cls.db).query_db(query, data)
        return [cls(row) for row in result] if result else []
    '''

    @classmethod
    def getUpcoming(cls, limit=None):
        """Get future events by comparing against timezone-adjusted current time.
        
        Instead of converting all database times in SQL, we convert the
        current time to match the storage timezone. This is more efficient
        and keeps the query simple.
        
        Args:
            limit: Optional maximum number of events to return
            
        Returns:
            List of Event objects scheduled to start in the future
        """
        # Get current time in storage timezone for accurate comparison
        now_in_storage_tz = cls._get_utc_now_as_storage_timezone()
        
        query = """
        SELECT e.*
        FROM event e
        WHERE e.start_time > %(now)s
        ORDER BY e.start_time ASC
        """
        if limit:
            query += f" LIMIT {limit}"
        query += ";"
        
        data = {'now': now_in_storage_tz}
        result = connectToMySQL(cls.db).query_db(query, data)
        return [cls(row) for row in result] if result else []

    '''
    @classmethod
    def getAllClosed(cls):
        """Get closed events using timezone-adjusted comparison."""
        now_in_storage_tz = cls._get_utc_now_as_storage_timezone()
        
        query = """
        SELECT e.*
        FROM event e
        WHERE e.end_time <= %(now)s
        ORDER BY e.end_time DESC;
        """
        data = {'now': now_in_storage_tz}
        result = connectToMySQL(cls.db).query_db(query, data)
        return [cls(row) for row in result] if result else []
    '''
    '''
    @classmethod
    def getAllWithStatus(cls):
        """Get all events with computed status using timezone-adjusted comparison."""
        now_in_storage_tz = cls._get_utc_now_as_storage_timezone()
        
        query = """
        SELECT
        e.*,
        CASE
            WHEN %(now)s < e.start_time THEN 'upcoming'
            WHEN %(now)s >= e.end_time THEN 'closed'
            ELSE 'open'
        END AS status
        FROM event e
        ORDER BY e.start_time ASC;
        """
        data = {'now': now_in_storage_tz}
        result = connectToMySQL(cls.db).query_db(query, data)
        return [cls(row) for row in result] if result else []
    '''
    @classmethod
    def _get_utc_now_as_storage_timezone(cls):
        """
        Get current UTC time expressed in storage timezone format.
        
        This allows us to compare storage times (Pacific) with current time
        by converting current time TO storage timezone instead of converting
        all stored times TO UTC in the query.
        
        Returns:
            datetime: Current time in storage timezone (naive datetime)
        """
        now_utc = datetime.now(timezone.utc)
        now_storage = now_utc + STORAGE_TIMEZONE_OFFSET
        return now_storage.replace(tzinfo=None)  # Return as naive datetime
    
    @staticmethod
    def compute_status(start_raw, end_raw):
        """Compute event status by converting stored Pacific times to UTC for comparison.
        
        Times are stored in the database in Pacific timezone (PST, UTC-8).
        This method converts them to UTC before comparing with current UTC time.
        """
        from datetime import timedelta
        
        now_utc = datetime.now(timezone.utc)
        
        # Parse stored times (which are in Pacific timezone)
        start_local = Events.parse_datetime(start_raw)
        end_local = Events.parse_datetime(end_raw)
        
        if not start_local and not end_local:
            return 'Unknown'
        
        # Pacific timezone is UTC-8 (PST)
        pacific_offset = timedelta(hours=-8)
        
        # Convert Pacific times to UTC for comparison
        if start_local:
            # Treat stored time as Pacific (naive datetime), convert to UTC
            start_local_aware = start_local.replace(tzinfo=timezone(pacific_offset))
            start_utc = start_local_aware.astimezone(timezone.utc)
        else:
            start_utc = None
        
        if end_local:
            # Treat stored time as Pacific (naive datetime), convert to UTC
            end_local_aware = end_local.replace(tzinfo=timezone(pacific_offset))
            end_utc = end_local_aware.astimezone(timezone.utc)
        else:
            end_utc = None
        
        # Now compare with current UTC time
        if start_utc and end_utc:
            if now_utc < start_utc:
                return 'Waiting'
            if now_utc > end_utc:
                return 'Closed'
            return 'Open'
        if start_utc and not end_utc:
            return 'Waiting' if now_utc < start_utc else 'Open'
        if end_utc and not start_utc:
            return 'Closed' if now_utc > end_utc else 'Open'
        
        return 'Unknown'

    @staticmethod
    def parse_datetime(value):
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
