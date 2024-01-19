# -*- coding: utf-8 -*-
import os
import sys

from devicetest.api import Asserts

from test_case import ITestCase


class ProcessCheck(ITestCase):

    def __init__(self, controllers):
        super().__init__(controllers)

    def setup(self):
        super().setup()
        self.step('SmokeTest: ########## First check key processes start ##############')

    def process(self):
        Asserts.assert_true(os.path.exists(os.path.join(self.local_resource_path, 'process.txt')))
        self.step('get process.txt content')
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
        self.step('lose process is: {}'.format(lose_process))
        if lose_process:
            self.step('SmokeTest: error: {}, These processes do not exist!!!'.format(lose_process))
            device_num = ''
            self.common_oh.shell(self.Phone1, 'cd /data/log/faultlog/temp && tar -cf after_test_cppcrash{}.tar cppcrash*'.format(device_num))
            self.common_oh.pullFile(self.Phone1, '/data/log/faultlog/temp/after_test_cppcrash{}.tar'.format(device_num), os.path.normpath(self.local_save_path))
            # fault logger
            self.common_oh.shell(self.Phone1, 'cd /data/log/faultlog/faultlogger && tar -cf after_test_jscrash{}.tar jscrash*'.format(device_num))
            self.common_oh.pullFile(self.Phone1, '/data/log/faultlog/faultlogger/after_test_jscrash{}.tar'.format(device_num), os.path.normpath(self.local_save_path))
            self.step('SmokeTest: SmokeTest find some key problems!')
            self.step('SmokeTest: End of check, test failed!')
            Asserts.assert_true(len(lose_process) == 0)
        self.step('process check pass')

    def teardown(self):
        self.step('SmokeTest: first processes check is ok')
        super().teardown()
