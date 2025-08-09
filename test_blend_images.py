import cv2
from src.imageScripts.Image import filter_pixels_2x2, blend_images, save_image

def test_blend_images():
    # 1. 确保assets目录存在
    import os
    asset_dir = 'assets'
    if not os.path.exists(asset_dir) or not os.path.isdir(asset_dir):
        print(f"错误: 资源文件夹'{asset_dir}'不存在")
        return
    
    # 2. 获取assets文件夹中的图片文件(仅限英文文件名)
    import glob
    image_files = []
    for ext in ['*.jpg', '*.png', '*.jpeg', '*.bmp']:
        for file in glob.glob(os.path.join(asset_dir, ext)):
            try:
                # 检查文件名是否只包含ASCII字符
                if file.encode('ascii', errors='ignore').decode('ascii') == file:
                    image_files.append(file)
            except UnicodeEncodeError:
                continue
    
    # 3. 如果没有足够图片，使用默认生成的测试图片
    if len(image_files) < 2:
        raise Exception("没有足够的图片用于测试, 请在assets文件夹中添加至少两张图片")
    
    # 4. 随机选择两张不同的图片
    import random
    selected_images = random.sample(image_files, 2)
    image1 = cv2.imread(selected_images[0])
    image2 = cv2.imread(selected_images[1])
    
    print(f"使用的测试图片: {selected_images[0]} 和 {selected_images[1]}")

    # 2. 对两张图像应用不同的过滤模式
    top_left_bottom_right = filter_pixels_2x2(image1, "左上右下")
    top_right_bottom_left = filter_pixels_2x2(image2, "右上左下")

    # 3. 混合图像 (alpha=0.5 表示50%透明度)
    blended = blend_images(top_left_bottom_right, top_right_bottom_left, alpha=0.5)

    # 4. 保存结果
    save_image(top_left_bottom_right, 'test_output/top_left_bottom_right.png')
    save_image(top_right_bottom_left, 'test_output/top_right_bottom_left.png')
    save_image(blended, 'test_output/blended_result.png')

    print("测试完成，结果已保存到test_output目录")

if __name__ == "__main__":
    test_blend_images()
