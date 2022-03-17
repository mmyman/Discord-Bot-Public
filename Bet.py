class Bet:
    def __init__(self):
        self.title = ""
        self.believers = []
        self.believe_bets = []
        self.doubters = []
        self.doubt_bets = []


    def believe(self, id, amt):
        self.believers.append(id)
        self.believe_bets.append(amt)

    def doubt(self, id, amt):
        self.doubters.append(id)
        self.doubt_bets.append(amt)

    def set_title(self, title):
        self.title = title
    def reset(self):
        self.believers = []
        self.believe_bets = []
        self.doubters = []
        self.doubt_bets = []