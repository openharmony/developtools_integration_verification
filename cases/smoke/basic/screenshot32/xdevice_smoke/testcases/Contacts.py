# -*- coding: utf-8 -*-
import os

from devicetest.api import Asserts
from devicetest.log.logger import print_info

from test_case import ITestCase


class Contacts(ITestCase):
    ability_name = 'com.ohos.contacts.MainAbility'
    bundle_name = 'com.ohos.contacts'

    def __init__(self, controllers):
        super().__init__(controllers)

    def setup(self):
        self.step('前置条件1：回到桌面')
        self.common_oh.goHome(self.Phone1)
        self.step('前置条件2：检查当前界面是否在桌面')
        self.common_oh.checkIfTextExist(self.Phone1, '相机')


    def process(self):
        self.step('步骤1：启动联系人应用')
        self.common_oh.startAbility(self.Phone1, self.ability_name, self.bundle_name)
        # self.common_oh.wait(self.Phone1, 5)
        # 控件检查
        self.step('步骤2：检查是否进入联系人')
        self.common_oh.checkIfTextExist(self.Phone1, '电话')
        self.common_oh.checkIfTextExist(self.Phone1, '5')
        self.common_oh.checkIfTextExist(self.Phone1, '联系人')
        self.step('步骤3：联系人截图对比')
        # 截图对比
        contacts_pic = 'contacts.jpeg'
        self.take_picture_to_local(contacts_pic)
        self.crop_picture(contacts_pic)
        similarity = self.compare_image_similarity(contacts_pic)
        print_info('相似度为：{}%'.format(similarity))
        self.asserts.assert_greater_equal(similarity, self.STANDARD_SIMILARITY)

    def teardown(self):
        self.step('收尾1：停掉联系人应用')
        self.common_oh.forceStopAbility(self.Phone1, self.bundle_name)
