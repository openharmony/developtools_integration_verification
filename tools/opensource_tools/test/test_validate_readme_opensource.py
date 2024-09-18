# test/test_validate_readme_opensource.py

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import os
import json
import shutil
from src.validate_readme_opensource import validate_readme_opensource

class TestValidateReadmeOpenSource(unittest.TestCase):

    def setUp(self):
        self.test_dir = 'test_validate'
        if not os.path.exists(self.test_dir):
            os.makedirs(self.test_dir)
        self.valid_readme = [
            {
                "Name": "elfutils",
                "License": "LGPL-2.1, LGPL-3.0, GPL-2.0",
                "License File": "COPYING-GPLV2",
                "Version Number": "0.188",
                "Owner": "zhanghaibo0@huawei.com",
                "Upstream URL": "https://sourceware.org/elfutils/",
                "Description": "A collection of tools and libraries."
            }
        ]
        self.invalid_readme = [
            {
                "Name": "elfutils",
                "License": "LGPL-2.1, LGPL-3.0, GPL-2.0",
                # Missing 'License File'
                "Version Number": "0.188",
                "Owner": "zhanghaibo0@huawei.com",
                "Upstream URL": "https://sourceware.org/elfutils/",
                "Description": "A collection of tools and libraries."
            }
        ]
        self.valid_path = os.path.join(self.test_dir, 'valid_README.OpenSource')
        self.invalid_path = os.path.join(self.test_dir, 'invalid_README.OpenSource')

        with open(self.valid_path, 'w', encoding='utf-8') as f:
            json.dump(self.valid_readme, f, indent=2, ensure_ascii=False)

        with open(self.invalid_path, 'w', encoding='utf-8') as f:
            json.dump(self.invalid_readme, f, indent=2, ensure_ascii=False)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_validate_valid_readme(self):
        valid, errors = validate_readme_opensource(self.valid_path)
        self.assertTrue(valid)
        self.assertEqual(len(errors), 0)

    def test_validate_invalid_readme(self):
        valid, errors = validate_readme_opensource(self.invalid_path)
        self.assertFalse(valid)
        self.assertIn("Component 1 is missing required field: License File", errors)

if __name__ == '__main__':
    unittest.main()
