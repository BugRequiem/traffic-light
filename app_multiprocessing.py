import threading
import time
from enum import Enum
from utils.socket import SocketServer
from utils.camera import GstreamerCamera
from utils.model.model import Model
from utils.debug import Debug
import json
import atexit
import multiprocessing
import numpy as np
import cv2
import sys
import queue


def detect(lock, config, shape, freq, detect_msg_queue, shared_frame_array, socket_queue, error_queue):
    """
    模型推理进程
    """
    message = 'suspend'
    model = Model(config['model'])
    while True:
        if not detect_msg_queue.empty():
            message = detect_msg_queue.get()
        if message == 'suspend':
            message = detect_msg_queue.get()
        elif message == 'stop':
            sys.exit(0)
        elif message == 'resume':
            with lock:
                frame = np.frombuffer(shared_frame_array.get_obj(), dtype=np.uint8).reshape(shape)
            start_time = time.time()
            try:
                result = model(frame=frame)
            except Exception as e:
                error_queue.put(e)
                sys.exit(-1)
            finish_time = time.time()
            task_time = finish_time - start_time    # 单次任务所用时间
            print("tast_time = ", task_time)
            # result_queue.put(result)
            socket_queue.put(result)
            delay_time = 1 / freq - task_time
            if delay_time > 0:
                time.sleep(delay_time)


def capture(lock, config, shape, cap_msg_queue, shared_frame_array, error_queue):
    """
    捕获图像进程
    """
    message = 'suspend'
    camera = GstreamerCamera(config['camera'])
    while True:
        if not cap_msg_queue.empty():
            message = cap_msg_queue.get()
        if message == 'suspend':
            message = cap_msg_queue.get()
        elif message == 'stop':
            sys.exit(0)
        elif message == 'resume':
            try:
                frame = camera.read()
            except Exception as e:
                error_queue.put(e)
                sys.exit(-1)
            with lock:
                np.frombuffer(shared_frame_array.get_obj(), dtype=np.uint8).reshape(shape)[:] = frame

def send():
    "发送socket消息的子线程"
    # message = 'stop'
    while True:
        # if not socket_queue.empty():
        message = socket_queue.get()
        # print(message)
        # if message == 'stop':
        #     message = socket_queue.get()
        # elif message == 'start':
        #     result = result_queue.get()
        server.send_json(message)

def receive():
    while True:
        receive_data = server.receive_json()
        if receive_data['action'] == 'start':
            response_data = {"status" : 'success', "message" : 'start detecting'}
            # server.send_json(response_data)
            socket_queue.put(response_data)
            cap_msg_queue.put('resume')
            detect_msg_queue.put('resume')
        if receive_data['action'] == 'stop':
            cap_msg_queue.put('suspend')
            detect_msg_queue.put('suspend')
            response_data = {"status" : 'success', "message" : 'stop detecting'}
            # server.send_json(response_data)
            socket_queue.put(response_data)


if __name__ == '__main__':
    # 获取配置信息
    with open('config.json', 'r', encoding='utf-8') as file:
        config = json.load(file)
        print(f'App config:\n{json.dumps(config, indent=4)}')
    # TODO 读配置进行shape和size计算
    shape = (1080, 1920, 3)
    size = 1080 * 1920 * 3

    shared_frame_array = multiprocessing.Array('B', size)
    detect_msg_queue = multiprocessing.Queue()
    cap_msg_queue = multiprocessing.Queue()
    # result_queue = multiprocessing.Queue()
    error_queue = multiprocessing.Queue()
    socket_queue = multiprocessing.Queue()
    lock = multiprocessing.Lock()
    detect_processing = multiprocessing.Process(target=detect, args=(lock, config, shape, 1, detect_msg_queue, shared_frame_array, socket_queue, error_queue))
    capture_processing = multiprocessing.Process(target=capture, args=(lock, config, shape, cap_msg_queue, shared_frame_array, error_queue))

    detect_processing.daemon = True
    capture_processing.daemon = True

    detect_processing.start()
    capture_processing.start()

    server = SocketServer(config['socket'])
    server.start()

    # socket_queue = queue.Queue()
    send_thread = threading.Thread(target=send)
    receive_thread = threading.Thread(target=receive)
    
    send_thread.start()
    receive_thread.start()
