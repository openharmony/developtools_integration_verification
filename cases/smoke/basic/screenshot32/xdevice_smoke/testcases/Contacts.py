# -*- coding: utf-8 -*-
import os

from devicetest.api import Asserts

from test_case import ITestCase


class Contacts(ITestCase):
    ability_name = 'com.ohos.contacts.MainAbility'
    bundle_name = 'com.ohos.contacts'

    def __init__(self, controllers):
        super().__init__(controllers)

    def setup(self):
        super().setup()
        self.step('contacts test start, start app')
        self.common_oh.startAbility(self.Phone1, self.ability_name, self.bundle_name)

    def process(self):
        self.common_oh.wait(self.Phone1, 5)
        # 控件检查
        self.step('contacts 控件检查')
        self.common_oh.checkIfTextExist(self.Phone1, '全部通话')
        self.common_oh.checkIfTextExist(self.Phone1, '未接来电')
        self.common_oh.checkIfTextExist(self.Phone1, '1')
        self.common_oh.checkIfTextExist(self.Phone1, '5')
        self.common_oh.checkIfTextExist(self.Phone1, '9')
        self.common_oh.checkIfTextExist(self.Phone1, '联系人')
        self.common_oh.checkIfTextExist(self.Phone1, '收藏')
        self.step('contacts截图对比')
        # 截图对比
        contacts_pic = 'contacts.jpeg'
        self.take_picture_to_local(contacts_pic)
        self.crop_picture(contacts_pic)
        similarity = self.compare_image_similarity(contacts_pic)[0]
        self.step('{}和标准图的相似度为{}%'.format(contacts_pic, similarity))
        Asserts.assert_greater_equal(similarity, self.STANDARD_SIMILARITY)

    def teardown(self):
        self.common_oh.forceStopAbility(self.Phone1, self.bundle_name)
        # self.collect_hilog('contacts.tar')
        self.step('contacts test finish')
        super().teardown()
