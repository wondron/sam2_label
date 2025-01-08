import sys, os

import pyqtgraph as pg  # 添加这行导入
from z_hyperData import HyperData
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QTextEdit,QLineEdit, QComboBox, QSpinBox
from PyQt5.QtWidgets import QHBoxLayout, QFileDialog, QSizePolicy, QSplitter, QSpacerItem, QTableWidgetItem, QMessageBox
from PyQt5.QtGui import QPixmap, QImage, QTextCursor
from PyQt5.QtCore import pyqtSignal, QThread, QUrl, QByteArray, Qt
from z_imageViewer import ImageViewer
from z_showfileTol import FileReview
import numpy as np
from z_samTool import SAM2ImageProcessor
import cv2
from PIL import Image

qLineEditStyle = """
            QLineEdit {
                border: 2px solid #8F8F91;
                border-radius: 5px;
                padding: 2px;
                background: white;
                selection-background-color: darkgray;
            }
        """
      
class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()   
        self.image_paths = dict()
        self.hyperData = HyperData()
        #sam 配置
        checkpoint = r"D:\01-code\00-python\sam2_label\checkpoints\sam2.1_hiera_base_plus.pt"
        model_cfg  = r"D:\01-code\00-python\sam2_label\sam2\configs\sam2.1\sam2.1_hiera_b+.yaml"
        self.samprocessor = SAM2ImageProcessor(checkpoint, model_cfg)

    def initUI(self):
        self.setWindowTitle('食材标注软件')
        self.posipts = []
        self.negepts = []
        # 创建一个水平分割器
        self.initUILeft()
        self.initUIMidl()
        self.initUIRigt()

        # 将三个窗口添加到分割器中
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.left_widget)
        splitter.addWidget(self.midl_widget)
        splitter.addWidget(self.rigt_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 1)

        # 将分割器添加到主窗口的布局中
        main_layout = QVBoxLayout()
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)
        
    def initUILeft(self):
        # 创建左边的窗口
        self.left_widget = QWidget()
        left_layout = QVBoxLayout()
        self.left_widget.setLayout(left_layout)

        # 在左边窗口中添加竖直排列的label
        self.fileViewer = FileReview()
        self.fileViewer.itemClicked.connect(self.on_image_clicked)
        left_layout.addWidget(self.fileViewer)
        left_layout.setStretch(0, 2)
            
        self.logger = QTextEdit()
        left_layout.addWidget(self.logger)
        left_layout.setStretch(1, 1)
            
    def initUIMidl(self):
        # 创建中间的窗口
        self.midl_widget = QWidget()
        middle_layout = QVBoxLayout()
        self.midl_widget.setLayout(middle_layout)

        # 在中间窗口中添加一个QTextEdit        
        label_layout = QHBoxLayout()
        lbl_remote_path = QLabel("文件路径")
        label_layout.addWidget(lbl_remote_path)
        self.edit_remote_path = QLineEdit("D:/00-dataset/1106/鲫鱼--")
        label_layout.addWidget(self.edit_remote_path)
        self.btn_get_imagefiles = QPushButton("文件路径")
        self.btn_get_imagefiles.clicked.connect(self.on_btn_filePath_select)
        label_layout.addWidget(self.btn_get_imagefiles)
        middle_layout.addLayout(label_layout)
        
        self.imgviewer = ImageViewer()
        self.imgviewer.set_sam_mode(True)
        middle_layout.addWidget(self.imgviewer)
         
    def initUIRigt(self):
        # 创建右边的窗口
        self.rigt_widget = QWidget()
        right_layout = QVBoxLayout()
        self.rigt_widget.setLayout(right_layout)
        
        self.btn_clear = QPushButton("清空标记")
        self.btn_clear.clicked.connect(self.on_clear_flag)
        right_layout.addWidget(self.btn_clear)

        self.btn_sam_label = QPushButton("标注")
        self.btn_sam_label.clicked.connect(self.on_btn_sam_label)
        right_layout.addWidget(self.btn_sam_label)

        hLayout = QHBoxLayout()
        hLayout.addWidget(QLabel("闭运算比值"))
        self.close_ratio = QSpinBox()
        self.close_ratio.setMaximum(9999)
        self.close_ratio.setValue(100)  # 初始化值为10
        hLayout.addWidget(self.close_ratio)
        right_layout.addLayout(hLayout)

        hlayout_1 = QHBoxLayout()
        hlayout_1.addWidget(QLabel("填充比值"))
        self.area_ratio = QSpinBox()
        self.area_ratio.setMaximum(9999)
        self.area_ratio.setValue(10)  # 初始化值为10
        hlayout_1.addWidget(self.area_ratio)
        right_layout.addLayout(hlayout_1)

        hlayout_2 = QHBoxLayout()
        hlayout_2.addWidget(QLabel("小面积去除值"))
        self.filter_area = QSpinBox()
        self.filter_area.setMaximum(9999)
        self.filter_area.setValue(300)  # 初始化值为10
        hlayout_2.addWidget(self.filter_area)
        right_layout.addLayout(hlayout_2)

        self.btn_relabel = QPushButton("使用上次标记点")
        self.btn_relabel.clicked.connect(self.on_btn_relabel_clicked)
        right_layout.addWidget(self.btn_relabel)

        self.btn_extract = QPushButton("提取光谱")
        self.btn_extract.clicked.connect(self.on_btn_extract_clicked)
        right_layout.addWidget(self.btn_extract)
        
        # 创建光谱曲线显示控件并进行优化配置
        self.spectrum_plot = pg.PlotWidget(
            title='光谱曲线',
            labels={'left': '反射率', 'bottom': '波长 (nm)'},
            background='w',
            axisItems={'bottom': pg.AxisItem(orientation='bottom', pen='k')}
        )
        
        # 设置网格样式
        self.spectrum_plot.showGrid(x=True, y=True, alpha=0.3)
        
        # 设置坐标轴样式
        self.spectrum_plot.getAxis('left').setPen(color='k', width=1)
        self.spectrum_plot.getAxis('bottom').setPen(color='k', width=1)
        
        # 设置边距
        self.spectrum_plot.setContentsMargins(10, 10, 10, 10)
        
        # 添加到布局
        right_layout.addWidget(self.spectrum_plot)

        # 初始化曲线数据
        self.spectrum_curve = self.spectrum_plot.plot(pen=pg.mkPen(color='b', width=2))
        
        # 创建一个竖直空白占用伸缩杆
        # stretch_spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        # right_layout.addItem(stretch_spacer)
        self.save_spectrum = QPushButton("保存光谱信息")
        self.save_spectrum.clicked.connect(self.on_btn_save_spectrum_clicked)
        right_layout.addWidget(self.save_spectrum)
        
    def write(self, text):
        cursor = self.logger.textCursor()
        cursor.insertText(text)
        self.logger.moveCursor(QTextCursor.End)
        
    def on_btn_filePath_select(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        directory = self.edit_remote_path.text()
        folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹", directory = directory, options=options)
        if folder_path == "":
            return
        
        self.edit_remote_path.setText(folder_path)
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.hdr']
        self.image_paths.clear()
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if any(file.lower().endswith(ext) for ext in image_extensions):
                    filename = os.path.basename(file).split('.')[0]
                    self.image_paths[filename] = os.path.join(root, file)
        
        self.fileViewer.update_list(self.image_paths)     
        
    def on_btn_relabel_clicked(self):
        self.imgviewer.set_label_pts(self.posipts, self.negepts)

    def on_image_clicked(self, item_name, item_index):
        self.mask_mat = None
        self.mean_spectrum = None
        self.min_sepctrum = None
        self.max_spectrum = None
        if item_name.endswith('.hdr'):
            self.data_cube, self.rgb_image, self.hyper_sprectrumList = self.hyperData.read_hdr_file(item_name)
            # 将numpy数组转换为QPixmap
            height, width, channel = self.rgb_image.shape
            bytes_per_line = 3 * width
            qimage = QImage(self.rgb_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimage)
        else:
            self.data_cube = None
            self.rgb_image = None
            self.hyper_sprectrumList = None
            pixmap = QPixmap(item_name)
            
        print(item_name)        
        self.imgviewer.display_image(pixmap)
        self.item_index = item_index
        self.cur_image_path = item_name
        
    def on_btn_save_spectrum_clicked(self):
        if self.min_sepctrum is None:
            QMessageBox.warning(self, "警告", "请先进行光谱提取操作！")
            return
        
        # 保存光谱数据到CSV文件
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        
        base_name = os.path.basename(self.cur_image_path).split('.')[0]
        
        file_path, _ = QFileDialog.getSaveFileName(self, "保存光谱数据", base_name, "CSV Files (*.csv);;All Files (*)", options=options)
        
        if file_path:
            try:
                # 确保文件以.csv结尾
                if not file_path.lower().endswith('.csv'):
                    file_path += '.csv'
                
                # 将数据组合成二维数组
                data = np.vstack((self.hyper_sprectrumList, 
                                self.mean_spectrum,
                                self.min_sepctrum,
                                self.max_sepctrum))
                
                # 转置数据以便每列代表一个变量
                data = data.T
                
                # 添加表头
                header = "波长(nm),平均光谱,最小光谱,最大光谱"
                
                # 保存到CSV文件
                np.savetxt(file_path, data, delimiter=',', header=header, comments='', fmt='%.4f')
                
                QMessageBox.information(self, "保存成功", f"光谱数据已成功保存到：\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "保存失败", f"保存光谱数据时出错：\n{str(e)}")
        
        

    def on_btn_sam_label(self):
        posipts, negepts = self.imgviewer.get_label_pts()
            
        # 防呆处理：如果只有负样本点，提示用户
        if posipts.size == 0:
            QMessageBox.warning(self, "警告", "请至少标注一个正样本点！")
            return
        
        self.posipts = posipts
        self.negepts = negepts
        
        # 正常处理
        aaa = np.ones(posipts.shape[0])
        if len(negepts) > 0:
            result = np.vstack((posipts, negepts))
            bbb = np.ones(negepts.shape[0]) * -1
            labels = np.hstack((aaa, bbb))
        else:
            result = posipts
            labels = aaa

        image_path = list(self.image_paths.values())[self.item_index]
        # 将RGB图像转换为PIL Image格式
        if self.rgb_image is not None:
            image = Image.fromarray(self.rgb_image)
        else:
            image = Image.open(image_path)
        
        contours, self.mask_mat = self.samprocessor.detect(image, result,labels, self.close_ratio.value(), self.area_ratio.value(), self.filter_area.value())
        self.imgviewer.display_edge(contours)

    def on_clear_flag(self):
        self.imgviewer.clear_flag()
    
    def on_btn_extract_clicked(self):
        if self.hyperData is None or self.mask_mat is None:
            QMessageBox.warning(self, "警告", "未生成蒙版！")
            return
        self.mean_spectrum, self.min_sepctrum, self.max_sepctrum = self.hyperData.extract_band(self.data_cube, self.mask_mat)
        # 检查光谱数据是否存在
        if self.hyper_sprectrumList is None:
            QMessageBox.warning(self, "警告", "未加载光谱数据！")
            return
            
        # 清空之前的曲线
        self.spectrum_plot.clear()
        # 绘制平均光谱曲线
        self.spectrum_plot.plot(self.hyper_sprectrumList, self.mean_spectrum, pen='r', name='平均光谱')
        # 绘制最大光谱曲线
        self.spectrum_plot.plot(self.hyper_sprectrumList, self.max_sepctrum, pen='g', name='最大光谱')
        # 绘制最小光谱曲线
        self.spectrum_plot.plot(self.hyper_sprectrumList, self.min_sepctrum, pen='b', name='最小光谱')
        # 设置图表标题和标签
        self.spectrum_plot.addLegend()
    
    
           
if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = Window()
    main_window.resize(1200, 800)  # 设置初始窗口大小为1200x800像素
    main_window.show()
    main_window.original_stdout = sys.stdout
    sys.stdout = main_window
    sys.exit(app.exec_())