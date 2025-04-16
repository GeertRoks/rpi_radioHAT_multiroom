import os
import time
import signal

import tcp_client as tcp
from states import Sources

class Radio:
    def __init__(self):
        # Setup connections to Snapcast and MPD servers
        self.snap = tcp.SnapClient(os.getenv("SNAP_IP"), os.getenv("SNAP_PORT"))
        self.mpd = tcp.MPDClient(os.getenv("MPD_IP"), os.getenv("MPD_PORT"))

        self.source_selected = Sources.OFF

        # Event flags
        self.flags = {"radio_station": False,
                      "source_select": False,
                      "exit": False}
        signal.signal(signal.SIGINT, self.exit_event)

        # Set Snapcast info
        self.client_id = os.getenv("SNAP_CLIENT_ID")
        self.group_id = self.getGroupID(self.snap.sendCommand("Server.GetStatus"))

    def __del__(self):
        del self.snap
        del self.mpd

    def getGroupID(self, server_data_json):
        groups = server_data_json["result"]["server"]["groups"]
        for group in groups:
            for client in group["clients"]:
                if client["id"] == self.client_id:
                    return group["id"]

    def radio_button_event(self, channel):
        if self.source_selected == Sources.RADIO:
            print("Radio button: next")
            self.flags["radio_station"] = True

    def source_switch_event(self, channel):
        # TODO: write to log instead
        print(f"Source switch event: {channel}")
        self.flags["source_select"] = True

    def exit_event(self, signum, frame):
        print("Ctrl+C detected, exiting now ...")
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        self.flags["exit"] = True


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

    def run(self, gpio):
        while not self.flags["exit"]:

            # TODO: handle snapcast onUpdate notifications before emptying
            # empty the TCP stream
            self.mpd.empty()
            self.snap.empty()

            # Handle Radio station button
            if self.flags["radio_station"]:
                self.flags["radio_station"] = False
                self.mpd.sendCommand("next")
                # blink the Radio LED to indicate that the press is registered
                gpio.setRadioLed(False)
                time.sleep(0.1)
                gpio.setRadioLed(True)

            # Handle Source select switch
            if self.flags["source_select"]:
                self.flags["source_select"] = False
                self.updateSourceSelect(gpio.getSourceSelectState(), gpio.setLedState)

