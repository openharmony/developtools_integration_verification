# -*- coding: utf-8 -*-
import os
import re
import sys

from devicetest.api import Asserts
from devicetest.aw.OpenHarmony import DeviceInfoHelper
from devicetest.log.logger import print_info

from test_case import ITestCase
from xdevice import DeviceState


class Launcher(ITestCase):

    def __init__(self, controllers):
        super().__init__(controllers)

    def setup(self):
        pass

    def process(self):
        for retry in range(3):
            try:
                self.step('步骤1.{}：点亮屏幕'.format(retry))
                self.common_oh.wake(self.Phone1)
                self.step('步骤2.{}：回到桌面'.format(retry))
                self.common_oh.goHome(self.Phone1)
                self.common_oh.wait(self.Phone1, 1)
                self.step('步骤3.{}：创建临时目录'.format(retry))
                self.common_oh.shell(self.Phone1, 'mkdir -p /data/local/tmp/screen_test/train_set')
                # 屏幕常亮
                self.step('步骤4{}：设置屏幕常亮'.format(retry))
                DeviceInfoHelper.setSleep(self.Phone1, time_sleep=600)
                # self.common_oh.shell(self.Phone1, 'power-shell setmode 602')
                # # 检查屏幕点亮状态
                # power_state = self.common_oh.shell(self.Phone1, 'hidumper -s 3308')
                # # self.common_oh.wait(self.Phone1, 2)
                # self.step('步骤5：检查屏幕状态')
                # self.asserts.assert_in('State=2', power_state)
                # 控件检查
                self.step('步骤5.{}：检查是否在桌面'.format(retry))
                self.common_oh.checkIfTextExist(self.Phone1, '相机')
                self.common_oh.checkIfTextExist(self.Phone1, '音乐')
                # 截图对比
                self.step('步骤6.{}：截图对比'.format(retry))
                launcher_pic = 'launcher.jpeg'
                self.take_picture_to_local(launcher_pic)
                similarity = self.compare_image_similarity(launcher_pic)
                print_info('相似度为：{}%'.format(similarity))
                self.asserts.assert_greater_equal(similarity, self.STANDARD_SIMILARITY)
                break
            except:
                if retry < 2:
                    self.step('步骤7.{}：启动失败，重启设备，重试'.format(retry))
                    self.common_oh.shell(self.Phone1, 'rm -rf /data/*')
                    self.common_oh.safeReboot(self.Phone1)
                    # for i in range(5):
                    #     try:
                    #         print_info('检查屏幕是否已点亮')
                    #         self.common_oh.getScreenStatus(self.Phone1)
                    #         break
                    #     except:
                    #         self.common_oh.wait(self.Phone1, 14)
                else:
                    self.step('步骤8.{}：重试了3次，启动失败，收集crash'.format(retry))
                    self.common_oh.shell(self.Phone1, 'cd /data/log/faultlog/temp && tar -cf after_test_cppcrash{}.tar cppcrash*'.format(self.device_name))
                    self.common_oh.pullFile(self.Phone1, '/data/log/faultlog/temp/after_test_cppcrash{}.tar'.format(self.device_name), os.path.normpath(self.local_save_path))
                    # fault logger
                    self.common_oh.shell(self.Phone1, 'cd /data/log/faultlog/faultlogger && tar -cf after_test_jscrash{}.tar jscrash*'.format(self.device_name))
                    self.common_oh.pullFile(self.Phone1, '/data/log/faultlog/faultlogger/after_test_jscrash{}.tar'.format(self.device_name), os.path.normpath(self.local_save_path))
                    raise

    def teardown(self):
        self.step('收尾动作1：cat /proc/`pidof foundation`/smaps_rollup')
        self.common_oh.shell(self.Phone1, 'cat /proc/`pidof foundation`/smaps_rollup')
