import os
import time
import tcp_client as tcp
import source_control as src
from helpers import GracefulExiter

class Radio:
    def __init__(self):
        # Setup connections to Snapcast and MPD servers
        self.snap = tcp.SnapClient(os.getenv("SNAP_IP"), os.getenv("SNAP_PORT"))
        self.mpd = tcp.MPDClient(os.getenv("MPD_IP"), os.getenv("MPD_PORT"))
        self.source_selector = src.SourceState()
        self.radio_btn_flag = False

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
                if self.source_selector.getState() != src.Sources.OFF:
                    self.source_selector.off()
                    print(self.source_selector.getState())
                    self.snap.sendCommand("Client.SetVolume", "{\"id\":\"" + os.getenv("SNAP_CLIENT_ID") + "\",\"volume\":{\"muted\": true }}")
                    gpio.setRadioLed(False)
                    gpio.setSpotifyLed(False)
            elif (source_select_state["radio"]):
                # radio
                if self.source_selector.getState() != src.Sources.RADIO:
                    self.source_selector.radio()
                    print(self.source_selector.getState())
                    self.snap.sendCommand("Client.SetVolume", "{\"id\":\"" + os.getenv("SNAP_CLIENT_ID") + "\",\"volume\":{\"muted\": false }}")
                    self.snap.sendCommand("Group.SetStream", "{\"id\": \"" + self.group_id + "\",\"stream_id\": \"Radio\"}")
                    gpio.setRadioLed(True)
                    gpio.setSpotifyLed(False)
            elif (source_select_state["spotify"]):
                # spotify
                if self.source_selector.getState() != src.Sources.SPOTIFY:
                    self.source_selector.spotify()
                    print(self.source_selector.getState())
                    self.snap.sendCommand("Client.SetVolume", "{\"id\":\"" + os.getenv("SNAP_CLIENT_ID") + "\",\"volume\":{\"muted\": false }}")
                    self.snap.sendCommand("Group.SetStream", "{\"id\": \"" + self.group_id + "\",\"stream_id\": \"Spotify\"}")
                    gpio.setRadioLed(False)
                    gpio.setSpotifyLed(True)

            if self.radio_btn_flag:
                self.radio_btn_flag = False
                if self.source_selector.getState() == src.Sources.RADIO:
                    print("Radio button: next")
                    self.mpd.sendCommand("next")
                    # blink the Radio LED to indicate that the press is registered
                    gpio.setRadioLed(False)
                    time.sleep(0.1)
                    gpio.setRadioLed(True)

            if flag.exit():
                break
