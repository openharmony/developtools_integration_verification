# -*- coding: utf-8 -*-
import os

from devicetest.api import Asserts
from devicetest.log.logger import print_info

from test_case import ITestCase


class NotificationBar(ITestCase):

    def __init__(self, controllers):
        super().__init__(controllers)

    def setup(self):
        self.step('前置条件1：回到桌面')
        self.common_oh.goHome(self.Phone1)
        self.step('前置条件2：检查当前界面是否在桌面')
        self.common_oh.checkIfTextExist(self.Phone1, '相机')

    def process(self):
        for i in range(2):
            try:
                self.step('步骤1：第 {} 次下拉控制中心'.format(i))
                self.common_oh.swipe(self.Phone1, x1=500, y1=0, x2=500, y2=80)
                self.common_oh.wait(self.Phone1, 2)
                # 控件检查
                #self.step('步骤2：检查文本"控制中心"是否存在')
                #self.common_oh.checkIfTextExist(self.Phone1, '控制中心')
                #self.common_oh.checkIfTextExist(self.Phone1, 'WLAN')
                #break
            except:
                if i == 1:
                    raise
        # 截图对比
        self.step('步骤3：控制中心截图对比')
        notification_pic = 'notification_bar.jpeg'
        self.take_picture_to_local(notification_pic)
        self.crop_picture(notification_pic)
        similarity = self.compare_image_similarity(notification_pic)
        print_info('相似度为：{}%'.format(similarity))
        self.asserts.assert_greater_equal(similarity, self.STANDARD_SIMILARITY)

    def teardown(self):
        self.step('收尾1：上滑收回控制中心')
        for i in range(2):
            self.step('第 {} 次上滑收起控制中心'.format(i))
            self.common_oh.swipe(self.Phone1, x1=500, y1=500, x2=500, y2=300)
            self.common_oh.wait(self.Phone1, 1)
