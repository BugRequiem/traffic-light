import threading
import time
from utils.socket import SocketServer
from utils.camera import GstreamerCamera
from utils.model.model import Model
import json
import atexit
import multiprocessing
import numpy as np
import sys
import logging
import atexit
import os


def detect(lock, config, shape, freq, detect_msg_queue, shared_frame_array, socket_queue, error_queue):
    """
    模型推理进程
    """
    # 自动进入暂停状态，等待开始消息
    message = 'suspend'
    logger = logging.getLogger('app_logger')
    try:
        model = Model(config['model'])
    except Exception as e:
        logger.error(f'Model init error: {e}')
        error_queue.put(("detect", str(e)))
        sys.exit(-1)
    logger.info("detect init success, start detect processing.")
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
                logger.error(f'Model inference error: {e}')
                error_queue.put(("detect", str(e)))
                sys.exit(-1)
            finish_time = time.time()
            task_time = finish_time - start_time    # 单次任务所用时间
            logger.debug(f"tast_time = {task_time}")
            socket_queue.put(result)                # 结果存放入socket消息队列
            delay_time = 1 / freq - task_time       # 根据发送频率计算延时
            if delay_time > 0:
                time.sleep(delay_time)


def capture(lock, config, shape, cap_msg_queue, shared_frame_array, error_queue):
    """
    捕获图像进程
    """
    # 自动进入暂停状态，等待开始消息
    message = 'suspend'
    logger = logging.getLogger('app_logger')
    try:
        camera = GstreamerCamera(config['camera'])
    except Exception as e:
        camera.close()
        logger.error(f'Camera init error: {e}')
        error_queue.put(("capture", str(e)))
        sys.exit(-1)
    logger.info("capture init success, start capture processing.")
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
                logger.debug('read a frame')
            except Exception as e:
                camera.close()
                logger.error(f'Camera read error: {e}')
                error_queue.put(("capture", str(e)))
                sys.exit(-1)
            with lock:
                np.frombuffer(shared_frame_array.get_obj(), dtype=np.uint8).reshape(shape)[:] = frame
            if config['camera']['mode'] == 'video':
                time.sleep(1 / config['camera']['framerate'])


def send():
    """
    发送socket消息的子线程
    """
    while True:
        message = socket_queue.get()
        if message is None:
            return
        try:
            server.send_json(message)
        except Exception as e:
            logger.error(f'Socket send message error: {e}')
            error_queue.put(("send", str(e)))
            return

def receive():
    """
    接收socket消息的子线程
    """
    while True:
        try:
            receive_data = server.receive_json()
            if receive_data is None:
                socket_queue.put(None)
                raise RuntimeError('None data received')
        except Exception as e:
            logger.error(f'Socket receive message error: {e}')
            error_queue.put(("receive", str(e)))
            return
        if receive_data['action'] == 'start':
            response_data = {"status" : 'success', "message" : 'start detecting'}
            cap_msg_queue.put('resume')         # 继续相机捕获进程
            detect_msg_queue.put('resume')      # 继续模型检测进程
            socket_queue.put(response_data)     # 将成功消息添加到socket消息队列
        elif receive_data['action'] == 'stop':
            response_data = {"status" : 'success', "message" : 'stop detecting'}
            cap_msg_queue.put('suspend')        # 暂停相机捕获进程
            detect_msg_queue.put('suspend')     # 暂停模型检测进程
            socket_queue.put(response_data)     # 将成功消息添加到socket消息队列

def app_cleanup():
    if detect_processing.is_alive():
        detect_processing.terminate()
    if capture_processing.is_alive():
        capture_processing.terminate()
    detect_processing.join()
    capture_processing.join()
    logger.info("app will restart after 10 seconds")
    server.stop()
    listener.stop()
    log_queue.close()
    log_queue.join_thread()
    detect_msg_queue.close()
    detect_msg_queue.join_thread()
    cap_msg_queue.close()
    cap_msg_queue.join_thread()
    error_queue.close()
    error_queue.join_thread()
    socket_queue.close()
    socket_queue.join_thread()
    time.sleep(10)
    os.execv(sys.executable, ['python'] + sys.argv)
    

