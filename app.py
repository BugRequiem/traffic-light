import threading
import time
from enum import Enum
from utils.socket import SocketServer
from utils.camera import GstreamerCamera
from utils.model.sample import ModelSample
import json
import atexit


class State(Enum):
    STOP = 0
    START = 1


class App:

    def __init__(self, config):
        self.config = config
        self.server = SocketServer(self.config['socket'])       # 初始化socket
        self.camera = GstreamerCamera(self.config['camera'])    # 初始化相机
        self.model = ModelSample(self.config['model'])          # 初始化模型
        self.lock = threading.Lock()                            # 声明互斥锁
        self.detect_flag = False                                # 声明检测线程标志
        self.status = State.STOP                                # 声明检测线程运行状态
    
    def run(self):
        self.server.start()
        while True:
            # 阻塞接收客户端消息
            receive_data = self.server.receive_json()
            if receive_data == None:
                continue
            # 接收到客户端的启动消息
            if self.status == State.STOP:  # 如果检测线程未启动
                if receive_data['action'] == 'start':
                    response_data = {"status" : 'success', "message" : 'start detecting'}
                    self.server.send_json(response_data)
                    detect_thread = threading.Thread(target=self.send_results)
                    self.detect_flag = True
                    detect_thread.start()
                    self.status = State.START
            # 接收到客户端的停止消息
            if self.status == State.START:  # 如果检测线程启动
                if receive_data['action'] == 'stop':
                    with self.lock:
                        self.detect_flag = False
                    detect_thread.join()
                    response_data = {"status" : 'success', "message" : 'stop detecting'}
                    self.server.send_json(response_data)
                    self.status = State.STOP
    
    # 推理与结果发送线程函数
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
            # result = self.model(frame=frame)      # 模型推理获得结果
            self.server.send_json(json_data)        # socket发送结果
            finish_time = time.time()
            task_time = finish_time - start_time    # 单次任务所用时间
            time.sleep(1 - task_time)               # 每秒发送一条消息

    def stop(self):
        self.server.stop()
        self.camera.close()


if __name__ == '__main__':
    # 获取配置信息
    with open('config.json', 'r', encoding='utf-8') as file:
        config = json.load(file)
        print(f'App config:\n{json.dumps(config, indent=4)}')
    # 创建并启动服务器
    app = App(config)
    atexit.register(app.stop())
    app.run()
