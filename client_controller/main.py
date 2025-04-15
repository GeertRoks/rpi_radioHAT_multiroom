import os
from dotenv import load_dotenv
import json

import source_control as src
import tcp_client as tcp
from helpers import GracefulExiter
from gpio_config import GPIO_Config

# Main Program

# Load environment variables from .env file
load_dotenv()

# Setup connections to Snapcast and MPD servers
snap = tcp.SnapClient(os.getenv("SNAP_IP"), os.getenv("SNAP_PORT"))
mpd = tcp.MPDClient(os.getenv("MPD_IP"), os.getenv("MPD_PORT"))

# setup GPIO
gpio = GPIO_Config()

source_selector = src.SourceState()
json_data = snap.sendCommand("Server.GetStatus")
#print(json.dumps(json_data["result"]["server"]["groups"][0], indent=2))

# Get Group ID
groups = json_data["result"]["server"]["groups"]
for group in groups:
    for client in group["clients"]:
        if client["id"] == os.getenv("SNAP_CLIENT_ID"):
            group_id = group["id"]
            break


flag = GracefulExiter()
radio_btn_pressed = False
while True:

    # TODO: handle snap onUpdate notifications before emptying
    # empty the TCP stream
    mpd.empty()
    snap.empty()

    # Source select switch
    source_select_state = gpio.getSourceSelectState()
    if (source_select_state["radio"] and source_select_state["spotify"]):
        # off
        if source_selector.getState() != src.Sources.OFF:
            source_selector.off()
            print(source_selector.getState())
            snap.sendCommand("Client.SetVolume", "{\"id\":\"" + os.getenv("SNAP_CLIENT_ID") + "\",\"volume\":{\"muted\": true }}")
            gpio.setRadioLed(False)
            gpio.setSpotifyLed(False)
    elif (source_select_state["radio"]):
        # radio
        if source_selector.getState() != src.Sources.RADIO:
            source_selector.radio()
            print(source_selector.getState())
            snap.sendCommand("Client.SetVolume", "{\"id\":\"" + os.getenv("SNAP_CLIENT_ID") + "\",\"volume\":{\"muted\": false }}")
            snap.sendCommand("Group.SetStream", "{\"id\": \"" + group_id + "\",\"stream_id\": \"Radio\"}")
            gpio.setRadioLed(True)
            gpio.setSpotifyLed(False)
    elif (source_select_state["spotify"]):
        # spotify
        if source_selector.getState() != src.Sources.SPOTIFY:
            source_selector.spotify()
            print(source_selector.getState())
            snap.sendCommand("Client.SetVolume", "{\"id\":\"" + os.getenv("SNAP_CLIENT_ID") + "\",\"volume\":{\"muted\": false }}")
            snap.sendCommand("Group.SetStream", "{\"id\": \"" + group_id + "\",\"stream_id\": \"Spotify\"}")
            gpio.setRadioLed(False)
            gpio.setSpotifyLed(True)

    # Radio station button
    if source_selector.getState() == src.Sources.RADIO:
        radio_btn_state = gpio.getRadioBtnState()
        if (not radio_btn_state and not radio_btn_pressed):
            # send Next command to MPD
            mpd.sendCommand("next")
            print("send next to MPD")
            radio_btn_pressed = True
        elif (radio_btn_state and radio_btn_pressed):
            print("RADIO_BTN: done")
            radio_btn_pressed = False


    if flag.exit():
        break

del snap
del mpd

