import os
from typing import Union, overload, TypeVar

import numpy as np
from PIL import Image
from numpy.typing import NDArray

from src.api.Typing import Type_Position

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
    
    参数:
        image1: 第一张输入图像(RGB/RGBA格式)
        image2: 第二张输入图像(RGB/RGBA格式)
        
    返回:
        叠加后的RGBA图像，numpy.ndarray[uint8]类型(4通道)
        
    处理逻辑:
        1. 创建最大尺寸的画布
        2. 将第一张图像放入画布左上角
        3. 将第二张图像的非透明像素叠加到画布上
        4. 保持alpha通道为255(不透明)
    """
    # 获取最大宽高作为画布尺寸
    max_width = max(image1.shape[1], image2.shape[1])
    max_height = max(image1.shape[0], image2.shape[0])

    # 创建画布并初始化alpha通道为255(不透明)
    canvas = np.zeros((max_height, max_width, 4), dtype=np.uint8)
    canvas[:, :, 3] = 255

    # 处理第一张图像(RGB转RGBA)
    if image1.shape[2] == 3:  # RGB格式
        canvas[:image1.shape[0], :image1.shape[1], :3] = image1
    else:  # RGBA格式
        canvas[:image1.shape[0], :image1.shape[1]] = image1

    # 处理第二张图像 - 只叠加非透明像素
    if image2.shape[2] == 3:  # RGB格式
        # 整个图像都是不透明的
        canvas[:image2.shape[0], :image2.shape[1], :3] = image2
    else:  # RGBA格式
        # 使用numpy布尔索引高效处理
        mask = image2[..., 3] > 0
        y_end = min(image2.shape[0], max_height)
        x_end = min(image2.shape[1], max_width)
        canvas[:y_end, :x_end][mask[:y_end, :x_end]] = image2[mask]

    return canvas

def blend_images_small(
    image1: NDArray[np.uint8],
    image2: NDArray[np.uint8],
) -> NDArray[np.uint8]:
    """
    两张图像叠加，以最小宽高作为画布，中心对齐并保持宽高比缩放
    
    参数:
        image1: 第一张输入图像(RGBA格式)
        image2: 第二张输入图像(RGBA格式)
        
    返回:
        叠加后的RGBA图像，以最小宽高作为画布，中心对齐
        
    处理逻辑:
        1. 确定最小宽高作为画布尺寸
        2. 分别计算两张图像的缩放比例
        3. 保持宽高比缩放图像
        4. 将缩放后的图像中心对齐放置
        5. 叠加非透明像素
    """
    # 确定最小画布尺寸
    min_width = min(image1.shape[1], image2.shape[1])
    min_height = min(image1.shape[0], image2.shape[0])
    
    # 创建透明画布
    canvas = np.zeros((min_height, min_width, 4), dtype=np.uint8)
    
    def scale_and_center(img: NDArray[np.uint8]) -> NDArray[np.uint8]:
        """缩放图像并中心对齐"""
        # 计算缩放比例
        h, w = img.shape[:2]
        scale = max(min_width / w, min_height / h)
        
        # 使用PIL进行高质量缩放
        pil_img = Image.fromarray(img)
        new_size = (int(w * scale), int(h * scale))
        scaled_img = np.array(pil_img.resize(new_size, Image.Resampling.LANCZOS))
        
        # 计算中心偏移
        offset_x = (min_width - new_size[0]) // 2
        offset_y = (min_height - new_size[1]) // 2
        
        # 创建临时画布
        temp_canvas = np.zeros((min_height, min_width, 4), dtype=np.uint8)
        
        # 将缩放后的图像放入中心
        y_start = max(0, offset_y)
        y_end = min(min_height, offset_y + new_size[1])
        x_start = max(0, offset_x)
        x_end = min(min_width, offset_x + new_size[0])
        
        img_y_start = max(0, -offset_y)
        img_y_end = min(new_size[1], min_height - offset_y)
        img_x_start = max(0, -offset_x)
        img_x_end = min(new_size[0], min_width - offset_x)
        
        temp_canvas[y_start:y_end, x_start:x_end] = scaled_img[
            img_y_start:img_y_end, img_x_start:img_x_end
        ]
        
        return temp_canvas
    
    # 处理第一张图像
    scaled1 = scale_and_center(image1)
    canvas[scaled1[..., 3] > 0] = scaled1[scaled1[..., 3] > 0]
    
    # 处理第二张图像
    scaled2 = scale_and_center(image2)
    canvas[scaled2[..., 3] > 0] = scaled2[scaled2[..., 3] > 0]
    
    return canvas


def blend_on_canvas(
    canvas: NDArray[np.uint8],
    overlay: NDArray[np.uint8],
) -> NDArray[np.uint8]:
    """
    将overlay图像叠加到canvas上，保持canvas尺寸不变，overlay会保持比例缩放到最合适填充
    
    参数:
        canvas: 作为画布的输入图像(RGB/RGBA格式)
        overlay: 要叠加的图像(RGB/RGBA格式)
        
    返回:
        叠加后的图像，保持canvas的尺寸和格式
        
    处理逻辑:
        1. 如果canvas是RGB格式，转换为RGBA
        2. 当尺寸相同时直接叠加，否则将overlay保持比例缩放到最适合canvas的尺寸
        3. 将overlay中心对齐放置到canvas上
        4. 只叠加非透明像素
    """
    # 确保canvas是RGBA格式
    if canvas.shape[2] == 3:  # RGB格式
        rgba_canvas = np.zeros((canvas.shape[0], canvas.shape[1], 4), dtype=np.uint8)
        rgba_canvas[..., :3] = canvas
        rgba_canvas[..., 3] = 255  # 设置alpha通道为不透明
    else:  # RGBA格式
        rgba_canvas = canvas.copy()
    
    # 检查尺寸是否相同
    canvas_height, canvas_width = rgba_canvas.shape[:2]
    overlay_height, overlay_width = overlay.shape[:2]
    
    if canvas_height == overlay_height and canvas_width == overlay_width:
        # 尺寸相同，直接叠加
        if overlay.shape[2] == 4:  # RGBA格式
            mask = overlay[..., 3] > 0
            rgba_canvas[mask] = overlay[mask]
        else:  # RGB格式
            rgba_canvas[..., :3] = overlay
    else:
        # 尺寸不同，需要缩放
        # 计算保持比例且能覆盖canvas的最小缩放尺寸
        scale = max(canvas_width / overlay_width, canvas_height / overlay_height)
        new_width = int(overlay_width * scale)
        new_height = int(overlay_height * scale)
        
        # 使用PIL进行高质量缩放
        if overlay.shape[2] == 3:  # RGB格式
            pil_overlay = Image.fromarray(overlay).convert('RGBA')
        else:  # RGBA格式
            pil_overlay = Image.fromarray(overlay)
        
        scaled_overlay = np.array(pil_overlay.resize((new_width, new_height), Image.Resampling.LANCZOS))
        
        # 计算中心偏移
        offset_x = (canvas_width - new_width) // 2
        offset_y = (canvas_height - new_height) // 2
        
        # 将缩放后的overlay放入canvas中心
        y_start = max(0, offset_y)
        y_end = min(canvas_height, offset_y + new_height)
        x_start = max(0, offset_x)
        x_end = min(canvas_width, offset_x + new_width)
        
        img_y_start = max(0, -offset_y)
        img_y_end = min(new_height, canvas_height - offset_y)
        img_x_start = max(0, -offset_x)
        img_x_end = min(new_width, canvas_width - offset_x)
        
        # 只叠加非透明像素
        if scaled_overlay.shape[2] == 4:  # RGBA格式
            mask = scaled_overlay[img_y_start:img_y_end, img_x_start:img_x_end, 3] > 0
            rgba_canvas[y_start:y_end, x_start:x_end][mask] = scaled_overlay[img_y_start:img_y_end, img_x_start:img_x_end][mask]
        else:  # RGB格式
            rgba_canvas[y_start:y_end, x_start:x_end, :3] = scaled_overlay[img_y_start:img_y_end, img_x_start:img_x_end]
    
    return rgba_canvas

def prepare_blend_images(
    canvas: NDArray[np.uint8],
    overlay: NDArray[np.uint8],
) -> tuple[NDArray[np.uint8], NDArray[np.uint8]]:
    """
    准备要混合的图像，对overlay进行与blend_on_canvas相同的缩放处理但不叠加
    
    参数:
        canvas: 基础图像(RGB/RGBA格式)
        overlay: 要缩放的图像(RGB/RGBA格式)
        
    返回:
        元组(原样canvas, 缩放后的overlay)
        
    处理逻辑:
        1. 保持canvas不变
        2. 对overlay进行与blend_on_canvas相同的缩放处理
        3. 返回处理后的两张图像
    """
    # 计算overlay的缩放比例
    canvas_height, canvas_width = canvas.shape[:2]
    overlay_height, overlay_width = overlay.shape[:2]
    
    # 计算保持比例且能覆盖canvas的最小缩放尺寸
    scale = max(canvas_width / overlay_width, canvas_height / overlay_height)
    new_width = int(overlay_width * scale)
    new_height = int(overlay_height * scale)
    
    # 使用PIL进行高质量缩放
    if overlay.shape[2] == 3:  # RGB格式
        pil_overlay = Image.fromarray(overlay).convert('RGBA')
    else:  # RGBA格式
        pil_overlay = Image.fromarray(overlay)
    
    scaled_overlay = np.array(pil_overlay.resize((new_width, new_height), Image.Resampling.LANCZOS))
    
    # 计算中心偏移
    offset_x = (canvas_width - new_width) // 2
    offset_y = (canvas_height - new_height) // 2
    
    # 创建与canvas同尺寸的透明画布
    if canvas.shape[2] == 3:  # RGB格式
        rgba_canvas = np.zeros((canvas_height, canvas_width, 4), dtype=np.uint8)
        rgba_canvas[..., :3] = canvas
        rgba_canvas[..., 3] = 255  # 设置alpha通道为不透明
    else:  # RGBA格式
        rgba_canvas = canvas.copy()
    
    # 将缩放后的overlay放入临时画布中心
    y_start = max(0, offset_y)
    y_end = min(canvas_height, offset_y + new_height)
    x_start = max(0, offset_x)
    x_end = min(canvas_width, offset_x + new_width)
    
    img_y_start = max(0, -offset_y)
    img_y_end = min(new_height, canvas_height - offset_y)
    img_x_start = max(0, -offset_x)
    img_x_end = min(new_width, canvas_width - offset_x)
    
    # 创建临时画布存放缩放后的overlay
    temp_canvas = np.zeros_like(rgba_canvas)
    temp_canvas[y_start:y_end, x_start:x_end] = scaled_overlay[img_y_start:img_y_end, img_x_start:img_x_end]
    
    return rgba_canvas, temp_canvas

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
            output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'output')
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
