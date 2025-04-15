import os
import time

import tcp_client as tcp
from helpers import GracefulExiter
from helpers import Sources

class Radio:
    def __init__(self):
        # Setup connections to Snapcast and MPD servers
        self.snap = tcp.SnapClient(os.getenv("SNAP_IP"), os.getenv("SNAP_PORT"))
        self.mpd = tcp.MPDClient(os.getenv("MPD_IP"), os.getenv("MPD_PORT"))

        self.source_selected = Sources.OFF

        # TODO: combine all flags in an object
        self.exit_flag = GracefulExiter()
        self.radio_btn_flag = False
        self.source_switch_flag = False

        # Get Group ID
        json_data = self.snap.sendCommand("Server.GetStatus")
        groups = json_data["result"]["server"]["groups"]
        for group in groups:
            for client in group["clients"]:
                if client["id"] == os.getenv("SNAP_CLIENT_ID"):
                    self.group_id = group["id"]
                    break

    def __del__(self):
        del self.snap
        del self.mpd

    def radio_btn_callback(self, channel):
        if self.source_selected == Sources.RADIO:
            print("Radio button: next")
            self.radio_btn_flag = True

    def source_switch_callback(self, channel):
        # TODO: write to log instead
        print(f"Source switch event: {channel}")
        self.source_switch_flag = True


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
        while True:

            # TODO: handle snapcast onUpdate notifications before emptying
            # empty the TCP stream
            self.mpd.empty()
            self.snap.empty()

            if self.radio_btn_flag:
                self.radio_btn_flag = False
                self.mpd.sendCommand("next")
                # blink the Radio LED to indicate that the press is registered
                gpio.setRadioLed(False)
                time.sleep(0.1)
                gpio.setRadioLed(True)

            if self.source_switch_flag:
                self.source_flag = False
                self.updateSourceSelect(gpio.getSourceSelectState(), gpio.setLedState)

            if self.exit_flag.exit():
                break
