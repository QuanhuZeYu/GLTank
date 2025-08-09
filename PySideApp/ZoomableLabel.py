from PySide6.QtCore import QPoint, QPointF, Qt, QRect
from PySide6.QtGui import QTransform, QWheelEvent, QMouseEvent, QPixmap, QPaintEvent
from PySide6.QtWidgets import QLabel
from typing import Optional


class ZoomableImageLabel(QLabel):
    """可缩放的图像标签"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmap_original: Optional[QPixmap] = None
        self.scale_factor: float = 1.0
        self.zoom_step: float = 0.1
        self.min_scale: float = 0.1
        self.max_scale: float = 10.0
        self.last_mouse_pos: QPoint = QPoint()
        self.is_panning: bool = False
        self.offset: QPointF = QPointF(0, 0)

        # 启用鼠标追踪
        self.setMouseTracking(True)
        # 设置焦点策略，使组件可以接收键盘事件
        self.setFocusPolicy(Qt.StrongFocus)
        # 设置对齐方式为居中
        self.setAlignment(Qt.AlignCenter)
        # 设置缩放模式
        self.setScaledContents(False)

    def set_image(self, pixmap: QPixmap) -> None:
        """设置图像"""
        if pixmap.isNull():
            return

        self.pixmap_original = pixmap
        self.scale_factor = 1.0
        self.offset = QPointF(0, 0)
        self.update_pixmap()

    def update_pixmap(self) -> None:
        """更新显示的图像"""
        if self.pixmap_original is None:
            return

        # 计算缩放后的图像大小
        scaled_size = self.pixmap_original.size() * self.scale_factor

        # 创建变换矩阵
        transform = QTransform()
        transform.scale(self.scale_factor, self.scale_factor)

        # 应用变换
        scaled_pixmap = self.pixmap_original.transformed(transform, Qt.SmoothTransformation)

        # 设置图像
        super().setPixmap(scaled_pixmap)

        # 调整偏移量，确保图像不会移出视图
        self.adjust_offset()

    def adjust_offset(self) -> None:
        """调整偏移量，确保图像不会移出视图"""
        if self.pixmap_original is None:
            return

        pixmap = self.pixmap()
        if pixmap.isNull():
            return

        # 计算图像的可见区域
        view_rect = self.rect()
        pixmap_rect = QRect(0, 0, pixmap.width(), pixmap.height())

        # 调整水平偏移
        if pixmap_rect.width() <= view_rect.width():
            # 如果图像宽度小于视图宽度，则居中显示
            self.offset.setX(0)
        else:
            # 确保图像不会移出视图
            min_x = view_rect.width() - pixmap_rect.width()
            max_x = 0
            self.offset.setX(max(min(self.offset.x(), max_x), min_x))

        # 调整垂直偏移
        if pixmap_rect.height() <= view_rect.height():
            # 如果图像高度小于视图高度，则居中显示
            self.offset.setY(0)
        else:
            # 确保图像不会移出视图
            min_y = view_rect.height() - pixmap_rect.height()
            max_y = 0
            self.offset.setY(max(min(self.offset.y(), max_y), min_y))

    def wheelEvent(self, event: QWheelEvent) -> None:
        """处理鼠标滚轮事件"""
        if self.pixmap_original is None:
            return

        # 获取鼠标位置
        mouse_pos = event.position()

        # 计算缩放因子
        delta = event.angleDelta().y()
        zoom_in = delta > 0

        # 保存旧的缩放因子
        old_scale = self.scale_factor

        # 更新缩放因子
        if zoom_in:
            self.scale_factor = min(self.scale_factor * (1 + self.zoom_step), self.max_scale)
        else:
            self.scale_factor = max(self.scale_factor * (1 - self.zoom_step), self.min_scale)

        # 更新图像
        self.update_pixmap()

        # 更新偏移量，使鼠标位置处的图像点保持不变
        if old_scale != self.scale_factor:
            # 计算鼠标位置相对于图像中心的偏移
            center_x = self.width() / 2 + self.offset.x()
            center_y = self.height() / 2 + self.offset.y()
            mouse_offset_x = mouse_pos.x() - center_x
            mouse_offset_y = mouse_pos.y() - center_y

            # 计算新的偏移量
            scale_change = self.scale_factor / old_scale
            new_mouse_offset_x = mouse_offset_x * scale_change
            new_mouse_offset_y = mouse_offset_y * scale_change

            # 更新偏移量
            self.offset.setX(self.offset.x() + (mouse_offset_x - new_mouse_offset_x))
            self.offset.setY(self.offset.y() + (mouse_offset_y - new_mouse_offset_y))

            # 调整偏移量
            self.adjust_offset()

            # 更新图像
            self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """处理鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self.is_panning = True
            self.last_mouse_pos = event.position().toPoint()
            self.setCursor(Qt.ClosedHandCursor)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """处理鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            self.is_panning = False
            self.setCursor(Qt.ArrowCursor)

    def mouseMoveEvent(self, event: QMouseEvent):
        """处理鼠标移动事件"""
        if self.is_panning:
            # 计算鼠标移动的距离
            delta = event.position().toPoint() - self.last_mouse_pos
            self.last_mouse_pos = event.position().toPoint()

            # 更新偏移量
            self.offset += QPointF(delta.x(), delta.y())

            # 调整偏移量
            self.adjust_offset()

            # 更新图像
            self.update()

    def paintEvent(self, event):
        """重写绘制事件"""
        if self.pixmap() is None or self.pixmap().isNull():
            super().paintEvent(event)
            return

        # 创建绘制器
        from PySide6.QtGui import QPainter
        painter = QPainter(self)

        # 计算图像的绘制位置
        pixmap = self.pixmap()
        x = (self.width() - pixmap.width()) / 2 + self.offset.x()
        y = (self.height() - pixmap.height()) / 2 + self.offset.y()

        # 绘制图像
        painter.drawPixmap(int(x), int(y), pixmap)
