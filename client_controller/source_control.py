from enum import Enum

class Sources(Enum):
    OFF = 0
    RADIO = 1
    SPOTIFY = 2

class SourceState:
    source_state = 0

    def __init__(self):
        self.off()

    def off(self):
        self.source_state = Sources.OFF
        # set Snapcast source to None

    def radio(self):
        self.source_state = Sources.RADIO
        # set Snapcast source to Radio

    def spotify(self):
        self.source_state = Sources.SPOTIFY
        # set Snapcast source to Spotify

    def getState(self):
        return self.source_state

