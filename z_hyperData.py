import spectral, cv2
import numpy as np
from spectral import settings


class HyperData:
    def __init__(self):
        settings.envi_support_nonlowercase_params = True
    
    def read_hdr_file(self, hdr_path):
        """
        读取高光谱hdr文件
        :param hdr_path: hdr文件路径
        :return: 高光谱数据立方体 (numpy数组)
        """
        try:
            # 使用spectral库读取hdr文件
            img = spectral.open_image(hdr_path).load()
            
            # 将数据立方体转换为RGB图像
            rgb_image = spectral.get_rgb(img, (29, 19, 9))  # 使用常见的波段组合
            # 将浮点型数据转换为8位整型
            rgb_image = (rgb_image * 255).astype(np.uint8)
            
            return img, rgb_image, np.array(img.bands.centers)
        except Exception as e:
            print(f"读取hdr文件失败: {str(e)}")
            return None, None, None
    
    def extract_band(self, data_cube, mask_mat):
        mask_array = np.array(mask_mat) > 0 
        masked_data = data_cube[mask_array, :]
        
        # 计算平均光谱、最大值光谱、最小值光谱
        average_spectrum = masked_data.mean(axis=0)
        max_spectrum = masked_data.max(axis=0)
        min_spectrum = masked_data.min(axis=0)
        
        return average_spectrum, max_spectrum, min_spectrum


if __name__ == '__main__':
    hdr_path = r'D:\00-dataset\高光谱\号角酥（生熟左边两个）.hdr'
    hyper_data = HyperData()
    data_cube, rgb_data, _ = hyper_data.read_hdr_file(hdr_path)  # 添加第三个返回值
    mask_data = cv2.imread('mask.png', cv2.IMREAD_GRAYSCALE)
    a, _, _ = hyper_data.extract_band(data_cube, mask_data)
    print(a)