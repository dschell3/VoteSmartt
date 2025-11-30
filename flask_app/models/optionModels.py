'''
==============================================================================
Option Model - represents operations for options/candidates in voting events
==============================================================================

This module provides the Option class for managing candidates or choices
that users can vote for within an event. Each option belongs to exactly
one event (many-to-one relationship via option_event_id foreign key).

Database Table: `option` (backticks required - reserved word in SQL)
Columns:
    - option_id (int): Primary key, auto-increment
    - option_text (varchar): Display text for the option/candidate name
    - option_event_id (int): Foreign key to event.event_id

Class Relationships:
    - Option *--1 Event: Many options belong to one event
    - Option 1--* Vote: One option can have many votes

VoteSmartt Rules:
    - Each event must have at least 2 options for voting
    - Options can only be modified when event status is 'Waiting'
    - Deleting an option cascades to delete associated votes
'''
from flask_app.config.mysqlconnection import connectToMySQL

db = "mydb"

class Option:
    """
    Represents a voting option/candidate within an event.
    Attributes correspond to the 'option' database table.
    """
    db = db

    def __init__(self, data):
        """ 
        Initialize an Option instance from database row data.
        """
        self.option_id = data['option_id']
        self.option_text = data['option_text']
        self.option_event_id = data['option_event_id']

    # =========================================================================
    # CREATE OPERATIONS
    # =========================================================================
    
    @classmethod
    def create(cls, data):
        """
        Called when creating a new event or adding candidates to an
        existing event (when event status is 'Waiting').
        
        Args:
            data (dict): Dictionary containing:
                         - 'option_text' (str): Display text for the option
                         - 'option_event_id' (int): ID of parent event
        
        Returns:
            int: The option_id of the newly created option, or False on failure
        """
        query = '''
        INSERT INTO `option` (option_text, option_event_id)
        VALUES (%(option_text)s, %(option_event_id)s);
        '''
        return connectToMySQL(db).query_db(query, data)
    
    # =========================================================================
    # READ OPERATIONS
    # =========================================================================

    @classmethod
    def getByEventId(cls, data):
        """
        Retrieve all options belonging to a specific event.
        
        Args:
            data (dict): Dictionary containing:
                         - 'event_id' (int): ID of event to get options for
        
        Returns:
            list[Option]: List of Option objects for the event.
                          Returns empty list if no options exist.
        """
        query = "SELECT * FROM `option` WHERE option_event_id = %(event_id)s;"
        results = connectToMySQL(db).query_db(query, data)
        return [cls(row) for row in results]
    
    # =========================================================================
    # UPDATE OPERATIONS
    # =========================================================================
    
    @classmethod
    def update(cls, data):
        """
        Update an existing option's display text.
        Used when editing event candidates. Only the option_text can be
        modified; the option_id and option_event_id can't be.
        
        Args:
            data (dict): Dictionary containing:
                         - 'option_id' (int): ID of option to update
                         - 'option_text' (str): New display text
        
        Returns:
            bool: True if update was successful, False otherwise.
        """
        query = """
        UPDATE `option` 
        SET option_text = %(option_text)s
        WHERE option_id = %(option_id)s;
        """
        return connectToMySQL(db).query_db(query, data)
    
    # =========================================================================
    # DELETE OPERATIONS
    # =========================================================================

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

    @classmethod
    def deleteByEventId(cls, data):
        """Delete all options that belong to a specific event.

        Args:
            data (dict): Must contain 'event_id'

        Returns:
            bool|int: Result of the delete query (driver-specific). True/number of rows deleted on success.
        """
        query = "DELETE FROM `option` WHERE option_event_id = %(event_id)s;"
        return connectToMySQL(db).query_db(query, data)
    