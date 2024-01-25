# -*- coding: utf-8 -*-
import os

from test_case import ITestCase


class ProcessCheck(ITestCase):

    def __init__(self, controllers):
        super().__init__(controllers)

    def setup(self):
        self.step('前置条件1: 检查process.txt配置文件是否存在')
        self.asserts.assert_true(os.path.exists(os.path.join(self.local_resource_path, 'process.txt')))

    def process(self):
        self.step('步骤1: 检查process是否存在')
        with open(os.path.join(self.local_resource_path, 'process.txt'), 'r+') as f:
            text = f.read()
            two_check_process_list = text.split('#####')[1].split()[0:-1]
            other_process_list = text.split('#####')[2].split()
        lose_process = []
        for pname in two_check_process_list:
            pids = self.common_oh.shell(self.Phone1, 'pidof {}'.format(pname))
            try:
                pidlist = pids.split()
                for pid in pidlist:
                    int(pid)
                    self.step('{} pid is {}'.format(pname, pid))
            except:
                lose_process.append(pname)
            self.common_oh.wait(self.Phone1, 1)

        all_p = self.common_oh.shell(self.Phone1, 'ps -elf')
        for pname in other_process_list:
            if pname not in all_p:
                lose_process.append(pname)
        try:
            self.asserts.assert_true(len(lose_process) == 0)
        except:
            self.step('步骤2:丢失的进程有: {}'.format(lose_process))
            self.common_oh.shell(self.Phone1, 'cd /data/log/faultlog/temp && tar -cf after_test_cppcrash{}.tar cppcrash*'.format(self.device_name))
            self.common_oh.pullFile(self.Phone1, '/data/log/faultlog/temp/after_test_cppcrash{}.tar'.format(self.device_name), os.path.normpath(self.local_save_path))
            # fault logger
            self.common_oh.shell(self.Phone1, 'cd /data/log/faultlog/faultlogger && tar -cf after_test_jscrash{}.tar jscrash*'.format(self.device_name))
            self.common_oh.pullFile(self.Phone1, '/data/log/faultlog/faultlogger/after_test_jscrash{}.tar'.format(self.device_name), os.path.normpath(self.local_save_path))
            self.step('步骤2: 冒烟测试失败，丢失的进程有: {}'.format(lose_process))
            raise

    def teardown(self):
        self.step('后置条件1: 进程检查结束')
