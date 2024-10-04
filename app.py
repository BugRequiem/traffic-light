import threading
import time
from enum import Enum
from utils.socket import SocketServer
from utils.camera import GstreamerCamera
from utils.model import DetectModel
import json
import atexit


class State(Enum):
    STOP = 0
    START = 1


class App:

    def __init__(self, config):
        self.config = config
        self.server = None
        self.init_socket()
        self.camera = None
        self.init_camera()
        self.model = DetectModel()
        self.camera = GstreamerCamera()
        self.lock = threading.Lock()
        self.detect_flag = False
        self.status = State.STOP
    
    def init_socket(self):
        host = self.config['socket']['host']
        port = self.config['socket']['port']
        self.server = SocketServer(host, port)
    
    def init_camera(self):
        device = self.config['camera']['device']
        width = self.config['camera']['width']
        height = self.config['camera']['height']
        framerate = self.config['camera']['framerate']
        pformat = self.config['camera']['pformat']
        self.camera = GstreamerCamera(device, width, height, framerate, pformat)

    
    def run(self):
        self.server.start()
        while True:
            # 等待接收客户端的启动消息
            receive_data = self.server.receive_json()
            if receive_data == None:
                continue
            if self.status == State.STOP:  # 如果检测线程未启动
                if receive_data['action'] == 'start':
                    response_data = {"status" : 'success', "message" : 'start detecting'}
                    self.server.send_json(response_data)
                    detect_thread = threading.Thread(target=self.send_results)
                    self.detect_flag = True
                    detect_thread.start()
                    self.status = State.START
            # 等待接收客户端的停止消息
            if self.status == State.START:  # 如果检测线程启动
                if receive_data['action'] == 'stop':
                    with self.lock:
                        self.detect_flag = False
                    detect_thread.join()
                    response_data = {"status" : 'success', "message" : 'stop detecting'}
                    self.server.send_json(response_data)
                    self.status = State.STOP
    
    def send_results(self):
        while True:
            with self.lock:
                if self.detect_flag == False:
                    break
            # 调用model的detect方法获取到检测结果
            json_data = {'datas': [
                {
                    'label': 'green',
                    'confidence': '0.9',
                    'location': [1, 2, 3, 4]
                }
            ]}
            start_time = time.time()
            frame = self.camera.read()              # 从摄像头读取帧
            result = self.model.inference(frame)    # 模型推理获得结果
            self.server.send_json(json_data)        # socket发送结果
            finish_time = time.time()
            task_time = finish_time - start_time    # 单次任务所用时间
            time.sleep(1 - task_time)  # 每秒发送一条消息

    def stop(self):
        self.server.stop()
        self.camera.close()


if __name__ == '__main__':
    # 获取配置信息
    with open('config.json', 'r', encoding='utf-8') as file:
        config = json.load(file)
        print(f'App config:\n{json.dumps(config, indent=4)}')

    app = App(config)
    atexit.register(app.stop())
    app.run()
