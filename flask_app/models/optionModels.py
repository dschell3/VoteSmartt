from flask_app.config.mysqlconnection import connectToMySQL

db = "mydb"
# columns in option table are: option_id, option_text, option_event_id
# option is a reserved word in SQL, so table name MUST be enclosed in backticks

class Option:
    db = db

    def __init__(self, data):
        self.option_id = data['option_id']
        self.option_text = data['option_text']
        self.option_event_id = data['option_event_id']

    @classmethod
    def getByEventId(cls, data):
        query = "SELECT * FROM `option` WHERE option_event_id = %(event_id)s;"
        results = connectToMySQL(db).query_db(query, data)
        return [cls(row) for row in results]
    
    '''
    @classmethod
    def getAll(cls):
        query = "SELECT * FROM `option`;"
        result = connectToMySQL(db).query_db(query)
        events = []
        for i in result:
            events.append(cls(i))
        return events
    '''

    @classmethod
    def create(cls, data):
        query = '''
        INSERT INTO `option` (option_text, option_event_id)
        VALUES (%(option_text)s, %(option_event_id)s);
        '''
        return connectToMySQL(db).query_db(query, data)
    
    @classmethod
    def deleteByEventId(cls, data):
        query = "DELETE FROM `option` WHERE option_event_id = %(event_id)s;"
        return connectToMySQL(db).query_db(query, data)
    
    @classmethod
    def update(cls, data):
        """Update an existing option's text.
        
        Args:
            data (dict): Must contain 'option_id' and 'option_text'
        
        Returns:
            bool: True if successful, False otherwise
        """
        query = """
        UPDATE `option` 
        SET option_text = %(option_text)s
        WHERE option_id = %(option_id)s;
        """
        return connectToMySQL(db).query_db(query, data)
    
    @classmethod
    def deleteById(cls, data):
        """Delete a specific option by its ID.
        
        Args:
            data (dict): Must contain 'option_id'
        
        Returns:
            bool: True if successful, False otherwise
        
        Note:
            This will cascade delete any votes associated with this option
            due to the ON DELETE CASCADE foreign key constraint.
        """
        query = "DELETE FROM `option` WHERE option_id = %(option_id)s;"
        return connectToMySQL(db).query_db(query, data)    
    