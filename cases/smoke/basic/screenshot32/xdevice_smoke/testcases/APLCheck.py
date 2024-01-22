# -*- coding: utf-8 -*-
import os

from APL_compare_03.compare import apl_check_main
from devicetest.api import Asserts

from test_case import ITestCase


class APLCheck(ITestCase):

    def __init__(self, controllers):
        super().__init__(controllers)
        self.apl_path = os.path.join(os.path.dirname(self.testcases_path), 'APL_compare_03', 'apl_compare.log')

    def setup(self):
        self.step('APL check start')

    def process(self):
        self.step('clear apl_compare.log first')
        # 先删除文件内容
        if os.path.exists(self.apl_path):
            self.step('{} exist, delete before test'.format(self.apl_path))
            with open(self.apl_path, 'w') as f:
                f.write('')
        self.step('call APL_compare_03.compare.py ...')
        apl_check_main(self.device_name)
        self.step('{} exist?:{}'.format(self.apl_path, os.path.exists(self.apl_path)))
        with open(self.apl_path, mode='r', encoding='utf-8', errors='ignore') as f:
            f.seek(0)
            apl_result = f.read()
        Asserts.assert_not_in('APL Check failed', apl_result)

    def teardown(self):
        self.step('APL check finish')
