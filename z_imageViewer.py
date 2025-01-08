from PyQt5.QtWidgets import QLabel, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsRectItem, QGraphicsPathItem
from PyQt5.QtGui import QPainter, QMouseEvent, QWheelEvent, QPixmap, QPen, QRadialGradient, QPainterPath
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtWidgets import QApplication
import sys, cv2
import numpy as np


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
        self.show_circle_radius = 15
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

        #PATHITEM
        self.path_item = None

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
        posite_pts = np.array([[int(qp.x()), int(qp.y())] for qp in self.positive_pts])
        negetv_pts = np.array([[int(qp.x()), int(qp.y())] for qp in self.negetive_pts])
        return posite_pts, negetv_pts
    
    def set_label_pts(self, posite_pts, negetv_pts):
        self.clear_flag()
        
        for pt in posite_pts:
            self.positive_pts.append(QPointF(pt[0], pt[1]))
            radius = self.show_circle_radius
            circleItem = QGraphicsEllipseItem(pt[0] - radius/2.0, pt[1] - radius/2.0, radius, radius)
            self.circleItems.append(circleItem)
            brush = QRadialGradient(pt[0], pt[1], radius/2.0)
            brush.setColorAt(0, Qt.green)
            brush.setColorAt(1, Qt.transparent)
            circleItem.setBrush(brush)
            circleItem.setPen(QPen(Qt.transparent))  # 外接圆的外径变成透明
            self.scene.addItem(circleItem)

        for pt in negetv_pts:
            self.negetive_pts.append(QPointF(pt[0], pt[1]))
            radius = self.show_circle_radius
            circleItem = QGraphicsEllipseItem(pt[0] - radius/2.0, pt[1] - radius/2.0, radius, radius)
            self.circleItems.append(circleItem)
            brush = QRadialGradient(pt[0], pt[1], radius/2.0)
            brush.setColorAt(0, Qt.red)
            brush.setColorAt(1, Qt.transparent)
            circleItem.setBrush(brush)
            circleItem.setPen(QPen(Qt.transparent))  # 外接圆的外径变成透明
            self.scene.addItem(circleItem)
        
    def set_sam_mode(self, enable):
        self.rect_enable = not enable
        self.pts_enable = enable    
        
    def set_rect_mode(self, enable):
        self.rect_enable = enable
        self.pts_enable = not enable
                
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.position_label.move(10, int(self.height() - self.position_label.height() * 1.5))
        
    def display_edge(self, edge_image):
        try:
            if edge_image is None:
                return

            self.clear_flag()
            path_item = QPainterPath()
            y_coords, x_coords = np.nonzero(edge_image)
            for x, y in zip(x_coords, y_coords):
                path_item.addRect(x, y, 1, 1)

            self.path_item = QGraphicsPathItem(path_item)
            pen = QPen(Qt.green)
            pen.setWidth(2)
            self.path_item.setPen(pen)
            self.scene.addItem(self.path_item)     
        except Exception as e:
            print(f"显示边缘图像出错: {e}")

    def display_image(self, pixmap):
        try:
            self.clear_flag()
            self.scene.clear()
            self.pixmap_item = QGraphicsPixmapItem(pixmap)
            self.scene.addItem(self.pixmap_item)
            self.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)

            # 添加红框
            self.add_red_border()   
            pixmap_width = pixmap.width()
            pixmap_height = pixmap.height()
            min_dimension = min(pixmap_width, pixmap_height)
            self.show_circle_radius = int(min_dimension / 40)
        except Exception as e:
            print(f"display image出错: {e}")
            
    def clear_flag(self):
        try:
            for circleItem in self.circleItems:
                self.scene.removeItem(circleItem)
            self.circleItems.clear()
            self.negetive_pts.clear()
            self.positive_pts.clear()

            if self.path_item:
                self.scene.removeItem(self.path_item)
                self.path_item = None
            
            if self.rect_item:
                self.scene.removeItem(self.rect_item)
                self.rect_item = None
                
        except Exception as e:
            print(f"display image出错: {e}")
        
    def set_show_radius(self, radius_val):
        self.set_show_radius = radius_val

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

        if event.button() == Qt.LeftButton and self.pts_enable and self.pixmap_item:
            scene_pos = self.mapToScene(event.pos())
            self.positive_pts.append(QPointF(scene_pos.x(), scene_pos.y()))
            radius = self.show_circle_radius
            circleItem = QGraphicsEllipseItem(scene_pos.x() - radius/2.0, scene_pos.y() - radius/2.0, radius, radius)
            self.circleItems.append(circleItem)
            brush = QRadialGradient(scene_pos.x(), scene_pos.y(), radius/2.0)
            brush.setColorAt(0, Qt.green)
            brush.setColorAt(1, Qt.transparent)
            circleItem.setBrush(brush)
            circleItem.setPen(QPen(Qt.transparent))  # 外接圆的外径变成透明
            self.scene.addItem(circleItem)

        if event.button() == Qt.RightButton and self.pts_enable and self.pixmap_item:
            scene_pos = self.mapToScene(event.pos())
            self.negetive_pts.append(QPointF(scene_pos.x(), scene_pos.y()))
            radius = self.show_circle_radius
            circleItem = QGraphicsEllipseItem(scene_pos.x() - radius/2.0, scene_pos.y() - radius/2.0, radius, radius)
            self.circleItems.append(circleItem)
            brush = QRadialGradient(scene_pos.x(), scene_pos.y(), radius/2.0)
            brush.setColorAt(0, Qt.red)
            brush.setColorAt(1, Qt.transparent)
            circleItem.setBrush(brush)
            circleItem.setPen(QPen(Qt.transparent))  # 外接圆的外径变成透明
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
    image_path = 'E:/dataset/鲫鱼/200_00fb306e03d311f5c33830ab89f65c5b.jpg'
    pixmap = QPixmap(image_path)
    if pixmap.isNull():
        print(f"无法加载图像: {image_path}")
    else:
        window.display_image(pixmap)
        window.show()

    # 读取hehe.bmp图像
        image_path = "hehe.bmp"
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        image_np = np.array(image)
        window.display_edge(image_np)



    sys.exit(app.exec_())