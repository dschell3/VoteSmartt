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

    def getWinners(self):        # returns List[Dict] of winning option(s) or None
        if not self.rows:
            return []
        max_votes = self.rows[0]['votes'] if self.rows else 0
        if max_votes == 0:
            return []
        return [r for r in self.rows if r['votes'] == max_votes]
    
    def getWinnerOptionIds(self):  # returns List[int] of winner option IDs
        return [w['option_id'] for w in self.getWinners()]

    def getTotalVotes(self):    # returns int total votes cast in the event
        if not self.rows:
            return 0
        return sum(r['votes'] for r in self.rows)

    def getWinnerVoteTotal(self):   # returns int votes for winning option
        winners = self.getWinners()
        return winners[0]['votes'] if winners else 0

    def getWinnerPercentage(self):  # returns float percentage of votes for winning option
        winners = self.getWinners()
        return winners[0]['percentage'] if winners else 0.0

        

