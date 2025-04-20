import re # regex

from tcp_client import MPDClient, ConnectionError

class InternetRadio:
    def __init__(self, ip, port, playlist_name = "radio_stations"):
        try:
            self.mpd = MPDClient(ip, port)
        except ConnectionError as e:
            print(f"ERROR: failed to create MPDClient.\n\t{e}")
            raise e

        self.playlist_name = playlist_name
        self.setLoopingPlaylist()

    def setLoopingPlaylist(self):
        status = self.mpd.sendCommand("status")
        single_state = re.findall(r'single:\s+(\d+)', status)[0]
        repeat_state = re.findall(r'repeat:\s+(\d+)', status)[0]
        if single_state == "1":
            self.mpd.sendCommand("single 0")
        if repeat_state == "0":
            self.mpd.sendCommand("repeat 1")

    def next(self):
        if not self.playlistIsLoaded():
            self.loadPlaylist()

        if not self.isPlaying():
            self.startPlaying()

        self.mpd.sendCommand("next")

    def startPlaying(self):
        self.mpd.sendCommand("play")

    def isPlaying(self):
        status = self.mpd.sendCommand("status")
        play_state = re.findall(r'state:\s+(\w+)', status)[0]
        if play_state == "play":
            return True
        return False

    def loadPlaylist(self):
        self.mpd.sendCommand("clear")
        self.mpd.sendCommand(f"load {self.playlist_name}")

    def playlistIsLoaded(self):
        playlist = self.mpd.sendCommand(f"listplaylist {self.playlist_name}")
        queue = self.mpd.sendCommand("playlistinfo")

        # Split playlist into individual lines, removing empty lines
        playlist_lines = [line.strip() for line in playlist.split('\n') if line.strip()]
        queue_pos = 0
        for playlist_line in playlist_lines:
            if playlist_line == 'OK':
                # Special handling for OK marker
                # Check if there are any more 'file:' entries in the queue
                remaining_queue = queue[queue_pos:]
                if 'file:' in remaining_queue:
                    print("Error: Extra entries found in queue")
                    return False
                print("Success: Playlist matches queue exactly")
                return True
            remaining_queue = queue[queue_pos:]
            match = re.search(re.escape(playlist_line), remaining_queue)
            if not match:
                print(f"Error: Could not find '{playlist_line}' in queue")
                return False

            # Update position to after the match
            queue_pos += match.end()

        # If we get here, we haven't found an OK marker
        print("Error: Missing OK marker in playlist")
        return False
