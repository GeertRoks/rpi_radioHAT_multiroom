import os

import tcp_client as tcp

class Snapcast:
    def __init__(self):
        self.snap = tcp.SnapClient(os.getenv("SNAP_IP"), os.getenv("SNAP_PORT"))

        # Set Snapcast info
        self.syncStateWithServer()
        self.client_id = os.getenv("SNAP_CLIENT_ID")
        self.group_id = self.getGroupID()

    def __del__(self):
        del self.snap

    def syncStateWithServer(self):
        self.server_state = self.snap.sendCommand("Server.GetStatus")

    def getGroupID(self):
        groups = self.server_state["result"]["server"]["groups"]
        for group in groups:
            for client in group["clients"]:
                if client["id"] == self.client_id:
                    return group["id"]
        # TODO: throw exception?
        return None

    def getGroupData(self):
        groups = self.server_state["result"]["server"]["groups"]
        for group in groups:
            if group["id"] == self.group_id:
                return group
        # TODO: throw exception?
        return None

    def getClientData(self):
        group = self.getGroupData()
        for client in group["clients"]:
            if client["id"] == self.client_id:
                return client
        # TODO: throw exception?
        return None

    def mute(self):
        self.snap.sendCommand("Client.SetVolume", "{\"id\":\"" + os.getenv("SNAP_CLIENT_ID") + "\",\"volume\":{\"muted\": true }}")

    def unmute(self):
        self.snap.sendCommand("Client.SetVolume", "{\"id\":\"" + os.getenv("SNAP_CLIENT_ID") + "\",\"volume\":{\"muted\": false }}")

    def setSourceToRadio(self):
        self.snap.sendCommand("Group.SetStream", "{\"id\": \"" + self.group_id + "\",\"stream_id\": \"Radio\"}")

    def setSourceToSpotify(self):
        self.snap.sendCommand("Group.SetStream", "{\"id\": \"" + self.group_id + "\",\"stream_id\": \"Spotify\"}")

    def isClientMuted(self):
        client = self.getClientData()
        if not client:
            # TODO: write this to a log instead, or throw exception
            print ("Error: no client data available")
            return None
        return client["config"]["volume"]["muted"]

