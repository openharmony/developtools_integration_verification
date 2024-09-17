import unittest
import os
import json
import shutil
from unittest.mock import patch
from src.generate_readme_opensource import generate_readme_opensource

class TestGenerateReadmeOpenSource(unittest.TestCase):

    def setUp(self):
        self.test_output_dir = 'test_output'
        if not os.path.exists(self.test_output_dir):
            os.makedirs(self.test_output_dir)

    def tearDown(self):
        if os.path.exists(self.test_output_dir):
            shutil.rmtree(self.test_output_dir)

    @patch('builtins.input', side_effect=[
        # First component
        'elfutils',  # Name
        'LGPL-2.1, LGPL-3.0, GPL-2.0',  # License
        'COPYING-GPLV2',  # License File
        '0.188',  # Version Number
        'zhanghaibo0@huawei.com',  # Owner
        'https://sourceware.org/elfutils/',  # Upstream URL
        'A collection of tools and libraries.',  # Description
        'y',  # Add another component
        # Second component
        'OpenSSL',  # Name
        'Apache-2.0',  # License
        'LICENSE',  # License File
        '1.1.1',  # Version Number
        'opensource@openssl.org',  # Owner
        'https://www.openssl.org/',  # Upstream URL
        'A robust, commercial-grade, full-featured toolkit for the TLS and SSL protocols.',  # Description
        'n'  # Do not add another component
    ])
    def test_generate_readme_opensource(self, mock_inputs):
        generate_readme_opensource(self.test_output_dir)
        readme_path = os.path.join(self.test_output_dir, 'README.OpenSource')
        self.assertTrue(os.path.exists(readme_path))

        with open(readme_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        expected_data = [
            {
                "Name": "elfutils",
                "License": "LGPL-2.1, LGPL-3.0, GPL-2.0",
                "License File": "COPYING-GPLV2",
                "Version Number": "0.188",
                "Owner": "zhanghaibo0@huawei.com",
                "Upstream URL": "https://sourceware.org/elfutils/",
                "Description": "A collection of tools and libraries."
            },
            {
                "Name": "OpenSSL",
                "License": "Apache-2.0",
                "License File": "LICENSE",
                "Version Number": "1.1.1",
                "Owner": "opensource@openssl.org",
                "Upstream URL": "https://www.openssl.org/",
                "Description": "A robust, commercial-grade, full-featured toolkit for the TLS and SSL protocols."
            }
        ]
        self.assertEqual(data, expected_data)

if __name__ == '__main__':
    unittest.main()

