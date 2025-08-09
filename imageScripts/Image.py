import os
from typing import Union, overload, Literal, TypeVar

import numpy as np
from PIL import Image
from numpy.typing import NDArray

from PySideApp.App import Type_Position

# 定义类型变量
T = TypeVar('T', bound=np.generic)

@overload
def adjust_levels(image: NDArray[np.uint8], in_min: Union[int, float] = 0, 
                 in_max: Union[int, float] = 255, out_min: Union[int, float] = 0, 
                 out_max: Union[int, float] = 255, gamma: float = 1.0) -> NDArray[np.uint8]: ...

@overload
def adjust_levels(image: NDArray[np.float32], in_min: Union[int, float] = 0, 
                 in_max: Union[int, float] = 255, out_min: Union[int, float] = 0, 
                 out_max: Union[int, float] = 255, gamma: float = 1.0) -> NDArray[np.uint8]: ...

def adjust_levels(image: NDArray, in_min: Union[int, float] = 0, 
                 in_max: Union[int, float] = 255, out_min: Union[int, float] = 0, 
                 out_max: Union[int, float] = 255, gamma: float = 1.0) -> NDArray[np.uint8]:
    """
    类似PS的色阶调整
    :param image: 输入图像（RGB格式），numpy.ndarray类型
    :param in_min: 输入黑场（默认0），整数或浮点数
    :param in_max: 输入白场（默认255），整数或浮点数
    :param out_min: 输出黑场（默认0），整数或浮点数
    :param out_max: 输出白场（默认255），整数或浮点数
    :param gamma: 伽马值（中间调，1.0为不变），浮点数
    :return: 调整后的图像，numpy.ndarray[uint8]类型
    """
    # 转换为浮点型
    image = image.astype(np.float32) / 255.0
    
    # 计算输入范围
    in_range = in_max - in_min
    out_range = out_max - out_min
    
    # 应用色阶调整
    image = np.clip((image - in_min/255.0) * (255.0/in_range), 0, 1)
    
    # 应用伽马校正
    image = np.power(image, gamma)
    
    # 映射到输出范围
    image = image * out_range + out_min
    image = np.clip(image, 0, 255).astype(np.uint8)
    
    return image

