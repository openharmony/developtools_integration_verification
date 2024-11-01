import unittest
import pandas as pd
import json
from src.spdx_license_matcher import SPDXLicenseMatcher
import os

class TestSPDXLicenseMatcher(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 创建临时测试数据
        cls.test_excel_path = 'test_oh_spdx_license_match.xlsx'
        cls.test_json_path = 'test_spdx.json'
        cls.output_excel_path = 'test_output.xlsx'
        
        # Excel测试数据，包含分号分隔的许可证名
        df = pd.DataFrame({
            'cc_url': ['https://example.com/license1', 'https://example.com/license2'],
            'spdx_fixed_license_name': ['Apache License 2.0', 'Creative Commons Attribution 4.0 International;MIT License']
        })
        df.to_excel(cls.test_excel_path, index=False)
        
        # JSON测试数据，包含格式规范化的SPDX映射
        spdx_data = {
            "Apache License 2.0": "Apache-2.0",
            "Creative Commons Attribution 4.0 International": "CC-BY-4.0",
            "MIT License": "MIT"
        }
        with open(cls.test_json_path, 'w', encoding='utf-8') as f:
            json.dump(spdx_data, f)

    @classmethod
    def tearDownClass(cls):
        # 删除临时文件
        os.remove(cls.test_excel_path)
        os.remove(cls.test_json_path)
        os.remove(cls.output_excel_path)

    def setUp(self):
        # 初始化 SPDXLicenseMatcher 实例
        self.matcher = SPDXLicenseMatcher(self.test_excel_path, self.test_json_path)

    def test_load_data(self):
        # 测试数据加载
        self.assertIsNotNone(self.matcher.df)
        self.assertGreater(len(self.matcher.spdx_mapping), 0)
        
    def test_copy_url_column(self):
        # 测试URL列复制
        self.matcher.copy_url_column()
        self.assertIn('match_url', self.matcher.df.columns)
        self.assertEqual(self.matcher.df['match_url'][0], 'https://example.com/license1')

    def test_match_license_column(self):
        # 测试许可证匹配，包含分号分隔的许可证名
        self.matcher.match_license_column()
        self.assertIn('match_license', self.matcher.df.columns)
        # 验证匹配结果
        self.assertEqual(self.matcher.df['match_license'][0], 'Apache-2.0')
        self.assertEqual(self.matcher.df['match_license'][1], 'CC-BY-4.0;MIT')

    def test_save_to_excel(self):
        # 测试保存到Excel文件
        self.matcher.copy_url_column()
        self.matcher.match_license_column()
        self.matcher.save_to_excel(self.output_excel_path)
        self.assertTrue(os.path.exists(self.output_excel_path))
        # 验证保存内容
        df_saved = pd.read_excel(self.output_excel_path)
        self.assertIn('match_license', df_saved.columns)
        self.assertEqual(df_saved['match_license'][0], 'Apache-2.0')
        self.assertEqual(df_saved['match_license'][1], 'CC-BY-4.0;MIT')

if __name__ == '__main__':
    unittest.main()
