# -*- coding: utf-8 -*-
import os

from devicetest.api import Asserts
from devicetest.log.logger import print_info

from test_case import ITestCase


class Mms(ITestCase):
    ability_name = 'com.ohos.mms.MainAbility'
    bundle_name = 'com.ohos.mms'

    def __init__(self, controllers):
        super().__init__(controllers)

    def setup(self):
        self.step('前置条件1：回到桌面')
        self.common_oh.goHome(self.Phone1)
        self.step('前置条件2：检查当前界面是否在桌面')
        self.common_oh.checkIfTextExist(self.Phone1, '相机')


    def process(self):
        self.step('步骤1：启动短信应用')
        self.common_oh.startAbility(self.Phone1, self.ability_name, self.bundle_name)
        # self.common_oh.wait(self.Phone1, 5)
        self.step('步骤2：检查"信息"是否存在')
        # 控件检查
        self.common_oh.checkIfTextExist(self.Phone1, '信息')
        # 截图对比
        self.step('步骤2：短信截图对比')
        mms_pic = 'mms.jpeg'
        self.take_picture_to_local(picture_name=mms_pic)
        self.crop_picture(mms_pic)
        similarity = self.compare_image_similarity(mms_pic)
        print_info('相似度为：{}%'.format(similarity))
        self.asserts.assert_greater_equal(similarity, self.STANDARD_SIMILARITY)

    def teardown(self):
        self.step('收尾1：停掉短信应用')
        self.common_oh.forceStopAbility(self.Phone1, self.bundle_name)
