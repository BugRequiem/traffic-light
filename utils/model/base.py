import tensorrt as trt
from torch2trt import TRTModule
import numpy as np
import torch
from abc import ABC, abstractmethod


class ModelBase(ABC):
    
    def __init__(self, modelcfg):
        path = modelcfg["mpath"]
        input_name = modelcfg["input"]
        output_name = modelcfg["output"]
        logger = trt.Logger(trt.Logger.INFO)
        with open(path, "rb") as f, trt.Runtime(logger) as runtime:
            engine=runtime.deserialize_cuda_engine(f.read())
        self.model = TRTModule(engine, input_names=[input_name], output_names=[output_name])
        self.imgsz = (modelcfg["imgsz"], modelcfg["imgsz"])
    
    def __call__(self, *args, **kwargs):
        return self.predict(kwargs['frame'])

    @abstractmethod
    def preprocess(self, frame):
        pass
        

    def inference(self, image):
        img_input = image.astype(np.float16)
        img_input = torch.from_numpy(img_input)
        img_input = img_input.to(0)             # to GPU0
        output = self.model(img_input)
        return output
        

    @abstractmethod
    def postprocess(self, output):
        pass

    def predict(self, frame):
        image = self.preprocess(frame)
        output = self.inference(image)
        result = self.postprocess(output)
        return result
