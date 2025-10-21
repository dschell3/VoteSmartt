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
    
    # Additional methods for updating or retrieving options can be added here as needed.

    # Is a method to get all options needed? If so, implement similarly to Events.getAll()

    # Is a method to update an option needed? If so, implement similarly to Events.editEvent()

    # Is a method to delete an option by its own ID needed? If so, implement similarly to Events.deleteEvent()

    # Is a method to get vote counts for options needed? If so, implement as required.

    