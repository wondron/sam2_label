import torch, cv2
from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor
from PIL import Image
import numpy as np

class SAM2ImageProcessor:
    def __init__(self, checkpoint, model_cfg, device="cpu"):
        self.predictor = SAM2ImagePredictor(build_sam2(model_cfg, checkpoint, device=device))

    def process_image(self, image_path, point_coords, point_labels, multimask_output=False):
        image_data = Image.open(image_path)
        self.predictor.set_image(image_data)
        masks, _, _ = self.predictor.predict(
            point_coords=point_coords,
            point_labels=point_labels,
            multimask_output=multimask_output,
        )
        mask_image = Image.fromarray((masks[0] * 255).astype(np.uint8))
        mask_array = np.array(mask_image)

        # 使用opencv实现halcon的fill_up的作用
        # 首先将mask_array转换为二值图像
        _, binary_mask = cv2.threshold(mask_array, 127, 255, cv2.THRESH_BINARY)

        # 使用形态学操作填充孔洞
        kernel = np.ones((30, 30), np.uint8)
        filled_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel)

        # 获取filled_mask的边缘
        edges = cv2.Canny(filled_mask, 100, 200)
        
        return edges


    
if __name__ == "__main__":
    checkpoint = r"D:\01-code\00-python\sam2_label\checkpoints\sam2.1_hiera_base_plus.pt"
    model_cfg = r"D:\01-code\00-python\sam2_label\sam2\configs\sam2.1\sam2.1_hiera_b+.yaml"
    image_path = r'D:/00-dataset/1106/鲫鱼--/Baidu_0061.jpeg'
    processor = SAM2ImageProcessor(checkpoint, model_cfg)
    contours = processor.process_image(image_path, point_coords=[[200, 400]], point_labels=[1])
    
    print(contours)