'''
==============================================================================
Result Model - Aggregates and computes voting results for events
==============================================================================

This module provides the Result class for calculating and presenting vote
tallies, percentages, and winner determination for completed voting events.

This is NOT a database-backed model. Unlike Events, Option, Vote, and
User models, Result does not correspond to a database table. Instead, it is
a computed/aggregate class that wraps vote tally data retrieved from the
Vote model and enriches it with calculated fields (percentages, winners).

Class Relationships:
    - Result --uses-- Vote: Retrieves vote tallies via Vote.tallyVotesForEvent()
    - Result --uses-- Option: Indirectly through vote tally (option_id, option_text)
    - Event 1--1 Result: One result summary per event (computed on demand)

VoteSmartt Rules:
    - Results are displayed after an event's status becomes 'Closed'
    - The singleEvent template uses Result to show voting outcomes
    - Supports tie detection (multiple winners with equal votes)
'''

from flask_app.models.voteModels import Vote

db = "mydb"

class Result:
    """
    Computes and presents voting results for a specific event. Retrieves vote tallies
    and calculates percentages, totals, and winners on instantiation.
    """
    
    def __init__(self, data):
        """
        Initialize a Result instance and immediately calculate vote tallies.
        """
        self.event_id = data['event_id']
        self.rows = self.calculate()

    # =========================================================================
    # CALCULATION METHODS
    # =========================================================================

    def calculate(self):
        """
        Retrieves raw vote counts from Vote.tallyVotesForEvent() and enriches
        each row with a 'percentage' field. Results are sorted by vote count
        descending (highest votes first) as returned by the Vote model.
        
        Args:
            None
        
        Returns:
            list[dict]: List of option tally dictionaries, each containing:
                        - 'option_id' (int): Option's database ID
                        - 'option_text' (str): Option's display text  
                        - 'votes' (int): Number of votes received
                        - 'percentage' (float): Rounded to 1 decimal place
                        Returns empty list if no votes exist.
        """
        rows = Vote.tallyVotesForEvent({'event_id': self.event_id}) or []
        total = sum(r['votes'] for r in rows) if rows else 0
        for r in rows:
            r['percentage'] = round((r['votes'] / total * 100), 1) if total else 0.0
        return rows 

    # =========================================================================
    # WINNER DETERMINATION METHODS
    # =========================================================================

    def getWinners(self):
        """
        Identify the winning option(s) with the highest vote count. Supports tie 
        detection by returning all options that won. Returns empty list if no votes.
        
        Args:
            None
        
        Returns:
            list[dict]: List of winning option(s), each containing:
                        - 'option_id' (int): Winner's database ID
                        - 'option_text' (str): Winner's display text
                        - 'votes' (int): Winner's vote count
                        - 'percentage' (float): Winner's percentage
                        Returns empty list if no votes exist or all have 0 votes.
        """
        if not self.rows:
            return []
        max_votes = self.rows[0]['votes'] if self.rows else 0
        if max_votes == 0:
            return []
        return [r for r in self.rows if r['votes'] == max_votes]
    
    def getWinnerOptionIds(self):
        """
        Get the option IDs of the winning option(s).
        Convenience method for cases where only the IDs are needed,
        such as highlighting winners in the UI.
        
        Args:
            None
        
        Returns:
            list[int]: List of option_id values for winning option(s).
                       Returns empty list if no winner exists.
        """
        return [w['option_id'] for w in self.getWinners()]
    
    # =========================================================================
    # AGGREGATE STATISTICS METHODS
    # =========================================================================

    def getTotalVotes(self):
        """
        Calculate the total number of votes cast in the event.
        
        Args:
            None (uses self.rows)
        
        Returns:
            int: Sum of all votes for all options. Returns 0 if no votes were cast.
        """
        if not self.rows:
            return 0
        return sum(r['votes'] for r in self.rows)

