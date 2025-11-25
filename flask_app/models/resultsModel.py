from flask_app.config.mysqlconnection import connectToMySQL
from flask_app.models.voteModels import Vote

db = "mydb"

class Result:
    db = db

    def __init__(self, data):
        self.event_id = data['event_id']
        self.rows = self.calculate()

    def calculate(self):
        rows = Vote.tallyVotesForEvent({'event_id': self.event_id}) or []
        total = sum(r['votes'] for r in rows) if rows else 0
        for r in rows:
            r['percentage'] = round((r['votes'] / total * 100), 1) if total else 0.0
        return rows 
<<<<<<< HEAD
    
    # can use calculate() to help to get the results for the methods below
    # access via cls.rows
    @classmethod
    def getWinner(cls):
        ...
        # Implement logic to return the winning option for a given event


    @classmethod
    def getTotalVotes(cls):
        ...
        # Implement logic to return the total votes for a given event


    @classmethod
    def getWinnerVoteTotal(cls):
        ...
        # Implement logic to return the total votes for the winning option


    @classmethod
    def getWinnerPercentage(cls):
        ...
        # Implement logic to return the percentage of votes for the winning option



=======

    def getWinner(self):        # returns Dict of winning option or None
        if not self.rows:
            return None
        return self.rows[0] # rows are sorted by votes desc in calculate()

    def getTotalVotes(self):    # returns int total votes cast in the event
        if not self.rows:
            return 0
        return sum(r['votes'] for r in self.rows)

    def getWinnerVoteTotal(self):   # returns int number of votes for winning option
        winner = self.getWinner()
        if not winner:
            return 0
        return winner['votes']

    def getWinnerPercentage(self):  # returns float percentage of votes for winning option
        winner = self.getWinner()
        if not winner:
            return 0.0
        return winner['percentage']
>>>>>>> c96f2cccd8edfa7cc05c71fb6138c4ac6f1d27fb

    # Additional methods for result processing can be added here as needed.

        

