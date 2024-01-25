# -*- coding: utf-8 -*-
from devicetest.api import Asserts
from devicetest.log.logger import print_info

from test_case import ITestCase


class CrashCheck(ITestCase):

    def __init__(self, controllers):
        super().__init__(controllers)

    def setup(self):
        self.step('前置条件1：开始crash测试')
        self.common_oh.remount(self.Phone1)
        self.common_oh.wait(self.Phone1, 1)

    def process(self):
        self.step('步骤1：获取crash信息')
        crashes = self.common_oh.shell(self.Phone1, 'cd /data/log/faultlog/temp && grep "Process name" -rnw ./')
        print_info('crashes: {}'.format(crashes))
        self.common_oh.wait(self.Phone1, 1)
        self.asserts.assert_not_in('foundation', crashes)
        self.asserts.assert_not_in('render_service', crashes)
        self.asserts.assert_not_in('appspawn', crashes)

    def teardown(self):
        self.step('收尾1：将crash文件压缩打包后回传到本地')
        self.common_oh.shell(self.Phone1, 'cd /data/log/faultlog/temp && tar -cf crash_log.tar cppcrash*')
        self.common_oh.pullFile(self.Phone1, '/data/log/faultlog/temp/crash_log.tar', self.local_save_path)
