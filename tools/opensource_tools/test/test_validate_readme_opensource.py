import unittest
from unittest.mock import patch, mock_open, MagicMock
import json
import os

# 确保导入 OpenSourceValidator 类
from src.validate_readme_opensource import OpenSourceValidator


class TestOpenSourceValidator(unittest.TestCase):
    def setUp(self):
        self.project_root = "/fake/project/root"
        self.validator = OpenSourceValidator(self.project_root)
        self.readme_content_valid = json.dumps(
            [
                {
                    "Name": "TestLibrary",
                    "License": "MIT",
                    "License File": "LICENSE",
                    "Version Number": "1.0.0",
                    "Owner": "TestOwner",
                    "Upstream URL": "http://example.com",
                    "Description": "A test library.",
                }
            ]
        )
        self.readme_content_missing_fields = json.dumps(
            [
                {
                    "Name": "TestLibrary",
                    # Missing 'License'
                    "License File": "LICENSE",
                    "Version Number": "1.0.0",
                    "Owner": "TestOwner",
                    "Upstream URL": "http://example.com",
                    "Description": "A test library.",
                }
            ]
        )
        self.invalid_json_content = "{ invalid json }"
        self.reference_data = [
            {
                "Name": "TestLibrary",
                "License": "MIT",
                "Version Number": "1.0.0",
                "Upstream URL": "http://example.com",
            }
        ]

    @patch("os.walk")
    @patch("builtins.open", new_callable=mock_open, read_data="")
    def test_validate_format_valid(self, mock_file, mock_os_walk):
        # 模拟 os.walk 返回一个 README.OpenSource 文件
        mock_os_walk.return_value = [(self.project_root, [], ["README.OpenSource"])]
        # 模拟打开文件并返回有效内容
        mock_file.return_value.read.return_value = self.readme_content_valid

        self.validator.run_validation(validate_format=True, validate_content=False)
        # 如果没有异常，则测试通过

    @patch("os.walk")
    @patch("builtins.open", new_callable=mock_open, read_data="")
    def test_validate_format_missing_fields(self, mock_file, mock_os_walk):
        mock_os_walk.return_value = [(self.project_root, [], ["README.OpenSource"])]
        mock_file.return_value.read.return_value = self.readme_content_missing_fields

        self.validator.run_validation(validate_format=True, validate_content=False)
        # 检查日志或假设如果出现异常，测试将失败

    @patch("os.walk")
    @patch("builtins.open", new_callable=mock_open, read_data="")
    def test_validate_format_invalid_json(self, mock_file, mock_os_walk):
        mock_os_walk.return_value = [(self.project_root, [], ["README.OpenSource"])]
        mock_file.return_value.read.return_value = self.invalid_json_content

        self.validator.run_validation(validate_format=True, validate_content=False)
        # 检查是否正确处理 JSON 解码错误

    @patch("os.walk")
    @patch("builtins.open", new_callable=mock_open)
    def test_validate_content_valid(self, mock_open_builtin, mock_os_walk):
        # 模拟 os.walk 返回一个 README.OpenSource 文件
        mock_os_walk.return_value = [(self.project_root, [], ["README.OpenSource"])]

        # 模拟打开文件并返回有效内容
        def side_effect_open(file, mode="r", encoding=None):
            if "README.OpenSource" in file:
                return mock_open(read_data=self.readme_content_valid)()
            elif "reference_data.json" in file:
                return mock_open(read_data=json.dumps(self.reference_data))()
            else:
                raise FileNotFoundError

        mock_open_builtin.side_effect = side_effect_open

        # 初始化验证器并加载参考数据
        self.validator.reference_data = self.reference_data

        # 模拟 os.path.exists 返回 True（表示许可证文件存在）
        with patch("os.path.exists", return_value=True):
            self.validator.run_validation(validate_format=False, validate_content=True)
            # 如果没有异常，则测试通过

    @patch("os.walk")
    @patch("builtins.open", new_callable=mock_open)
    def test_validate_content_license_file_missing(
        self, mock_open_builtin, mock_os_walk
    ):
        # 与上一个测试类似
        mock_os_walk.return_value = [(self.project_root, [], ["README.OpenSource"])]

        def side_effect_open(file, mode="r", encoding=None):
            if "README.OpenSource" in file:
                return mock_open(read_data=self.readme_content_valid)()
            elif "reference_data.json" in file:
                return mock_open(read_data=json.dumps(self.reference_data))()
            else:
                raise FileNotFoundError

        mock_open_builtin.side_effect = side_effect_open

        self.validator.reference_data = self.reference_data

        # 模拟 os.path.exists 返回 False（表示许可证文件不存在）
        with patch("os.path.exists", return_value=False):
            self.validator.run_validation(validate_format=False, validate_content=True)
            # 检查是否正确处理许可证文件缺失

    @patch("os.walk")
    @patch("builtins.open", new_callable=mock_open)
    def test_validate_content_field_mismatch(self, mock_open_builtin, mock_os_walk):
        # 修改 README 内容以包含不匹配的字段
        readme_content_mismatch = json.dumps(
            [
                {
                    "Name": "TestLibrary",
                    "License": "Apache-2.0",  # 应为 'MIT'
                    "License File": "LICENSE",
                    "Version Number": "1.0.0",
                    "Owner": "TestOwner",
                    "Upstream URL": "http://example.com",
                    "Description": "A test library.",
                }
            ]
        )

        mock_os_walk.return_value = [(self.project_root, [], ["README.OpenSource"])]

        def side_effect_open(file, mode="r", encoding=None):
            if "README.OpenSource" in file:
                return mock_open(read_data=readme_content_mismatch)()
            elif "reference_data.json" in file:
                return mock_open(read_data=json.dumps(self.reference_data))()
            else:
                raise FileNotFoundError

        mock_open_builtin.side_effect = side_effect_open

        self.validator.reference_data = self.reference_data

        # 模拟 os.path.exists 返回 True
        with patch("os.path.exists", return_value=True):
            self.validator.run_validation(validate_format=False, validate_content=True)
            # 检查是否正确处理字段不匹配


if __name__ == "__main__":
    unittest.main()
