import cv2
import numpy as np
import os
import glob
import random
from imageScripts.Image import adjust_levels, filter_pixels_2x2, blend_images, save_image

def test_levels_and_blend():
    # 1. 确保assets目录存在
    asset_dir = 'assets'
    if not os.path.exists(asset_dir) or not os.path.isdir(asset_dir):
        print(f"错误: 资源文件夹'{asset_dir}'不存在")
        return

    # 2. 获取assets文件夹中的所有图片文件
    image_files = glob.glob(os.path.join(asset_dir, '*.jpg')) + \
                 glob.glob(os.path.join(asset_dir, '*.png'))

    if len(image_files) < 2:
        print(f"错误: assets文件夹中需要至少2张图片，当前只有{len(image_files)}张")
        return

    # 3. 随机选择两张不同的图片
    selected_images = random.sample(image_files, 2)
    try:
        from imageScripts.Image import safe_imread
        image1 = safe_imread(selected_images[0])
        image2 = safe_imread(selected_images[1])
    except ValueError as e:
        print(f"错误: {str(e)}")
        return

    print(f"使用的测试图片: {selected_images[0]} 和 {selected_images[1]}")

    # 4. 处理第一张图片: 色阶0-25 + 左上右下过滤
    processed_A = adjust_levels(image1, out_min=0, out_max=25)
    processed_A = filter_pixels_2x2(processed_A, "左上右下")

    # 5. 处理第二张图片: 色阶25-255 + 右上左下过滤
    processed_B = adjust_levels(image2, out_min=25, out_max=255)
    processed_B = filter_pixels_2x2(processed_B, "右上左下")

    # 6. 混合处理后的图片
    blended = blend_images(processed_A, processed_B)

    # 7. 确保输出目录存在
    output_dir = 'test_output'
    os.makedirs(output_dir, exist_ok=True)

    # 8. 保存结果(PNG格式以支持透明通道)
    save_image(processed_A, os.path.join(output_dir, 'processed_A.png'))
    save_image(processed_B, os.path.join(output_dir, 'processed_B.png'))
    save_image(blended, os.path.join(output_dir, 'blended_result.png'))

    print("测试完成，结果已保存到test_output目录(PNG格式)")

if __name__ == "__main__":
    test_levels_and_blend()
