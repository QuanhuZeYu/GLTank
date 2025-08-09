import os
import random
import time

from src.imageScripts.Image import adjust_levels, safe_imread, save_image

def main():
    # 确保output目录存在
    os.makedirs("output", exist_ok=True)

    # 获取assets目录下所有图片文件
    assets_dir = "assets"
    image_files = [f for f in os.listdir(assets_dir)
                  if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    if len(image_files) < 2:
        print("需要至少两张图片进行测试")
        return

    # 随机选择两张不同的图片
    img1_path, img2_path = random.sample(image_files, 2)
    img1_path = os.path.join(assets_dir, img1_path)
    img2_path = os.path.join(assets_dir, img2_path)

    # 读取图片
    try:
        img1 = safe_imread(img1_path)
        img2 = safe_imread(img2_path)
    except Exception as e:
        print(f"读取图片失败: {e}")
        return

    # 应用色阶调整
    # 第一张: 输入0-255, 输出0-25
    adjusted1 = adjust_levels(img1, out_max=25)

    # 第二张: 输入0-255, 输出25-255
    adjusted2 = adjust_levels(img2, out_min=25)

    # 保存结果
    base1 = os.path.splitext(os.path.basename(img1_path))[0]
    base2 = os.path.splitext(os.path.basename(img2_path))[0]

    save_image(adjusted1, f"test_output/{base1}_out0-25.jpg")
    save_image(adjusted2, f"test_output/{base2}_out25-255.jpg")

    time.sleep(3)

    print("色阶调整测试完成，结果已保存到output目录")

if __name__ == "__main__":
    main()
