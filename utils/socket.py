import socket
import json


class SocketServer:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None
        self.conn = None
        self.addr = None

    def start(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(self.host, self.port)
        self.socket.listen(1)
        self.client, self.addr = self.socket.accept()

    def stop(self):
        if self.socket:
            if self.client:
                self.client.close()
                self.addr = None
                self.client = None
            self.socket.close()
            self.socket = None

    def send_json(self, json_data):
        json_str = json.dumps(json_data)
        self.client.sendall(json_str.encode('utf-8'))

    def receive_json(self):
        json_str = self.client.recv(1024)
        json_data = json.loads(json_str.decode('utf-8'))