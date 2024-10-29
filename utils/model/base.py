import tensorrt as trt
from torch2trt import TRTModule
import numpy as np
import torch
import cv2
from abc import ABC, abstractmethod


class ModelBase(ABC):
    
    def __init__(self, modelcfg):
        self.path = modelcfg["mpath"]
        self.input_name = modelcfg["input"]
        self.output_name = modelcfg["output"]
        self.model = None
        self.conf = modelcfg['conf']
        self.imgsz = modelcfg['imgsz']
        self.save = modelcfg['save']
    
    def __call__(self, *args, **kwargs):
        return self.predict(kwargs['frame'])

    @abstractmethod
    def load(self):
        # logger = trt.Logger(trt.Logger.INFO)
        # with open(path, "rb") as f, trt.Runtime(logger) as runtime:
        #     engine=runtime.deserialize_cuda_engine(f.read())
        # self.model = TRTModule(engine, input_names=[input_name], output_names=[output_name])
        # self.imgsz = (modelcfg["imgsz"], modelcfg["imgsz"])
        pass

    @abstractmethod
    def preprocess(self, frame):
        pass

    @abstractmethod
    def inference(self, image):
        # img_input = image.astype(np.float16)
        # img_input = torch.from_numpy(img_input)
        # img_input = img_input.to(0)             # to GPU0
        # output = self.model(img_input)
        # return output
        pass

    @abstractmethod
    def postprocess(self, output):
        pass

    def save(self, image, result):
        if image is None:
            print("empty image!")
            return
        height, width, channels = image.shape
        datas = result['datas']
        for data in datas:
            color = (0, 255, 0)
            if data['label'] == 'green':
                color = (0, 255, 0)
            elif data['label'] == 'red':
                color = (0, 0, 255)
            else:
                color = (0, 255, 255)
            start_point = (int(data['location'][0]), int(data['location'][1]))
            end_point = (int(data['location'][2]), int(data['location'][3]))
            thickness = 2
            cv2.rectangle(image, start_point, end_point, color, thickness)
        cv2.imwrite('./save/output.jpg', image)

    def predict(self, frame):
        image = self.preprocess(frame)
        output = self.inference(image)
        result = self.postprocess(output)
        if self.save:
            self.save(image, result)
        return result
