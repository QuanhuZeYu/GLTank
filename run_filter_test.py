import unittest
from tests.test_filter_pixels import TestFilterPixels

if __name__ == "__main__":
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestFilterPixels)
    # 运行测试
    unittest.TextTestRunner(verbosity=2).run(suite)
