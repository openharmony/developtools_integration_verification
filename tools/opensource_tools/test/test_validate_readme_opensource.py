#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2024 Huawei Device Co., Ltd.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Unit tests for validate_readme_opensource.py.
"""

import unittest
from unittest.mock import patch, MagicMock
from src.validate_readme_opensource import OpenSourceValidator, REQUIRED_FIELDS


class TestOpenSourceValidator(unittest.TestCase):
    """Test cases for OpenSourceValidator."""

    @patch("os.walk")
    def test_find_all_readmes(self, mock_os_walk):
        """Test finding all README.OpenSource files."""
        mock_os_walk.return_value = [
            ("/project", ["subdir1", "subdir2"], ["README.OpenSource"]),
            ("/project/subdir1", [], ["README.OpenSource"]),
            ("/project/subdir2", [], ["README.OpenSource"]),
        ]

        validator = OpenSourceValidator(project_root="/project")
        readme_paths = validator.find_all_readmes()

        self.assertEqual(readme_paths, [
            "/project/README.OpenSource",
            "/project/subdir1/README.OpenSource",
            "/project/subdir2/README.OpenSource"
        ])

    @patch("builtins.open", new_callable=MagicMock)
    def test_validate_format_valid(self, mock_open):
        """Test format validation with valid data."""
        mock_open.return_value.__enter__.return_value.read.return_value = MagicMock(
            return_value='[{"Name": "Software A", "License": "MIT", '
            '"License File": "LICENSE", "Version Number": "1.0.0", '
            '"Owner": "Owner A", "Upstream URL": "https://example.com", '
            '"Description": "A software project", "Dependencies": []}]'
        )

        validator = OpenSourceValidator(project_root="/project")
        # Mock JSON load
        with patch("json.load", return_value=[
            {
                "Name": "Software A",
                "License": "MIT",
                "License File": "LICENSE",
                "Version Number": "1.0.0",
                "Owner": "Owner A",
                "Upstream URL": "https://example.com",
                "Description": "A software project",
                "Dependencies": []
            }
        ]):
            valid = validator.validate_format("/project/README.OpenSource")

        self.assertTrue(valid)

    @patch("builtins.open", new_callable=MagicMock)
    def test_validate_format_invalid_missing_field(self, mock_open):
        """Test format validation with missing required field."""
        mock_open.return_value.__enter__.return_value.read.return_value = MagicMock(
            return_value='[{"Name": "Software A", "License": "MIT", '
            '"License File": "LICENSE", "Version Number": "1.0.0", '
            '"Owner": "Owner A", "Upstream URL": "https://example.com", '
            '"Dependencies": []}]'
        )

        validator = OpenSourceValidator(project_root="/project")
        # Mock JSON load
        with patch("json.load", return_value=[
            {
                "Name": "Software A",
                "License": "MIT",
                "License File": "LICENSE",
                "Version Number": "1.0.0",
                "Owner": "Owner A",
                "Upstream URL": "https://example.com",
                # Missing "Description" field
                "Dependencies": []
            }
        ]):
            valid = validator.validate_format("/project/README.OpenSource")

        self.assertFalse(valid)

    @patch("builtins.open", new_callable=MagicMock)
    @patch("os.path.exists", return_value=True)
    def test_validate_content_valid_without_file_check(self, mock_exists, mock_open):
        """Test content validation without checking license files."""
        mock_open.return_value.__enter__.return_value.read.return_value = MagicMock(
            return_value='[{"Name": "Software A", "License": "MIT", '
            '"License File": "LICENSE", "Version Number": "1.0.0", '
            '"Owner": "Owner A", "Upstream URL": "https://example.com", '
            '"Description": "A software project", "Dependencies": []}]'
        )

        reference_data = [
            {
                "Name": "Software A",
                "License": "MIT",
                "License File": "LICENSE",
                "Version Number": "1.0.0",
                "Owner": "Owner A",
                "Upstream URL": "https://example.com",
                "Description": "A software project"
            }
        ]

        validator = OpenSourceValidator(project_root="/project")
        validator.reference_data = reference_data

        # Mock JSON load
        with patch("json.load", return_value=[
            {
                "Name": "Software A",
                "License": "MIT",
                "License File": "LICENSE",
                "Version Number": "1.0.0",
                "Owner": "Owner A",
                "Upstream URL": "https://example.com",
                "Description": "A software project",
                "Dependencies": []
            }
        ]):
            valid = validator.validate_content("/project/README.OpenSource")

        self.assertTrue(valid)

    @patch("builtins.open", new_callable=MagicMock)
    @patch("os.path.exists", return_value=True)
    def test_validate_content_valid_with_file_check(self, mock_exists, mock_open):
        """Test content validation with license file check."""
        mock_open.return_value.__enter__.return_value.read.return_value = MagicMock(
            return_value='[{"Name": "Software A", "License": "MIT", '
            '"License File": "LICENSE", "Version Number": "1.0.0", '
            '"Owner": "Owner A", "Upstream URL": "https://example.com", '
            '"Description": "A software project", "Dependencies": []}]'
        )

        reference_data = [
            {
                "Name": "Software A",
                "License": "MIT",
                "License File": "LICENSE",
                "Version Number": "1.0.0",
                "Owner": "Owner A",
                "Upstream URL": "https://example.com",
                "Description": "A software project"
            }
        ]

        validator = OpenSourceValidator(project_root="/project")
        validator.reference_data = reference_data

        # Mock JSON load
        with patch("json.load", return_value=[
            {
                "Name": "Software A",
                "License": "MIT",
                "License File": "LICENSE",
                "Version Number": "1.0.0",
                "Owner": "Owner A",
                "Upstream URL": "https://example.com",
                "Description": "A software project",
                "Dependencies": []
            }
        ]):
            valid = validator.validate_content("/project/README.OpenSource")

        self.assertTrue(valid)

    @patch("os.path.exists")
    def test_validate_license_file_valid(self, mock_exists):
        """Test license file validation when file exists."""
        mock_exists.return_value = True

        validator = OpenSourceValidator(project_root="/project")
        valid = validator.validate_license_file("/project/README.OpenSource", "LICENSE")

        self.assertTrue(valid)

    @patch("os.path.exists")
    def test_validate_license_file_invalid(self, mock_exists):
        """Test license file validation when file does not exist."""
        mock_exists.return_value = False

        validator = OpenSourceValidator(project_root="/project")
        valid = validator.validate_license_file("/project/README.OpenSource", "LICENSE")

        self.assertFalse(valid)

    @patch("builtins.open", new_callable=MagicMock)
    @patch("os.path.exists")
    def test_validate_dependencies_valid(self, mock_exists, mock_open):
        """Test dependencies validation with valid dependencies."""
        mock_open.return_value.__enter__.return_value.read.return_value = MagicMock(
            return_value='[{"Name": "Software A", "License": "MIT", '
            '"License File": "LICENSE", "Version Number": "1.0.0", '
            '"Owner": "Owner A", "Upstream URL": "https://example.com", '
            '"Description": "A software project", '
            '"Dependencies": ["dep1", "dep2"]}]'
        )
        mock_exists.return_value = True

        validator = OpenSourceValidator(project_root="/project")

        # Mock JSON load
        with patch("json.load", return_value=[
            {
                "Name": "Software A",
                "License": "MIT",
                "License File": "LICENSE",
                "Version Number": "1.0.0",
                "Owner": "Owner A",
                "Upstream URL": "https://example.com",
                "Description": "A software project",
                "Dependencies": ["dep1", "dep2"]
            }
        ]):
            valid = validator.validate_dependencies(["dep1", "dep2"], "/project/README.OpenSource")

        self.assertTrue(valid)

    @patch("builtins.open", new_callable=MagicMock)
    def test_validate_dependencies_invalid(self, mock_open):
        """Test dependencies validation with invalid dependencies."""
        mock_open.return_value.__enter__.return_value.read.return_value = MagicMock(
            return_value='[{"Name": "Software A", "License": "MIT", '
            '"License File": "LICENSE", "Version Number": "1.0.0", '
            '"Owner": "Owner A", "Upstream URL": "https://example.com", '
            '"Description": "A software project", '
            '"Dependencies": ["dep1", 123]}]'
        )

        validator = OpenSourceValidator(project_root="/project")

        # Mock JSON load
        with patch("json.load", return_value=[
            {
                "Name": "Software A",
                "License": "MIT",
                "License File": "LICENSE",
                "Version Number": "1.0.0",
                "Owner": "Owner A",
                "Upstream URL": "https://example.com",
                "Description": "A software project",
                "Dependencies": ["dep1", 123]  # Non-string dependency
            }
        ]):
            valid = validator.validate_dependencies(["dep1", 123], "/project/README.OpenSource")

        self.assertFalse(valid)


if __name__ == "__main__":
    unittest.main()
