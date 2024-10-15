import cv2


class GstreamerCamera:

    def __init__(self, cameracfg):
        self.device = cameracfg['device']
        self.width = cameracfg['width']
        self.height = cameracfg['height']
        self.framerate = cameracfg['framerate']
        self.pformat = cameracfg['pformat']
        if self.pformat == 'MJPG':
            self.gstreamer_pipeline = (
                f"v4l2src device={self.device} ! "
                f"image/jpeg, width={self.width}, height={self.height}, framerate={self.framerate}/1 ! "
                "jpegdec ! "        # 解码
                "videoconvert ! "   # 格式转换
                "appsink"           # 发送给应用程序
            )
        elif self.pformat == 'YUYV':
            self.gstreamer_pipeline = (
                f"v4l2src device=/dev/video0 ! "
                f"video/x-raw, format=YUY2, width={self.width}, height={self.height}, framerate={self.framerate}/1 ! "
                "videoconvert ! "
                "appsink"
            )
        print(self.gstreamer_pipeline)
        self.cap = cv2.VideoCapture(self.gstreamer_pipeline, cv2.CAP_GSTREAMER)
        if not self.cap.isOpened():
            raise OSError('Open camera failed.')
    
    def read(self):
        ret, frame = self.cap.read()
        if not ret:
            raise OSError('Read camera failed.')
        return frame

    def close(self):
        if self.cap.isOpened():
            self.cap.release()
            self.cap = None
