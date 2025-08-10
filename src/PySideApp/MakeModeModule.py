import os
from typing import Dict, List, Any

import numpy as np
from PIL.ImageQt import QImage
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton,
                               QLabel, QComboBox, QFileDialog, QScrollArea,
                               QFrame, QSpinBox, QCheckBox)

import src.imageScripts.Image
from src.PySideApp.ZoomableLabel import ZoomableImageLabel


class MakeModeModule:
    """
    制作模式模块，负责图片选择、参数调整和图片处理功能
    """
    def __init__(self, parent: QWidget, preview_widget: ZoomableImageLabel) -> None:
        """
        初始化制作模式模块

        Args:
            parent: 父级容器
            preview_widget: 图片预览组件
        """
        self.parent = parent
        self.preview_widget = preview_widget

        # 创建主容器
        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)

        # 使用字典统一管理图片、状态和UI组件
        self.card_states: Dict[str, Dict[str, Any]] = {}  # {path: {param: value, 'card': {...}, 'index': n}}

        # 创建UI组件
        self.create_selection_container()
        self.create_image_management_container()

        # 添加制作按钮
        self.make_button = QPushButton("制作")
        self.layout.addWidget(self.make_button)
        self.make_button.clicked.connect(self.process_images)

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
        self.add_image_button.clicked.connect(self.add_images)

    def create_image_management_container(self) -> None:
        """创建图片管理容器"""
        self.image_management_scroll = QScrollArea()
        self.image_management_scroll.setWidgetResizable(True)
        self.layout.addWidget(self.image_management_scroll)

        self.image_management_widget = QWidget()
        self.image_management_layout = QVBoxLayout(self.image_management_widget)
        self.image_management_scroll.setWidget(self.image_management_widget)

        self.update_image_cards()

    def add_images(self) -> None:
        """添加图片"""
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.bmp *.gif)")

        if file_dialog.exec():
            # 获取当前最大索引
            max_index = max((state['index'] for state in self.card_states.values()), default=-1)
            
            for i, file_path in enumerate(file_dialog.selectedFiles(), start=max_index + 1):
                if file_path not in self.card_states:
                    # 初始化新图片的状态和索引
                    self.card_states[file_path] = {
                        'index': i,
                        'main_canvas': False,
                        'position': 0,
                        'input_min': 0,
                        'input_max': 255,
                        'output_min': 0,
                        'output_max': 255
                    }
            self.update_image_cards()

    def update_image_cards(self) -> None:
        """更新图片卡片显示"""
        # 先保存所有卡片当前状态
        for path, state in self.card_states.items():
            if 'card' in state and state['card']:
                card = state['card']
                state.update({
                    'main_canvas': card['main_canvas'].isChecked(),
                    'position': card['position'].currentIndex(),
                    'input_min': card['input_min'].value(),
                    'input_max': card['input_max'].value(),
                    'output_min': card['output_min'].value(),
                    'output_max': card['output_max'].value()
                })

        # 清空当前布局
        self.clear_layout(self.image_management_layout)

        # 按索引排序图片路径
        sorted_paths = sorted(self.card_states.keys(), 
                            key=lambda p: self.card_states[p]['index'])

        # 重新创建所有卡片
        for i, image_path in enumerate(sorted_paths):
            # 创建新卡片
            card = self.create_image_card(i, image_path)
            self.image_management_layout.addWidget(card['frame'])
            
            # 保存卡片引用到状态字典
            self.card_states[image_path]['card'] = card
            self.card_states[image_path]['index'] = i
            
            # 恢复保存的状态
            state = self.card_states[image_path]
            card['main_canvas'].setChecked(state['main_canvas'])
            card['position'].setCurrentIndex(state['position'])
            card['input_min'].setValue(state['input_min'])
            card['input_max'].setValue(state['input_max'])
            card['output_min'].setValue(state['output_min'])
            card['output_max'].setValue(state['output_max'])

    def create_image_card(self, index: int, image_path: str) -> Dict[str, Any]:
        """创建图片卡片"""
        card_frame = QFrame()
        card_frame.setFrameStyle(QFrame.Panel | QFrame.Raised)
        card_frame.setLineWidth(1)
        card_layout = QVBoxLayout(card_frame)

        # 添加主画布选择框
        main_canvas_check = QCheckBox("主画布")
        main_canvas_check.stateChanged.connect(lambda state, idx=index: self.update_main_canvas_selection(idx, state))
        card_layout.addWidget(main_canvas_check)

        # 添加图片路径标签
        image_label = QLabel(f"图片: {os.path.basename(image_path)[:30] + '...' if len(os.path.basename(image_path)) > 10 else os.path.basename(image_path)}")
        card_layout.addWidget(image_label)

        # 添加图片预览
        image_preview = QLabel()
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            image_preview.setPixmap(pixmap)
        else:
            image_preview.setText("无法加载图片")
        image_preview.setFixedSize(QSize(64, 64))
        image_preview.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(image_preview)

        # 添加删除按钮
        delete_button = QPushButton("删除")
        delete_button.clicked.connect(lambda: self.delete_image(index))
        card_layout.addWidget(delete_button)

        # 添加参数调整标签
        params_label = QLabel("参数调整")
        card_layout.addWidget(params_label)

        # 创建参数调整容器
        params_container = QFrame()
        params_layout = QVBoxLayout(params_container)
        card_layout.addWidget(params_container)

        card_layout.addStretch()

        # 添加位置选择
        position_label = QLabel("选择像素位置")
        params_layout.addWidget(position_label)

        position_combo = QComboBox()
        position_combo.addItems(["左上角", "右上角", "左下角", "右下角", "左上右下", "右上左下"])
        params_layout.addWidget(position_combo)

        # 添加输入色阶最小值
        input_min_label = QLabel("输入色阶最小值")
        params_layout.addWidget(input_min_label)

        input_min_spin = QSpinBox()
        input_min_spin.setRange(0, 255)
        input_min_spin.setValue(0)
        params_layout.addWidget(input_min_spin)

        # 添加输入色阶最大值
        input_max_label = QLabel("输入色阶最大值")
        params_layout.addWidget(input_max_label)

        input_max_spin = QSpinBox()
        input_max_spin.setRange(0, 255)
        input_max_spin.setValue(255)
        params_layout.addWidget(input_max_spin)

        # 添加输出色阶最小值
        output_min_label = QLabel("输出色阶最小值")
        params_layout.addWidget(output_min_label)

        output_min_spin = QSpinBox()
        output_min_spin.setRange(0, 255)
        output_min_spin.setValue(0)
        params_layout.addWidget(output_min_spin)

        # 添加输出色阶最大值
        output_max_label = QLabel("输出色阶最大值")
        params_layout.addWidget(output_max_label)

        output_max_spin = QSpinBox()
        output_max_spin.setRange(0, 255)
        output_max_spin.setValue(255)
        params_layout.addWidget(output_max_spin)

        return {
            'frame': card_frame,
            'preview': image_preview,
            'main_canvas': main_canvas_check,
            'position': position_combo,
            'input_min': input_min_spin,
            'input_max': input_max_spin,
            'output_min': output_min_spin,
            'output_max': output_max_spin
        }

    def delete_image(self, index: int) -> None:
        """删除图片"""
        # 找到对应索引的图片路径
        target_path = next(
            (path for path, state in self.card_states.items() 
             if state['index'] == index), None)
            
        if target_path:
            # 删除对应图片
            del self.card_states[target_path]
            
            # 重新索引剩余卡片
            for i, path in enumerate(sorted(
                self.card_states.keys(), 
                key=lambda p: self.card_states[p]['index']
            )):
                self.card_states[path]['index'] = i
                
            self.update_image_cards()

    def update_main_canvas_selection(self, index: int, state: int) -> None:
        """更新主画布选择状态"""
        if state == Qt.Checked:
            # 取消其他所有卡片的选择状态
            for path, state_data in self.card_states.items():
                if state_data['index'] != index and state_data['card']['main_canvas'].isChecked():
                    state_data['card']['main_canvas'].setChecked(False)
    
    def process_images(self) -> None:
        """处理图片"""
        # 按索引排序获取图片路径
        sorted_paths = sorted(self.card_states.keys(),
                            key=lambda p: self.card_states[p]['index'])
        
        # 查找主画布
        main_canvas_index = next(
            (i for i, path in enumerate(sorted_paths)
             if self.card_states[path]['card']['main_canvas'].isChecked()), 0)
        
        # 使用主画布尺寸作为基础
        main_image_path = sorted_paths[main_canvas_index]
        main_image = src.imageScripts.Image.safe_imread(main_image_path)
        result_image = np.zeros((main_image.shape[0], main_image.shape[1], 4), dtype=np.uint8)

        # 先处理主画布
        main_card = self.card_states[main_image_path]['card']
        input_min = main_card['input_min'].value()
        input_max = main_card['input_max'].value()
        output_min = main_card['output_min'].value()
        output_max = main_card['output_max'].value()
        main_image = src.imageScripts.Image.adjust_levels(main_image, input_min, input_max, output_min, output_max)
        position = main_card['position'].currentText()
        main_image = src.imageScripts.Image.filter_pixels_2x2(main_image, position)
        result_image = src.imageScripts.Image.blend_on_canvas(result_image, main_image)

        # 处理其他图片
        for i, image_path in enumerate(sorted_paths):
            if i == main_canvas_index: # 跳过主画布
                continue
                
            image_card = self.card_states[image_path]['card']
            image = src.imageScripts.Image.safe_imread(image_path)
            input_min = image_card['input_min'].value()
            input_max = image_card['input_max'].value()
            output_min = image_card['output_min'].value()
            output_max = image_card['output_max'].value()
            image = src.imageScripts.Image.adjust_levels(image, input_min, input_max, output_min, output_max)

            position = image_card['position'].currentText()
            _, image = src.imageScripts.Image.prepare_blend_images(main_image, image) # 获取匹配主画布缩放裁切后的图片
            image = src.imageScripts.Image.filter_pixels_2x2(image, position) # 处理2x2像素块
            result_image = src.imageScripts.Image.blend_on_canvas(result_image, image) # 将图片叠加到主画布上

        src.imageScripts.Image.save_image(result_image, "result_blend")
        q_image = QImage(result_image.data, result_image.shape[1], result_image.shape[0], QImage.Format_RGBA8888)
        self.preview_widget.set_image(QPixmap.fromImage(q_image))

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
