import os
import sys
from typing import Dict, List, Optional, Union, Any, Callable
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel, QComboBox, QFileDialog, QScrollArea, QFrame,
                               QSpinBox, QSplitter, QLayout)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QSize

from PySideApp.ZoomableLabel import ZoomableImageLabel


class MyApp:
    """
    应用布局：
        - root - 垂直容器
            - 水平容器 `可以手动拉伸内部元素进行调整`
                - 垂直容器 `模式选择 选择图片 管理图片 设置制作参数的顶层容器`

                    - 标签(text: "模式选择")
                    - 水平容器 `模式选择容器`
                        - 按钮(text: "制作模式")
                        - 按钮(text: "查看模式")


                    - 标签(text: "{动态设置 默认: 请选择模式}")
                    - 垂直容器 `选择容器`
                        - 标签(text: "选择图片")
                        - 按钮(text: "添加图片")

                    - 垂直容器 `管理图片 设置参数容器 图片列表`
                        - 垂直容器 `元素容器 卡片`
                            - 标签(text: "图片: {imagePath}")
                            - 图片预览器(size: 64x64)
                            - 按钮(text: "删除")

                            { `卡片容器`
                            - 标签(text: "参数调整")
                            - 垂直容器 `参数调整容器`
                                - 标签(text: "选择像素位置")
                                - 选择框(items: "左上角", "右上角", "左下角", "右下角")
                                - 标签(text: "输入色阶最小值")
                                - 输入框(type: int, value: 0, min: 0, max: 255)
                                - 标签(text: "输入色阶最大值")
                                - 输入框(type: int, value: 255, min: 0, max: 255)
                                - 标签(text: "输出色阶最小值")
                                - 输入框(type: int, value: 0, min: 0, max: 255)
                                - 标签(text: "输出色阶最大值")
                                - 输入框(type: int, value: 255, min: 0, max: 255)
                            }
                - 图片预览器 `PySideApp.ZoomableLabel`
    """
    def __init__(self) -> None:
        # 创建应用程序
        self.app: QApplication = QApplication(sys.argv)
        
        # 创建主窗口
        self.window: QWidget = QWidget()
        self.window.setWindowTitle("光棱坦克(制作/查看)器")
        self.window.resize(1200, 800)
        
        # 创建根布局（垂直布局）
        self.root_layout: QVBoxLayout = QVBoxLayout(self.window)
        
        # 创建可拉伸的水平分割器
        self.main_splitter: QSplitter = QSplitter(Qt.Horizontal)
        self.root_layout.addWidget(self.main_splitter)
        
        # 创建左侧控制面板容器
        self.control_panel: QWidget = QWidget()
        self.control_layout: QVBoxLayout = QVBoxLayout(self.control_panel)
        self.main_splitter.addWidget(self.control_panel)
        
        # 创建右侧图片预览区
        self.preview_widget: ZoomableImageLabel = ZoomableImageLabel()
        self.preview_widget.setText("预览区域")
        self.preview_widget.setMinimumSize(500, 500)
        self.preview_widget.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.main_splitter.addWidget(self.preview_widget)
        
        # 设置分割器的初始大小
        self.main_splitter.setSizes([400, 800])
        
        # 创建模式选择部分
        self.create_mode_selection()
        
        # 创建动态内容区域
        self.dynamic_content: QWidget = QWidget()
        self.dynamic_layout: QVBoxLayout = QVBoxLayout(self.dynamic_content)
        self.control_layout.addWidget(self.dynamic_content)
        
        # 初始化图片列表
        self.image_paths: List[str] = []
        self.image_cards: List[Dict[str, Any]] = []
        
        # 默认显示制作模式
        self.switch_to_make_mode()
    
    def create_mode_selection(self) -> None:
        """创建模式选择部分"""
        # 添加模式选择标签
        self.mode_label: QLabel = QLabel("模式选择")
        self.control_layout.addWidget(self.mode_label)
        
        # 创建模式选择容器（水平布局）
        self.mode_container: QHBoxLayout = QHBoxLayout()
        self.control_layout.addLayout(self.mode_container)
        
        # 添加两个模式按钮
        self.make_mode_button: QPushButton = QPushButton("制作模式")
        self.view_mode_button: QPushButton = QPushButton("查看模式")
        self.mode_container.addWidget(self.make_mode_button)
        self.mode_container.addWidget(self.view_mode_button)
        
        # 连接按钮信号
        self.make_mode_button.clicked.connect(self.switch_to_make_mode)
        self.view_mode_button.clicked.connect(self.switch_to_view_mode)
        
        # 添加动态模式标签
        self.dynamic_mode_label: QLabel = QLabel("请选择模式")
        self.control_layout.addWidget(self.dynamic_mode_label)
    
    def switch_to_make_mode(self) -> None:
        """切换到制作模式"""
        # 更新动态模式标签
        self.dynamic_mode_label.setText("当前模式: 制作模式")
        
        # 清空动态内容区域
        self.clear_layout(self.dynamic_layout)
        
        # 创建选择容器
        self.create_selection_container()
        
        # 创建图片管理容器
        self.create_image_management_container()
        
        # 添加制作按钮
        self.make_button: QPushButton = QPushButton("制作")
        self.dynamic_layout.addWidget(self.make_button)
        self.make_button.clicked.connect(self.process_images)
    
    def create_selection_container(self) -> None:
        """创建选择容器"""
        # 创建选择容器
        self.selection_container: QFrame = QFrame()
        self.selection_layout: QVBoxLayout = QVBoxLayout(self.selection_container)
        self.dynamic_layout.addWidget(self.selection_container)
        
        # 添加选择图片标签
        self.select_image_label: QLabel = QLabel("选择图片")
        self.selection_layout.addWidget(self.select_image_label)
        
        # 添加添加图片按钮
        self.add_image_button: QPushButton = QPushButton("添加图片")
        self.selection_layout.addWidget(self.add_image_button)
        self.add_image_button.clicked.connect(self.add_images)
    
    def create_image_management_container(self) -> None:
        """创建图片管理容器"""
        # 创建图片管理容器的滚动区域
        self.image_management_scroll: QScrollArea = QScrollArea()
        self.image_management_scroll.setWidgetResizable(True)
        self.dynamic_layout.addWidget(self.image_management_scroll)
        
        # 创建图片管理容器
        self.image_management_widget: QWidget = QWidget()
        self.image_management_layout: QVBoxLayout = QVBoxLayout(self.image_management_widget)
        self.image_management_scroll.setWidget(self.image_management_widget)
        
        # 更新图片列表显示
        self.update_image_cards()
    
    def switch_to_view_mode(self) -> None:
        """切换到查看模式"""
        # 更新动态模式标签
        self.dynamic_mode_label.setText("当前模式: 查看模式")
        
        # 清空动态内容区域
        self.clear_layout(self.dynamic_layout)
        
        # 创建查看模式的控件
        view_label = QLabel("查看模式 - 功能待实现")
        self.dynamic_layout.addWidget(view_label)
    
    def clear_layout(self, layout: Optional[QLayout]) -> None:
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
    
    def add_images(self) -> None:
        """添加图片"""
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            for file_path in selected_files:
                if file_path not in self.image_paths:
                    self.image_paths.append(file_path)
            
            # 更新图片列表显示
            self.update_image_cards()
    
    def update_image_cards(self) -> None:
        """更新图片卡片显示"""
        # 清空图片列表
        self.clear_layout(self.image_management_layout)
        self.image_cards = []
        
        # 添加图片卡片
        for i, image_path in enumerate(self.image_paths):
            # 创建图片卡片
            card = self.create_image_card(i, image_path)
            self.image_management_layout.addWidget(card['frame'])
            self.image_cards.append(card)
    
    def create_image_card(self, index: int, image_path: str) -> Dict[str, Any]:
        """创建图片卡片"""
        # 创建卡片容器
        card_frame = QFrame()
        card_frame.setFrameStyle(QFrame.Panel | QFrame.Raised)
        card_frame.setLineWidth(1)
        card_layout = QVBoxLayout(card_frame)
        
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
        
        # 返回卡片信息
        return {
            'frame': card_frame,
            'preview': image_preview,
            'position': position_combo,
            'input_min': input_min_spin,
            'input_max': input_max_spin,
            'output_min': output_min_spin,
            'output_max': output_max_spin
        }
    
    def delete_image(self, index: int) -> None:
        """删除图片"""
        if 0 <= index < len(self.image_paths):
            del self.image_paths[index]
            self.update_image_cards()
    
    def process_images(self) -> None:
        """
        1. 读取cards列表中的图片逐个处理 `防止图像过多`
        2. 根据card中的参数调整图片
            2.1 读取card图片地址中的图片到内存中准备处理
            2.2 调用imageScripts/Image.py中的adjust_levels函数处理图片
            2.3 读取card中的选择像素位置参数 准备第二步处理adjust_levels处理后的图片
                2.3.1 以2x2为单位平铺图像开始处理，如果最后一行或一列不足则补充一行或者一列透明像素开始处理 最后步骤将补充的这一行列像素删除
                2.3.2 根据选择的像素参数处理2x2像素块 选择左上角则在该2x2保留左上角像素其它像素调整为全透明 其他参数同理
                2.3.3 调整完透明度后 如果开始补充了透明像素 则删除补充的透明像素
            2.4 最后结果为 调整了色阶 并调整了透明度的图像
        3. 将结果图像按照顺序透明度叠图 序号低的在底层 序号高的在上层
        4. 返回结果图像
        :return: 返回图像
        """
        # 这里应该实现图片处理逻辑
        # 可以使用 imageScripts/Image.py 中的 adjust_levels 函数
        print("处理图片功能待实现")

        # 如果有图片，显示第一张图片在预览区域
        if self.image_paths:
            self.preview_widget.set_image(QPixmap(self.image_paths[0]))
    
    def run(self) -> int:
        """运行应用程序"""
        self.window.show()
        return self.app.exec()


if __name__ == "__main__":
    app = MyApp()
    sys.exit(app.run())