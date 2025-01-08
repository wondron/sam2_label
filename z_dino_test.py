import requests, json, yaml, cv2
import numpy as np

class DinoDetector:
    def __init__(self, config_path):
        self.load_config(config_path)


    def load_config(self, config_path):
        with open(config_path, 'r', encoding='utf-8') as yaml_file:
            config = yaml.safe_load(yaml_file)
        
        if config is None:
            return None, None, None
        
        self.url = config['DINO_SERVER']['api_url']
        self.box_thre = config['DINO_SERVER']['box_thre']
        self.text_thre = config['DINO_SERVER']['text_thre']
        self.roi_scale = config['DINO_SERVER']['ROI_Scale']
        self.filter_scale = config['DINO_SERVER']['filter_Scale']
        print(f"Dino param:\n\turl:{self.url}\n\tbox_thre: {self.box_thre}\n\ttext_thre: {self.text_thre}")
        print("Dino init done!")


    def str2numpy(self, data_str):
        data_str_cleaned = data_str.replace('[', '').replace(']', '')
        data_array = np.fromstring(data_str_cleaned, sep=' ').reshape(-1, 4)
        return data_array


    def split_image(self, image_data, discri, response):
        boxes = self.str2numpy(response["boxes"])
        labels = response['phrases']
        print(labels)
        image_cv = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)
        h, w, _ = image_cv.shape
        
        # 提取labels中和discri相同字符串的序号
        matching_indices = [i for i, label in enumerate(labels) if discri in label]
        
        # 缩放并筛选匹配的boxes
        matching_boxes = boxes[matching_indices] * [w, h, w, h]
        
        # 计算缩放后的矩形区域
        cx, cy = matching_boxes[:, 0], matching_boxes[:, 1]
        width = matching_boxes[:, 2] * self.roi_scale
        height = matching_boxes[:, 3] * self.roi_scale
        x1 = np.clip((cx - width/2).astype(int), 0, w)
        y1 = np.clip((cy - height/2).astype(int), 0, h)
        x2 = np.clip((cx + width/2).astype(int), 0, w)
        y2 = np.clip((cy + height/2).astype(int), 0, h)
        
        # 创建二值图像并绘制矩形
        binary_image = np.zeros((h, w), dtype=np.uint8)
        for (x1, y1, x2, y2) in zip(x1, y1, x2, y2):
            binary_image[y1:y2, x1:x2] = 1
            
        # 获取轮廓并计算最小外接矩形
        contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        min_rectangles = [cv2.boundingRect(cnt) for cnt in contours]
        
        # 找到最大面积的矩形
        max_rect = max(min_rectangles, key=lambda r: r[2]*r[3])
        max_area = max_rect[2] * max_rect[3]
        
        # 过滤面积大于最大面积/scale的矩形
        filter_area = max_area / self.filter_scale
        class_rect = [rect for rect in min_rectangles if rect[2]*rect[3] >= filter_area]
        
        # 裁剪图像
        cropped_images = [image_cv[y:y+h, x:x+w] for x, y, w, h in class_rect]
        
        return cropped_images, class_rect
        

    def detect(self, image_data, discri):
        if image_data is None:
            return None
        
        files = {"image": ("test_image.jpg", image_data, "image/jpeg")}
        data = {
            "discri": discri, 
            "box_thre": str(self.box_thre), 
            "text_thre": str(self.text_thre),
        }
        
        response = requests.post(self.url, files=files, data=data)
        if response.status_code != 200:
            print(f"error, Failed to call service: {response.status_code}")
            return None, []
        crop_images, min_rectangle = self.split_image(image_data, discri, response.json())
        return crop_images, min_rectangle
    
    
if __name__ == "__main__":
    image_path = r"D:\00-dataset\鲍鱼\300_201112150815130.png"
    try:
        image_data = open(image_path, "rb").read()
    except:
        print("Failed to open image")
        image_data = None
    discri = "food"
    detector = DinoDetector('config/config.yaml')
    images, rects = detector.detect(image_data, discri)
    print(rects)