import sys, os


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
        #sam 配置
        checkpoint = r"D:\\python\\sam2_label\\checkpoints\\sam2.1_hiera_base_plus.pt"
        model_cfg  = r"D:\\python\\sam2_label\\sam2\\configs\\sam2.1\\sam2.1_hiera_b+.yaml"
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

        # 创建一个竖直空白占用伸缩杆
        stretch_spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        right_layout.addItem(stretch_spacer)
        
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
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
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
        pixmap = QPixmap(item_name)
        print(item_name)        
        self.imgviewer.display_image(pixmap)
        self.item_index = item_index
        self.cur_image_path = item_name


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
        image = Image.open(image_path)
        contours = self.samprocessor.detect(image, result,labels, self.close_ratio.value(), self.area_ratio.value(), self.filter_area.value())
        self.imgviewer.display_edge(contours)

    
    def on_clear_flag(self):
        self.imgviewer.clear_flag()
    
           
if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = Window()
    main_window.show()
    main_window.original_stdout = sys.stdout
    sys.stdout = main_window
    sys.exit(app.exec_())