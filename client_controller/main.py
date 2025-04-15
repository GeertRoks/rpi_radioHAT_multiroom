import os
from dotenv import load_dotenv
import socket
import json

import RPi.GPIO as GPIO

import signal


# source: https://stackoverflow.com/questions/24426451/how-to-terminate-loop-gracefully-when-ctrlc-was-pressed-in-python
class GracefulExiter():
    def __init__(self):
        self.state = False
        signal.signal(signal.SIGINT, self.change_state)

    def change_state(self, signum, frame):
        print("Ctrl+C detected, exiting now ...")
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        self.state = True

    def exit(self):
        return self.state

class ServiceClient:
    def __init__(self, ip, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((ip, int(port)))

    def __del__(self):
        self.sock.close()

    def readMessage(self):
        message = ""

        while True:
            chunk = self.sock.recv(1024)
            if not chunk:
                break
            message += chunk.decode()

            # Check for message completion criteria
            if b'\n' in chunk:
                break

        return message

    def sendCommand(self, command):
        return self.sendToServer(command)

    def sendToServer(self, msg):
        self.sock.send(f"{msg}\n".encode())
        data = self.readMessage()
        json_data = json.loads(data)
        return json_data

class MPDClient(ServiceClient):
    def __init__(self, ip, port):
        super().__init__(ip, port)
        data = self.sock.recv(1024)
        print(data.decode())

    def __del__(self):
        super().__del__()

class SnapClient(ServiceClient):
    msg_count = 0
    def __init__(self, ip, port):
        super().__init__(ip, port)

    def __del__(self):
        super().__del__()

    def sendCommand(self, command, params = None):
        msg_id = f"{socket.gethostname()}-msg-{self.msg_count}"
        msg = "{\"id\":\"" + msg_id + "\",\"jsonrpc\":\"2.0\",\"method\":\"" + command + "\""
        if params:
            msg += ",\"params\":" + params
        msg += "}\n"
        self.msg_count += 1
        return self.sendToServer(msg)

class RadioState:

    def __init__(self):
        pass

    def ensureRadioPlaylistIsLoaded(self):
        # check entries in radio_stations.m3u
        # compare with current playlist
        pass

    def ensureRadioPlaying(self):
        # ensure radio playlist is loaded
        # get mpd status
        # check if mpd is playing
        # if not then send play command
        pass

class SourceState:
    source_state = 0

    def __init__(self):
        self.off()

    def off(self):
        self.source_state = 0
        # set Snapcast source to None

    def radio(self):
        self.source_state = 1
        # set Snapcast source to Radio
    
    def spotify(self):
        self.source_state = 2
        # set Snapcast source to Spotify

    def getState(self):
        return self.source_state


# Main Program

# Load environment variables from .env file
load_dotenv()

# Setup connections to Snapcast and MPD servers
snap = SnapClient(os.getenv("SNAP_IP"), os.getenv("SNAP_PORT"))
mpd = MPDClient(os.getenv("MPD_IP"), os.getenv("MPD_PORT"))

source_selector = SourceState()
json_data = snap.sendCommand("Server.GetStatus")
print(json.dumps(json_data["result"]["server"]["groups"][0], indent=2))

# Get Group ID
groups = json_data["result"]["server"]["groups"]
for group in groups:
    for client in group["clients"]:
        if client["id"] == os.getenv("SNAP_CLIENT_ID"):
            group_id = group["id"]
            break


# Define GPIO ports
SPOTIFY_LED = 17
RADIO_LED = 27
RADIO_BTN = 24
SRC_SEL_RADIO = 22
SRC_SEL_SPOTIFY = 23

GPIO.setmode(GPIO.BCM)
GPIO.setup(SPOTIFY_LED, GPIO.OUT)
GPIO.setup(RADIO_LED, GPIO.OUT)
GPIO.setup(RADIO_BTN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(SRC_SEL_RADIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(SRC_SEL_SPOTIFY, GPIO.IN, pull_up_down=GPIO.PUD_UP)

flag = GracefulExiter()
radio_btn_pressed = False
while True:
    # Radio station button
    radio_btn_state = GPIO.input(RADIO_BTN)
    if (radio_btn_state == GPIO.LOW and not radio_btn_pressed):
        # send Next command to MPD
        mpd.sendCommand("next")
        print("send next to MPD")
        radio_btn_pressed = True
    elif (radio_btn_state == GPIO.HIGH and radio_btn_pressed):
        print("RADIO_BTN: done")
        radio_btn_pressed = False

    # Source select switch
    source_select_state = ( GPIO.input(SRC_SEL_RADIO), GPIO.input(SRC_SEL_SPOTIFY) )
    if (source_select_state[0] and source_select_state[1]):
        # off
        if source_selector.getState() != 0:
            source_selector.off()
            print(source_selector.getState())
            # TODO: maybe use muting instead of setting the source to /dev/null?
            snap.sendCommand("Group.SetStream", "{\"id\":\"" + group_id + "\",\"stream_id\":\"None\"}")
            GPIO.output(SPOTIFY_LED, GPIO.LOW)
            GPIO.output(RADIO_LED, GPIO.LOW)
    elif (source_select_state[0]):
        # radio
        if source_selector.getState() != 1:
            snap.sendCommand("Group.SetStream", "{\"id\": \"" + group_id + "\",\"stream_id\": \"Radio\"}")
            source_selector.radio()
            print(source_selector.getState())
            GPIO.output(SPOTIFY_LED, GPIO.LOW)
            GPIO.output(RADIO_LED, GPIO.HIGH)
    elif (source_select_state[1]):
        # spotify
        if source_selector.getState() != 2:
            snap.sendCommand("Group.SetStream", "{\"id\": \"" + group_id + "\",\"stream_id\": \"Spotify\"}")
            source_selector.spotify()
            print(source_selector.getState())
            GPIO.output(SPOTIFY_LED, GPIO.HIGH)
            GPIO.output(RADIO_LED, GPIO.LOW)


    if flag.exit():
        break

del snap
del mpd
GPIO.cleanup()

