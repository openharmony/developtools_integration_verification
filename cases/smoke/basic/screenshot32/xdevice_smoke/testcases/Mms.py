# -*- coding: utf-8 -*-
import os

from devicetest.api import Asserts

from test_case import ITestCase


class Mms(ITestCase):
    ability_name = 'com.ohos.mms.MainAbility'
    bundle_name = 'com.ohos.mms'

    def __init__(self, controllers):
        super().__init__(controllers)

    def setup(self):
        super().setup()
        self.step('MMS test start, start app')
        self.common_oh.startAbility(self.Phone1, self.ability_name, self.bundle_name)

    def process(self):
        self.common_oh.wait(self.Phone1, 5)
        self.step('控件检查')
        # 控件检查
        self.common_oh.checkIfTextExist(self.Phone1, '信息')
        self.common_oh.checkIfTextExist(self.Phone1, '没有会话信息')
        # 截图对比
        self.step('mms 截图对比')
        mms_pic = 'mms.jpeg'
        self.take_picture_to_local(picture_name=mms_pic)
        self.crop_picture(mms_pic)
        similarity = self.compare_image_similarity(mms_pic)[0]
        self.step('{}和标准图的相似度为{}%'.format(mms_pic, similarity))
        Asserts.assert_greater_equal(similarity, self.STANDARD_SIMILARITY)

    def teardown(self):
        self.common_oh.forceStopAbility(self.Phone1, self.bundle_name)
        self.step('MMS test finish')
        super().teardown()
