import socket
import json
import time

IP = '192.168.20.120'
PORT = 12345

if __name__ == '__main__':
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((IP, PORT))

    # 发送开启检测指令
    json_data = {"action" : "start"}
    json_str = json.dumps(json_data)
    client.sendall(json_str.encode('utf-8'))
    while True:
        json_str = client.recv(1024)
        json_data = json.loads(json_str.decode('utf-8'))
        print(json_data)

