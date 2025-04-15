import os
import time
from enum import Enum

import tcp_client as tcp
from helpers import GracefulExiter

class Sources(Enum):
    OFF = 0
    RADIO = 1
    SPOTIFY = 2

class Radio:
    def __init__(self):
        # Setup connections to Snapcast and MPD servers
        self.snap = tcp.SnapClient(os.getenv("SNAP_IP"), os.getenv("SNAP_PORT"))
        self.mpd = tcp.MPDClient(os.getenv("MPD_IP"), os.getenv("MPD_PORT"))

        # TODO: combine all flags in an object
        self.radio_btn_flag = False
        self.source_selected = Sources.OFF

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
        self.radio_btn_flag = True

    def run(self, gpio):
        flag = GracefulExiter()
        while True:

            # TODO: handle snapcast onUpdate notifications before emptying
            # empty the TCP stream
            self.mpd.empty()
            self.snap.empty()

            # Source select switch
            source_select_state = gpio.getSourceSelectState()
            if (source_select_state["radio"] and source_select_state["spotify"]):
                # off
                if self.source_selected != Sources.OFF:
                    self.source_selected = Sources.OFF
                    print(self.source_selected)
                    self.snap.sendCommand("Client.SetVolume", "{\"id\":\"" + os.getenv("SNAP_CLIENT_ID") + "\",\"volume\":{\"muted\": true }}")
                    gpio.setRadioLed(False)
                    gpio.setSpotifyLed(False)
            elif (source_select_state["radio"]):
                # radio
                if self.source_selected != Sources.RADIO:
                    self.source_selected = Sources.RADIO
                    print(self.source_selected)
                    self.snap.sendCommand("Client.SetVolume", "{\"id\":\"" + os.getenv("SNAP_CLIENT_ID") + "\",\"volume\":{\"muted\": false }}")
                    self.snap.sendCommand("Group.SetStream", "{\"id\": \"" + self.group_id + "\",\"stream_id\": \"Radio\"}")
                    gpio.setRadioLed(True)
                    gpio.setSpotifyLed(False)
            elif (source_select_state["spotify"]):
                # spotify
                if self.source_selected != Sources.SPOTIFY:
                    self.source_selected = Sources.SPOTIFY
                    print(self.source_selected)
                    self.snap.sendCommand("Client.SetVolume", "{\"id\":\"" + os.getenv("SNAP_CLIENT_ID") + "\",\"volume\":{\"muted\": false }}")
                    self.snap.sendCommand("Group.SetStream", "{\"id\": \"" + self.group_id + "\",\"stream_id\": \"Spotify\"}")
                    gpio.setRadioLed(False)
                    gpio.setSpotifyLed(True)

            if self.radio_btn_flag:
                self.radio_btn_flag = False
                if self.source_selected == Sources.RADIO:
                    print("Radio button: next")
                    self.mpd.sendCommand("next")
                    # blink the Radio LED to indicate that the press is registered
                    gpio.setRadioLed(False)
                    time.sleep(0.1)
                    gpio.setRadioLed(True)

            if flag.exit():
                break
