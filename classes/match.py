class Match:
    def __init__(self, mID, mStart, p1, p2, mDuration):
        self.mID = mID
        self.mStart = mStart
        self.p1 = p1
        self.p2 = p2
        self.mDuration = mDuration

    def to_dict(self):
        return {
            "mID": self.mID,
            "mStart": self.mStart,
            "p1": self.p1,
            "p2": self.p2,
            "mDuration": self.mDuration
        }