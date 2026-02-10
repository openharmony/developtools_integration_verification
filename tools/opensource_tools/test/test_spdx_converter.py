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
Unit tests for SPDX License Converter.
"""

import unittest
from pathlib import Path
from src.spdx_converter import SPDXLicenseConverter


class TestSPDXLicenseConverter(unittest.TestCase):
    """Test cases for SPDXLicenseConverter."""

    def setUp(self):
        """Set up test fixtures."""
        # Use the default spdx.json path
        spdx_json = Path(__file__).parent.parent / "data" / "spdx.json"
        self.converter = SPDXLicenseConverter(str(spdx_json))

    def test_mit_variants(self):
        """Test MIT license variants."""
        test_cases = [
            ("MIT License", "MIT"),
            ("The MIT License", "MIT"),
            ("mit", "MIT"),
        ]
        for original, expected in test_cases:
            with self.subTest(original=original):
                result = self.converter.convert(original)
                self.assertEqual(result, expected)

    def test_apache_variants(self):
        """Test Apache license variants."""
        test_cases = [
            ("Apache License V2.0", "Apache-2.0"),
            ("Apache 2.0 License", "Apache-2.0"),
            ("Apache License 2.0", "Apache-2.0"),
            ("Apache V2", "Apache-2.0"),
            ("Apache-2.0", "Apache-2.0"),  # Already SPDX
        ]
        for original, expected in test_cases:
            with self.subTest(original=original):
                result = self.converter.convert(original)
                self.assertEqual(result, expected)

    def test_bsd_variants(self):
        """Test BSD license variants."""
        test_cases = [
            ("BSD 3-Clause License", "BSD-3-Clause"),
            ("BSD 3 License", "BSD-3-Clause"),
            ("BSD 2-Clause License", "BSD-2-Clause"),
        ]
        for original, expected in test_cases:
            with self.subTest(original=original):
                result = self.converter.convert(original)
                self.assertEqual(result, expected)

    def test_gpl_lgpl_variants(self):
        """Test GPL/LGPL license variants."""
        test_cases = [
            ("GPL V2.0", "GPL-2.0-only"),  # Converts to -only by default
            ("GPL V2", "GPL-2.0-only"),
            ("GPL-2.0", "GPL-2.0-only"),  # Adds -only suffix
            ("LGPL V2.1", "LGPL-2.1-only"),
            ("LGPL V2.0", "LGPL-2.0-only"),
            ("LGPL-2.1", "LGPL-2.1-only"),  # Adds -only suffix
        ]
        for original, expected in test_cases:
            with self.subTest(original=original):
                result = self.converter.convert(original)
                self.assertEqual(result, expected)

    def test_multiple_licenses(self):
        """Test multi-license strings."""
        test_cases = [
            ("Apache License V2.0, MIT", "Apache-2.0; MIT"),
            ("Apache License V2.0 / MIT", "Apache-2.0; MIT"),
            ("Apache License V2.0; MIT", "Apache-2.0; MIT"),
            ("Apache License V2.0 or MIT", "Apache-2.0; MIT"),
            ("Apache License V2.0 OR MIT", "Apache-2.0; MIT"),
        ]
        for original, expected in test_cases:
            with self.subTest(original=original):
                result = self.converter.convert(original)
                self.assertEqual(result, expected)

    def test_with_exception(self):
        """Test WITH exception licenses."""
        test_cases = [
            ("Apache-2.0 WITH LLVM-exception", "Apache-2.0 WITH LLVM-exception"),
            ("Apache-2.0_WITH_LLVM-exception", "Apache-2.0 WITH LLVM-exception"),
            ("GPL-2.0-with-GCC-exception", "GPL-2.0-with-GCC-exception"),
        ]
        for original, expected in test_cases:
            with self.subTest(original=original):
                result = self.converter.convert(original)
                self.assertEqual(result, expected)

    def test_public_domain(self):
        """Test public domain license."""
        result = self.converter.convert("Public domain")
        self.assertEqual(result, "0BSD")

    def test_unknown_license(self):
        """Test that unknown licenses are preserved."""
        result = self.converter.convert("Unknown Custom License")
        self.assertEqual(result, "Unknown Custom License")

    def test_null_and_none(self):
        """Test null and none values."""
        test_cases = ["null", "none", "None"]
        for value in test_cases:
            with self.subTest(value=value):
                result = self.converter.convert(value)
                self.assertEqual(result, value)

    def test_validate_spdx_id(self):
        """Test the validate_spdx_id method."""
        # Valid SPDX IDs
        self.assertTrue(self.converter.validate_spdx_id("MIT"))
        self.assertTrue(self.converter.validate_spdx_id("Apache-2.0"))
        self.assertTrue(self.converter.validate_spdx_id("GPL-2.0-only"))

        # Valid WITH exception format
        self.assertTrue(self.converter.validate_spdx_id("Apache-2.0 WITH LLVM-exception"))
        self.assertTrue(self.converter.validate_spdx_id("GPL-2.0-with-GCC-exception"))

        # Additional valid licenses (not in standard SPDX)
        self.assertTrue(self.converter.validate_spdx_id("Unicode-DFS-2022"))

        # Invalid SPDX IDs
        self.assertFalse(self.converter.validate_spdx_id("GPL-2.0"))
        self.assertFalse(self.converter.validate_spdx_id("LGPL-2.1"))
        self.assertFalse(self.converter.validate_spdx_id("Invalid-License"))

        # Invalid WITH exception format
        self.assertFalse(self.converter.validate_spdx_id("Apache-2.0 WITH Invalid-exception"))


if __name__ == "__main__":
    unittest.main()
