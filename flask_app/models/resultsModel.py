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
    # access via self.rows
    def getWinner(self):
        if not self.rows:
            return None
        return self.rows[0] # rows are sorted by votes desc in calculate()

    def getTotalVotes(self):
        if not self.rows:
            return 0
        return sum(r['votes'] for r in self.rows)

    def getWinnerVoteTotal(self):
        winner = self.getWinner()
        if not winner:
            return 0
        return winner['votes']

    def getWinnerPercentage(self):
        winner = self.getWinner()
        if not winner:
            return 0.0
        return winner['percentage']

    # Additional methods for result processing can be added here as needed.

        

