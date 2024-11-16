import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QListWidget, QListWidgetItem
from PyQt5.QtWidgets import QToolButton, QSizePolicy, QSplitter
from PyQt5.QtCore import pyqtSignal, Qt


class FileReview(QWidget):
    # 定义一个信号，用于传递点击的项名称
    itemClicked = pyqtSignal(str, int)

    def __init__(self, title="Collapsible List", parent=None):
        super(FileReview, self).__init__(parent)
        self.setWindowTitle("Collapsible List Example")
        
        # 垂直布局
        self.layout = QVBoxLayout(self)
        
        # 创建折叠按钮
        self.toggle_button = QToolButton(text=title)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(True)
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toggle_button.setArrowType(Qt.DownArrow)
        self.toggle_button.clicked.connect(self.on_toggle)

        # 创建列表控件
        self.list_widget = QListWidget()
        self.list_widget.setFrameShape(QListWidget.NoFrame)
        self.list_widget.setStyleSheet("background-color: transparent;")
        
        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.setFrameShape(QListWidget.NoFrame)
        self.splitter.setStyleSheet("background-color: transparent;")
        
        # 添加到布局中
        self.layout.addWidget(self.toggle_button)
        self.layout.addWidget(self.list_widget)
        self.layout.addWidget(self.splitter)
        
        # 调整布局填充和间隙
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # 设置展开/折叠按钮大小策略
        self.toggle_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # 连接列表项的点击事件
        self.list_widget.itemClicked.connect(self.on_item_clicked)
                
    def setCurrentIndex(self, index):
        if len(self.items.keys()) <= index and index < 0:
            return
        slct_item = self.list_widget.item(index)
        self.list_widget.setCurrentItem(slct_item)
        self.itemClicked.emit(self.items[slct_item.text()], index)

    def on_toggle(self):
        """
        当用户点击按钮时，切换列表的显示/隐藏状态。
        """
        if self.toggle_button.isChecked():
            self.list_widget.show()
            self.toggle_button.setArrowType(Qt.DownArrow)
        else:
            self.list_widget.hide()
            self.toggle_button.setArrowType(Qt.RightArrow)

    def update_list(self, items):
        """
        更新列表中的项。
        :param items: 列表，包含要显示的项名称。
        """
        self.list_widget.clear()
        self.items = items
        
        for key, val in items.items():
            QListWidgetItem(key, self.list_widget)
            
        if len(list(items.keys())):
            first_item = self.list_widget.item(0)
            self.list_widget.setCurrentItem(first_item)
            self.on_item_clicked(first_item)

    def on_item_clicked(self, item):
        item_index = self.list_widget.row(item)
        self.itemClicked.emit(self.items[item.text()], item_index)

class MainWindow(QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle("Collapsible List Demo")
        self.setGeometry(300, 100, 300, 400)

        # 创建一个主布局
        layout = QVBoxLayout(self)
        # 创建可折叠列表控件
        self.collapsible_list = FileReview("Items List")
        self.collapsible_list.update_list({'1': '2','2': '2','3': '2','4': '2','5': '2','6': '2','7': '2'})

        # 将折叠列表添加到布局
        layout.addWidget(self.collapsible_list)
        # 连接信号到槽函数
        self.collapsible_list.itemClicked.connect(self.on_item_clicked)

    def on_item_clicked(self, item_name, item_index):
        """
        处理列表项点击事件。
        """
        print(f"Clicked on: {item_index}_{item_name}")

if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())
