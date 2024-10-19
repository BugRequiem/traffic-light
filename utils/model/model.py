from utils.model.base import ModelBase
import numpy as np
import cv2
import torchvision.transforms as transforms
import json
from ultralytics import YOLOv10
import torch


class Model(ModelBase):

    def  __init__(self, modelcfg):
        super().__init__(modelcfg)
        with open('class_config.json', 'r', encoding='utf-8') as file:
            self.classcfg = json.load(file)
        self.load()
        print(f'class config:\n{json.dumps(self.classcfg, indent=4)}')
        print("-----------------------------------------------------------------")

    def load(self):
        self.model = YOLOv10(self.path, task='detect')
        # 提前载入模型到内存
        self.model(torch.zeros((1, 3, 640, 640)))

    def preprocess(self, frame):
        # image = cv2.resize(frame, self.imgsz)   # to (640, 640, 3)
        # image = image.transpose(2, 0, 1)        # to (3, 640, 640)
        # image = np.expand_dims(image, axis=0)   # to (1, 3, 640, 640)
        return frame

    def inference(self, image):
        return self.model(image, save=False, conf=self.conf, imgsz=self.imgsz)
    
    def postprocess(self, output):
        classes = self.classcfg['class']
        for i in output:
            box = i.boxes.xyxy.tolist()
            conf = i.boxes.conf.cpu().tolist()     
            obj_num = len(box)
            cls = i.boxes.cls.tolist()
            result = []
            for j in range(obj_num):
                result.append([classes[str(int(cls[j]))], box[j][0],box[j][1], box[j][2], box[j][3], conf[j]])    
        result = {
        'datas': [{
            'label': result[i][0],
            'confidence' : result[i][5],
            'location': [result[i][1], result[i][2], result[i][3], result[i][4]]               
        }
        for i in range(0,len(result))
        ]}
        # json_result = json.dumps(result)
        return result