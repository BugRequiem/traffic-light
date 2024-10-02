import threading
from utils.socket import SocketServer

IP = '192.168.20.120'
PORT = 12345


if __name__ == '__main__':
    server = SocketServer(IP, PORT)