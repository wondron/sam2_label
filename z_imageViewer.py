from PyQt5.QtWidgets import QLabel, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsRectItem
from PyQt5.QtGui import QPainter, QMouseEvent, QWheelEvent, QPixmap, QPen
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtWidgets import QApplication
import sys


style_sheet = """
            background-color: rgba(240, 240, 240, 0.8);
            border: 1px solid #ccc;
            border-radius: 5px;
            padding: 5px;
            font-family: Arial, sans-serif;
            font-size: 12px;
            color: #116f11;
            text-align: center;
            font-weight: bold;
        """


class ImageViewer(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.scaleFactor = 1.15
        self.pixmap_item = None
        
        #矩形使能
        self.rect_enable = True
        self.rect_item = None
        self.rect_info = None
        self.start_pos = None
        self.end_pos = None
        
        #点集使能
        self.pts_enable = False
        self.positive_pts = []
        self.negetive_pts = []
        self.circleItems = []
        
        #位置label
        self.dragging = False
        self.position_label = QLabel()
        self.position_label.setStyleSheet("background-color: white;")
        self.position_label.setFixedWidth(100)
        self.position_label.setFixedHeight(25)
        self.position_label.setStyleSheet(style_sheet)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.position_label.setParent(self)
        self.position_label.move(10, int(self.height() - self.position_label.height() * 1.5))
        self.position_label.show()
        
    def get_label_pts(self):
        return self.positive_pts, self.negetive_pts
        
    def set_sam_mode(self, enable):
        self.rect_enable = not enable
        self.pts_enable = enable    
        
    def set_rect_mode(self, enable):
        self.rect_enable = enable
        self.pts_enable = not enable
                
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.position_label.move(10, int(self.height() - self.position_label.height() * 1.5))
        
    def display_image(self, pixmap):
        if self.rect_item:
            self.scene.removeItem(self.rect_item)
        self.rect_item = None
        self.rect_info = None
        self.scene.clear()
        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.pixmap_item)
        self.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)
        # 添加红框
        self.add_red_border()

    def wheelEvent(self, event: QWheelEvent):
        if event.angleDelta().y() > 0:
            self.scale(self.scaleFactor, self.scaleFactor)
        else:
            self.scale(1 / self.scaleFactor, 1 / self.scaleFactor)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.start_pos = None
            #矩形绘图
            if self.rect_enable:
                self.start_pos = self.mapToScene(event.pos())
                if(self.start_pos.x() < 0):
                    self.start_pos.setX(0)

                if(self.start_pos.y() < 0):
                    self.start_pos.setY(0)

                if self.rect_item:
                    self.scene.removeItem(self.rect_item)
                self.rect_item = QGraphicsRectItem()
                self.rect_item.setPen(Qt.red)
                self.scene.addItem(self.rect_item)
                
        elif event.button() == Qt.MiddleButton:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            self.dragging = True
            self.origin = event.pos()
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event: QMouseEvent):
        #绘制矩形
        if self.start_pos:
            self.end_pos = self.mapToScene(event.pos())

            if(self.end_pos.x() > self.pixmap_item.boundingRect().width()):
                self.end_pos.setX(self.pixmap_item.boundingRect().width())
            
            if(self.end_pos.y() > self.pixmap_item.boundingRect().height()):
                self.end_pos.setY(self.pixmap_item.boundingRect().height())

            sub_pos = self.end_pos - self.start_pos
            if((sub_pos.x() < 0) or (sub_pos.y() < 0)):
                if self.rect_item is not None:
                    self.scene.removeItem(self.rect_item)
                    self.rect_item = None

                return

            self.rect_info = QRectF(self.start_pos, self.end_pos)
            if not self.rect_item:
                self.rect_item = QGraphicsRectItem()
                self.rect_item.setPen(Qt.red)
                self.scene.addItem(self.rect_item)

            self.rect_item.setRect(self.rect_info)
        
        #图像拖动
        if self.dragging:
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - (event.x() - self.origin.x()))
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - (event.y() - self.origin.y()))
            self.origin = event.pos()
            
        # 更新鼠标位置信息
        scene_pos = self.mapToScene(event.pos())
        self.position_label.setText(f"X: {int(scene_pos.x())}, Y: {int(scene_pos.y())}")

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            # return
            self.start_pos = None
            self.end_pos = None
        
        if event.button() == Qt.MiddleButton:
            self.setDragMode(QGraphicsView.NoDrag)
            self.dragging = False
            self.unsetCursor()

        if event.button() == Qt.LeftButton and self.pts_enable:
            scene_pos = self.mapToScene(event.pos())
            self.positive_pts.append(QPointF(scene_pos.x(), scene_pos.y()))
            circleItem = QGraphicsEllipseItem(scene_pos.x(), scene_pos.y(), 5, 5)
            pen = QPen(Qt.green, 2)
            circleItem.setPen(pen)
            self.scene.addItem(circleItem)

        if event.button() == Qt.RightButton and self.pts_enable:
            scene_pos = self.mapToScene(event.pos())
            self.negetive_pts.append(QPointF(scene_pos.x(), scene_pos.y()))
            circleItem = QGraphicsEllipseItem(scene_pos.x(), scene_pos.y(), 5, 5)
            pen = QPen(Qt.red, 2)
            circleItem.setPen(pen)
            self.scene.addItem(circleItem)

    def add_red_border(self):
        if self.pixmap_item:
            rect = self.pixmap_item.boundingRect()
            border_rect = QGraphicsRectItem(rect)
            border_rect.setPen(Qt.black)
            self.scene.addItem(border_rect)

    def get_label_rect(self):
        img_size = []
        if self.rect_info is not None:
            img_size.append(int(self.rect_info.left()))
            img_size.append(int(self.rect_info.top()))
            img_size.append(int(self.rect_info.right()))
            img_size.append(int(self.rect_info.bottom()))
        
        return img_size
    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageViewer()
    window.set_sam_mode(True)
    image_path = r".\model\test.jpg"
    pixmap = QPixmap(image_path)
    if pixmap.isNull():
        print(f"无法加载图像: {image_path}")
    else:
        window.display_image(pixmap)
        window.show()
    sys.exit(app.exec_())