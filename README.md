# Jetson Nano + YOLOv10交通信号灯识别

## 1. 摄像头配置

```shell
# 命令行下
# 修改摄像头参数
v4l2-ctl --device=/dev/video0 --set-fmt-video=width=1920,height=1080,pixelformat=MJPG
# 查看修改结果
v4l2-ctl --device=/dev/video0 --all
# 可以看到有如下参数信息
Video input : 0 (Camera 1: ok)
Format Video Capture:
        Width/Height      : 1920/1080
        Pixel Format      : 'MJPG'
        Field             : None
        Bytes per Line    : 0
        Size Image        : 4147789
        Colorspace        : sRGB
        Transfer Function : Default (maps to sRGB)
        YCbCr/HSV Encoding: Default (maps to ITU-R 601)
        Quantization      : Default (maps to Full Range)
        Flags             : 
Crop Capability Video Capture:
        Bounds      : Left 0, Top 0, Width 1920, Height 1080
        Default     : Left 0, Top 0, Width 1920, Height 1080
        Pixel Aspect: 1/1
```

## 2. 启动服务器

### 2.1 更改配置文件config.json

```json
{
    "socket": {
        "host" : "192.168.20.120",      // ip地址
        "port" : 12345,                 // 端口号
        "broadcast_port" : 37020        // 广播端口号
    },
    "camera": {
        "mode" : "camera",              // 为"camera"时调用摄像头，为"video"时使用本地视频测试
        "device" : "/dev/vedio0",       // 摄像头路径或视频路径
        "width" : 1920,                 // 摄像头宽度
        "height" : 1080,                // 摄像头高度
        "framerate" : 30,               // 摄像头帧率
        "pformat" : "MJPG"              // 摄像头采集图像格式，可用MJPG和YUYV格式，使用MJPG速度更快
    },
    "model": {
        "mpath" : "models/traffic_light.engine",
        "imgsz" : 640,                  // 模型输入大小
        "conf" : 0.5,                   // 置信度
        "save" : false,                 // 是否保存图片结果到"./save"文件夹下
        "input" : "images",             // 输入层名称，默认即可
        "output" : "output0"            // 输出层名称，默认即可
    },
    "debug": {
        "islog": true                   // 启用DEBUG打印
    },
    "app": {
        "freq": 1,                      // 识别（即结果发送）频率
        "python": "/home/dlinano/miniforge3/envs/TensorRT/bin/python",
        "restart_time": 10              // 重启app等待时间（second）
    }
}
```

### 2.2 启动app_multiprocessing.py

```shell
# 推荐使用多进程版本app_multiprocessing.py
cd ~/workspace/traffic-light        # 进入项目目录
conda activate TensorRT             # 激活conda环境
python app_multiprocessing.py       # 启动app
```

### 2.3 简要测试socket接口

- 使用client.py测试socket接口，需要更改client.py中的`IP`和`PORT`与服务器相同
    ```shell
    python client.py
    ```

### 2.4 日志文件

- app运行日志文件为`app.log`
- app所有输出日志文件为`app_start.log`

### 2.5 异常处理

- 当socket出现异常，将关闭程序并在10秒后尝试重新启动，客户端需要**重新连接**
- 当摄像头出现异常，将关闭摄像头进程并向客户端发送错误消息，且模型识别进程将**暂停**。程序会自动尝试重新启动摄像头进程，需要客户端重新发送启动检测消息。
- 当模型检测出现异常，将关闭检测进程并向客户端发送错误消息，摄像头进程仍然会**继续执行**。程序会自动尝试重新启动检测进程，需要客户端重新发送启动检测消息。

### 2.6 设置开机自启动

```shell
# 在项目目录下运行以下命令
./add_reboot_cron.sh
```
