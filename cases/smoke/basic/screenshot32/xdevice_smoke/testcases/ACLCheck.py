# -*- coding: utf-8 -*-
import os.path

from acls_check.acl_check import acl_check_main
from devicetest.api import Asserts

from test_case import ITestCase


class ACLCheck(ITestCase):

    def __init__(self, controllers):
        super().__init__(controllers)
        self.native_sa = os.path.join(os.path.dirname(self.testcases_path), 'acls_check', 'native_sa.log')

    def setup(self):
        self.step('前置条件1：ACL check 开始')

    def process(self):
        self.step('步骤1：clear native_sa.log first')
        # 先删除文件内容
        if os.path.exists(self.native_sa):
            self.step('{} exist, delete before test'.format(self.native_sa))
            with open(self.native_sa, 'w') as f:
                f.write('')
        self.step('步骤2：call acls_check.acl_check.py...')
        acl_check_main(self.device_name)
        self.step('步骤3：{} exist?:{}'.format(self.native_sa, os.path.exists(self.native_sa)))
        with open(self.native_sa, mode='r', encoding='utf-8', errors='ignore') as f:
            f.seek(0)
            acl_result = f.read()
        self.asserts.assert_not_in('ACL check failed', acl_result)

    def teardown(self):
        self.step('收尾：ACL check finish')
