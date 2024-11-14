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

### 查看摄像头

## 启动服务器

### 更改配置文件config.json

```json
{
    "socket": {
        "host" : "192.168.20.120",      // ip地址
        "port" : 12345                  // 端口号
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
    }
}
```

### 启动app.py

```shell
cd ~/workspace/traffic-light        # 进入项目目录
conda activate TensorRT             # 激活conda环境
python app.py                       # 启动app
```

### 简要测试socket接口

- 使用client.py测试socket接口，需要更改client.py中的`IP`和`PORT`与服务器相同
    ```shell
    python client.py
    ```

