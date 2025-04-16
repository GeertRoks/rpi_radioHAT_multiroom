import os
import signal

from snapcast import Snapcast
import tcp_client as tcp
from states import Sources

class Radio:
    def __init__(self):
        self.snapclient = Snapcast()

        # TODO: create MPD class that contains MPD state, like is playing and playlist is loaded
        self.mpd = tcp.MPDClient(os.getenv("MPD_IP"), os.getenv("MPD_PORT"))

        # Event flags
        self.flags = {"radio_station": False,
                      "source_select": False,
                      "exit": False}
        signal.signal(signal.SIGINT, self.exit_event)

        self.source_selected = Sources.OFF

    def __del__(self):
        del self.mpd

    def setSourceState(self, state):
        self.source_selected = state
        match state:
            case Sources.OFF:
                self.snapclient.mute()

            case Sources.RADIO:
                self.snapclient.setSourceToRadio()
                self.snapclient.unmute()

            case Sources.SPOTIFY:
                self.snapclient.setSourceToSpotify()
                self.snapclient.unmute()


    def updateSourceSelect(self, new_state, notify):
        if self.source_selected != new_state:
            self.setSourceState(new_state)
            notify(new_state)

    def getSourceSelectStateFromSnapcastServer(self):
        if self.snapclient.isClientMuted():
            return Sources.OFF

        group = self.snapclient.getGroupData()
        if not group:
            # TODO: write this to a log instead, or throw exception
            print("Error: no group data available")
            return None

        match group["stream_id"]:
            case "Radio":
                return Sources.RADIO
            case "Spotify":
                return Sources.SPOTIFY
            case _:
                # TODO: write this to a log instead, or throw exception
                print("Unkown stream currently playing")
                return None

    def radio_button_event(self, channel):
        if self.source_selected == Sources.RADIO:
            # TODO: write to log instead
            print("Radio button: next")
            self.flags["radio_station"] = True

    def source_switch_event(self, channel):
        # TODO: write to log instead
        print(f"Source switch event: {channel}")
        self.flags["source_select"] = True

    def exit_event(self, signum, frame):
        # TODO: write to log instead
        print("Ctrl+C detected, exiting now ...")
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        self.flags["exit"] = True


    def run(self, gpio):
        # Synchronize state of the Radio with the Snapcast server
        self.snapclient.syncStateWithServer()
        self.updateSourceSelect(self.getSourceSelectStateFromSnapcastServer(), gpio.setSourceSelectLeds)

        while not self.flags["exit"]:

            # TODO: handle snapcast onUpdate notifications
            # TODO: manage emptying in respective classes
            self.snapclient.snap.empty()
            self.mpd.empty()

            # Handle Radio station button
            if self.flags["radio_station"]:
                self.flags["radio_station"] = False
                gpio.blinkLed(gpio.RADIO_LED, repeat=2, period=0.1)
                self.mpd.sendCommand("next")

            # Handle Source select switch
            if self.flags["source_select"]:
                self.flags["source_select"] = False
                self.updateSourceSelect(gpio.getSourceSelectState(), gpio.setSourceSelectLeds)

