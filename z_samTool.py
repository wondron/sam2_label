import torch, cv2, os
from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor
from PIL import Image
import numpy as np
from tqdm import tqdm

class SAM2ImageProcessor:
    def __init__(self, checkpoint, model_cfg, device="cpu"):
        self.predictor = SAM2ImagePredictor(build_sam2(model_cfg, checkpoint, device=device))

    def process_image(self, image_data, point_coords, point_labels):
        self.predictor.set_image(image_data)
        masks, _, _ = self.predictor.predict(
            point_coords=point_coords,
            point_labels=point_labels,
            multimask_output=False,
        )
        mask_array = masks[0]
        uint8_array = (mask_array * 255).astype(np.uint8)
        return uint8_array
    
    
    def process_image_box(self, image_data, box_list, white_ratio = 0.5):
        # 使用边界框进行预测
        self.predictor.set_image(image_data)
        masks, _, _ = self.predictor.predict(
            point_coords=None,
            point_labels=None,
            box=np.array(box_list),
            multimask_output=False,
        )
        
        # 处理mask结果
        uint8_array = (masks[0] * 255).astype(np.uint8)
        
        # 计算中心区域白色像素比例
        h, w = uint8_array.shape
        center = uint8_array[h//4:3*h//4, w//4:3*w//4]
        ratio = np.mean(center == 255)
        
        # 根据比例决定是否反转图像
        if ratio < white_ratio:
            uint8_array = 255 - uint8_array
            
        return uint8_array
    
    
    def get_used_show_image(self, ori_mat, mask_mat, close_ratio = 25, filter_ratio = 100):
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (mask_mat.shape[1]//close_ratio, mask_mat.shape[0]//close_ratio))  # 创建5x5椭圆结构元素
        opened_image = cv2.morphologyEx(mask_mat, cv2.MORPH_OPEN, kernel)  # 执行开运算

        filter_area = mask_mat.shape[0] * mask_mat.shape[1] // filter_ratio
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(opened_image, connectivity=8)
        for i in range(1, num_labels):
            if stats[i, cv2.CC_STAT_AREA] < filter_area:
                opened_image[labels == i] = 0       

        canny_border = cv2.Canny(opened_image, 100, 200)
        white_pixels = np.column_stack(np.where(canny_border == 255))
        drawed_image = cv2.cvtColor(ori_mat, cv2.COLOR_RGB2BGR)
        for i, (y, x) in enumerate(white_pixels):
            cv2.circle(drawed_image, (x, y), 2, (0, 255, 0), -1)
        
        return opened_image, drawed_image
    
    def get_smooth_image(self, input_mat, ratio = 100, area_ratio = 10, filter_area = 100):
        height, width = input_mat.shape
        kernel_size = (int(width/ratio), int(height/ratio))
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, kernel_size)
        filled_image = cv2.morphologyEx(input_mat, cv2.MORPH_CLOSE, kernel)

        # 去除面积小于500的连通域
        invert_image = cv2.bitwise_not(filled_image)
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(invert_image, connectivity=8)

        min_size = height * width * area_ratio / ratio / ratio
        for i in range(1, num_labels):
            if stats[i, cv2.CC_STAT_AREA] < min_size:
                invert_image[labels == i] = 0
                
        invert_image = cv2.bitwise_not(invert_image)

        # 去除面积小于filter_area的连通域
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(invert_image, connectivity=8)
        for i in range(1, num_labels):
            if stats[i, cv2.CC_STAT_AREA] < filter_area:
                invert_image[labels == i] = 0
            else:
                print(f"区域面积: {stats[i, cv2.CC_STAT_AREA]}")

        # 使用Canny算子获取边缘
        edges = cv2.Canny(invert_image, 100, 200)
        return edges, invert_image

    def detect(self, image_data, point_coords, point_labels, ratio = 100, area_ratio = 10, filter_area = 100):
        mask_mat = self.process_image(image_data, point_coords, point_labels)
        filled_mat, fill_mat = self.get_smooth_image(mask_mat, ratio, area_ratio, filter_area)
        return filled_mat, fill_mat

def get_image_paths(folder_path):
    """
    获取指定文件夹下所有图像文件路径
    :param folder_path: 文件夹路径
    :return: 图像文件路径列表
    """
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif']
    image_paths = []
    
    # 遍历文件夹
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # 检查文件扩展名
            if os.path.splitext(file)[1].lower() in image_extensions:
                image_paths.append(os.path.join(root, file))
    
    return image_paths


    
if __name__ == "__main__":
    checkpoint = "D:/01-code/00-python/sam2_label/checkpoints/sam2.1_hiera_base_plus.pt"
    model_cfg  = "D:/01-code/00-python/sam2_label/sam2/configs/sam2.1/sam2.1_hiera_b+.yaml"
    image_path = r'D:\00-dataset\1218\贝壳类\青口\200_0a74f112144d3d3e3860a8ac458b3674.jpg'
    image_data = Image.open(image_path)
    numpy_image = np.array(image_data)

    processor = SAM2ImageProcessor(checkpoint, model_cfg)
    
    image_paths = get_image_paths(r'D:\00-dataset\分类\02_葡萄\阳光玫瑰')
    for  path in tqdm(image_paths):
        try:
            basename = os.path.basename(path)
            image_data = Image.open(path)
            numpy_image = np.array(image_data)
            height, width = numpy_image.shape[:2]
            
            mask_mat = processor.process_image_box(image_data, [0, 0, width, height])
            mask_mat, show_mat = processor.get_used_show_image(numpy_image, mask_mat, 25, 100)
            save_path = 'save_image/' + basename
            cv2.imwrite(save_path, show_mat)
        except:
            print(path)