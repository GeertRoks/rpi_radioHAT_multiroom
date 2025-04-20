from os import getenv
import signal

from snapcast import Snapcast
from internetradio import InternetRadio
from states import Sources

class EnvironmentVariableNotFound(Exception):
    pass

class Radio:
    def __init__(self):
        snap_client_id = self.loadEnvironmentVariable("SNAP_CLIENT_ID")
        snap_ip = self.loadEnvironmentVariable("SNAP_IP")
        snap_port = self.loadEnvironmentVariable("SNAP_PORT")
        mpd_ip = self.loadEnvironmentVariable("MPD_IP")
        mpd_port = self.loadEnvironmentVariable("MPD_PORT")
        try:
            self.snapclient = Snapcast(snap_ip, snap_port, snap_client_id)
        except Exception as e:
            raise e

        try:
            self.internetradio = InternetRadio(mpd_ip, mpd_port)
        except Exception as e:
            raise e

        # Event flags
        self.flags = {"next_radio_station": False,
                      "source_select": False,
                      "exit": False}
        signal.signal(signal.SIGINT, self.exit_event)

        self.source_selected = Sources.OFF

    def loadEnvironmentVariable(self, env):
        value = getenv(env)
        if not value:
            raise EnvironmentVariableNotFound(f"ERROR: {env} not defined")
        return value

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
            self.flags["next_radio_station"] = True

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
            self.snapclient.snap.flush()
            self.internetradio.mpd.flush()

            # Handle Radio station button
            if self.flags["next_radio_station"]:
                self.flags["next_radio_station"] = False
                gpio.blinkLed(gpio.RADIO_LED, repeat=2, period=0.1)
                self.internetradio.next()

            # Handle Source select switch
            if self.flags["source_select"]:
                self.flags["source_select"] = False
                self.updateSourceSelect(gpio.getSourceSelectState(), gpio.setSourceSelectLeds)

