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


    # TODO: - ALEX - Implement the methods below
    # These methods should process self.rows to return the required information

    def getWinner(self):        # returns Dict of winning option or None
        ...

    def getTotalVotes(self):    # returns int total votes cast in the event
        ...

    def getWinnerVoteTotal(self):   # returns int number of votes for winning option
       ...

    def getWinnerPercentage(self):  # returns float percentage of votes for winning option
        ...

    # Additional methods for result processing can be added here as needed.

        

