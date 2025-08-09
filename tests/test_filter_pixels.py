# -*- coding: utf-8 -*-
import unittest
import cv2
import numpy as np
import os
import sys
import io
import random
from pathlib import Path

# 强制使用UTF-8编码解决Windows终端中文乱码问题
if sys.stdout.encoding != 'UTF-8':
    import ctypes
    ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到Python路径，以便导入imageScripts模块
sys.path.append(str(Path(__file__).parent.parent))

from imageScripts.Image import filter_pixels_2x2, save_image

class TestFilterPixels(unittest.TestCase):
    def setUp(self):
        # 设置测试图像路径
        self.assets_dir = Path("assets")
        self.output_dir = Path("test_output")
        
        # 确保输出目录存在并有写入权限
        if not self.output_dir.exists():
            try:
                self.output_dir.mkdir(parents=True, exist_ok=True)
                print(f"创建输出目录: {self.output_dir}")
            except Exception as e:
                print(f"创建输出目录失败: {e}")
        
        # 获取assets目录中的所有图像文件
        self.image_files = []
        for ext in ['.png', '.jpg', '.jpeg']:
            self.image_files.extend(list(self.assets_dir.glob(f'*{ext}')))
        
        # 如果找到图像文件，随机选择最多3个用于测试
        if self.image_files:
            sample_size = min(3, len(self.image_files))
            # 使用ASCII字符较少的文件名（如果可能）
            simple_files = [f for f in self.image_files if all(ord(c) < 128 for c in f.name)]
            if simple_files:
                self.test_images = [f.as_posix() for f in random.sample(simple_files, min(sample_size, len(simple_files)))]
            else:
                self.test_images = [f.as_posix() for f in random.sample(self.image_files, sample_size)]
        else:
            self.test_images = []
        
        # 定义所有过滤模式
        self.filter_modes = ["左上角", "右上角", "左下角", "右下角", "左上右下", "右上左下"]
        
        # 定义模式对应的英文文件名
        self.mode_to_filename = {
            "左上角": "top_left",
            "右上角": "top_right",
            "左下角": "bottom_left",
            "右下角": "bottom_right",
            "左上右下": "top_left_bottom_right",
            "右上左下": "top_right_bottom_left"
        }
    
    def test_filter_pixels_2x2_all_modes(self):
        """测试filter_pixels_2x2函数的所有模式"""
        
        # 尝试从随机选择的图像文件中读取图像
        image = None
        if self.test_images:
            for test_image_path in self.test_images:
                try:
                    image = cv2.imread(test_image_path)
                    if image is not None:
                        print(f"使用图像文件进行测试: {test_image_path}")
                        break
                except Exception as e:
                    print(f"读取图像失败 {test_image_path}: {e}")
        
        # 如果无法读取任何图像文件，则创建一个测试图像
        if image is None:
            print("无法读取任何图像文件，使用生成的测试图像")
            image = np.ones((100, 100, 3), dtype=np.uint8) * 128
            # 添加一些随机颜色块以便更好地测试过滤效果
            for i in range(0, 100, 10):
                for j in range(0, 100, 10):
                    color = np.random.randint(0, 255, 3, dtype=np.uint8)
                    image[i:i+5, j:j+5] = color
        
        # 测试所有过滤模式
        for mode in self.filter_modes:
            with self.subTest(mode=mode):
                # 应用过滤器
                filtered_image = filter_pixels_2x2(image, mode)
                
                # 验证输出图像尺寸与输入相同
                self.assertEqual(filtered_image.shape, image.shape)
                
                # 验证输出图像不是全黑的
                self.assertGreater(np.sum(filtered_image), 0, f"模式 '{mode}' 产生了全黑图像")
                
                # 使用英文文件名保存过滤后的图像用于视觉检查
                filename = self.mode_to_filename.get(mode, f"filtered_{mode}")
                output_path = str(self.output_dir / f"{filename}.png")
                try:
                    # 确保输出目录存在
                    import os
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    
                    # 直接使用cv2.imwrite保存图像
                    save_success = cv2.imwrite(output_path, filtered_image)
                    
                    if not save_success:
                        print(f"cv2.imwrite保存失败，尝试使用save_image函数: {output_path}")
                        save_success = save_image(filtered_image, output_path)
                except Exception as e:
                    print(f"保存图像时发生异常: {e}")
                    save_success = False
                
                # 验证保存成功，但如果失败不要中断测试
                if not save_success:
                    print(f"警告: 保存过滤后的图像失败: {output_path}")
                else:
                    print(f"成功保存图像: {output_path}")
    
    def test_filter_pixels_2x2_pixel_patterns(self):
        """测试filter_pixels_2x2函数的像素模式是否正确"""
        
        # 创建一个简单的4x4测试图像，每个像素都有唯一值
        test_image = np.zeros((4, 4, 3), dtype=np.uint8)
        for y in range(4):
            for x in range(4):
                # 为每个像素设置唯一的RGB值
                test_image[y, x] = [y*50+10, x*50+10, (y+x)*30+10]
        
        # 测试左上角模式
        filtered = filter_pixels_2x2(test_image, "左上角")
        # 检查2x2块中的左上角像素是否被保留
        self.assertTrue(np.array_equal(filtered[0, 0], test_image[0, 0]))
        self.assertTrue(np.array_equal(filtered[0, 2], test_image[0, 2]))
        self.assertTrue(np.array_equal(filtered[2, 0], test_image[2, 0]))
        self.assertTrue(np.array_equal(filtered[2, 2], test_image[2, 2]))
        # 检查其他像素是否为零
        self.assertTrue(np.array_equal(filtered[0, 1], [0, 0, 0]))
        self.assertTrue(np.array_equal(filtered[1, 0], [0, 0, 0]))
        
        # 测试右下角模式
        filtered = filter_pixels_2x2(test_image, "右下角")
        # 检查2x2块中的右下角像素是否被保留
        self.assertTrue(np.array_equal(filtered[1, 1], test_image[1, 1]))
        self.assertTrue(np.array_equal(filtered[1, 3], test_image[1, 3]))
        self.assertTrue(np.array_equal(filtered[3, 1], test_image[3, 1]))
        self.assertTrue(np.array_equal(filtered[3, 3], test_image[3, 3]))
        # 检查其他像素是否为零
        self.assertTrue(np.array_equal(filtered[0, 0], [0, 0, 0]))
        self.assertTrue(np.array_equal(filtered[2, 2], [0, 0, 0]))
    
    def test_filter_pixels_2x2_odd_dimensions(self):
        """测试filter_pixels_2x2函数处理奇数维度图像的情况"""
        
        # 创建一个5x7的测试图像（奇数高度和宽度）
        test_image = np.ones((5, 7, 3), dtype=np.uint8) * 100
        
        # 应用过滤器
        filtered_image = filter_pixels_2x2(test_image, "左上角")
        
        # 验证输出图像尺寸与输入相同
        self.assertEqual(filtered_image.shape, test_image.shape)
        
        # 检查边界处理
        # 最后一行应该被保留
        self.assertTrue(np.any(filtered_image[4, :6] > 0))
        # 最后一列应该被保留
        self.assertTrue(np.any(filtered_image[:4, 6] > 0))
        # 右下角像素应该被保留
        self.assertTrue(np.array_equal(filtered_image[4, 6], test_image[4, 6]))

if __name__ == "__main__":
    unittest.main()
