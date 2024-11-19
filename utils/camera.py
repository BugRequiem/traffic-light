import cv2
import logging


class GstreamerCamera:

    def __init__(self, cameracfg):
        self.mode = cameracfg['mode']
        self.device = cameracfg['device']
        self.width = cameracfg['width']
        self.height = cameracfg['height']
        self.framerate = cameracfg['framerate']
        self.pformat = cameracfg['pformat']
        self.logger = logging.getLogger('app_logger')
        self.cap = None
        self.initcap()
        if self.cap is None or not self.cap.isOpened():
            # self.logger.error('open camera failed.')
            raise RuntimeError('Open camera failed! Check your camera param.')
    
    def initcap(self):
        if self.mode == 'camera':
            if self.pformat == 'MJPG':
                self.gstreamer_pipeline = (
                    f"v4l2src device={self.device} ! "
                    f"image/jpeg, width={self.width}, height={self.height}, framerate={self.framerate}/1 ! "
                    "jpegdec ! "                        # 解码
                    "videoconvert ! "                   # 格式转换
                    "videoflip method=rotate-180 ! "    # 反转图像
                    "appsink"                           # 发送给应用程序
                )
            elif self.pformat == 'YUYV':
                self.gstreamer_pipeline = (
                    f"v4l2src device=/dev/video0 ! "
                    f"video/x-raw, format=YUY2, width={self.width}, height={self.height}, framerate={self.framerate}/1 ! "
                    "videoconvert ! "
                    "appsink"
                )
        elif self.mode == 'video':
            self.gstreamer_pipeline = (
                f"filesrc location={self.device} ! "
                "qtdemux ! "
                "h264parse ! "
                "omxh264dec ! "
                "nvvidconv ! "
                "video/x-raw, format=(string)BGRx ! "
                "videoconvert ! "
                "video/x-raw, format=(string)BGR ! "
                "appsink")
        self.cap = cv2.VideoCapture(self.gstreamer_pipeline, cv2.CAP_GSTREAMER)
    
    def read(self):
        ret, frame = self.cap.read()
        if not ret:
            # self.logger.error('read camera failed.')
            raise RuntimeError('Read camera failed.')
        return frame

    def close(self):
        if self.cap.isOpened():
            self.cap.release()
            self.cap = None
