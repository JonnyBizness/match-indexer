class Match:
    def __init__(self, mID=None, mStart=None, p1=None, p2=None, mDuration=0, p1Score=0, p2Score=0, p1Characters=None, p2Characters=None):
        self.mID = mID
        self.mStart = mStart
        self.p1 = p1
        self.p2 = p2
        self.mDuration = mDuration
        self.p1Score = p1Score
        self.p2Score = p2Score
        self.p1Characters = p1Characters if p1Characters is not None else []
        self.p2Characters = p2Characters if p2Characters is not None else []

    def to_dict(self):
        return {
            "mID": self.mID,
            "mStart": self.mStart,
            "p1": self.p1,
            "p2": self.p2,
            "mDuration": self.mDuration,
            "p1Score": self.p1Score,
            "p2Score": self.p2Score,
            "p1Characters": self.p1Characters,
            "p2Characters": self.p2Characters
        }