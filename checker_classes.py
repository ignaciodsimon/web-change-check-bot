class TrackedElement:
    """
        Class to store the information of a tracked address.
    """

    # Class constructor
    def __init__(self, url=None,
                 lastChecksum=None,
                 periodicity=None,
                 content=None,
                 lastChangeAmount=None,
                 minimumChangeThreshold=None,
                 ID=None):
        self.url = url
        self.lastChecksum = lastChecksum
        self.periodicity = periodicity
        self.content = content
        self.lastChangeAmount = lastChangeAmount
        self.minimumChangeThreshold = minimumChangeThreshold
        self.ID = ID

    # Getters / setters
    def getContent(self):
        return self.content

    def getID(self):
        return self.ID

    def setID(self, ID):
        self.ID = ID

    def setContent(self, content):
        self.content = content

    def getMinimumChangeThreshold(self):
        return self.minimumChangeThreshold

    def setMinimumChangeThreshold(self, newThreshold):
        self.minimumChangeThreshold = newThreshold

    def setLastChangeAmount(self, lastChangeAmount):
        self.lastChangeAmount = lastChangeAmount

    def getLastChangeAmount(self):
        return self.lastChangeAmount

    def getLastChecksum(self):
        return self.lastChecksum

    def setLastChecksum(self, checksum):
        self.lastChecksum = checksum

    def getPeriodicity(self):
        return self.periodicity

    def setPeriodicity(self, periodicity):
        self.periodicity = periodicity

    def getURL(self):
        return self.url

    def setURL(self, url):
        self.url = url
