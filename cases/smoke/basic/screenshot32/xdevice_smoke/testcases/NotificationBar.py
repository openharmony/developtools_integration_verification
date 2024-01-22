# -*- coding: utf-8 -*-
import os

from devicetest.api import Asserts

from test_case import ITestCase


class NotificationBar(ITestCase):

    def __init__(self, controllers):
        super().__init__(controllers)

    def setup(self):
        super().setup()
        self.step('预置条件：Notification Bar测试开始')

    def process(self):
        for i in range(2):
            self.step('步骤1：第 {} 次下拉控制中心'.format(i))
            self.common_oh.swipe(self.Phone1, x1=500, y1=0, x2=500, y2=80)
            self.common_oh.wait(self.Phone1, 1)
        self.common_oh.wait(self.Phone1, 5)
        self.step('步骤2：控制中心控件检查')
        # 控件检查
        self.common_oh.checkIfTextExist(self.Phone1, '控制中心')
        self.common_oh.checkIfTextExist(self.Phone1, 'WLAN')
        self.common_oh.checkIfTextExist(self.Phone1, '截屏')
        self.common_oh.checkIfTextExist(self.Phone1, '位置信息')
        self.common_oh.checkIfTextExist(self.Phone1, '飞行模式')
        self.common_oh.checkIfTypeExist(self.Phone1, 'Slider')
        # 截图对比
        self.step('步骤3：控制中心截图对比')
        notification_pic = 'notification_bar.jpeg'
        self.take_picture_to_local(notification_pic)
        self.crop_picture(notification_pic)
        similarity = self.compare_image_similarity(notification_pic)[0]
        self.step('{}和标准图的相似度为{}%'.format(notification_pic, similarity))
        Asserts.assert_greater_equal(similarity, self.STANDARD_SIMILARITY)

    def teardown(self):
        self.step('收尾：Notification Bar测试结束')
        for i in range(2):
            self.step('第 {} 次上滑收起控制中心'.format(i))
            self.common_oh.swipe(self.Phone1, x1=500, y1=500, x2=500, y2=300)
            self.common_oh.wait(self.Phone1, 1)
        # self.collect_hilog('NotificationBar.tar')
        super().teardown()
