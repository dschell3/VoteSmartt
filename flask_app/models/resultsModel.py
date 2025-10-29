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


    # Additional methods for result processing can be added here as needed.
        

