import threading
import time
from enum import Enum
from utils.socket import SocketServer
import json

IP = '192.168.20.120'
PORT = 12345

lock = threading.Lock()
flag = False

class State(Enum):
    STOP = 0
    START = 1

class App:
    def __init__(self, host, port):
        self.server = SocketServer(host, port)
        self.lock = threading.Lock()
        self.detect_flag = False
        self.status = State.STOP
    
    def run(self):
        self.server.start()
        while True:
            # 等待接收客户端的启动消息
            receive_data = self.server.receive_json()
            if self.status == State.STOP:
                if receive_data['action'] == 'start':
                    response_data = {"status" : 'success', "message" : 'start detecting'}
                    self.server.send_json(response_data)
                    detect_thread = threading.Thread(target=self.send_results)
                    self.detect_flag = True
                    detect_thread.start()
                    self.status = State.START
            # 等待接收客户端的停止消息
            if self.status == State.START:
                if receive_data['action'] == 'stop':
                    with self.lock:
                        self.detect_flag = False
                    detect_thread.join()
                    response_data = {"status" : 'success', "message" : 'stop detecting'}
                    self.server.send_json(response_data)
                    self.status = State.STOP
    
    def send_results(self):
        counter = 0
        while True:
            with self.lock:
                if self.detect_flag == False:
                    break
            if counter == 6:
                json_data = {'datas': [
                    {
                        'label': 'green',
                        'confidence': '0.9',
                        'location': [1, 2, 3, 4]
                    }
                ]}
            else:
                json_data = {'datas': [
                    {
                        'label': 'red',
                        'confidence': '0.9',
                        'location': [1, 2, 3, 4]
                    }
                ]}
            self.server.send_json(json_data)
            counter += 1
            print(f'send times: {counter}')
            time.sleep(1)  # 每秒发送一条消息

    def stop(self):
        self.server.stop()


if __name__ == '__main__':
    with open('config.json', 'r', encoding='utf-8') as file:
        config = json.load(file)
        print(f'App config:\n{json.dumps(config, indent=4)}')
    app = App(IP, PORT)
    # app.run()
    # app.stop()


        
