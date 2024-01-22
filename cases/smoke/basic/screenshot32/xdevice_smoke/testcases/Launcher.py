# -*- coding: utf-8 -*-
import os
import re
import sys

from devicetest.api import Asserts

from test_case import ITestCase
from xdevice import DeviceState


class Launcher(ITestCase):

    def __init__(self, controllers):
        super().__init__(controllers)

    def setup(self):
        self.step('SmokeTest start')
        super().setup()

    def process(self):
        normal = False
        for retry in range(3):
            self.common_oh.shell(self.Phone1, 'mkdir -p /data/local/tmp/screen_test/train_set')
            self.step('第 {} 次唤醒设备({})'.format(retry, self.device_name))
            self.common_oh.wake(self.Phone1)
            self.common_oh.goHome(self.Phone1)
            # 屏幕常亮
            self.common_oh.shell(self.Phone1, 'power-shell setmode 602')
            self.common_oh.wait(self.Phone1, 2)
            # 收集hilog
            self.collect_hilog('system_start_log_{}.tar'.format(self.device_name))
            # 检查设备是否连接
            assert self.Phone1.device_state == DeviceState.CONNECTED, AssertionError('device unconnected')
            self.step('device connected')
            # 检查屏幕点亮状态
            self.check_power_state()
            # 控件检查
            try:
                self.common_oh.checkIfTextExist(self.Phone1, '相机')
                self.common_oh.checkIfTextExist(self.Phone1, '备忘录')
                self.common_oh.checkIfTextExist(self.Phone1, 'SmartPerf')
                self.common_oh.checkIfTextExist(self.Phone1, '计算器')
                self.common_oh.checkIfTextExist(self.Phone1, '音乐')
                self.common_oh.checkIfTextExist(self.Phone1, '时钟')
                component_exist = True
            except:
                component_exist = False
            # 截图对比
            launcher_pic = 'launcher.jpeg'
            self.take_picture_to_local(launcher_pic)
            similarity = self.compare_image_similarity(launcher_pic)[0]
            self.step('{}和标准图的相似度为{}%'.format(launcher_pic, similarity))
            cmp_rst = similarity >= 60
            if component_exist and cmp_rst:
                normal = True
                break
            else:
                self.step('SmokeTest: launcher failed, reboot and try!!!')
                self.common_oh.shell(self.Phone1, 'rm -rf /data/*;reboot')
                self.common_oh.wait(self.Phone1, 50)
        if not normal:
            device_num = ''
            self.common_oh.shell(self.Phone1, 'cd /data/log/faultlog/temp && tar -cf after_test_cppcrash{}.tar cppcrash*'.format(device_num))
            self.common_oh.pullFile(self.Phone1, '/data/log/faultlog/temp/after_test_cppcrash{}.tar'.format(device_num), os.path.normpath(self.local_save_path))
            # fault logger
            self.common_oh.shell(self.Phone1, 'cd /data/log/faultlog/faultlogger && tar -cf after_test_jscrash{}.tar jscrash*'.format(device_num))
            self.common_oh.pullFile(self.Phone1, '/data/log/faultlog/faultlogger/after_test_jscrash{}.tar'.format(device_num), os.path.normpath(self.local_save_path))
            self.step('冒烟测试失败: 无法进系统或者进桌面主页检查出了问题!')
            self.step('结束冒烟测试!')
        Asserts.assert_true(normal)

    def check_power_state(self):
        power_state = self.common_oh.shell(self.Phone1, 'hidumper -s 3308')
        self.common_oh.wait(self.Phone1, 2)
        self.step('hidumper -s 3308 return: {}'.format(power_state))
        Asserts.assert_true(('State=1' in power_state) or ('State=2' in power_state))

    def teardown(self):
        self.common_oh.shell(self.Phone1, 'cat /proc/`pidof foundation`/smaps_rollup')
        self.step('Launcher finish')
        super().teardown()