def safe_imread(image_path: str) -> NDArray[np.uint8]:
    """
    安全读取图像文件，支持中文/特殊字符路径
    :param image_path: 图像文件路径
    :return: RGB格式图像数据，numpy.ndarray[uint8]类型
    :raises: ValueError 如果图像读取失败
    """
    try:
        with Image.open(image_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            return np.array(img)
    except Exception as e:
        raise ValueError(f"无法读取图像 {image_path}: {str(e)}")

def get_max_image_dimensions(images: list[str]) -> tuple[int, int]:
    """
    获取图像列表中最大宽和高
    :param images: 图像路径列表
    :return: 最大宽和高
    :raises: ValueError 如果图像读取失败
    """
    max_width = max_height = 0
    
    for image in images:
        with Image.open(image) as img:
            width, height = img.size
            max_width = max(max_width, width)
            max_height = max(max_height, height)
    
    return max_width, max_height

def filter_pixels_2x2(image: NDArray[np.uint8], mode: Type_Position) -> NDArray[np.uint8]:
    """
    2x2像素过滤
    :param image: 输入图像，numpy.ndarray[uint8]类型
    :param mode: 筛选模式(使用中文)，可选值为:
                "左上角", "右上角", "左下角", "右下角", "左上右下", "右上左下"
    :return: 处理后的新图像，不保留的像素被设为透明(RGBA格式)
    """
    # 转换为PIL图像
    if len(image.shape) == 2:  # 灰度图
        pil_img = Image.fromarray(image).convert('RGBA')
    elif image.shape[2] == 3:  # RGB
        pil_img = Image.fromarray(image).convert('RGBA')
    else:  # RGBA
        pil_img = Image.fromarray(image)
    
    # 获取图像数据
    img_data = np.array(pil_img)
    height, width = img_data.shape[:2]
    
    # 处理2x2块
    emptyPix = [0,0,0,0]
    for y in range(0, height - 1, 2):
        for x in range(0, width - 1, 2):
            # 根据模式设置不保留的像素为完全透明
            if mode == "左上角":
                img_data[y, x+1] = img_data[y+1, x] = img_data[y+1, x+1] = emptyPix
            elif mode == "右上角":
                img_data[y, x] = img_data[y+1, x] = img_data[y+1, x+1] = emptyPix
            elif mode == "左下角":
                img_data[y, x] = img_data[y, x+1] = img_data[y+1, x+1] = emptyPix
            elif mode == "右下角":
                img_data[y, x] = img_data[y, x+1] = img_data[y+1, x] = emptyPix
            elif mode == "左上右下":
                img_data[y, x+1] = img_data[y+1, x] = emptyPix
            elif mode == "右上左下":
                img_data[y, x] = img_data[y+1, x+1] = emptyPix
    
    return img_data

def blend_images(
    image1: NDArray[np.uint8], 
    image2: NDArray[np.uint8],
) -> NDArray[np.uint8]:
    """
    将两张图像叠加，以最大宽高作为画布，左上角对齐
    
    :param image1: 第一张输入图像（RGB/RGBA）
    :param image2: 第二张输入图像（RGB/RGBA）
    :return: 叠加后的RGBA图像，numpy.ndarray[uint8]类型(4通道)
    """
    # 获取最大宽高
    max_width = max(image1.shape[1], image2.shape[1])
    max_height = max(image1.shape[0], image2.shape[0])

    # 创建画布
    new_image = np.zeros((max_height, max_width, 4), dtype=np.uint8)
    new_image[:, :, 3] = 255  # 设置alpha通道为255

    # 将图像复制到画布
    new_image[:image1.shape[0], :image1.shape[1], :3] = image1[..., :3]  # 确保只取前3通道
    for y in range(image2.shape[0]):
        for x in range(image2.shape[1]):
            if image2[y, x, 3] != 0:  # 只有非透明像素才复制
                new_image[y, x, :3] = image2[y, x, :3]

    return new_image


def save_image(image: NDArray[np.uint8], file_path: str) -> bool:
    """
    保存NumPy数组表示的图像到指定文件路径，使用PIL库支持中文路径

    如果路径传入的是basename 寻找根目录下的 output 文件夹 然后将basename添加png后缀保存
    basename 需要检查是否存在同名文件 如果存在则自动添加序号在后缀前 basename-{n}.png

    :param image: 输入图像，numpy.ndarray[uint8]类型
    :param file_path: 保存图像的文件路径，支持各种图像格式（如.jpg, .png, .bmp等） 或者是不包含后缀的basename名称
    :return: 保存是否成功
    """
    try:
        # 处理basename情况
        if not os.path.dirname(file_path) and not os.path.splitext(file_path)[1]:
            # 创建output目录
            output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'output')
            os.makedirs(output_dir, exist_ok=True)

            # 构造基础文件名
            base_name = file_path
            ext = '.png'

            # 处理文件名冲突
            counter = 1
            final_path = os.path.join(output_dir, f"{base_name}{ext}")
            while os.path.exists(final_path):
                final_path = os.path.join(output_dir, f"{base_name}-{counter}{ext}")
                counter += 1
        else:
            final_path = file_path
            # 确保目录存在
            directory = os.path.dirname(final_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)

        # 根据输入数组形状确定图像模式
        if len(image.shape) == 2:  # 灰度图
            mode = 'L'
        elif image.shape[2] == 3:  # RGB
            mode = 'RGB'
        else:  # RGBA
            mode = 'RGBA'

        # 创建PIL图像
        pil_image = Image.fromarray(image, mode)

        # 处理质量参数
        quality = 95  # 默认质量

        # 根据文件扩展名确定保存选项
        file_ext = os.path.splitext(final_path)[1].lower()
        save_options = {}

        if file_ext in ['.jpg', '.jpeg']:
            save_options['quality'] = quality
            save_options['subsampling'] = 0  # 禁用色度子采样
            if mode == 'RGBA':
                pil_image = pil_image.convert('RGB')  # JPEG不支持alpha通道
        elif file_ext == '.png':
            save_options['compress_level'] = 0  # 无损压缩
            save_options['optimize'] = True

        # 保存图像
        pil_image.save(final_path, **save_options)
        return True
    except Exception as e:
        print(f"保存图像失败: {e}")
        return False
