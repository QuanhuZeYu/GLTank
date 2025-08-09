import os
from typing import List, Dict, Any, Optional

import numpy as np
from PIL.ImageQt import QImage
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                              QLabel, QFileDialog, QScrollArea, QFrame, QSpinBox)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QSize
from numpy._typing import NDArray

from imageScripts.Image import get_max_image_dimensions, safe_imread, adjust_levels, save_image
from PySideApp.ZoomableLabel import ZoomableImageLabel


def ndarray_to_pixmap(arr: NDArray) -> QPixmap:
    """将numpy数组转换为QPixmap，支持RGB和RGBA格式
    
    Args:
        arr: 输入数组，形状为(h,w,3)或(h,w,4)，dtype为uint8
        
    Returns:
        QPixmap对象
        
    Raises:
        ValueError: 如果输入数组不符合要求
    """
    # 验证数组形状和类型
    if arr.ndim != 3 or arr.shape[2] not in (3, 4) or arr.dtype != np.uint8:
        raise ValueError("Array must be (h, w, 3) or (h, w, 4) and uint8 type")

    height, width, channels = arr.shape
    # 根据通道数选择格式
    if channels == 3:
        format = QImage.Format_RGB888
        bytes_per_line = 3 * width
    else:  # channels == 4
        format = QImage.Format_RGBA8888
        bytes_per_line = 4 * width

    # 创建内存连续的数组
    if not arr.flags['C_CONTIGUOUS']:
        arr = np.ascontiguousarray(arr)

    # 创建QImage并转换
    qimage = QImage(arr.data, width, height, bytes_per_line, format)
    if qimage.isNull():
        raise ValueError("Failed to create QImage from array")
        
    return QPixmap.fromImage(qimage.copy())

class ViewModeModule:
    """
    查看模式模块，负责图片选择和色阶调整功能
    """
    def __init__(self, parent: QWidget, preview_widget: ZoomableImageLabel) -> None:
        """
        初始化查看模式模块
        
        Args:
            parent: 父级容器
            preview_widget: 图片预览组件
        """
        self.parent = parent
        self.preview_widget = preview_widget
        
        # 创建主容器
        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        
        # 当前选中的图片路径
        self.current_image_path: Optional[str] = None
        
        # 添加当前图片标签
        self.current_image_label = QLabel("当前没有选择图片")
        self.layout.addWidget(self.current_image_label)
        
        # 创建UI组件
        self.create_selection_container()
        self.create_levels_adjustment_container()
        
        # 添加解析按钮
        self.analyze_button = QPushButton("解析图片")
        self.layout.addWidget(self.analyze_button)
        self.analyze_button.clicked.connect(self.analyze_image)
        
        # 添加弹簧组件
        self.layout.addStretch()
    
    def get_container(self) -> QWidget:
        """获取模块容器"""
        return self.container
    
    def create_selection_container(self) -> None:
        """创建选择容器"""
        self.selection_container = QFrame()
        self.selection_layout = QVBoxLayout(self.selection_container)
        self.layout.addWidget(self.selection_container)
        
        # 添加选择图片标签
        self.select_image_label = QLabel("选择图片")
        self.selection_layout.addWidget(self.select_image_label)
        
        # 添加添加图片按钮
        self.add_image_button = QPushButton("添加图片")
        self.selection_layout.addWidget(self.add_image_button)
        self.add_image_button.clicked.connect(self.add_image)
    
    def create_levels_adjustment_container(self) -> None:
        """创建色阶调整容器"""
        self.levels_container = QFrame()
        self.levels_layout = QVBoxLayout(self.levels_container)
        self.layout.addWidget(self.levels_container)
        
        # 添加色阶范围标签
        self.levels_label = QLabel("选择色阶范围")
        self.levels_layout.addWidget(self.levels_label)
        
        # 添加输入色阶最小值
        self.input_min_label = QLabel("输入色阶最小值")
        self.levels_layout.addWidget(self.input_min_label)
        
        self.input_min_spin = QSpinBox()
        self.input_min_spin.setRange(0, 255)
        self.input_min_spin.setValue(0)
        self.levels_layout.addWidget(self.input_min_spin)
        
        # 添加输入色阶最大值
        self.input_max_label = QLabel("输入色阶最大值")
        self.levels_layout.addWidget(self.input_max_label)
        
        self.input_max_spin = QSpinBox()
        self.input_max_spin.setRange(0, 255)
        self.input_max_spin.setValue(255)
        self.levels_layout.addWidget(self.input_max_spin)
    
    def add_image(self) -> None:
        """添加图片（覆盖旧的）"""
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                self.current_image_path = selected_files[0]
                self.current_image_label.setText(f"当前图片: {os.path.basename(self.current_image_path)}")
    
    def analyze_image(self) -> None:
        """解析图片"""
        try:
            if not self.current_image_path:
                return
                
            # 读取图片
            image = safe_imread(self.current_image_path)
            if image is None:
                return
                
            # 调整色阶
            input_min = self.input_min_spin.value()
            input_max = self.input_max_spin.value()
            adjusted_image = adjust_levels(image, input_min, input_max, 0, 255)
            
            # 检查调整后的图像数据
            if adjusted_image is None or adjusted_image.size == 0:
                return

            pixmap = ndarray_to_pixmap(adjusted_image)
            self.preview_widget.set_image(pixmap)
            
        except Exception:
            import traceback
            traceback.print_exc()
    
    def clear_layout(self, layout) -> None:
        """递归清除布局中的所有控件"""
        if layout is None:
            return
        
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                self.clear_layout(item.layout())
