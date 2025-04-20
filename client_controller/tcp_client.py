import socket
import json

class ConnectionError(Exception):
    pass

class SocketError(Exception):
    pass


class ServiceClient:
    def __init__(self, ip, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((ip, int(port)))
        except socket.error as e:
            print(e)
            raise ConnectionError(f"Can't reach server located at {ip}:{port}")

    def __del__(self):
        self.sock.close()

    def readMessage(self):
        message = ""

        # keep reading TCP stream untill newline character
        while True:
            chunk = self.sock.recv(1024)
            if not chunk:
                break
            message += chunk.decode()

            if b'\n' in chunk:
                break

        return message

    def sendToServer(self, msg):
        try:
            self.sock.send(f"{msg}\n".encode())
        except socket.error as e:
            if self.sock._closed:
                raise SocketError("ERROR: trying to send message, while socket is already closed")
            raise SocketError(f"ERROR: something when wrong when sending the message. \n\t {e}")
        return self.readMessage()

    # source: https://stackoverflow.com/questions/1655560/how-do-you-flush-python-sockets
    def empty(self):
        self.sock.setblocking(0)
        while True:
            try:
                self.sock.recv(1024)
            except BlockingIOError:
                self.sock.setblocking(1)
                return



class MPDClient(ServiceClient):
    def __init__(self, ip, port):
        super().__init__(ip, port)
        print(self.readMessage())

    def __del__(self):
        super().__del__()

    def sendCommand(self, command):
        return self.sendToServer(command)



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
        data = self.sendToServer(msg)
        try:
            json_data = json.loads(data)
        except Exception as e:
            raise e
        return json_data


