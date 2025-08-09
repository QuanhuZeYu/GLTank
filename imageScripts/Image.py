import cv2
import numpy as np
from numpy.typing import NDArray
from typing import Union, overload, Literal, TypeVar

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
    :param image: 输入图像（BGR格式），numpy.ndarray类型
    :param in_min: 输入黑场（默认0），整数或浮点数
    :param in_max: 输入白场（默认255），整数或浮点数
    :param out_min: 输出黑场（默认0），整数或浮点数
    :param out_max: 输出白场（默认255），整数或浮点数
    :param gamma: 伽马值（中间调，1.0为不变），浮点数
    :return: 调整后的图像，numpy.ndarray[uint8]类型
    """
    # 归一化到[0,1]范围
    float_image: NDArray[np.float64] = image.astype('float')
    image: NDArray[np.float64] = cv2.normalize(float_image, None, 0.0, 1.0, cv2.NORM_MINMAX)

    # 计算缩放因子
    scale_factor: float = 1.0 / (in_max / 255 - in_min / 255)
    
    # 线性拉伸黑场/白场
    image: NDArray[np.float64] = np.clip((image - in_min / 255) * scale_factor, 0, 1)

    # 伽马校正（中间调）
    image: NDArray[np.float64] = np.power(image, gamma)

    # 映射到输出范围
    output_range: float = out_max - out_min
    image: NDArray[np.float64] = image * output_range + out_min
    image: NDArray[np.uint8] = np.clip(image, 0, 255).astype('uint8')

    return image