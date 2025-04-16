import os
import signal

import tcp_client as tcp
from states import Sources

class Radio:
    def __init__(self):
        # Setup connections to Snapcast and MPD servers
        self.snap = tcp.SnapClient(os.getenv("SNAP_IP"), os.getenv("SNAP_PORT"))
        self.mpd = tcp.MPDClient(os.getenv("MPD_IP"), os.getenv("MPD_PORT"))

        # Event flags
        self.flags = {"radio_station": False,
                      "source_select": False,
                      "exit": False}
        signal.signal(signal.SIGINT, self.exit_event)

        # Set Snapcast info
        self.snapcast_server_state = self.snap.sendCommand("Server.GetStatus")
        self.client_id = os.getenv("SNAP_CLIENT_ID")
        self.group_id = self.getGroupID(self.snapcast_server_state)

        self.source_selected = Sources.OFF

    def __del__(self):
        del self.snap
        del self.mpd

    def getGroupID(self, server_data_json):
        groups = server_data_json["result"]["server"]["groups"]
        for group in groups:
            for client in group["clients"]:
                if client["id"] == self.client_id:
                    return group["id"]

    def setSourceState(self):
        match self.source_selected:
            case Sources.OFF:
                self.snap.sendCommand("Client.SetVolume", "{\"id\":\"" + os.getenv("SNAP_CLIENT_ID") + "\",\"volume\":{\"muted\": true }}")

            case Sources.RADIO:
                self.snap.sendCommand("Client.SetVolume", "{\"id\":\"" + os.getenv("SNAP_CLIENT_ID") + "\",\"volume\":{\"muted\": false }}")
                self.snap.sendCommand("Group.SetStream", "{\"id\": \"" + self.group_id + "\",\"stream_id\": \"Radio\"}")

            case Sources.SPOTIFY:
                self.snap.sendCommand("Client.SetVolume", "{\"id\":\"" + os.getenv("SNAP_CLIENT_ID") + "\",\"volume\":{\"muted\": false }}")
                self.snap.sendCommand("Group.SetStream", "{\"id\": \"" + self.group_id + "\",\"stream_id\": \"Spotify\"}")


    def updateSourceSelect(self, new_state, notify):
        if self.source_selected != new_state:
            self.source_selected = new_state
            self.setSourceState()
            notify(new_state)

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

    def getSourceSelectStateFromSnapcastServer(self):
        groups = self.snapcast_server_state["result"]["server"]["groups"]
        for group in groups:
            if group["id"] == self.group_id:
                for client in group["clients"]:
                    if client["id"] == self.client_id:
                        if client["config"]["volume"]["muted"]:
                            return Sources.OFF

                match group["stream_id"]:
                    case "Radio":
                        return Sources.RADIO
                    case "Spotify":
                        return Sources.SPOTIFY
                    case _:
                        # TODO: write this to a log instead, or throw exception
                        print("Unkown stream currently playing")
                        return None


    def run(self, gpio):
        # Synchronize state of the Radio with the Snapcast server
        self.snapcast_server_state = self.snap.sendCommand("Server.GetStatus")
        self.updateSourceSelect(self.getSourceSelectStateFromSnapcastServer(), gpio.setSourceSelectLeds)

        while not self.flags["exit"]:

            # TODO: handle snapcast onUpdate notifications before emptying
            # empty the TCP stream
            self.mpd.empty()
            self.snap.empty()

            # Handle Radio station button
            if self.flags["radio_station"]:
                self.flags["radio_station"] = False
                gpio.blinkLed(gpio.RADIO_LED, repeat=2, period=0.1)
                self.mpd.sendCommand("next")

            # Handle Source select switch
            if self.flags["source_select"]:
                self.flags["source_select"] = False
                self.updateSourceSelect(gpio.getSourceSelectState(), gpio.setSourceSelectLeds)