if __name__ == '__main__':
    atexit.register(app_cleanup)
    # 获取配置信息
    with open('config.json', 'r', encoding='utf-8') as file:
        config = json.load(file)
    height = config['camera']['height']
    width = config['camera']['width']
    shape = (height, width, 3)
    size = height * width * 3
    freq = config['app']['freq']

    # 定义进程间共享变量，存放图像数据
    shared_frame_array = multiprocessing.Array('B', size)
    # 定义互斥锁，用于访问共享资源shared_frame_array
    lock = multiprocessing.Lock()
    # 定义消息队列
    detect_msg_queue = multiprocessing.Queue()
    cap_msg_queue = multiprocessing.Queue()
    error_queue = multiprocessing.Queue()
    socket_queue = multiprocessing.Queue()
    log_queue = multiprocessing.Queue(-1)

    # 初始化logger
    queue_handler = logging.handlers.QueueHandler(log_queue)
    formatter = logging.Formatter('[%(asctime)s] - [%(name)s] - [%(levelname)s] - %(message)s')
    file_handler = logging.FileHandler('app.log')
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger = logging.getLogger('app_logger')
    logger.setLevel(logging.INFO)
    logger.addHandler(queue_handler)
    listener = logging.handlers.QueueListener(log_queue, *[console_handler, file_handler])
    # 开启logger监听
    listener.start()

    # 打印app配置信息
    logger.debug(f'App config:\n{json.dumps(config, indent=4)}')

    # 初始化socket服务器
    server = SocketServer(config['socket'])

    # 初始化子进程
    detect_processing = multiprocessing.Process(target=detect,
                                                args=(lock, config, shape, freq,
                                                      detect_msg_queue,
                                                      shared_frame_array,
                                                      socket_queue, error_queue))
    capture_processing = multiprocessing.Process(target=capture,
                                                args=(lock, config, shape, 
                                                      cap_msg_queue,
                                                      shared_frame_array,
                                                      error_queue))
    # 初始化子线程
    send_threading = threading.Thread(target=send, daemon=True)
    receive_threading = threading.Thread(target=receive, daemon=True)

    # 设置为守护进程，在主进程退出后子进程自动退出
    detect_processing.daemon = True
    capture_processing.daemon = True
    # 开启进程
    detect_processing.start()
    capture_processing.start()

    # 等待客户端连接
    server.start()

    # 开启主进程的子线程
    send_threading.start()
    receive_threading.start()

    # 同一进行异常处理
    while True:
        error = error_queue.get()
        if error[0] == 'send' or error[0] == 'receive':
            sys.exit(-1)
        if error[0] == 'capture':
            logger.error('failed in capture processing, suspend detect processing.')
            # TODO 将异常消息加入socket_queue中
            # 暂停检测进程
            detect_msg_queue.put("suspend")
            capture_processing.join()
            # 尝试重新启动摄像头进程
            capture_processing = multiprocessing.Process(target=capture,
                                                         args=(lock, config, shape, 
                                                               cap_msg_queue,
                                                               shared_frame_array,
                                                               error_queue))
            logger.info('try to restart capture processing...')
            capture_processing.start()
        elif error[0] == 'detect':
            logger.error('failed in detect processing, suspend capture processing.')
            # TODO 将异常消息加入socket_queue中
            # 暂停摄像头进程
            cap_msg_queue.put("suspend")
            detect_processing.join()
            detect_processing = multiprocessing.Process(target=detect,
                                                        args=(lock, config, shape, freq,
                                                                detect_msg_queue,
                                                                shared_frame_array,
                                                                socket_queue, error_queue))
            logger.info('try to restart detect processing...')
            detect_processing.start()
