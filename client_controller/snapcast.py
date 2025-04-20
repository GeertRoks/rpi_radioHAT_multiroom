from os import getenv

from tcp_client import ConnectionError, SnapClient

class EnvironmentVariableNotFound(Exception):
    pass

class Snapcast:
    def __init__(self, ip, port):
        try:
            self.snap = SnapClient(ip, port)
        except ConnectionError as e:
            print(f"ERROR: failed to create SnapClient.\n\t{e}")
            raise e

        self.client_id = getenv("SNAP_CLIENT_ID")
        if not self.client_id:
            print(self.client_id)
            raise EnvironmentVariableNotFound("ERROR: SNAP_CLIENT_ID not defined")

        # Set Snapcast info
        self.syncStateWithServer()
        self.group_id = self.getGroupID()


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
        self.snap.sendCommand("Client.SetVolume", "{\"id\":\"" + self.client_id + "\",\"volume\":{\"muted\": true }}")

    def unmute(self):
        self.snap.sendCommand("Client.SetVolume", "{\"id\":\"" + self.client_id + "\",\"volume\":{\"muted\": false }}")

    def setSourceToRadio(self):
        self.snap.sendCommand("Group.SetStream", "{\"id\": \"" + self.group_id + "\",\"stream_id\": \"Radio\"}")

    def setSourceToSpotify(self):
        self.snap.sendCommand("Group.SetStream", "{\"id\": \"" + self.group_id + "\",\"stream_id\": \"Spotify\"}")

    def isClientMuted(self):
        client = self.getClientData()
        if not client:
            # TODO: write this to a log instead, or throw exception
            print ("ERROR: no client data available")
            return None
        return client["config"]["volume"]["muted"]

